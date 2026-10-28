-- Run one statement at a time in the Frankfurt Athena SQL editor.
-- Terraform can adopt these tables; choose the same column names/types/paths.
CREATE DATABASE IF NOT EXISTS energy_pipeline;

CREATE EXTERNAL TABLE IF NOT EXISTS energy_pipeline.fact_germany_renewable_generation (
    country STRING, country_code STRING, year BIGINT,
    bioenergy_twh DOUBLE, solar_twh DOUBLE, wind_twh DOUBLE,
    hydro_twh DOUBLE, total_renewable_twh DOUBLE
)
STORED AS PARQUET
LOCATION 's3://keerthivasan-energy-pipeline-20261028/curated/fact_germany_renewable_generation/';

CREATE EXTERNAL TABLE IF NOT EXISTS energy_pipeline.mart_germany_renewable_trends (
    year BIGINT, total_renewable_twh DOUBLE, wind_twh DOUBLE,
    solar_twh DOUBLE, hydro_twh DOUBLE, bioenergy_twh DOUBLE,
    yoy_change_twh DOUBLE, yoy_growth_pct DOUBLE
)
STORED AS PARQUET
LOCATION 's3://keerthivasan-energy-pipeline-20261028/curated/mart_germany_renewable_trends/';

CREATE EXTERNAL TABLE IF NOT EXISTS energy_pipeline.mart_germany_energy_mix_latest (
    source STRING, year BIGINT, generation_twh DOUBLE, renewable_mix_pct DOUBLE
)
STORED AS PARQUET
LOCATION 's3://keerthivasan-energy-pipeline-20261028/curated/mart_germany_energy_mix_latest/';
