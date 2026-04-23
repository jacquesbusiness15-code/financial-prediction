"""CM variance / anomaly detection, ranked by € impact for prioritization."""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect(df: pd.DataFrame, z_threshold: float = 1.3,
           mom_pct_threshold: float = 0.50,
           labor_ratio_warn: float = 0.85,
           exclude_dq_flagged: bool = True) -> pd.DataFrame:
    """Return a DataFrame of flagged rows with severity + € impact.

    Hard rules (judge-friendly):
      * cm_db < 0                                    → HARD flag, severity=high
      * labor_ratio > labor_ratio_warn (default .85) → HARD flag
      * labor_ratio > 1.0                            → severity escalated to high

    Statistical rules (on top of hard rules):
      * |cm_db_pct - rolling_mean| > z_threshold * rolling_std   (1.3σ)
      * |cm_db_pct_mom_pct| > mom_pct_threshold                  (50%)
      * regime flip: cm_db < 0 while 12M mean was > 0
      * cm_vs_plan_pct < -15%

    If `exclude_dq_flagged` and the column `dq_accrual_flag` exists, rows in
    those periods are dropped from the anomaly ranking (accruals would
    otherwise dominate the leaderboard).
    """
    d = df.copy()
    if "cm_db_pct" not in d.columns:
        return pd.DataFrame()

    # --- Hard rules ---
    flag_negative = d.get("cm_db", pd.Series(0, index=d.index)) < 0
    labor_ratio = d.get("labor_ratio", pd.Series(np.nan, index=d.index))
    flag_labor = labor_ratio > labor_ratio_warn
    flag_labor_over = labor_ratio > 1.0

    # --- Statistical rules ---
    mu = d.get("cm_db_pct_roll6_mean")
    sd = d.get("cm_db_pct_roll6_std")
    z = (d["cm_db_pct"] - mu) / sd.replace(0, np.nan) if mu is not None and sd is not None else pd.Series(np.nan, index=d.index)
    flag_z = z.abs() > z_threshold

    flag_mom = d.get("cm_db_pct_mom_pct", pd.Series(False, index=d.index)).abs() > mom_pct_threshold

    rolling_12_mean = (d.sort_values(["cost_center_id", "period"])
                       .groupby("cost_center_id")["cm_db"]
                       .transform(lambda s: s.rolling(12, min_periods=3).mean()))
    flag_flip = (d["cm_db"] < 0) & (rolling_12_mean > 0)

    flag_plan = d.get("cm_vs_plan_pct", pd.Series(0, index=d.index)) < -0.15

    d["anomaly_flag"] = (flag_negative | flag_labor | flag_z | flag_mom
                         | flag_flip | flag_plan)
    d["anomaly_z"] = z
    d["anomaly_reasons"] = [
        ", ".join(r for cond, r in [
            (fn, "CM < 0"),
            (fl, f"labor ratio {lr:.0%}"),
            (fz, f"z={zi:.1f}σ" if pd.notna(zi) else "z-outlier"),
            (fm, "big MoM jump"),
            (ff, "regime flip to negative"),
            (fp, "plan miss >15%"),
        ] if cond)
        for fn, fl, fz, fm, ff, fp, zi, lr in zip(
            flag_negative, flag_labor, flag_z, flag_mom, flag_flip, flag_plan,
            z, labor_ratio.fillna(0))
    ]

    # Optionally drop accrual/data-quality periods
    if exclude_dq_flagged and "dq_accrual_flag" in d.columns:
        d = d[~d["dq_accrual_flag"].fillna(False)]

    flagged = d[d["anomaly_flag"]].copy()
    if flagged.empty:
        return flagged

    impact_cols = [c for c in ["cm_db_mom", "cm_db_yoy", "cm_vs_plan_delta"]
                   if c in flagged.columns]
    flagged["impact_eur"] = (flagged[impact_cols].abs().max(axis=1)
                             if impact_cols else flagged["cm_db"].abs())

    # Severity: start from impact bucket, escalate on hard rules
    impact = flagged["impact_eur"].fillna(0)
    sev = pd.cut(impact, bins=[-np.inf, 5_000, 25_000, np.inf],
                 labels=["low", "medium", "high"]).astype(object)
    sev = sev.where(~flagged.get("cm_db", pd.Series(0, index=flagged.index)).lt(0), "high")
    labor_over = flagged.get("labor_ratio", pd.Series(0, index=flagged.index)) > 1.0
    sev = sev.where(~labor_over, "high")
    flagged["severity"] = sev

    flagged = flagged.sort_values("impact_eur", ascending=False).reset_index(drop=True)
    return flagged


def top_n(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    flagged = detect(df)
    if flagged.empty:
        return flagged
    keep = [c for c in [
        "period", "region", "cost_center_id", "cost_center_name",
        "customer_name", "service_type",
        "cm_db", "cm_db_pct", "labor_ratio",
        "cm_db_mom", "cm_db_yoy", "cm_vs_plan_delta",
        "impact_eur", "severity", "anomaly_reasons",
    ] if c in flagged.columns]
    return flagged[keep].head(n)
