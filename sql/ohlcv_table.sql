CREATE DATABASE IF NOT EXISTS stock_market_app;

USE stock_market_app;

CREATE TABLE IF NOT EXISTS ohlcv_table (
    symbol VARCHAR(12) NOT NULL,
    time_window VARCHAR(256) NOT NULL,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume INT,
    PRIMARY KEY (symbol)
);

-- DROP TABLE ohlcv_table;