from enum import Enum


class TradedObjectType(Enum):
    """ Type of the traded object """
    TRADED_STOCK = 0
    EXCHANGE_TRADED_FUND = 1


class TradeTimeWindow(Enum):
    """ Time window of the market data point """
    INTRADAY = 0
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
