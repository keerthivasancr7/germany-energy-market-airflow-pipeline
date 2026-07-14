from __future__ import annotations

import json
import time
from pathlib import Path

from include.src.config import DATA_DIR
from include.src.extract import extract_renewable_generation
from include.src.load import load_raw_renewables
from include.src.quality import run_quality_checks
from include.src.transform import transform_energy_marts


def run_pipeline() -> dict:
    start = time.perf_counter()
    raw_file = extract_renewable_generation()
    loaded_rows = load_raw_renewables(raw_file)
    metrics = transform_energy_marts()
    quality = run_quality_checks()
    runtime_seconds = round(time.perf_counter() - start, 2)
    result = {
        "raw_file": str(raw_file),
        "loaded_rows": loaded_rows,
        "runtime_seconds": runtime_seconds,
        **metrics,
        "quality_checks": quality,
    }
    metrics_path = DATA_DIR / "pipeline_metrics.json"
    metrics_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
