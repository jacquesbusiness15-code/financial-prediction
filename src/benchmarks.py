"""Historical and regional benchmarks for a given (cost_center, period)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def history_for(df: pd.DataFrame, cost_center_id, window_months: int = 12) -> pd.DataFrame:
    sub = df[df["cost_center_id"] == cost_center_id].sort_values("period")
    return sub.tail(window_months)


def yoy_baseline(df: pd.DataFrame, cost_center_id, period) -> pd.Series | None:
    target = period - pd.DateOffset(years=1)
    match = df[(df["cost_center_id"] == cost_center_id) & (df["period"] == target)]
    return None if match.empty else match.iloc[0]


def regional_peers(df: pd.DataFrame, row: pd.Series,
                   match_service: bool = True) -> pd.DataFrame:
    """Peer cost centers in same region (and optionally same service) for same period.

    Single-region datasets: falls back to same service line for the same period
    across all cost centers, so the "peer median" comparison still makes sense.
    """
    single_region = df.get("region", pd.Series()).nunique() <= 1
    mask = df["period"] == row["period"]
    if not single_region:
        mask &= df["region"] == row["region"]
    if match_service and "service_type" in df.columns and pd.notna(row.get("service_type")):
        mask &= df["service_type"] == row["service_type"]
    mask &= df["cost_center_id"] != row["cost_center_id"]
    return df[mask]


def kpi_vs_peers(df: pd.DataFrame, row: pd.Series,
                 kpis: tuple[str, ...] = (
                    "cm_db_pct", "productivity_ratio", "absence_rate",
                    "subcontractor_share", "labor_cost_per_productive_hour",
                 )) -> pd.DataFrame:
    """Return a comparison table of this row vs regional peer median + percentile."""
    peers = regional_peers(df, row)
    out = []
    for k in kpis:
        if k not in df.columns:
            continue
        val = row.get(k)
        peer_vals = peers[k].dropna()
        if peer_vals.empty or pd.isna(val):
            continue
        pct = float((peer_vals < val).mean())
        out.append({
            "kpi": k,
            "value": float(val),
            "peer_median": float(peer_vals.median()),
            "peer_p25": float(peer_vals.quantile(0.25)),
            "peer_p75": float(peer_vals.quantile(0.75)),
            "percentile": pct,
        })
    return pd.DataFrame(out)


def history_stats(df: pd.DataFrame, cost_center_id,
                  col: str = "cm_db_pct") -> dict:
    sub = df[df["cost_center_id"] == cost_center_id][col].dropna()
    if sub.empty:
        return {}
    return {
        "mean": float(sub.mean()),
        "std": float(sub.std()),
        "min": float(sub.min()),
        "max": float(sub.max()),
        "last_12m_mean": float(sub.tail(12).mean()),
    }
