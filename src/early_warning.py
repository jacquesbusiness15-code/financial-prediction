"""Forward-looking, rule-based risk flags per cost center."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    EARLY_WARNING_SLOPE_THRESHOLD_PP,
    SUBCONTRACTOR_CREEP_THRESHOLD,
)


_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _bucket(impact: float, low: float, high: float) -> str:
    if impact >= high:
        return "high"
    if impact >= low:
        return "medium"
    return "low"


def _latest_per_cc(df: pd.DataFrame) -> pd.DataFrame:
    return (df.sort_values("period")
              .groupby("cost_center_id", sort=False, observed=True)
              .tail(1))


def _trend_slope(values: pd.Series, window: int = 3) -> float:
    vals = values.dropna().tail(window).values
    if len(vals) < 2:
        return np.nan
    return float(np.polyfit(np.arange(len(vals)), vals, 1)[0])


def detect(df: pd.DataFrame) -> pd.DataFrame:
    """Scan all cost centers for risk signals on their most recent observation."""
    if "cost_center_id" not in df.columns or "period" not in df.columns:
        return pd.DataFrame()

    signals: list[dict] = []
    df_sorted = df.sort_values(["cost_center_id", "period"])

    for cc_id, grp in df_sorted.groupby("cost_center_id", sort=False, observed=True):
        if grp.empty:
            continue
        latest = grp.iloc[-1]
        period = latest["period"]
        impact = abs(float(latest.get("cm_db", 0) or 0))
        default_sev = _bucket(impact, 5_000, 25_000)

        def emit(signal: str, detail: str, *, severity: str = default_sev,
                 impact_eur: float = impact) -> None:
            signals.append(dict(
                cost_center_id=cc_id, period=period,
                signal=signal, severity=severity,
                detail=detail, impact_eur=impact_eur,
            ))

        # 1. Declining CM trend AND below plan
        slope = _trend_slope(grp["cm_db_pct"].astype(float))
        cm_vs_plan = latest.get("cm_vs_plan_delta", 0) or 0
        if (pd.notna(slope) and slope < EARLY_WARNING_SLOPE_THRESHOLD_PP
                and cm_vs_plan < 0):
            emit("Declining CM trend",
                 f"3M slope {slope:+.2%}/mo, below plan by {cm_vs_plan:,.0f}€")

        # 2. Absence spike vs own history (>2 sigma)
        abs_series = grp["absence_rate"].dropna()
        latest_abs = latest.get("absence_rate")
        if len(abs_series) >= 3 and pd.notna(latest_abs):
            prior = abs_series.iloc[:-1]
            mu, sd = prior.mean(), prior.std()
            if sd and latest_abs > mu + 2 * sd:
                emit("Absence spike",
                     f"absence {latest_abs:.1%} vs avg {mu:.1%}")

        # 3. Productivity drop (slope in ratio pp/mo; divide threshold by 100)
        prod = latest.get("productivity_ratio")
        prod_slope = _trend_slope(grp["productivity_ratio"].astype(float))
        if (pd.notna(prod) and prod < 0.70 and pd.notna(prod_slope)
                and prod_slope < EARLY_WARNING_SLOPE_THRESHOLD_PP / 100.0):
            emit("Productivity drop",
                 f"productivity {prod:.0%}, trend {prod_slope:+.2%}/mo")

        # 4. Subcontractor creep vs planned ratio
        subc_share = latest.get("subcontractor_share")
        plan_subc = latest.get("plan_subcontractor_ratio")
        if (pd.notna(subc_share) and pd.notna(plan_subc)
                and subc_share - plan_subc > SUBCONTRACTOR_CREEP_THRESHOLD):
            emit("Subcontractor creep",
                 f"subcontractor share {subc_share:.0%} vs plan {plan_subc:.0%}")

        # 5. Contract renewal risk (ends within 90 days)
        ce = latest.get("contract_end")
        if pd.notna(ce):
            days = (ce - period).days
            if 0 <= days <= 90:
                emit("Contract renewal risk",
                     f"contract ends {ce.date()} (in {days}d)",
                     severity="high" if impact > 25_000 else "medium")

        # 6. Plan-gap widening (two consecutive worsening negatives)
        gap_series = grp["cm_vs_plan_delta"].dropna()
        if len(gap_series) >= 2:
            last, prev = gap_series.iloc[-1], gap_series.iloc[-2]
            if last < prev < 0:
                gap_impact = abs(float(last))
                emit("Plan gap widening",
                     f"gap worsened {prev:,.0f}€ → {last:,.0f}€",
                     severity=_bucket(gap_impact, 5_000, 25_000),
                     impact_eur=gap_impact)

    out = pd.DataFrame(signals)
    if out.empty:
        return out

    latest_rows = _latest_per_cc(df)[["cost_center_id", "cost_center_name",
                                      "region", "customer_name", "service_type"]]
    out = out.merge(latest_rows, on="cost_center_id", how="left")
    out = out.sort_values(
        ["severity", "impact_eur"],
        ascending=[True, False],
        key=lambda s: s.map(_SEVERITY_ORDER) if s.name == "severity" else s,
    )
    return out.reset_index(drop=True)
