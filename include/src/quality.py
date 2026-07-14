from __future__ import annotations

from pathlib import Path

import duckdb

from include.src.config import DB_PATH


def run_quality_checks(db_path: Path = DB_PATH) -> dict[str, int]:
    checks = {}
    with duckdb.connect(str(db_path)) as conn:
        checks["duplicate_years"] = conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT year, COUNT(*) AS row_count
                FROM fact_germany_renewable_generation
                GROUP BY year
                HAVING row_count > 1
            )
            """
        ).fetchone()[0]
        checks["null_years"] = conn.execute(
            "SELECT COUNT(*) FROM fact_germany_renewable_generation WHERE year IS NULL"
        ).fetchone()[0]
        checks["negative_generation_values"] = conn.execute(
            """
            SELECT COUNT(*) FROM fact_germany_renewable_generation
            WHERE bioenergy_twh < 0 OR solar_twh < 0 OR wind_twh < 0 OR hydro_twh < 0 OR total_renewable_twh < 0
            """
        ).fetchone()[0]
        checks["mart_rows"] = conn.execute("SELECT COUNT(*) FROM mart_germany_renewable_trends").fetchone()[0]

    failures = {name: value for name, value in checks.items() if name != "mart_rows" and value != 0}
    if checks["mart_rows"] == 0:
        failures["mart_rows"] = 0
    if failures:
        raise ValueError(f"Data quality checks failed: {failures}")
    return {key: int(value) for key, value in checks.items()}


if __name__ == "__main__":
    print(run_quality_checks())
