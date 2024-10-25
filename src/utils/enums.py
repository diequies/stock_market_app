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
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"
    THREE_MONTHS = "3mo"

    @classmethod
    def get_trade_time_window_from_name(cls, trade_time_window_name: str):
        for trade_time_window in TradeTimeWindow:
            if trade_time_window.name.lower() == trade_time_window_name.lower():
                return trade_time_window

        return TradeTimeWindow.DAILY


class YFINANCE_INTERVALS(Enum):
    """ The different interval options to request data to yahoo finance """
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    TEN_YEARS = "10y"

