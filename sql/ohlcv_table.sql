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
    open_date BIGINT NOT NULL,
    PRIMARY KEY (symbol, time_window, open_date)
);

-- DROP TABLE ohlcv_table;