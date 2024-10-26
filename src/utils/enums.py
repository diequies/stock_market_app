from dataclasses import dataclass
from enum import Enum


@dataclass
class YFinanceTime:
    time_in_seconds: int
    yfinance_notation: str


class TradedObjectType(Enum):
    """ Type of the traded object """
    STOCK = {
        'id': 0,
        'endpoint_name': 'available-traded'
    }
    ETF = {
        'id': 1,
        'endpoint_name': 'etf'
    }
    TRUST = {
        'id': 2,
        'endpoint_name': None
    }
    OTHER = {
        'id': 3,
        'endpoint_name': None
    }

    @classmethod
    def get_traded_object_type_from_name(cls, traded_object_type_name: str):
        for traded_object_type in TradedObjectType:
            if traded_object_type.name.lower() == traded_object_type_name.lower():
                return traded_object_type

        return TradedObjectType.OTHER


class TradeTimeWindow(Enum):
    """ Time window of the market data point """
    DAILY = YFinanceTime(time_in_seconds=60 * 60 * 24,
                         yfinance_notation="1d")
    WEEKLY = YFinanceTime(time_in_seconds=60 * 60 * 24 * 7,
                          yfinance_notation="1wk")
    MONTHLY = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30,
                           yfinance_notation="1mo")
    THREE_MONTHS = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 3,
                                yfinance_notation="1mo")

    @classmethod
    def get_trade_time_window_from_name(cls, trade_time_window_name: str):
        for trade_time_window in TradeTimeWindow:
            if (trade_time_window.value.yfinance_notation
                    == trade_time_window_name.lower()):
                return trade_time_window

        return TradeTimeWindow.DAILY


class YFinanceIntervals(Enum):
    """ The different interval options to request data to yahoo finance """
    ONE_WEEK = YFinanceTime(time_in_seconds=60 * 60 * 24 * 7,
                            yfinance_notation="1wk")
    ONE_MONTH = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30,
                             yfinance_notation="1mo")
    THREE_MONTHS = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 3,
                                yfinance_notation="3mo")
    SIX_MONTHS = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 6,
                              yfinance_notation="6mo")
    ONE_YEAR = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 12,
                            yfinance_notation="1y")
    TWO_YEARS = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 12 * 2,
                             yfinance_notation="2y")
    FIVE_YEARS = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 12 * 5,
                              yfinance_notation="5y")
    TEN_YEARS = YFinanceTime(time_in_seconds=60 * 60 * 24 * 30 * 12 * 10,
                             yfinance_notation="10y")
