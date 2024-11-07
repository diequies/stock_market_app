import logging
import math
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

    CALL_WAIT_TIME_SECONDS = 5

    def __init__(self):
        self.symbols_to_update_map: Dict[str, DataTradedObject] = (
            self._get_symbols_to_update_strings())
        self.batch_size = 500

    def update_trade_market_data(self) -> None:
        pass

    def back_fill_trade_market_data(self,
                                    period_to_back_fill: YFinanceIntervals,
                                    time_window: TradeTimeWindow) -> None:

        self.batch_size = 100

        for symbols_batch in self._build_symbol_batches():
            logger.info(f"Processing batch with {len(symbols_batch)} symbols.")
            current_data = get_market_trade_data(symbols=symbols_batch,
                                                 period=period_to_back_fill,
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
                         interval=time_window.value.yfinance_notation)
        df = (df.melt(ignore_index=False).reset_index(drop=False)
              .pivot(index=['Ticker', 'Date'], columns='Price').reset_index())
        df['Date'] = df['Date'].apply(lambda x: int(x.timestamp()))
        df.columns = ['symbol', 'open_date', 'close', 'high', 'low', 'open',
                      'volume']
        df = df.drop(['Adj Close'], axis=1, errors='ignore')
        return df

    @staticmethod
    def _merge_and_clean_data(new_data: DataFrame,
                              existing_data: DataFrame) -> DataFrame:
        combined_data = pd.concat([new_data, existing_data], ignore_index=True)
        return combined_data.drop_duplicates(subset=['symbol', 'open_data'], keep=False)

    def _prepare_symbols_for_update(
            self,
            data: DataFrame,
            time_window: TradeTimeWindow) -> List[DataTradedObject]:

        symbols_to_update = list()

        for symbol in data['symbol'].unique().tolist():
            symbol_data = data[data['symbol'] == symbol]
            list_ohlcv = [OHLCV(
                symbol=symbol,
                time_window=time_window,
                open=ohlcv['open'],
                high=ohlcv['high'],
                low=ohlcv['low'],
                close=ohlcv['close'],
                volume=ohlcv['volume'],
                open_date=ohlcv['open_date']
            ) for _, ohlcv in symbol_data.iterrows()]

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
        period_to_back_fill=YFinanceIntervals.FIVE_YEARS,
        time_window=TradeTimeWindow.DAILY)


if __name__ == '__main__':
    back_fill_trade_market_data()
