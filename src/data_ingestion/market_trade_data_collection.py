import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Generator, List

import pandas as pd
import yfinance as yf  # type: ignore
from pandas import DataFrame

from config.sentry_config import init_sentry
from utils.data_models import DataTradedObject, OHLCV
from utils.db_helpers import get_all_traded_objects_from_db, get_market_trade_data, \
    save_trade_market_data_in_db
from utils.enums import YFinanceIntervals, TradeTimeWindow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketTradeDataCollector:
    """ Collects and updates market trade data in the database. """

    CALL_WAIT_TIME_SECONDS = 2
    DEFAULT_BATCH_SIZE = 500
    MAX_WORKERS = 5

    def __init__(self):
        self.symbols_to_update_map: Dict[str, DataTradedObject] = (
            self._get_symbols_to_update_strings())
        self.batch_size = self.DEFAULT_BATCH_SIZE

    def update_trade_market_data(self) -> None:
        pass

    def back_fill_trade_market_data(self,
                                    period: YFinanceIntervals,
                                    time_window: TradeTimeWindow) -> None:

        self.batch_size = 100
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = [
                executor.submit(self._process_batch, symbols_batch, period,
                                time_window)
                for symbols_batch in self._build_symbol_batches()
            ]
            for future in as_completed(futures):
                future.result()  # This will raise any exceptions if they occurred

    def _process_batch(self, symbols_batch: List[str], period: YFinanceIntervals,
                       time_window: TradeTimeWindow) -> None:

        logger.info(f"Processing batch with {len(symbols_batch)} symbols.")
        current_data = get_market_trade_data(symbols=symbols_batch,
                                             period=period,
                                             time_window=time_window)
        fetched_data = self._fetch_yfinance_data(symbols=symbols_batch,
                                                 time_window=time_window)
        merged_data = self._merge_and_clean_data(new_data=fetched_data,
                                                 existing_data=current_data)
        symbols_to_update = (
            self._prepare_symbols_for_update(data=merged_data,
                                             time_window=time_window))
        save_trade_market_data_in_db(symbols_to_update)

    @staticmethod
    def _fetch_yfinance_data(symbols: List[str],
                             time_window: TradeTimeWindow) -> DataFrame:

        df = yf.download(symbols,
                         period='max',
                         interval=time_window.value.yfinance_notation,
                         group_by='ticker')
        df = df.stack(level=0).reset_index().rename(columns={"level_1": "symbol"})
        df["open_date"] = df["Date"].apply(lambda x: int(x.timestamp()))
        df = df[["symbol", 'open_data', "Open",
                 "High", "Low", "Close", "Volume"]].rename(
            columns={"Open": "open", "High": "high", "Low": "low", "Close": "close",
                     "Volume": "volume"}
        )

        return df

    @staticmethod
    def _merge_and_clean_data(new_data: DataFrame,
                              existing_data: DataFrame) -> DataFrame:
        combined_data = pd.concat([new_data, existing_data], ignore_index=True)
        return combined_data.drop_duplicates(subset=['symbol', 'open_data'],
                                             keep="last")

    def _prepare_symbols_for_update(
            self,
            data: DataFrame,
            time_window: TradeTimeWindow) -> List[DataTradedObject]:

        symbols_to_update = list()

        grouped_data = data.groupby('symbol')
        for symbol, group in grouped_data:
            list_ohlcv = [OHLCV(
                symbol=symbol,
                time_window=time_window,
                open=ohlcv['open'],
                high=ohlcv['high'],
                low=ohlcv['low'],
                close=ohlcv['close'],
                volume=ohlcv['volume'],
                open_date=ohlcv['open_date']
            ) for _, ohlcv in group.iterrows()]

            data_object = self.symbols_to_update_map[symbol]
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
    collector.back_fill_trade_market_data(
        period=YFinanceIntervals.FIVE_YEARS,
        time_window=TradeTimeWindow.DAILY)


if __name__ == '__main__':
    back_fill_trade_market_data()
