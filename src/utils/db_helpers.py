import os
import time
from typing import Set, List

import pandas.io.sql as psql
import pymysql
from pandas import DataFrame

from utils.data_models import TradedObject
from utils.enums import TradedObjectType, YFinanceIntervals, TradeTimeWindow


def get_mysql_connection():

    print("Connected to MySQL")

    return pymysql.connect(host=os.environ.get("AWS_RDS_HOST"),
                           user=os.environ.get("AWS_RDS_USER"),
                           password=os.environ.get("AWS_RDS_PASSWORD"),
                           db=os.environ.get("AWS_RDS_DB"),
                           port=int(os.environ.get("AWS_RDS_PORT")))


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

    cursor = con.cursor()

    cursor.execute(query)
    result = cursor.fetchall()

    return {
        TradedObject(
            name=data[0],
            symbol=data[1],
            exchange=data[2],
            exchange_short_name=data[3],
            object_type=TradedObjectType.get_traded_object_type_from_name(data[4])
        ) for data in result
    }


def save_new_traded_objects_in_db(traded_objects: Set[TradedObject]) -> None:

    con = get_mysql_connection()
    cursor = con.cursor()

    strings_to_persist = [
        (f"('{traded_object.name}', '{traded_object.symbol}', "
         f"'{traded_object.exchange}', '{traded_object.exchange_short_name}',"
         f"'{traded_object.object_type.name}')")
        for traded_object in traded_objects
    ]

    query = f"""
    INSERT INTO traded_objects (
    name, 
    symbol,
    exchange,
    exchange_short_name,
    object_type
    )
    VALUES {','.join(strings_to_persist)};"""

    cursor.execute(query)
    con.commit()


def get_market_trade_data(symbols: List[str], period: YFinanceIntervals,
                          time_window: TradeTimeWindow) -> DataFrame:

    con = get_mysql_connection()

    from_unix_time = int(time.time() - period.value.time_in_seconds)

    query = f"""
                SELECT
                    symbol,
                    open_date,
                    open,
                    high,
                    low,
                    close,
                    volume
                FROM ohlcv_table
                WHERE time_window = '{time_window.value.yfinance_notation}'
                AND open_date > {from_unix_time}
                AND symbol in (\'{"','".join(symbols)}\')
            """

    return psql.read_sql(query, con)
