-- price_trend_30day.sql
-- Daily average modal price for the last 7 days with a 7-day rolling average.
-- Used by: /api/analytics  →  results page price-trend chart.

WITH daily AS (
    SELECT
        arrival_date,
        AVG(modal_price) AS avg_price
    FROM commodity_prices
    WHERE LOWER(commodity) = LOWER(%(commodity)s)
      AND arrival_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY arrival_date
)
SELECT
    TO_CHAR(arrival_date, 'DD Mon') AS label,
    ROUND(avg_price::NUMERIC, 2) AS price,
    ROUND(
        AVG(avg_price) OVER (
            ORDER BY arrival_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::NUMERIC, 2
    )  AS rolling_avg
FROM daily
ORDER BY arrival_date;
