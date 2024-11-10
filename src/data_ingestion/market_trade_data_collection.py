import logging
import time
from http.client import HTTPException
from typing import Dict, Generator, List, Optional

import pandas as pd
import yfinance as yf  # type: ignore
from pandas import DataFrame
from requests import Timeout
from tenacity import retry, retry_if_exception_type, wait_exponential, \
    stop_after_attempt

from config.sentry_config import init_sentry
from utils.data_models import DataTradedObject, OHLCV
from utils.db_helpers import get_all_traded_objects_from_db, get_market_trade_data, \
    save_trade_market_data_in_db
from utils.enums import YFinanceIntervals, TradeTimeWindow, YFinanceTime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

BATCH_SIZE_BACK_FILL = 100
BATCH_SIZE_DEFAULT = 500


class MarketTradeDataCollector:
    """ Collects and updates market trade data in the database. """

    CALL_WAIT_TIME_SECONDS = 2
    LOOKBACK_PERIOD_BACK_FILL = 60 * 60 * 24 * 20
    MAX_RETRY = 3
    MIN_RETRY_WAIT_TIME = 2
    MAX_RETRY_WAIT_TIME = 10

    def __init__(self):
        try:
            self.symbols_to_update_map: Dict[str, DataTradedObject] = (
                self._get_symbols_to_update_strings())
            self.batch_size: int = BATCH_SIZE_DEFAULT
            logger.info("MarketTradeDataCollector initialised successfully.")
        except Exception as e:
            logger.error(f"Failed to initialise MarketTradeDataCollector: {e}")
            raise

    def collect_save_trade_market_data(self,
                                       period: YFinanceIntervals,
                                       time_window: TradeTimeWindow,
                                       batch_size: int) -> None:

        self.batch_size = batch_size
        total_batches = int(len(self.symbols_to_update_map) / self.batch_size)

        for batch_index, symbols_batch in enumerate(self._build_symbol_batches()):
            logger.info(f"Processing batch {batch_index + 1} of "
                        f"{total_batches} "
                        f"with {len(symbols_batch)} symbols.")
            try:
                self._process_batch(symbols_batch, period, time_window)
            except Exception as e:
                logger.error(f"Error processing batch {batch_index + 1} "
                             f"of {total_batches}: {e}")
                continue

    def _process_batch(self, symbols_batch: List[str], period: YFinanceIntervals,
                       time_window: TradeTimeWindow) -> None:
        try:
            current_data = get_market_trade_data(symbols=symbols_batch,
                                                 period=period,
                                                 time_window=time_window)
        except Exception as e:
            logger.error(f"Error retrieving current data for symbols batch: {e}")
            return

        symbols_batch = self._clean_existing_symbols(symbols=symbols_batch,
                                                     current_data=current_data)

        try:
            fetched_data = self._fetch_yfinance_data(symbols=symbols_batch,
                                                     time_window=time_window)
        except Exception as e:
            logger.error(f"Error fetching data from yfinance for batch: {e}")
            return

        current_data = current_data[current_data['symbol'].isin(symbols_batch)]
        merged_data = self._merge_and_clean_data(new_data=fetched_data,
                                                 existing_data=current_data)

        try:
            symbols_to_update = (
                self._prepare_symbols_for_update(data=merged_data,
                                                 time_window=time_window))
            save_trade_market_data_in_db(symbols_to_update)
            logger.info("Batch saved successfully to database.")
        except Exception as e:
            logger.error(f"Error saving batch data to database: {e}")

    def _clean_existing_symbols(self, symbols: List[str],
                                current_data: DataFrame) -> List[str]:
        try:
            time_threshold = int(time.time() - self.LOOKBACK_PERIOD_BACK_FILL)

            already_present_symbols = current_data[
                current_data['open_date'] <= time_threshold]['symbol'].unique().tolist()

            return list(set(symbols).difference(set(already_present_symbols)))
        except Exception as e:
            logger.error(f"Error cleaning existing symbols: {e}")
            return symbols  # Return all symbols in case of error

    @staticmethod
    @retry(
        retry=retry_if_exception_type((HTTPException, Timeout)),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_TIME,
                              max=MAX_RETRY_WAIT_TIME),
        stop=stop_after_attempt(MAX_RETRY),
        reraise=True
    )
    def _fetch_yfinance_data(symbols: List[str],
                             time_window: TradeTimeWindow) -> DataFrame:

        df = yf.download(symbols,
                         period='max',
                         interval=time_window.value.yfinance_notation,
                         group_by='ticker')
        df = df.stack(level=0).reset_index().rename(columns={"level_1": "symbol"})
        df["open_date"] = df["Date"].apply(lambda x: int(x.timestamp()))
        df["time_window"] = time_window.value.yfinance_notation
        df = df[["Ticker", 'open_date', "Open",
                 "High", "Low", "Close", "Volume", "time_window"]].rename(
            columns={"Open": "open", "High": "high", "Low": "low", "Close": "close",
                     "Volume": "volume", "Ticker": "symbol"}
        )
        logger.info(f"Successfully fetched data for {len(symbols)} symbols.")
        return df

    @staticmethod
    def _merge_and_clean_data(new_data: DataFrame,
                              existing_data: DataFrame) -> DataFrame:
        combined_data = pd.concat([new_data, existing_data], ignore_index=True)
        return combined_data.drop_duplicates(subset=['symbol', 'time_window',
                                                     'open_date'],
                                             keep=False)

    def _prepare_symbols_for_update(
            self,
            data: DataFrame,
            time_window: TradeTimeWindow) -> List[DataTradedObject]:

        symbols_to_update = list()

        # Make a copy of the symbol keys to avoid modifying the dictionary
        # during iteration
        symbols_copy = list(self.symbols_to_update_map.keys())

        grouped_data = data.groupby('symbol')
        for symbol, group in grouped_data:

            if symbol not in symbols_copy:
                continue  # Skip any symbols not in the original map

            list_ohlcv = [OHLCV(
                symbol=str(symbol),
                time_window=time_window,
                open=ohlcv['open'],
                high=ohlcv['high'],
                low=ohlcv['low'],
                close=ohlcv['close'],
                volume=ohlcv['volume'],
                open_date=ohlcv['open_date']
            ) for _, ohlcv in group.iterrows()]

            data_object = self.symbols_to_update_map[str(symbol)]
            data_object.ohlcv_list = list_ohlcv
            symbols_to_update.append(data_object)
        return symbols_to_update

    def _build_symbol_batches(self) -> Generator[List[str], None, None]:
        keys_list = list(self.symbols_to_update_map.keys())
        for i in range(0, len(keys_list), self.batch_size):
            yield keys_list[i:i + self.batch_size]

    @staticmethod
    def _get_symbols_to_update_strings() -> Dict[str, DataTradedObject]:
        traded_objects = get_all_traded_objects_from_db()
        traded_objects_map = {traded_object.symbol: DataTradedObject(
            traded_object=traded_object, ohlcv_list=list())
                              for traded_object in traded_objects}
        return traded_objects_map


def back_fill_trade_market_data():
    init_sentry()
    collector = MarketTradeDataCollector()
    collector.collect_save_trade_market_data(
        period=YFinanceIntervals.FIVE_YEARS,
        time_window=TradeTimeWindow.DAILY,
        batch_size=BATCH_SIZE_BACK_FILL
    )


def collect_save_new_market_data():
    init_sentry()
    collector = MarketTradeDataCollector()
    collector.collect_save_trade_market_data(
        period=YFinanceIntervals.ONE_MONTH,
        time_window=TradeTimeWindow.DAILY,
        batch_size=BATCH_SIZE_DEFAULT
    )


if __name__ == '__main__':
    back_fill_trade_market_data()
