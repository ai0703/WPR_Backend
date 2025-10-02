from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


BASE_URL = os.getenv("RUNS_API_BASE_URL", "http://127.0.0.1:5000")
DEFAULT_TOKEN = "1234567"


def fetch_runs(since: str, until: str, token: str | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}/api/runs"
    headers = {"Authorization": f"Bearer {token or os.getenv('INGEST_TOKEN', DEFAULT_TOKEN)}"}
    params = {"since": since, "until": until}

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    data = fetch_runs("2025-09-08 00:00:00", "2025-09-14 23:59:59")

    output_path = Path("scripts") / "runs_window_response.json"
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Status: ok")
    print(f"Saved response to {output_path}")


if __name__ == "__main__":
    main()


