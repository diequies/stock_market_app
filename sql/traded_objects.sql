CREATE DATABASE IF NOT EXISTS stock_market_app;

USE stock_market_app;

CREATE TABLE IF NOT EXISTS traded_objects (
    name VARCHAR(256),
    symbol VARCHAR(12) NOT NULL,
    exchange VARCHAR(256),
    exchange_short_name VARCHAR(256),
    time_window VARCHAR(256),
    PRIMARY KEY (symbol),
    FOREIGN KEY (symbol) REFERENCES ohlcv_table(symbol)
);