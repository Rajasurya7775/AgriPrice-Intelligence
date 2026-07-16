-- seasonal_scoring.sql
-- Scores every commodity currently active in the database by profit potential.
-- Logic: compare the 2-day recent average against the 3–7 day historical baseline.
--   >20% above baseline  → High profit potential  → status: in_season
--   >0%  above baseline  → Medium profit potential → status: upcoming
--   At or below baseline → Low profit potential    → status: avoid
--   No historical data   → Medium (insufficient baseline) → status: upcoming
-- Used by: /api/seasonal  →  seasonal crop planner page.

WITH recent AS (
    SELECT
        commodity,
        AVG(modal_price) AS recent_avg
    FROM commodity_prices
    WHERE arrival_date >= CURRENT_DATE - INTERVAL '2 days'
    GROUP BY commodity
),
historical AS (
    SELECT
        commodity,
        AVG(modal_price) AS hist_avg
    FROM commodity_prices
    WHERE arrival_date BETWEEN CURRENT_DATE - INTERVAL '7 days'
                           AND CURRENT_DATE - INTERVAL '3 days'
    GROUP BY commodity
)
SELECT
    r.commodity,
    ROUND(r.recent_avg::NUMERIC, 2) AS avg_price,

    CASE
        WHEN h.hist_avg IS NULL              THEN 'Medium'
        WHEN r.recent_avg > h.hist_avg * 1.2 THEN 'High'
        WHEN r.recent_avg > h.hist_avg * 1.05 THEN 'Medium'
        ELSE                                      'Low'
    END AS profit_potential,

    CASE
        WHEN h.hist_avg IS NULL              THEN 'upcoming'
        WHEN r.recent_avg > h.hist_avg * 1.2 THEN 'in_season'
        WHEN r.recent_avg > h.hist_avg       THEN 'upcoming'
        ELSE                                      'avoid'
    END AS status

FROM recent r
LEFT JOIN historical h ON r.commodity = h.commodity
ORDER BY r.recent_avg DESC
LIMIT 20;
