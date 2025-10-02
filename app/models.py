from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IngestKind(str, Enum):
    TOTAL_PIPELINE_OVERVIEW = "total_pipeline_overview"
    TOTAL_DEAL_VALUE_PIPELINE = "total_deal_value_pipeline"
    QUALIFICATION_WEIGHTED_PIPELINE = "qualification_weighted_pipeline"
    PIPELINE_PROGRESSION = "pipeline_progression"
    WON_LOST_ANALYSIS = "won_lost_analysis"
    REP_OVERVIEWS = "rep_overviews"
    REP_ANALYSIS_FOCUS = "rep_analysis_focus"
    REP_ANALYSES = "rep_analyses"
    REP_INSIGHTS = "rep_insights"
    PIPELINE_DEALS = "pipeline_deals"
    PIPELINE_METRICS = "pipeline_metrics"
    PIPELINE_STAGES = "pipeline_stages"
    TEAM_PERFORMANCE = "team_performance"
    REP_RGA_DATA = "rep_rga_data"
    PIPELINE_DEVELOPMENT = "pipeline_development"


class IngestBody(BaseModel):
    kind: IngestKind
    runId: str | None = Field(default=None, min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    ok: bool = True
    kind: IngestKind
    runId: str

