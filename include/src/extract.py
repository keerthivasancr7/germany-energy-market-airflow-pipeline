from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from include.src.config import RAW_DIR, RAW_RENEWABLE_FILE, RENEWABLE_SOURCE_URL


def extract_renewable_generation() -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        RENEWABLE_SOURCE_URL,
        headers={"User-Agent": "data-engineering-portfolio/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response, RAW_RENEWABLE_FILE.open("wb") as output:
        shutil.copyfileobj(response, output)
    return RAW_RENEWABLE_FILE


if __name__ == "__main__":
    print(extract_renewable_generation())
