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

    @classmethod
    def get_traded_object_type_from_name(cls, traded_object_type_name: str):
        for traded_object_type in TradedObjectType:
            if traded_object_type.name.lower() == traded_object_type_name.lower():
                return traded_object_type

        return TradedObjectType.STOCK


class TradeTimeWindow(Enum):
    """ Time window of the market data point """
    INTRADAY = 0
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3

    @classmethod
    def get_trade_time_window_from_name(cls, trade_time_window_name: str):
        for trade_time_window in TradeTimeWindow:
            if trade_time_window.name.lower() == trade_time_window_name.lower():
                return trade_time_window

        return TradeTimeWindow.DAILY
