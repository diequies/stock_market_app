import os
import time
from typing import Set, List

import pandas as pd
from pandas import DataFrame
from sqlalchemy import create_engine, text

from utils.data_models import TradedObject, DataTradedObject
from utils.enums import TradedObjectType, YFinanceIntervals, TradeTimeWindow


def get_mysql_connection():

    print("Connected to MySQL")

    database_uri = f"mysql+pymysql://{os.environ.get('AWS_RDS_USER')}:" \
                   f"{os.environ.get('AWS_RDS_PASSWORD')}@" \
                   f"{os.environ.get('AWS_RDS_HOST')}:" \
                   f"{os.environ.get('AWS_RDS_PORT')}/" \
                   f"{os.environ.get('AWS_RDS_DB')}"

    return create_engine(database_uri)


def get_all_traded_objects_from_db() -> Set[TradedObject]:
    con = get_mysql_connection()

    query = """
                SELECT
                    name,
                    symbol,
                    exchange,
                    exchange_short_name,
                    object_type
                FROM traded_objects
            """

    with con.connect() as connection:
        result = connection.execute(text(query))
        data_points = result.fetchall()

    return {
        TradedObject(
            name=data[0],
            symbol=data[1],
            exchange=data[2],
            exchange_short_name=data[3],
            object_type=TradedObjectType.get_traded_object_type_from_name(data[4])
        ) for data in data_points
    }


def save_new_traded_objects_in_db(traded_objects: Set[TradedObject]) -> None:

    con = get_mysql_connection()

    values = [
        {
            "name": traded_object.name,
            "symbol": traded_object.symbol,
            "exchange": traded_object.exchange,
            "exchange_short_name": traded_object.exchange_short_name,
            "object_type": traded_object.object_type.name
        }
        for traded_object in traded_objects
    ]

    query = text(f"""
    INSERT INTO traded_objects (
    name, 
    symbol,
    exchange,
    exchange_short_name,
    object_type
    )
    VALUES (
    :name, :symbol, :exchange, :exchange_short_name, :object_type
    )""")

    with con.connect() as connection:
        connection.execute(query, values)
        connection.commit()


def get_market_trade_data(symbols: List[str], period: YFinanceIntervals,
                          time_window: TradeTimeWindow) -> DataFrame:

    con = get_mysql_connection()

    from_unix_time = int(time.time() - period.value.time_in_seconds)

    query = f"""
                SELECT
                    symbol,
                    time_window,
                    open_date,
                    close,
                    high,
                    low,
                    open,
                    volume
                FROM ohlcv_table
                WHERE time_window = '{time_window.value.yfinance_notation}'
                AND open_date > {from_unix_time}
                AND symbol in (\'{"','".join(symbols)}\')
            """

    return pd.read_sql(query, con)


def save_trade_market_data_in_db(objects_list: List[DataTradedObject]) -> None:

    con = get_mysql_connection()

    values = [
        {
            "symbol": ohlcv.symbol,
            "time_window": ohlcv.time_window.value.yfinance_notation,
            "open": ohlcv.open,
            "high": ohlcv.high,
            "low": ohlcv.low,
            "close": ohlcv.close,
            "volume": ohlcv.volume,
            "open_date": ohlcv.open_date
        }
        for data_list in objects_list for ohlcv in data_list.ohlcv_list
    ]

    query = text(f"""
    INSERT INTO ohlcv_table (
    symbol,
    time_window,
    open,
    high,
    low,
    close,
    volume,
    open_date
    )
    VALUES (
        :symbol, :time_window, :open, :high, :low, :close, :volume, :open_date
    )
    ON DUPLICATE KEY UPDATE 
        open = VALUES(open),
        high = VALUES(high),
        low = VALUES(low),
        close = VALUES(close),
        volume = VALUES(volume)""")

    with con.connect() as connection:
        connection.execute(query, values)
        connection.commit()
