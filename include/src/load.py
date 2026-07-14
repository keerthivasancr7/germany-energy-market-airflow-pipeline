from __future__ import annotations

from pathlib import Path

import duckdb

from include.src.config import DB_PATH, RAW_RENEWABLE_FILE, WAREHOUSE_DIR


def load_raw_renewables(csv_path: Path = RAW_RENEWABLE_FILE, db_path: Path = DB_PATH) -> int:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute("DROP TABLE IF EXISTS raw_renewable_generation")
        conn.execute(
            """
            CREATE TABLE raw_renewable_generation AS
            SELECT * FROM read_csv_auto(?, header=true)
            """,
            [str(csv_path)],
        )
        rows = conn.execute("SELECT COUNT(*) FROM raw_renewable_generation").fetchone()[0]
    return int(rows)


if __name__ == "__main__":
    print(load_raw_renewables())
