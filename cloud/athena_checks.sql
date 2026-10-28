-- Run one statement at a time. Query success alone is not a data-quality pass.
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT year) AS unique_years,
       MIN(year) AS first_year, MAX(year) AS latest_year
FROM energy_pipeline.fact_germany_renewable_generation;

SELECT year, total_renewable_twh, yoy_change_twh, yoy_growth_pct
FROM energy_pipeline.mart_germany_renewable_trends
ORDER BY year DESC LIMIT 5;

SELECT source, year, ROUND(generation_twh, 2) AS generation_twh,
       ROUND(renewable_mix_pct, 2) AS renewable_mix_pct
FROM energy_pipeline.mart_germany_energy_mix_latest
ORDER BY generation_twh DESC;

-- Reconcile the latest energy-mix total to the latest fact total.
SELECT f.year, f.total_renewable_twh, SUM(m.generation_twh) AS mix_total_twh,
       ABS(f.total_renewable_twh - SUM(m.generation_twh)) < 0.001 AS totals_match
FROM energy_pipeline.fact_germany_renewable_generation f
JOIN energy_pipeline.mart_germany_energy_mix_latest m ON f.year = m.year
GROUP BY f.year, f.total_renewable_twh;
