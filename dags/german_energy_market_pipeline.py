from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="german_energy_market_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["data-engineering", "energy", "duckdb", "portfolio"],
)
def german_energy_market_pipeline():
    @task
    def extract():
        from include.src.extract import extract_renewable_generation
        return str(extract_renewable_generation())

    @task
    def load(raw_file: str):
        from pathlib import Path
        from include.src.load import load_raw_renewables
        return load_raw_renewables(Path(raw_file))

    @task
    def transform():
        from include.src.transform import transform_energy_marts
        return transform_energy_marts()

    @task
    def quality_checks():
        from include.src.quality import run_quality_checks
        return run_quality_checks()

    raw_file = extract()
    load(raw_file) >> transform() >> quality_checks()


german_energy_market_pipeline()
