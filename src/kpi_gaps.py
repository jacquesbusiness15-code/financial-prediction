"""KPI gap detector: names additional data points that would sharpen the
cost-driver diagnosis for a given contract-period.

Rules fire when a driver class is material AND the disambiguating column
is missing/empty from the input row. Output is locale-stable: only i18n
keys are returned, so the UI and LLM layers pick the language.

Consumed by:
    - src.contract_detail_page    (renders a card for decision-makers)
    - src.llm_copilot              (enriches the ExplainContext so the AI
                                   cites the gaps instead of hallucinating)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd

from src.drivers import Driver


@dataclass(frozen=True)
class KpiGap:
    id: str
    title_key: str
    reason_key: str

    def as_dict(self) -> dict:
        return asdict(self)


_LABOR_CLASSES = {"labor", "training"}
_ABSENCE_CLASS = "absence"
_SUB_CLASS = "subcontractor"
_REVENUE_CLASS = "revenue"

_MATERIALITY_RATIO = 0.15  # driver counts as "material" at >=15% of |observed|
_RESIDUAL_RATIO = 0.10      # residual flagged when >=10% of |observed|

_GAP_DEFS: tuple[tuple[str, str, str], ...] = (
    ("overtime_hours",       "gaps.overtime_hours.title",       "gaps.overtime_hours.reason"),
    ("headcount_fte",        "gaps.headcount_fte.title",        "gaps.headcount_fte.reason"),
    ("absence_reason",       "gaps.absence_reason.title",       "gaps.absence_reason.reason"),
    ("subcontractor_hours",  "gaps.subcontractor_hours.title",  "gaps.subcontractor_hours.reason"),
    ("subcontractor_reason", "gaps.subcontractor_reason.title", "gaps.subcontractor_reason.reason"),
    ("billable_hours",       "gaps.billable_hours.title",       "gaps.billable_hours.reason"),
    ("price_per_hour",       "gaps.price_per_hour.title",       "gaps.price_per_hour.reason"),
    ("customer_churn",       "gaps.customer_churn.title",       "gaps.customer_churn.reason"),
    ("quality_kpi",          "gaps.quality_kpi.title",          "gaps.quality_kpi.reason"),
    ("plan_values",          "gaps.plan_values.title",          "gaps.plan_values.reason"),
    ("missing_driver",       "gaps.missing_driver.title",       "gaps.missing_driver.reason"),
)
_GAP_BY_ID: dict[str, KpiGap] = {d[0]: KpiGap(*d) for d in _GAP_DEFS}


def _is_empty(row: pd.Series, col: str) -> bool:
    if row is None or col not in row.index:
        return True
    v = row[col]
    try:
        return pd.isna(v) or float(v) == 0.0
    except (TypeError, ValueError):
        return True


def _classify(d: Driver) -> str:
    # Local import avoids cycle: facility_overview imports drivers.
    from src.facility_overview import classify_driver
    return classify_driver(d)


def _is_material(d: Driver, observed_delta: float) -> bool:
    if not observed_delta:
        return abs(d.delta_eur) > 0
    return abs(d.delta_eur) >= _MATERIALITY_RATIO * abs(observed_delta)


def detect_gaps(current: pd.Series,
                drivers_list: list[Driver] | None,
                observed_delta: float,
                residual_eur: float,
                limit: int = 4) -> list[KpiGap]:
    """Return up to ``limit`` relevant gaps, in priority order.

    Priority follows the order of rules below — gaps tied to material drivers
    come first; structural gaps (plan, quality, residual) come last.
    """
    out: list[KpiGap] = []
    seen: set[str] = set()

    def add(gap_id: str) -> None:
        if gap_id in seen:
            return
        gap = _GAP_BY_ID.get(gap_id)
        if gap is None:
            return
        seen.add(gap_id)
        out.append(gap)

    drivers_list = drivers_list or []
    material_classes = {
        _classify(d) for d in drivers_list if _is_material(d, observed_delta)
    }

    if material_classes & _LABOR_CLASSES:
        if _is_empty(current, "overtime_hours"):
            add("overtime_hours")
        if _is_empty(current, "headcount_fte") and _is_empty(current, "fte_count"):
            add("headcount_fte")

    if _ABSENCE_CLASS in material_classes:
        if _is_empty(current, "sick_days") and _is_empty(current, "absence_days"):
            add("absence_reason")
        if _is_empty(current, "headcount_fte") and _is_empty(current, "fte_count"):
            add("headcount_fte")

    if _SUB_CLASS in material_classes:
        if _is_empty(current, "subcontractor_hours"):
            add("subcontractor_hours")
        if _is_empty(current, "subcontractor_reason"):
            add("subcontractor_reason")

    if _REVENUE_CLASS in material_classes:
        if _is_empty(current, "billable_hours") and _is_empty(current, "hours_billed"):
            add("billable_hours")
        if _is_empty(current, "price_per_hour") and _is_empty(current, "revenue_rate"):
            add("price_per_hour")
        if _is_empty(current, "customer_churn_flag"):
            add("customer_churn")

    if _is_empty(current, "quality_actual") and _is_empty(current, "quality_gap"):
        add("quality_kpi")
    if _is_empty(current, "cm_planned"):
        add("plan_values")

    if observed_delta and abs(residual_eur) >= _RESIDUAL_RATIO * abs(observed_delta):
        add("missing_driver")

    return out[:limit]
