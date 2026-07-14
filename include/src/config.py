from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
DB_PATH = WAREHOUSE_DIR / "energy_market.duckdb"
SQL_DIR = PROJECT_ROOT / "include" / "sql"

# Public sample source from Our World in Data's grapher CSV endpoint.
# This gives renewable electricity generation by source and country over time.
# The pipeline filters Germany and builds analytics marts from it.
RENEWABLE_SOURCE_URL = "https://ourworldindata.org/grapher/modern-renewable-energy-consumption.csv"
RAW_RENEWABLE_FILE = RAW_DIR / "modern-renewable-energy-consumption.csv"
