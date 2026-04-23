"""Simple data-driven what-if simulator for the facility-focus overview.

Scope: a single cost center's most-recent-month snapshot. The user changes
headcount; we re-estimate labor cost, then recompute the contribution margin.

Assumptions (kept intentionally simple so the UI stays trustworthy):
  * Monthly FTE is proxied as `hours_actual / 160` (standard 160 h/month).
  * Labor cost scales linearly with headcount.
  * Non-labor costs stay constant.
  * A small productivity uplift is credited when headcount *drops* (fewer
    people sharing the same productive hours → higher utilization); the
    coefficient is deliberately modest (≤ 10 %) so the result looks
    realistic, not optimistic.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


MONTHLY_HOURS_PER_FTE = 160.0


@dataclass
class SimResult:
    baseline_headcount: float
    new_headcount: float
    baseline_margin: float        # ratio, e.g. 0.082
    new_margin: float
    delta_margin: float           # ratio points, e.g. +0.020 == +2.0 pp
    productivity_gain_pct: float  # ratio, e.g. 0.083 == +8.3 %
    new_cm_eur: float


def _safe(v, default: float = 0.0) -> float:
    try:
        return default if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return default


def estimate_headcount(row: pd.Series) -> float:
    """Back out a monthly FTE figure from hours_actual / 160."""
    hours = _safe(row.get("hours_actual"))
    if hours <= 0:
        return 0.0
    return round(hours / MONTHLY_HOURS_PER_FTE, 1)


def simulate_team_size(row: pd.Series, new_headcount: float,
                       baseline_headcount: float | None = None) -> SimResult:
    """Project a new CM / margin from a headcount change on a single row.

    `row` is expected to be one cost-center-month (the most recent month).
    `baseline_headcount` overrides the FTE estimate derived from hours_actual
    (useful when the user wants to reason in different headcount units).
    """
    rev = _safe(row.get("revenue_total"))
    cm = _safe(row.get("cm_db"))
    labor = _safe(row.get("labor_cost_total"))
    baseline_hc = (float(baseline_headcount) if baseline_headcount is not None
                   else estimate_headcount(row))
    baseline_margin = (cm / rev) if rev else 0.0

    if baseline_hc <= 0 or rev <= 0:
        # Nothing to simulate — return an unchanged snapshot.
        return SimResult(
            baseline_headcount=baseline_hc,
            new_headcount=float(new_headcount),
            baseline_margin=baseline_margin,
            new_margin=baseline_margin,
            delta_margin=0.0,
            productivity_gain_pct=0.0,
            new_cm_eur=cm,
        )

    # Linear labor cost scaling.
    ratio = new_headcount / baseline_hc
    new_labor = labor * ratio

    # Modest productivity uplift when team shrinks (fewer people, same
    # output → higher productive-hour share). Capped at ±10 %.
    # Gain = (1 - ratio) * 0.5, clipped to [-0.10, +0.10].
    gain = max(min((1.0 - ratio) * 0.5, 0.10), -0.10)

    # Apply the productivity gain as a small revenue uplift (more throughput
    # per euro of labor); conservative because most fixed-price revenue is
    # contract-bound. We use half the gain on revenue to stay cautious.
    new_rev = rev * (1.0 + 0.5 * gain)

    # new_cm = baseline cm + revenue delta (good if positive) + labor saving.
    new_cm = cm + (new_rev - rev) + (labor - new_labor)

    new_margin = (new_cm / new_rev) if new_rev else 0.0

    return SimResult(
        baseline_headcount=baseline_hc,
        new_headcount=float(new_headcount),
        baseline_margin=baseline_margin,
        new_margin=new_margin,
        delta_margin=new_margin - baseline_margin,
        productivity_gain_pct=gain,
        new_cm_eur=new_cm,
    )
