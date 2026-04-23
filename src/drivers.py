"""Additive variance decomposition of ΔCM into operational drivers.

Given a 'current' row and a 'baseline' row (prior month, prior year, or plan),
break the change in Contribution Margin into revenue & cost components so that
the sum of drivers approximately equals the observed ΔCM.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd


REV_COMPONENTS = [
    ("Revenue — Fixed price",  "revenue_fixed"),
    ("Revenue — Hourly",       "revenue_hourly"),
    ("Revenue — Other",        "revenue_other"),
]

COST_COMPONENTS = [
    ("Labor — Direct",           "labor_direct",            +1),
    ("Labor — Overhead",         "labor_overhead",          +1),
    ("Labor — Vacation",         "vacation_cost",           +1),
    ("Labor — Sick leave",       "sick_cost",               +1),
    ("Labor — Training/Onboard", "training_cost",           +1),
    ("Subcontractor — External", "subcontractor_external",  +1),
    ("Subcontractor — Group",    "subcontractor_group",     +1),
    ("Subcontractor — Division", "subcontractor_division",  +1),
    ("Internal service EL1",     "internal_service_el1",    +1),
    ("Internal service EL2",     "internal_service_el2",    +1),
    ("Travel costs",             "travel_cost",             +1),
    ("Material costs",           "material_cost",           +1),
    ("Vehicle costs",            "vehicle_cost",            +1),
]


@dataclass
class Driver:
    name: str
    kind: str            # "revenue" or "cost"
    delta_eur: float     # € contribution to ΔCM (positive = good for CM)
    current: float
    baseline: float

    def as_dict(self) -> dict:
        return asdict(self)


def _v(row: pd.Series, col: str) -> float:
    x = row.get(col)
    try:
        return 0.0 if pd.isna(x) else float(x)
    except TypeError:
        return 0.0


def decompose(current: pd.Series, baseline: pd.Series) -> list[Driver]:
    """Return a list of Driver objects ranked by |delta_eur|.

    ΔCM contribution = +(Δrevenue_component) for revenue lines
                      = -(Δcost_component)    for cost lines
    (a cost increase reduces CM, so its contribution to ΔCM is negative)
    """
    drivers: list[Driver] = []

    for name, col in REV_COMPONENTS:
        cur, base = _v(current, col), _v(baseline, col)
        if cur == 0 and base == 0:
            continue
        drivers.append(Driver(name=name, kind="revenue",
                              delta_eur=cur - base, current=cur, baseline=base))

    # Fallback: if no breakdown columns populated, use total revenue
    if not any(d.kind == "revenue" for d in drivers):
        cur, base = _v(current, "revenue_total"), _v(baseline, "revenue_total")
        if cur != 0 or base != 0:
            drivers.append(Driver(name="Revenue — Total", kind="revenue",
                                  delta_eur=cur - base, current=cur, baseline=base))

    for name, col, _sign in COST_COMPONENTS:
        cur, base = _v(current, col), _v(baseline, col)
        if cur == 0 and base == 0:
            continue
        # cost ↑ ⇒ CM ↓, so contribution = -(Δcost)
        drivers.append(Driver(name=name, kind="cost",
                              delta_eur=-(cur - base), current=cur, baseline=base))

    drivers.sort(key=lambda d: abs(d.delta_eur), reverse=True)
    return drivers


def observed_delta(current: pd.Series, baseline: pd.Series,
                   cm_col: str = "cm_db") -> float:
    return _v(current, cm_col) - _v(baseline, cm_col)


def residual(drivers: list[Driver], observed: float) -> float:
    modeled = sum(d.delta_eur for d in drivers)
    return observed - modeled


def to_waterfall_df(drivers: list[Driver], observed: float,
                    top_k: int = 8) -> pd.DataFrame:
    """Waterfall-ready DataFrame: baseline → top drivers → residual → current.

    We keep top_k drivers by |impact| and aggregate the rest into 'Other drivers'.
    """
    kept = drivers[:top_k]
    other_sum = sum(d.delta_eur for d in drivers[top_k:])
    rows = [{"label": d.name, "delta": d.delta_eur, "kind": d.kind} for d in kept]
    if other_sum != 0:
        rows.append({"label": "Other drivers", "delta": other_sum, "kind": "other"})
    res = residual(drivers, observed)
    rows.append({"label": "Unexplained residual", "delta": res, "kind": "residual"})
    return pd.DataFrame(rows)


def pick_baseline(df_cc: pd.DataFrame, current_period, mode: str = "mom") -> pd.Series | None:
    """For a single-cost-center sorted df, return the baseline row for the mode."""
    df_cc = df_cc.sort_values("period")
    if mode == "mom":
        target = current_period - pd.DateOffset(months=1)
    elif mode == "yoy":
        target = current_period - pd.DateOffset(years=1)
    elif mode == "plan":
        # plan baseline: use current row but swap cm_db for cm_planned via caller
        return None
    else:
        raise ValueError(mode)
    match = df_cc[df_cc["period"] == target]
    return match.iloc[0] if not match.empty else None


def build_plan_baseline(current: pd.Series) -> pd.Series:
    """Synthesize a baseline row that reflects planned CM for vs-plan decomposition.

    We do not have a full planned P&L row, so for vs-plan analysis we use
    the ΔCM delta against cm_planned as a single 'Plan gap' driver rather
    than a full bridge. Called by the UI layer when mode='plan'.
    """
    base = current.copy()
    base["cm_db"] = current.get("cm_planned", 0.0)
    return base
