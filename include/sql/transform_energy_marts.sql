CREATE OR REPLACE TABLE stg_germany_renewables AS
SELECT
    Entity AS country,
    Code AS country_code,
    Year AS year,
    "Bioenergy and other renewables" AS bioenergy_twh,
    "Solar" AS solar_twh,
    "Wind" AS wind_twh,
    "Hydropower" AS hydro_twh
FROM renewable_generation_input
WHERE Entity = 'Germany';

CREATE OR REPLACE TABLE fact_germany_renewable_generation AS
SELECT
    country,
    country_code,
    year,
    COALESCE(bioenergy_twh, 0) AS bioenergy_twh,
    COALESCE(solar_twh, 0) AS solar_twh,
    COALESCE(wind_twh, 0) AS wind_twh,
    COALESCE(hydro_twh, 0) AS hydro_twh,
    ROUND(
        COALESCE(bioenergy_twh, 0)
        + COALESCE(solar_twh, 0)
        + COALESCE(wind_twh, 0)
        + COALESCE(hydro_twh, 0),
        3
    ) AS total_renewable_twh
FROM stg_germany_renewables
WHERE year IS NOT NULL;

CREATE OR REPLACE TABLE mart_germany_renewable_trends AS
SELECT
    year,
    total_renewable_twh,
    wind_twh,
    solar_twh,
    hydro_twh,
    bioenergy_twh,
    ROUND(
        total_renewable_twh - LAG(total_renewable_twh) OVER (ORDER BY year),
        3
    ) AS yoy_change_twh,
    ROUND(
        100.0 * (total_renewable_twh - LAG(total_renewable_twh) OVER (ORDER BY year))
        / NULLIF(LAG(total_renewable_twh) OVER (ORDER BY year), 0),
        2
    ) AS yoy_growth_pct
FROM fact_germany_renewable_generation
ORDER BY year;

CREATE OR REPLACE TABLE mart_germany_energy_mix_latest AS
WITH latest AS (
    SELECT *
    FROM fact_germany_renewable_generation
    WHERE year = (SELECT MAX(year) FROM fact_germany_renewable_generation)
)
SELECT 'wind' AS source, year, wind_twh AS generation_twh, ROUND(100.0 * wind_twh / NULLIF(total_renewable_twh, 0), 2) AS renewable_mix_pct FROM latest
UNION ALL
SELECT 'solar', year, solar_twh, ROUND(100.0 * solar_twh / NULLIF(total_renewable_twh, 0), 2) FROM latest
UNION ALL
SELECT 'hydro', year, hydro_twh, ROUND(100.0 * hydro_twh / NULLIF(total_renewable_twh, 0), 2) FROM latest
UNION ALL
SELECT 'bioenergy', year, bioenergy_twh, ROUND(100.0 * bioenergy_twh / NULLIF(total_renewable_twh, 0), 2) FROM latest
ORDER BY generation_twh DESC;
