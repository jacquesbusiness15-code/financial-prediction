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


@dataclass
class LeverContribution:
    name: str
    delta_cm_eur: float
    delta_margin: float


@dataclass
class MultiSimResult:
    baseline_margin: float
    new_margin: float
    delta_margin: float
    baseline_cm_eur: float
    new_cm_eur: float
    delta_cm_eur: float
    contributions: list[LeverContribution]


def simulate_multi(row: pd.Series, *,
                   new_headcount: float | None = None,
                   baseline_headcount: float | None = None,
                   absence_delta_pp: float = 0.0,
                   rate_delta_pct: float = 0.0,
                   subco_delta_pp: float = 0.0) -> MultiSimResult:
    """Compose headcount + three extra levers into one what-if result.

    All deltas are expressed relative to the current month: `absence_delta_pp`
    and `subco_delta_pp` are percentage-points (e.g. -0.02 = -2pp), and
    `rate_delta_pct` is a percent change (e.g. +0.05 = +5%).

    The result reports each lever's isolated contribution so the UI can render
    a waterfall.
    """
    rev = _safe(row.get("revenue_total"))
    cm = _safe(row.get("cm_db"))
    labor = _safe(row.get("labor_cost_total"))
    subco_total = _safe(row.get("subcontractor_total"))
    absence_rate = _safe(row.get("absence_rate"))
    baseline_margin = (cm / rev) if rev else 0.0

    contributions: list[LeverContribution] = []
    new_rev = rev
    new_cm = cm

    # Headcount lever (reuses simulate_team_size logic for consistency).
    if new_headcount is not None:
        hc_res = simulate_team_size(
            row,
            new_headcount=new_headcount,
            baseline_headcount=baseline_headcount,
        )
        hc_delta_cm = hc_res.new_cm_eur - cm
        # Propagate the headcount-adjusted revenue/cm as our new working point.
        hc_rev = new_rev * (
            hc_res.new_cm_eur / cm if cm else 1.0
        )  # fall back if cm is zero
        # Prefer the actual adjusted values from simulate_team_size:
        # recompute via the ratio used internally.
        if cm:
            # Derive headcount-adjusted revenue by re-running the internal
            # formula — keeps the chained levers consistent.
            baseline_hc = (float(baseline_headcount) if baseline_headcount is not None
                           else estimate_headcount(row))
            if baseline_hc > 0 and rev > 0:
                ratio = new_headcount / baseline_hc
                gain = max(min((1.0 - ratio) * 0.5, 0.10), -0.10)
                hc_rev = rev * (1.0 + 0.5 * gain)
        new_rev = hc_rev
        new_cm = hc_res.new_cm_eur
        contributions.append(LeverContribution(
            name="headcount",
            delta_cm_eur=hc_delta_cm,
            delta_margin=(new_cm / new_rev if new_rev else 0.0) - baseline_margin,
        ))

    # Absence lever: reducing absence shifts hours from idle-paid to productive.
    # Δ CM ≈ -Δ absence_rate * labor_cost (a drop in absence saves that share).
    if absence_delta_pp and labor > 0:
        abs_delta_cm = -absence_delta_pp * labor
        new_cm += abs_delta_cm
        contributions.append(LeverContribution(
            name="absence",
            delta_cm_eur=abs_delta_cm,
            delta_margin=(abs_delta_cm / new_rev) if new_rev else 0.0,
        ))

    # Billing-rate lever: revenue scales by rate_delta_pct; CM picks up the delta.
    if rate_delta_pct and rev > 0:
        rev_delta = rev * rate_delta_pct
        new_rev += rev_delta
        new_cm += rev_delta
        contributions.append(LeverContribution(
            name="rate",
            delta_cm_eur=rev_delta,
            delta_margin=(rev_delta / new_rev) if new_rev else 0.0,
        ))

    # Subcontractor-share lever: shifting share by pp changes subco cost by
    # (Δ pp * total_cost_base). We approximate total cost base as labor + subco.
    if subco_delta_pp:
        total_cost = labor + subco_total
        if total_cost > 0:
            subco_delta_cm = -subco_delta_pp * total_cost
            new_cm += subco_delta_cm
            contributions.append(LeverContribution(
                name="subco",
                delta_cm_eur=subco_delta_cm,
                delta_margin=(subco_delta_cm / new_rev) if new_rev else 0.0,
            ))

    new_margin = (new_cm / new_rev) if new_rev else 0.0

    return MultiSimResult(
        baseline_margin=baseline_margin,
        new_margin=new_margin,
        delta_margin=new_margin - baseline_margin,
        baseline_cm_eur=cm,
        new_cm_eur=new_cm,
        delta_cm_eur=new_cm - cm,
        contributions=contributions,
    )
