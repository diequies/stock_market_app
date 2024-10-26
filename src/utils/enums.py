from enum import Enum


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
    DAILY = {
        "yfinance_notation": "1d",
        "time_in_seconds": 60 * 60 * 24
    }
    WEEKLY = {
        "yfinance_notation": "1wk",
        "time_in_seconds": 60 * 60 * 24 * 7
    }
    MONTHLY = {
        "yfinance_notation": "1mo",
        "time_in_seconds": 60 * 60 * 24 * 30
    }
    THREE_MONTHS = {
        "yfinance_notation": "3mo",
        "time_in_seconds": 60 * 60 * 24 * 30 * 3
    }

    @classmethod
    def get_trade_time_window_from_name(cls, trade_time_window_name: str):
        for trade_time_window in TradeTimeWindow:
            if trade_time_window.name.lower() == trade_time_window_name.lower():
                return trade_time_window

        return TradeTimeWindow.DAILY


class YFINANCE_INTERVALS(Enum):
    """ The different interval options to request data to yahoo finance """
    ONE_WEEK = {
        "yfinance_notation": "1wk",
        "time_in_seconds": 60 * 60 * 24 * 7
    }
    ONE_MONTH = {
        "yfinance_notation": "1mo",
        "time_in_seconds": 60 * 60 * 24 * 30
    }
    THREE_MONTHS = {
        "yfinance_notation": "3mo",
        "time_in_seconds": 60 * 60 * 24 * 30 * 3
    }
    SIX_MONTHS = {
        "yfinance_notation": "6mo",
        "time_in_seconds": 60 * 60 * 24 * 30 * 6
    }
    ONE_YEAR = {
        "yfinance_notation": "1y",
        "time_in_seconds": 60 * 60 * 24 * 30 * 12
    }
    TWO_YEARS = {
        "yfinance_notation": "2y",
        "time_in_seconds": 60 * 60 * 24 * 30 * 12 * 2
    }
    FIVE_YEARS = {
        "yfinance_notation": "5y",
        "time_in_seconds": 60 * 60 * 24 * 30 * 12 * 5
    }
    TEN_YEARS = {
        "yfinance_notation": "10y",
        "time_in_seconds": 60 * 60 * 24 * 30 * 12 * 10
    }
