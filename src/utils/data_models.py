from dataclasses import dataclass
from typing import List

from src.utils.enums import TradedObjectType, TradeTimeWindow


@dataclass
class OHLCV:
    """ Market data point for a traded object """
    symbol: str
    time_window: TradeTimeWindow
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TradedObject:
    """ Class containing the object traded data """
    name: str
    symbol: str
    exchange: str
    exchange_short_name: str
    object_type: TradedObjectType

    def __hash__(self):
        return hash((self.name, self.symbol, self.exchange, self.exchange_short_name,
                     self.object_type.name))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.name == other.name and self.symbol == other.symbol
                and self.exchange == other.exchange
                and self.exchange_short_name == other.exchange_short_name
                and self.object_type.name == other.object_type.name)


@dataclass
class DataTradedObject(TradedObject):
    """ TradedObject including the trading data """
    ohlcv_list: List[OHLCV]
