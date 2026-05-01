"""Data-quality checks: flag accrual/reversal periods whose revenue is
anomalously high vs the trailing 12-month mean."""
from __future__ import annotations

import pandas as pd


ACCRUAL_RATIO_THRESHOLD = 1.8

_FLAG_COLS = ["period", "revenue_total", "trailing_mean", "ratio", "cm_db", "note"]


def detect_accrual_inflation(df: pd.DataFrame,
                             ratio_threshold: float = ACCRUAL_RATIO_THRESHOLD
                             ) -> pd.DataFrame:
    if df.empty or "period" not in df.columns:
        return pd.DataFrame(columns=_FLAG_COLS)

    agg = df.groupby("period")[["revenue_total", "cm_db"]].sum().sort_index()
    agg["trailing_mean"] = agg["revenue_total"].rolling(12, min_periods=6).mean().shift(1)
    agg["ratio"] = agg["revenue_total"] / agg["trailing_mean"]
    flagged = agg[agg["ratio"] > ratio_threshold]
    if flagged.empty:
        return pd.DataFrame(columns=_FLAG_COLS)
    flagged = flagged.reset_index()
    flagged["note"] = flagged["ratio"].map(
        lambda r: f"Revenue {r:.1f}x trailing 12M mean - likely accrual/reversal")
    return flagged[_FLAG_COLS]


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    flagged = detect_accrual_inflation(df)
    out = df.copy()
    out["dq_accrual_flag"] = (out["period"].isin(flagged["period"])
                              if not flagged.empty else False)
    return out
