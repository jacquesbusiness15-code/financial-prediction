"""Additive variance decomposition of delta-CM into operational drivers."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd


REV_COMPONENTS = [
    ("Revenue - Fixed price", "revenue_fixed"),
    ("Revenue - Hourly",      "revenue_hourly"),
    ("Revenue - Other",       "revenue_other"),
]

COST_COMPONENTS = [
    ("Labor - Direct",           "labor_direct",           +1),
    ("Labor - Overhead",         "labor_overhead",         +1),
    ("Labor - Vacation",         "vacation_cost",          +1),
    ("Labor - Sick leave",       "sick_cost",              +1),
    ("Labor - Training/Onboard", "training_cost",          +1),
    ("Subcontractor - External", "subcontractor_external", +1),
    ("Subcontractor - Group",    "subcontractor_group",    +1),
    ("Subcontractor - Division", "subcontractor_division", +1),
    ("Internal service EL1",     "internal_service_el1",   +1),
    ("Internal service EL2",     "internal_service_el2",   +1),
    ("Travel costs",             "travel_cost",            +1),
    ("Material costs",           "material_cost",          +1),
    ("Vehicle costs",            "vehicle_cost",           +1),
]


@dataclass
class Driver:
    name: str
    kind: str            # "revenue" or "cost"
    delta_eur: float     # contribution to delta-CM in EUR (positive = good for CM)
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


_PLAN_OFFSETS = {"mom": pd.DateOffset(months=1), "yoy": pd.DateOffset(years=1)}


def decompose(current: pd.Series, baseline: pd.Series) -> list[Driver]:
    """Return Driver rows ranked by |delta_eur|. Cost deltas are negated
    because a cost increase reduces CM."""
    drivers: list[Driver] = []

    for name, col in REV_COMPONENTS:
        cur, base = _v(current, col), _v(baseline, col)
        if cur or base:
            drivers.append(Driver(name, "revenue", cur - base, cur, base))

    if not any(d.kind == "revenue" for d in drivers):
        cur, base = _v(current, "revenue_total"), _v(baseline, "revenue_total")
        if cur or base:
            drivers.append(Driver("Revenue - Total", "revenue", cur - base, cur, base))

    for name, col, _sign in COST_COMPONENTS:
        cur, base = _v(current, col), _v(baseline, col)
        if cur or base:
            drivers.append(Driver(name, "cost", -(cur - base), cur, base))

    drivers.sort(key=lambda d: abs(d.delta_eur), reverse=True)
    return drivers


def observed_delta(current: pd.Series, baseline: pd.Series,
                   cm_col: str = "cm_db") -> float:
    return _v(current, cm_col) - _v(baseline, cm_col)


def residual(drivers: list[Driver], observed: float) -> float:
    return observed - sum(d.delta_eur for d in drivers)


def to_waterfall_df(drivers: list[Driver], observed: float,
                    top_k: int = 8) -> pd.DataFrame:
    rows = [{"label": d.name, "delta": d.delta_eur, "kind": d.kind}
            for d in drivers[:top_k]]
    other_sum = sum(d.delta_eur for d in drivers[top_k:])
    if other_sum:
        rows.append({"label": "Other drivers", "delta": other_sum, "kind": "other"})
    rows.append({"label": "Unexplained residual",
                 "delta": residual(drivers, observed), "kind": "residual"})
    return pd.DataFrame(rows)


def pick_baseline(df_cc: pd.DataFrame, current_period, mode: str = "mom") -> pd.Series | None:
    if mode == "plan":
        # vs-plan: caller uses build_plan_baseline instead.
        return None
    try:
        offset = _PLAN_OFFSETS[mode]
    except KeyError as e:
        raise ValueError(mode) from e
    target = current_period - offset
    match = df_cc.sort_values("period").loc[lambda d: d["period"] == target]
    return match.iloc[0] if not match.empty else None


def build_plan_baseline(current: pd.Series) -> pd.Series:
    base = current.copy()
    base["cm_db"] = current.get("cm_planned", 0.0)
    return base
