from __future__ import annotations

from typing import Any, Callable

from .models import IngestKind

JsonNormalizer = Callable[[dict[str, Any]], dict[str, Any]]


def normalize_payload(kind: IngestKind, payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize incoming payloads to match the expected storage shape."""

    normalizers: dict[IngestKind, JsonNormalizer] = {
        IngestKind.TOTAL_PIPELINE_OVERVIEW: _ensure_strings(
            "weightedWeekTables", "topMovers", "totals", "aiAnalysis"
        ),
        IngestKind.TOTAL_DEAL_VALUE_PIPELINE: _ensure_strings(
            "weightedWeekTables", "topMovers", "totals", "aiAnalysis"
        ),
        IngestKind.QUALIFICATION_WEIGHTED_PIPELINE: _ensure_strings(
            "weightedWeekTables", "topMovers", "totals", "aiAnalysis"
        ),
        IngestKind.PIPELINE_PROGRESSION: _ensure_strings("chartData"),
        IngestKind.WON_LOST_ANALYSIS: _ensure_strings(
            "won_lost_summary", "tables", "chart_data"
        ),
        IngestKind.REP_OVERVIEWS: _ensure_strings("reps"),
        IngestKind.REP_ANALYSIS_FOCUS: _ensure_strings("representatives"),
        IngestKind.REP_ANALYSES: _normalize_rep_analyses,
        IngestKind.REP_INSIGHTS: _normalize_rep_insights,
        IngestKind.PIPELINE_DEALS: _coerce_list("deals"),
        IngestKind.PIPELINE_METRICS: _identity,
        IngestKind.PIPELINE_STAGES: _coerce_list("stages"),
        IngestKind.TEAM_PERFORMANCE: _coerce_list("members"),
        IngestKind.REP_RGA_DATA: _ensure_strings("tableByRep"),
        IngestKind.PIPELINE_DEVELOPMENT: _normalize_pipeline_development,
    }

    normalizer = normalizers.get(kind)
    if not normalizer:
        raise ValueError(f"Unsupported ingest kind: {kind}")

    return normalizer(dict(payload))


def _identity(payload: dict[str, Any]) -> dict[str, Any]:
    return payload


def _ensure_strings(*keys: str) -> JsonNormalizer:
    import json

    def wrapper(payload: dict[str, Any]) -> dict[str, Any]:
        for key in keys:
            if key in payload:
                payload[key] = json.dumps(payload[key], ensure_ascii=False)
        return payload

    return wrapper


def _coerce_list(key: str) -> JsonNormalizer:
    def wrapper(payload: dict[str, Any]) -> dict[str, Any]:
        if key not in payload or payload[key] is None:
            payload[key] = []
        elif not isinstance(payload[key], list):
            payload[key] = [payload[key]]
        return payload

    return wrapper


def _normalize_rep_analyses(payload: dict[str, Any]) -> dict[str, Any]:
    import json

    analyses = payload.get("analyses") or []
    normalized = []
    for entry in analyses:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "repName": entry.get("repName") or entry.get("name"),
                "summaryParagraph": entry.get("summaryParagraph"),
                "bulletPoints": entry.get("bulletPoints", []),
                "metrics": json.dumps(entry.get("metrics", {}), ensure_ascii=False),
            }
        )

    payload["analyses"] = normalized
    return payload


def _normalize_rep_insights(payload: dict[str, Any]) -> dict[str, Any]:
    import json

    insights = payload.get("insights") or []
    normalized = []
    for entry in insights:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "repName": entry.get("repName") or entry.get("name"),
                "analysisParagraph": entry.get("analysisParagraph"),
                "bulletPoints": entry.get("bulletPoints", []),
                "dealFlags": json.dumps(entry.get("dealFlags", {}), ensure_ascii=False),
            }
        )

    payload["insights"] = normalized
    return payload


def _normalize_pipeline_development(payload: dict[str, Any]) -> dict[str, Any]:
    import json

    insights = payload.get("insights") or []
    payload["insights"] = [insight for insight in insights if isinstance(insight, dict)]
    if "totals" in payload:
        payload["totals"] = json.dumps(payload["totals"], ensure_ascii=False)
    return payload

