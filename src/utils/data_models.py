from dataclasses import dataclass
from typing import List, Optional

from utils.enums import TradedObjectType, TradeTimeWindow


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


class TradedObject:
    """ Class containing the object traded data """

    def __init__(
            self,
            name: Optional[str],
            symbol: str,
            exchange: Optional[str],
            exchange_short_name: Optional[str],
            object_type: TradedObjectType
    ):
        if name is None:
            self.name = ""
        else:
            self.name = name.replace("'", "")
        self.symbol = symbol
        if exchange is None:
            self.exchange = ""
        else:
            self.exchange = exchange.replace("'", "")
        if exchange_short_name is None:
            self.exchange_short_name = ""
        else:
            self.exchange_short_name = exchange_short_name.replace("'", "")
        self.object_type = object_type

    def __hash__(self):
        return hash((self.symbol, self.object_type.name))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.symbol == other.symbol
                and self.object_type.name == other.object_type.name)


@dataclass
class DataTradedObject(TradedObject):
    """ TradedObject including the trading data """
    ohlcv_list: List[OHLCV]
