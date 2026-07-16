CREATE TABLE commodity_prices (
    id              SERIAL PRIMARY KEY,
    state           VARCHAR(100),
    district        VARCHAR(100),
    market          VARCHAR(100),
    commodity       VARCHAR(100),
    variety         VARCHAR(100),
    min_price       NUMERIC(10, 2),
    max_price       NUMERIC(10, 2),
    modal_price     NUMERIC(10, 2),
    arrival_date    DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT commodity_prices_market_commodity_variety_arrival_date_key
        UNIQUE (market, commodity, variety, arrival_date)
);
CREATE INDEX idx_cp_arrival_date
    ON commodity_prices (arrival_date);

CREATE INDEX idx_cp_commodity
    ON commodity_prices (lower(commodity));

CREATE INDEX idx_cp_market
    ON commodity_prices (lower(market));

CREATE INDEX idx_cp_lookup
    ON commodity_prices (lower(commodity), market, arrival_date);