"""AWS Glue Python Shell 3.9 job; additional module: duckdb==1.4.3.

Reads the existing raw CSV from S3. Validates before publishing three Parquet
tables and a metrics JSON. Stable output keys avoid duplicate files on reruns.
"""
import hashlib
import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import duckdb

BUCKET = "keerthivasan-energy-pipeline-20261028"
INPUT_KEY = "raw/modern-renewable-energy-consumption.csv"
OUTPUT_PREFIX = "curated"
OUTPUT_TABLES = (
    "fact_germany_renewable_generation",
    "mart_germany_renewable_trends",
    "mart_germany_energy_mix_latest",
)

# Embedded from include/sql/transform_energy_marts.sql to keep Glue deployment
# self-contained. Do not upload a repository package or configure extra files.
TRANSFORM_SQL = """CREATE OR REPLACE TABLE stg_germany_renewables AS
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
"""


def build_outputs(csv_path, output_dir):
    """Local transform/validation, with no AWS calls. Return metrics and paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(":memory:") as conn:
        conn.execute("SET threads=1")
        conn.execute("SET memory_limit='256MB'")
        conn.execute(
            "CREATE TABLE raw_renewable_generation AS "
            "SELECT * FROM read_csv_auto(?, header=true)", [str(csv_path)]
        )
        columns = {row[0] for row in conn.execute(
            "DESCRIBE raw_renewable_generation"
        ).fetchall()}
        required = {"Entity", "Code", "Year", "Solar", "Wind", "Hydropower"}
        if required - columns:
            raise ValueError("Missing source columns: " + str(sorted(required - columns)))
        if "Bioenergy and other renewables" in columns:
            bioenergy = '"Bioenergy and other renewables"'
        elif {"Bioenergy", "Other renewables"} <= columns:
            bioenergy = 'COALESCE("Bioenergy", 0) + COALESCE("Other renewables", 0)'
        else:
            raise ValueError("Missing combined or split bioenergy source columns")

        # Validate Germany's original keys and amounts before null coalescing.
        if conn.execute("SELECT COUNT(*) FROM raw_renewable_generation "
                        "WHERE Entity='Germany' AND Year IS NULL").fetchone()[0]:
            raise ValueError("Germany source has null years")
        generation_columns = [c for c in (
            "Bioenergy and other renewables", "Bioenergy", "Other renewables",
            "Solar", "Wind", "Hydropower") if c in columns]
        for column in generation_columns:
            if conn.execute(f'''SELECT COUNT(*) FROM raw_renewable_generation
                WHERE Entity='Germany' AND "{column}" IS NOT NULL
                AND ("{column}" < 0 OR NOT isfinite(CAST("{column}" AS DOUBLE)))'''
            ).fetchone()[0]:
                raise ValueError("Invalid Germany generation value in " + column)

        conn.execute(f'''CREATE TEMP VIEW renewable_generation_input AS
            SELECT Entity, Code, Year,
                   {bioenergy} AS "Bioenergy and other renewables",
                   Solar, Wind, Hydropower
            FROM raw_renewable_generation''')
        conn.execute(TRANSFORM_SQL)
        rows = conn.execute(
            "SELECT COUNT(*) FROM fact_germany_renewable_generation"
        ).fetchone()[0]
        if rows == 0:
            raise ValueError("No Germany records found")
        duplicate_years = conn.execute('''SELECT COUNT(*) FROM (
            SELECT year FROM fact_germany_renewable_generation
            GROUP BY year HAVING COUNT(*) > 1)''').fetchone()[0]
        if duplicate_years:
            raise ValueError("Duplicate Germany years found")
        latest_year, latest_total = conn.execute('''SELECT year,
            total_renewable_twh FROM fact_germany_renewable_generation
            ORDER BY year DESC LIMIT 1''').fetchone()
        metrics = {
            "source_s3_uri": "s3://" + BUCKET + "/" + INPUT_KEY,
            "source_sha256": hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
            "raw_rows": conn.execute(
                "SELECT COUNT(*) FROM raw_renewable_generation"
            ).fetchone()[0],
            "germany_years": rows,
            "latest_year": latest_year,
            "latest_total_renewable_twh": float(latest_total),
            "duplicate_years": duplicate_years,
            "quality_checks": "passed",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "duckdb_version": duckdb.__version__,
            "output_rows": {},
        }
        files = {}
        for table in OUTPUT_TABLES:
            target = output_dir / (table + ".parquet")
            conn.execute(f"COPY {table} TO '{target.as_posix()}' "
                         "(FORMAT PARQUET, COMPRESSION SNAPPY)")
            metrics["output_rows"][table] = conn.execute(
                "SELECT COUNT(*) FROM " + table
            ).fetchone()[0]
            files[OUTPUT_PREFIX + "/" + table + "/data.parquet"] = target
    metrics_file = output_dir / "pipeline_metrics.json"
    metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    files[OUTPUT_PREFIX + "/metrics/pipeline_metrics.json"] = metrics_file
    return metrics, files


def run_pipeline(s3_client=None):
    if s3_client is None:
        import boto3
        s3_client = boto3.client("s3", region_name="eu-central-1")
    with tempfile.TemporaryDirectory(prefix="energy-") as directory:
        csv_path = Path(directory) / "source.csv"
        logging.info("Reading s3://%s/%s", BUCKET, INPUT_KEY)
        s3_client.download_file(BUCKET, INPUT_KEY, str(csv_path))
        metrics, files = build_outputs(csv_path, Path(directory) / "output")
        for key, local_path in files.items():
            s3_client.upload_file(str(local_path), BUCKET, key)
            logging.info("Published s3://%s/%s", BUCKET, key)
        print(json.dumps(metrics, indent=2))
        return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        run_pipeline()
    except Exception:
        logging.exception("Energy pipeline failed")
        raise
