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
    time_window: TradeTimeWindow
    ohlcv_list: List[OHLCV]
