WITH latest_prices AS (
    SELECT DISTINCT ON (market)
        commodity, market, district, state,
        modal_price, min_price, max_price,
        arrival_date AS fetched_at
    FROM commodity_prices
    WHERE LOWER(commodity) = LOWER(%s)
      AND arrival_date >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY market, arrival_date DESC
),
weekly_averages AS (
    SELECT
        market,
        date_trunc('week', arrival_date)  AS week_start,
        AVG(modal_price)  AS avg_price
    FROM commodity_prices
    WHERE LOWER(commodity) = LOWER(%s)
      AND arrival_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY market, date_trunc('week', arrival_date)
),
weekly_with_prev AS (
    SELECT
        market,
        week_start,
        avg_price,
        LAG(avg_price) OVER (PARTITION BY market ORDER BY week_start) AS prev_avg,
        ROW_NUMBER() OVER (PARTITION BY market ORDER BY week_start DESC) AS rn
    FROM weekly_averages
),
market_trends AS (
    SELECT
        market,
        CASE
            WHEN prev_avg IS NULL  THEN 'Stable'
            WHEN avg_price > prev_avg * 1.03 THEN 'Rising'
            WHEN avg_price < prev_avg * 0.97 THEN 'Falling'
            ELSE    'Stable'
        END AS trend_analysis
    FROM weekly_with_prev
    WHERE rn = 1
),
market_strengths AS (
    SELECT
        market,
        CASE
            WHEN STDDEV(modal_price) / NULLIF(AVG(modal_price), 0) * 100 < 5  THEN 'Strong'
            WHEN STDDEV(modal_price) / NULLIF(AVG(modal_price), 0) * 100 < 15 THEN 'Moderate'
            ELSE 'Weak'
        END AS trend_strength
    FROM commodity_prices
    WHERE LOWER(commodity) = LOWER(%s)
      AND arrival_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY market
)
SELECT
    lp.commodity, lp.market, lp.district, lp.state,
    lp.modal_price, lp.min_price, lp.max_price, lp.fetched_at,
    COALESCE(mt.trend_analysis, 'Stable') AS trend_analysis,
    COALESCE(ms.trend_strength, 'Weak')   AS trend_strength
FROM latest_prices lp
LEFT JOIN market_trends    mt ON LOWER(lp.market) = LOWER(mt.market)
LEFT JOIN market_strengths ms ON LOWER(lp.market) = LOWER(ms.market);
