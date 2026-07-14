from __future__ import annotations

from pathlib import Path

import duckdb

from include.src.config import DB_PATH, SQL_DIR


def transform_energy_marts(db_path: Path = DB_PATH) -> dict[str, int | float]:
    sql_path = SQL_DIR / "transform_energy_marts.sql"
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(sql_path.read_text())
        raw_rows = conn.execute("SELECT COUNT(*) FROM raw_renewable_generation").fetchone()[0]
        germany_years = conn.execute("SELECT COUNT(*) FROM fact_germany_renewable_generation").fetchone()[0]
        latest_year, latest_total = conn.execute(
            "SELECT year, total_renewable_twh FROM fact_germany_renewable_generation ORDER BY year DESC LIMIT 1"
        ).fetchone()
    return {
        "raw_rows": int(raw_rows),
        "germany_years": int(germany_years),
        "latest_year": int(latest_year),
        "latest_total_renewable_twh": float(latest_total),
    }


if __name__ == "__main__":
    print(transform_energy_marts())
