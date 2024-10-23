CREATE DATABASE IF NOT EXISTS stock_market_app;

USE stock_market_app;

CREATE TABLE IF NOT EXISTS traded_objects (
    name VARCHAR(256),
    symbol VARCHAR(256) NOT NULL,
    exchange VARCHAR(256),
    exchange_short_name VARCHAR(256),
    object_type VARCHAR(256) NOT NULL,
    PRIMARY KEY (symbol, object_type)
);

-- DROP TABLE traded_objects;