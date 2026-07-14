from __future__ import annotations

import shutil
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from include.src.config import RAW_DIR, RAW_RENEWABLE_FILE, RENEWABLE_SOURCE_URL


def extract_renewable_generation() -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        RENEWABLE_SOURCE_URL,
        headers={"User-Agent": "data-engineering-portfolio/1.0"},
    )
    try:
        response_context = urllib.request.urlopen(request, timeout=60)
    except urllib.error.URLError as exc:
        # Some macOS Python installations lack a configured CA bundle.
        # This project reads a public CSV only, so we fall back for local reproducibility.
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        response_context = urllib.request.urlopen(
            request, timeout=60, context=ssl._create_unverified_context()
        )

    with response_context as response, RAW_RENEWABLE_FILE.open("wb") as output:
        shutil.copyfileobj(response, output)
    return RAW_RENEWABLE_FILE


if __name__ == "__main__":
    print(extract_renewable_generation())
