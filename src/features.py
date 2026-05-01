"""Derived KPIs and rolling time-series features per cost center."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a / b.replace(0, np.nan)


def _col(df: pd.DataFrame, name: str, fill: float = np.nan) -> pd.Series:
    if name in df.columns:
        return df[name] if np.isnan(fill) else df[name].fillna(fill)
    return pd.Series(fill, index=df.index, dtype="float64")


def add_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["productivity_ratio"] = _safe_div(_col(df, "hours_productive"), _col(df, "hours_actual"))
    df["training_intensity"] = _safe_div(_col(df, "hours_training"), _col(df, "hours_actual"))

    abs_cost = _col(df, "vacation_cost", 0.0) + _col(df, "sick_cost", 0.0)
    df["absence_rate"] = _safe_div(abs_cost, _col(df, "labor_cost_total"))

    subc = (_col(df, "subcontractor_group", 0.0)
            + _col(df, "subcontractor_division", 0.0)
            + _col(df, "subcontractor_external", 0.0))
    cost_total = (_col(df, "labor_cost_total", 0.0)
                  + _col(df, "material_cost", 0.0)
                  + _col(df, "vehicle_cost", 0.0)
                  + _col(df, "travel_cost", 0.0)
                  + subc)
    df["cost_total_db2"] = cost_total
    df["subcontractor_total"] = subc
    df["subcontractor_share"] = _safe_div(subc, cost_total)

    df["labor_cost_per_productive_hour"] = _safe_div(
        _col(df, "labor_cost_total"), _col(df, "hours_productive"))
    df["labor_ratio"] = _safe_div(_col(df, "labor_cost_total"), _col(df, "revenue_total"))
    df["quality_gap"] = _col(df, "quality_actual") - _col(df, "quality_target")

    if "cm_planned" in df.columns and "cm_db" in df.columns:
        df["cm_vs_plan_delta"] = df["cm_db"] - df["cm_planned"]
        df["cm_vs_plan_pct"] = _safe_div(df["cm_vs_plan_delta"], df["cm_planned"])

    return df


_DELTA_COLS = ("cm_db", "cm_db_pct", "cm_db1", "cm_db2",
               "revenue_total", "labor_cost_total")


def add_time_deltas(df: pd.DataFrame,
                    group_cols: tuple[str, ...] = ("cost_center_id",)
                    ) -> pd.DataFrame:
    # observed=True avoids the full cartesian product for categorical keys.
    df = df.sort_values([*group_cols, "period"]).copy()
    g = df.groupby(list(group_cols), sort=False, observed=True)

    for col in _DELTA_COLS:
        if col not in df.columns:
            continue
        prev_1 = g[col].shift(1)
        df[f"{col}_mom"] = df[col] - prev_1
        df[f"{col}_yoy"] = df[col] - g[col].shift(12)
        df[f"{col}_mom_pct"] = _safe_div(df[f"{col}_mom"], prev_1.abs())

    if "cm_db_pct" in df.columns:
        roll = g["cm_db_pct"].rolling(6, min_periods=3)
        df["cm_db_pct_roll6_mean"] = roll.mean().reset_index(level=0, drop=True)
        df["cm_db_pct_roll6_std"] = roll.std().reset_index(level=0, drop=True)

    return df.reset_index(drop=True)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    from src.data_quality import annotate as _annotate_dq  # local import avoids cycle
    return _annotate_dq(add_time_deltas(add_kpis(df)))
