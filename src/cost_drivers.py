"""Trace each issue back to the exact data columns that caused it.

Where ``solution_finder.diagnose`` surfaces high-level issue codes
("labor_overrun", "subcontractor_creep", ...), this module drills one
level deeper: for a given issue and a given contract's history, it
identifies the specific cost columns (``labor_direct``,
``vacation_cost``, ``subcontractor_external``, ...) that drove the issue
and maps each to a concrete sub-action that would fix it.

Example:
    Issue: labor_overrun (labor_ratio 0.91 vs plan 0.75)
    Drivers:
      - labor_direct:  +42% vs 3-month avg  -> audit overtime / scheduling
      - vacation_cost: +180% vs 3-month avg -> review holiday stacking
      - sick_cost:     +95%  vs 3-month avg -> absence intervention
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import math
import pandas as pd


BASELINE_WINDOW_MONTHS = 3

# Columns whose movement can explain each issue, plus the recommended
# sub-action that directly targets that cost column.
ISSUE_DRIVER_COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    "labor_overrun": (
        ("labor_direct",   "audit_overtime"),
        ("labor_overhead", "reduce_labor_overhead"),
        ("training_cost",  "shorten_onboarding"),
        ("vacation_cost",  "stagger_vacations"),
        ("sick_cost",      "absence_intervention"),
    ),
    "subcontractor_creep": (
        ("subcontractor_external", "renegotiate_external_rates"),
        ("subcontractor_group",    "rebalance_group_sourcing"),
        ("subcontractor_division", "rebalance_division_sourcing"),
    ),
    "absence_spike": (
        ("sick_cost",     "absence_intervention"),
        ("vacation_cost", "stagger_vacations"),
    ),
    "productivity_drop": (
        ("labor_direct",  "audit_overtime"),
        ("hours_break",   "reduce_break_overrun"),
        ("hours_training", "shorten_onboarding"),
    ),
    "quality_gap": (
        ("training_cost", "shorten_onboarding"),
        ("labor_direct",  "audit_overtime"),
    ),
    "plan_gap_widening": (
        ("labor_cost_total",            "labor_cost_audit"),
        ("subcontractor_services_total","renegotiate_external_rates"),
        ("material_cost",               "procurement_review"),
        ("vehicle_cost",                "fleet_audit"),
        ("travel_cost",                 "travel_policy_review"),
    ),
    "sustained_loss": (
        ("labor_cost_total",            "labor_cost_audit"),
        ("subcontractor_services_total","renegotiate_external_rates"),
        ("material_cost",               "procurement_review"),
        ("vehicle_cost",                "fleet_audit"),
    ),
    "revenue_shortfall": (
        ("revenue_hourly", "reprice_hourly_detail"),
        ("revenue_fixed",  "renegotiate_fixed_price"),
    ),
    "renewal_risk": (
        ("revenue_total", "renewal_outreach_detail"),
    ),
}

# Minimum relative move a column must show vs its baseline to count as a
# driver. Without this, near-zero columns produce noisy percentages.
MIN_DELTA_ABS_EUR = 0.0
MIN_DELTA_REL = 0.05  # 5% change vs 3-month baseline


@dataclass(frozen=True)
class CostDriver:
    column: str
    current_eur: float
    baseline_eur: float
    delta_eur: float         # positive = grew (bad for costs, good for revenue)
    delta_pct: float | None  # vs baseline; None when baseline == 0
    sub_action_id: str       # catalog key, resolved via i18n (action.<id>.title)
    share_of_issue: float    # 0..1 share of the issue's total abs delta


def _num(row: pd.Series, key: str) -> float:
    v = row.get(key)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    return v


def _baseline_mean(history: pd.DataFrame, column: str,
                   exclude_last: bool = True,
                   window: int = BASELINE_WINDOW_MONTHS) -> float:
    if history is None or history.empty or column not in history.columns:
        return 0.0
    series = pd.to_numeric(history[column], errors="coerce").dropna()
    if exclude_last and len(series) >= 2:
        series = series.iloc[:-1]
    if series.empty:
        return 0.0
    return float(series.tail(window).mean())


def identify_drivers_for_issue(
    issue_code: str,
    latest_row: pd.Series,
    history: pd.DataFrame,
    top_n: int = 3,
) -> list[CostDriver]:
    """Return the top cost columns that drove ``issue_code`` this month.

    Each returned ``CostDriver`` points at the data column that moved, by
    how much vs its 3-month baseline, and the sub-action id that directly
    targets that column.
    """
    mapping = ISSUE_DRIVER_COLUMNS.get(issue_code)
    if not mapping:
        return []

    candidates: list[CostDriver] = []
    for column, sub_action_id in mapping:
        current = _num(latest_row, column)
        baseline = _baseline_mean(history, column)
        delta = current - baseline
        delta_pct = (delta / baseline) if baseline else None

        # Filter: need a material move in the "bad" direction.
        if not _is_bad_direction(issue_code, column, delta):
            continue
        if abs(delta) <= MIN_DELTA_ABS_EUR and (delta_pct is None
                                                or abs(delta_pct) < MIN_DELTA_REL):
            continue

        candidates.append(CostDriver(
            column=column,
            current_eur=current,
            baseline_eur=baseline,
            delta_eur=delta,
            delta_pct=delta_pct,
            sub_action_id=sub_action_id,
            share_of_issue=0.0,  # filled below
        ))

    if not candidates:
        return []

    total_abs = sum(abs(c.delta_eur) for c in candidates) or 1.0
    sized = [
        CostDriver(
            column=c.column, current_eur=c.current_eur,
            baseline_eur=c.baseline_eur, delta_eur=c.delta_eur,
            delta_pct=c.delta_pct, sub_action_id=c.sub_action_id,
            share_of_issue=abs(c.delta_eur) / total_abs,
        ) for c in candidates
    ]
    sized.sort(key=lambda c: abs(c.delta_eur), reverse=True)
    return sized[:top_n]


def _is_bad_direction(issue_code: str, column: str, delta: float) -> bool:
    """Grew costs are bad; shrunk revenue is bad."""
    if column.startswith("revenue_"):
        return delta < 0
    return delta > 0


def evidence_text(driver: CostDriver) -> str:
    """Compact one-line evidence summary for table cells."""
    pct = driver.delta_pct
    if pct is None:
        return f"{driver.column}: {driver.current_eur:+,.0f} EUR"
    return f"{driver.column}: {pct:+.0%} vs 3M avg"


__all__ = [
    "CostDriver",
    "ISSUE_DRIVER_COLUMNS",
    "identify_drivers_for_issue",
    "evidence_text",
]
