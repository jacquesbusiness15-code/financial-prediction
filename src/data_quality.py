"""Data-quality checks — flag periods that look like accruals / reversals.

Motivation: in the WISAG dataset, January 2026 shows revenue ≈ 2× the
trailing 12-month mean, which inflates CM and pollutes the anomaly
leaderboard. We flag these periods and (optionally) exclude them from
anomaly ranking so genuine operational issues surface.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


ACCRUAL_RATIO_THRESHOLD = 1.8


def detect_accrual_inflation(df: pd.DataFrame,
                             ratio_threshold: float = ACCRUAL_RATIO_THRESHOLD
                             ) -> pd.DataFrame:
    """Return one row per flagged period with revenue_ratio + CM inflation metric.

    Rule: aggregate revenue per period; compare to trailing 12-month mean.
    Any period where revenue > ratio_threshold × mean is flagged.
    """
    if df.empty or "period" not in df.columns:
        return pd.DataFrame(columns=["period", "revenue_total", "trailing_mean",
                                     "ratio", "cm_db", "note"])

    agg = (df.groupby("period")[["revenue_total", "cm_db"]]
             .sum().sort_index())
    agg["trailing_mean"] = (agg["revenue_total"]
                            .rolling(12, min_periods=6).mean().shift(1))
    agg["ratio"] = agg["revenue_total"] / agg["trailing_mean"]
    flagged = agg[agg["ratio"] > ratio_threshold].copy()
    if flagged.empty:
        return pd.DataFrame(columns=["period", "revenue_total", "trailing_mean",
                                     "ratio", "cm_db", "note"])
    flagged = flagged.reset_index()
    flagged["note"] = flagged["ratio"].map(
        lambda r: f"Revenue {r:.1f}× trailing 12M mean — likely accrual/reversal")
    return flagged[["period", "revenue_total", "trailing_mean",
                    "ratio", "cm_db", "note"]]


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """Add a boolean `dq_accrual_flag` column to `df` on flagged periods."""
    flagged = detect_accrual_inflation(df)
    out = df.copy()
    out["dq_accrual_flag"] = False
    if not flagged.empty:
        out.loc[out["period"].isin(flagged["period"]), "dq_accrual_flag"] = True
    return out
