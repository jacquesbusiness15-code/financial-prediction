"""Derived KPIs + rolling time-series features per cost center."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    b = b.replace(0, np.nan)
    return a / b


def add_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Add operational KPIs and cost-structure ratios."""
    df = df.copy()

    df["productivity_ratio"] = _safe_div(
        df.get("hours_productive", pd.Series(np.nan, index=df.index)),
        df.get("hours_actual", pd.Series(np.nan, index=df.index)),
    )

    absence_hours = (df.get("vacation_cost", 0) * 0 +  # placeholder if only costs
                     0)
    # Prefer a true absence rate in € if hour breakdown for absence is not in the data:
    abs_cost = df.get("vacation_cost", 0).fillna(0) + df.get("sick_cost", 0).fillna(0)
    labor_total = df.get("labor_cost_total", np.nan)
    df["absence_rate"] = _safe_div(abs_cost, labor_total)

    df["training_intensity"] = _safe_div(
        df.get("hours_training", pd.Series(np.nan, index=df.index)),
        df.get("hours_actual", pd.Series(np.nan, index=df.index)),
    )

    subc = (df.get("subcontractor_group", 0).fillna(0)
            + df.get("subcontractor_division", 0).fillna(0)
            + df.get("subcontractor_external", 0).fillna(0))
    cost_total = (df.get("labor_cost_total", 0).fillna(0)
                  + df.get("material_cost", 0).fillna(0)
                  + df.get("vehicle_cost", 0).fillna(0)
                  + df.get("travel_cost", 0).fillna(0)
                  + subc)
    df["cost_total_db2"] = cost_total
    df["subcontractor_total"] = subc
    df["subcontractor_share"] = _safe_div(subc, cost_total)

    df["labor_cost_per_productive_hour"] = _safe_div(
        df.get("labor_cost_total", np.nan),
        df.get("hours_productive", np.nan),
    )

    df["labor_ratio"] = _safe_div(
        df.get("labor_cost_total", np.nan),
        df.get("revenue_total", np.nan),
    )

    df["quality_gap"] = (df.get("quality_actual", np.nan)
                        - df.get("quality_target", np.nan))

    # vs-plan
    if "cm_planned" in df.columns and "cm_db" in df.columns:
        df["cm_vs_plan_delta"] = df["cm_db"] - df["cm_planned"]
        df["cm_vs_plan_pct"] = _safe_div(df["cm_vs_plan_delta"], df["cm_planned"])

    return df


def add_time_deltas(df: pd.DataFrame, group_cols: tuple[str, ...] = ("cost_center_id",)) -> pd.DataFrame:
    """Month-over-month and year-over-year deltas on CM metrics, per cost center."""
    df = df.sort_values(list(group_cols) + ["period"]).copy()
    g = df.groupby(list(group_cols), sort=False)

    for col in ("cm_db", "cm_db_pct", "cm_db1", "cm_db2", "revenue_total", "labor_cost_total"):
        if col not in df.columns:
            continue
        df[f"{col}_mom"] = g[col].diff(1)
        df[f"{col}_yoy"] = g[col].diff(12)
        df[f"{col}_mom_pct"] = _safe_div(df[f"{col}_mom"], g[col].shift(1).abs())

    # rolling stats for anomaly use
    if "cm_db_pct" in df.columns:
        df["cm_db_pct_roll6_mean"] = g["cm_db_pct"].transform(
            lambda s: s.rolling(6, min_periods=3).mean())
        df["cm_db_pct_roll6_std"] = g["cm_db_pct"].transform(
            lambda s: s.rolling(6, min_periods=3).std())

    return df.reset_index(drop=True)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Full feature pipeline."""
    from src.data_quality import annotate as _annotate_dq  # local import avoids cycle
    df = add_kpis(df)
    df = add_time_deltas(df)
    df = _annotate_dq(df)
    return df
