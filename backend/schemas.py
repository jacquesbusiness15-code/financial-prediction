"""Pydantic models for REST API requests & responses.

These mirror the dataclasses in src/drivers.py and src/data_loader.py but are
JSON-serializable for FastAPI.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- Dataset lifecycle ----------


class LoadDatasetRequest(BaseModel):
    source: str = Field(
        ...,
        description=(
            "Local path (data/foo.xlsx), HTTP URL to a CSV, or a Google "
            "Sheets share/publish URL. Google Sheets URLs are auto-converted "
            "to their CSV export form."
        ),
    )


class SchemaReportOut(BaseModel):
    matched: list[str]
    unmapped_input: list[str]
    missing_expected: list[str]
    missing_critical: list[str]
    strategy: Literal["header", "position"]
    expected_total: int
    ok: bool


class DatasetSummary(BaseModel):
    rows: int
    columns: int
    period_min: str | None = None
    period_max: str | None = None
    regions: int | None = None
    cost_centers: int | None = None
    revenue_total: float | None = None
    cm_db_total: float | None = None


class DatasetFacets(BaseModel):
    regions: list[str]
    services: list[str]
    period_min: str | None = None
    period_max: str | None = None


class LoadDatasetResponse(BaseModel):
    dataset_id: str
    summary: DatasetSummary
    schema_report: SchemaReportOut
    facets: DatasetFacets


# ---------- Portfolio ----------


class KpiBlock(BaseModel):
    revenue: float
    cm_db: float
    cm_planned: float
    plan_gap: float
    cost_centers: int
    anomalies_count: int


class HeatmapPayload(BaseModel):
    row_dim: Literal["region", "cost_center"]
    rows: list[str]
    columns: list[str]                       # ISO period strings
    z: list[list[float | None]]              # cm_db_pct matrix, rows × cols


class AnomalyRow(BaseModel):
    period: str
    region: str | None = None
    cost_center_id: str
    cost_center_name: str | None = None
    customer_name: str | None = None
    service_type: str | None = None
    cm_db: float | None = None
    cm_db_pct: float | None = None
    labor_ratio: float | None = None
    cm_db_mom: float | None = None
    cm_db_yoy: float | None = None
    cm_vs_plan_delta: float | None = None
    impact_eur: float
    severity: str
    anomaly_reasons: str


class TopCostCenter(BaseModel):
    cost_center_id: str
    cost_center_name: str | None = None
    region: str | None = None
    revenue_total: float
    cm_db: float
    cm_db_pct: float | None = None


class PortfolioResponse(BaseModel):
    kpis: KpiBlock
    heatmap: HeatmapPayload
    top_cost_centers: list[TopCostCenter]
    top_anomalies: list[AnomalyRow]


# ---------- Deep Dive ----------


class DriverOut(BaseModel):
    name: str
    kind: Literal["revenue", "cost", "other", "residual"]
    delta_eur: float
    current: float | None = None
    baseline: float | None = None


class WaterfallRow(BaseModel):
    label: str
    delta: float
    kind: str


class TimelinePoint(BaseModel):
    period: str
    cm_db: float | None = None
    cm_planned: float | None = None


class PeerKpi(BaseModel):
    kpi: str
    value: float
    peer_median: float
    peer_p25: float
    peer_p75: float
    percentile: float


class HistoryStats(BaseModel):
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    last_12m_mean: float | None = None


class DeepDiveResponse(BaseModel):
    cost_center_id: str
    cost_center_name: str | None = None
    region: str | None = None
    service_type: str | None = None
    period: str
    baseline_label: str
    observed_delta: float
    modeled_delta: float
    residual: float
    residual_pct: float | None = None
    drivers: list[DriverOut]
    waterfall: list[WaterfallRow]
    timeline: list[TimelinePoint]
    kpis_vs_peers: list[PeerKpi]
    history_stats: HistoryStats
    labor_ratio: float | None = None
    cm_current: float
    cm_baseline: float
    cm_current_pct: float | None = None
    hour_variance: float | None = None
    dq_accrual_flag: bool = False
    manager_comment: str | None = None


# ---------- Early Warnings ----------


class WarningRow(BaseModel):
    cost_center_id: str
    cost_center_name: str | None = None
    region: str | None = None
    customer_name: str | None = None
    service_type: str | None = None
    period: str
    signal: str
    severity: str
    detail: str
    impact_eur: float


class WarningsResponse(BaseModel):
    warnings: list[WarningRow]
    counts: dict[str, int]              # {"high": n, "medium": n, "low": n}
    total_impact_eur: float


# ---------- Plan vs Actual ----------


class PlanVsActualMonth(BaseModel):
    period: str
    revenue: float
    planned: float
    actual: float
    gap_eur: float
    gap_pct: float | None = None


class PlanVsActualResponse(BaseModel):
    months: list[PlanVsActualMonth]
    total_actual: float
    total_planned: float
    total_gap: float
    worst_month: str | None = None


# ---------- Chat / Explain ----------


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ExplainRequest(BaseModel):
    cost_center_id: str
    period: str                                      # ISO yyyy-mm-dd
    baseline_mode: Literal["mom", "yoy", "plan"] = "mom"


# ---------- Facility Overview (single-facility dashboard) ----------


class DriverItemOut(BaseModel):
    class_key: str                                  # "labor" | "absence" | ...
    icon: str
    title_key: str                                  # i18n key (e.g. "driver.labor")
    sub_key: str
    pct_change: float | None = None
    delta_eur: float


class ActionItemOut(BaseModel):
    key: str                                        # "shift" | "absence" | ...
    icon: str
    title_key: str
    sub_key: str
    impact_pct: float                               # ratio points, e.g. 0.032


class SparklinePointOut(BaseModel):
    period: str
    margin: float


class FacilityOverviewResponse(BaseModel):
    cost_center_id: str
    cost_center_name: str | None = None
    region: str | None = None
    service_type: str | None = None
    period: str
    icon: str
    status: Literal["critical", "warn", "healthy"]
    margin_pct: float | None = None
    margin_mom_delta: float | None = None
    sparkline: list[SparklinePointOut]
    worst_drivers: list[DriverItemOut]
    recommended_actions: list[ActionItemOut]
    baseline_headcount: float
    team_size_suggestion: int


# ---------- What-if simulator ----------


class SimulateTeamSizeRequest(BaseModel):
    cost_center_id: str
    new_headcount: float
    baseline_headcount: float | None = None
    period: str | None = None                       # optional month override


class SimulateTeamSizeResponse(BaseModel):
    baseline_headcount: float
    new_headcount: float
    baseline_margin: float
    new_margin: float
    delta_margin: float
    productivity_gain_pct: float
    new_cm_eur: float
