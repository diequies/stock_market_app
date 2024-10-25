import logging
import math
from typing import Dict, Generator
import yfinance as yf

from config.sentry_config import init_sentry
from utils.data_models import DataTradedObject
from utils.db_helpers import get_all_traded_objects_from_db
from utils.enums import YFINANCE_INTERVALS, TradeTimeWindow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketTradeDataCollector:
    """ Class to update the market trade data in the DB """

    BATCH_SIZE = 500
    CALL_WAIT_TIME_SECONDS = 5

    def __init__(self):
        self.symbols_to_update_map: Dict[str, DataTradedObject] = (
            self._get_symbols_to_update_strings())

    def update_trade_market_data(self) -> None:
        pass

    def back_fill_trade_market_data(self,
                                    period_to_back_fill: YFINANCE_INTERVALS) -> None:
        for symbols_batch in self._build_symbol_batches():
            yf.download(symbols_batch, period=period_to_back_fill.value,
                        interval=TradeTimeWindow.DAILY)

    def _build_symbol_batches(self) -> Generator[str]:
        keys_list = list(self.symbols_to_update_map.keys())
        n_batches = math.ceil(len(keys_list) / self.BATCH_SIZE)
        for batch in range(n_batches):
            print(f"Requesting data for batch {batch + 1} of {n_batches}")
            start_index = batch * self.BATCH_SIZE
            end_index = start_index + self.BATCH_SIZE
            yield keys_list[start_index:end_index]

    @staticmethod
    def _get_symbols_to_update_strings() -> Dict[str, DataTradedObject]:
        traded_objects = get_all_traded_objects_from_db()
        traded_objects_map = {traded_object.symbol: DataTradedObject(
            traded_object=traded_object, ohlcv_list=list())
                              for traded_object in traded_objects}
        return traded_objects_map


def main_market_trade_data_collection():
    init_sentry()
    MarketTradeDataCollector()


if __name__ == '__main__':
    main_market_trade_data_collection()
