"""Data-driven what-if simulator for the facility-focus overview.

Monthly FTE is proxied as hours_actual / 160. Labor cost scales linearly with
headcount; non-labor costs stay flat. A modest productivity uplift (capped at
+/-10%) is credited when headcount drops, applied as a half-weight revenue
uplift to stay conservative against fixed-price contract revenue.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


MONTHLY_HOURS_PER_FTE = 160.0
_PRODUCTIVITY_GAIN_CAP = 0.10


@dataclass
class SimResult:
    baseline_headcount: float
    new_headcount: float
    baseline_margin: float
    new_margin: float
    delta_margin: float
    productivity_gain_pct: float
    new_cm_eur: float


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


def _safe(v, default: float = 0.0) -> float:
    try:
        return default if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return default


def estimate_headcount(row: pd.Series) -> float:
    """Back out monthly FTE from hours_actual / 160."""
    hours = _safe(row.get("hours_actual"))
    if hours <= 0:
        return 0.0
    return round(hours / MONTHLY_HOURS_PER_FTE, 1)


def _baseline_hc(row: pd.Series, override: float | None) -> float:
    return float(override) if override is not None else estimate_headcount(row)


def _headcount_effect(rev: float, labor: float, ratio: float) -> tuple[float, float, float]:
    """Return (new_rev, new_labor, productivity_gain) for a given HC ratio.

    Gain = (1 - ratio) * 0.5, clipped to +/-10 %. Revenue picks up half the
    gain (fixed-price contracts dampen the upside).
    """
    gain = max(min((1.0 - ratio) * 0.5, _PRODUCTIVITY_GAIN_CAP),
               -_PRODUCTIVITY_GAIN_CAP)
    new_rev = rev * (1.0 + 0.5 * gain)
    new_labor = labor * ratio
    return new_rev, new_labor, gain


def simulate_team_size(row: pd.Series, new_headcount: float,
                       baseline_headcount: float | None = None) -> SimResult:
    """Project a new CM / margin from a headcount change on a single row."""
    rev = _safe(row.get("revenue_total"))
    cm = _safe(row.get("cm_db"))
    labor = _safe(row.get("labor_cost_total"))
    baseline_hc = _baseline_hc(row, baseline_headcount)
    baseline_margin = (cm / rev) if rev else 0.0

    if baseline_hc <= 0 or rev <= 0:
        return SimResult(
            baseline_headcount=baseline_hc,
            new_headcount=float(new_headcount),
            baseline_margin=baseline_margin,
            new_margin=baseline_margin,
            delta_margin=0.0,
            productivity_gain_pct=0.0,
            new_cm_eur=cm,
        )

    ratio = new_headcount / baseline_hc
    new_rev, new_labor, gain = _headcount_effect(rev, labor, ratio)
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


def simulate_multi(row: pd.Series, *,
                   new_headcount: float | None = None,
                   baseline_headcount: float | None = None,
                   absence_delta_pp: float = 0.0,
                   rate_delta_pct: float = 0.0,
                   subco_delta_pp: float = 0.0) -> MultiSimResult:
    """Compose headcount + absence + rate + subco levers into one what-if.

    `absence_delta_pp`/`subco_delta_pp` are pp (e.g. -0.02 = -2pp);
    `rate_delta_pct` is a percent change (e.g. +0.05 = +5%). Each lever's
    isolated CM/margin contribution is reported for waterfall rendering.
    """
    rev = _safe(row.get("revenue_total"))
    cm = _safe(row.get("cm_db"))
    labor = _safe(row.get("labor_cost_total"))
    subco_total = _safe(row.get("subcontractor_total"))
    baseline_margin = (cm / rev) if rev else 0.0

    contributions: list[LeverContribution] = []
    new_rev = rev
    new_cm = cm

    def add(name: str, delta_cm: float) -> None:
        contributions.append(LeverContribution(
            name=name,
            delta_cm_eur=delta_cm,
            delta_margin=(delta_cm / new_rev) if new_rev else 0.0,
        ))

    if new_headcount is not None:
        hc_res = simulate_team_size(
            row, new_headcount=new_headcount,
            baseline_headcount=baseline_headcount,
        )
        # Re-derive headcount-adjusted revenue so downstream levers chain off
        # the same internal formula simulate_team_size used.
        baseline_hc = _baseline_hc(row, baseline_headcount)
        if cm and baseline_hc > 0 and rev > 0:
            ratio = new_headcount / baseline_hc
            hc_rev, _, _ = _headcount_effect(rev, labor, ratio)
        else:
            hc_rev = new_rev * (hc_res.new_cm_eur / cm if cm else 1.0)
        new_rev = hc_rev
        new_cm = hc_res.new_cm_eur
        contributions.append(LeverContribution(
            name="headcount",
            delta_cm_eur=hc_res.new_cm_eur - cm,
            delta_margin=(new_cm / new_rev if new_rev else 0.0) - baseline_margin,
        ))

    # Absence: shifting paid-absent hours to productive saves that share of labor.
    if absence_delta_pp and labor > 0:
        delta = -absence_delta_pp * labor
        new_cm += delta
        add("absence", delta)

    # Billing rate: revenue scales by rate_delta_pct; CM absorbs the delta.
    if rate_delta_pct and rev > 0:
        delta_rev = rev * rate_delta_pct
        new_rev += delta_rev
        new_cm += delta_rev
        add("rate", delta_rev)

    # Subco share: delta_pp * (labor + subco) approximates the cost shift.
    if subco_delta_pp:
        total_cost = labor + subco_total
        if total_cost > 0:
            delta = -subco_delta_pp * total_cost
            new_cm += delta
            add("subco", delta)

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
