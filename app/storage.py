from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from .firebase import fetch_all_runs, fetch_run, write_payload


def upsert_payload(run_id: str, kind: str, payload: dict[str, Any]) -> None:
    write_payload(run_id, kind, payload)


def get_run(run_id: str) -> dict[str, Any] | None:
    return fetch_run(run_id)


def get_runs_matching_window(since: str, until: str) -> dict[str, dict[str, Any]]:
    all_runs = fetch_all_runs()
    filtered: dict[str, dict[str, Any]] = {}

    since_date = _coerce_date(since)
    until_date = _coerce_date(until)
    if since_date is None or until_date is None:
        raise ValueError("since and until must be valid ISO dates (YYYY-MM-DD)")

    for run_id, payload in all_runs.items():
        window = _extract_window_dates(run_id)
        if window is None:
            continue
        start_date, end_date = window

        if start_date == since_date and end_date == until_date:
            filtered[run_id] = payload

    return filtered


def _coerce_date(value: str):
    if not value:
        return None
    value = _sanitize_input(value)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _extract_window_dates(run_id: str):
    parts = run_id.split("_")
    if len(parts) < 3:
        return None
    start_raw = parts[-2].strip()
    end_raw = parts[-1].strip()

    start_dt = _coerce_datetime(start_raw)
    end_dt = _coerce_datetime(end_raw)

    if start_dt is None or end_dt is None:
        return None

    return start_dt.date(), end_dt.date()


def _coerce_datetime(value: str):
    value = _sanitize_input(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


_SANITIZE_PATTERN = re.compile(r"^[\"']|[\"']$")


def _sanitize_input(value: str) -> str:
    cleaned = value.strip().replace("^", "")
    cleaned = _SANITIZE_PATTERN.sub("", cleaned)
    return cleaned

