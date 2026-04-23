"""Forward-looking, rule-based risk flags per cost center.

Each rule produces a row with: cost_center_id, period, signal, severity,
detail (short human text), and impact_eur (€ at stake if the risk materializes).
Rules are explainable by design — no black-box ML in the early-warning layer.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _latest_per_cc(df: pd.DataFrame) -> pd.DataFrame:
    return (df.sort_values("period")
              .groupby("cost_center_id", sort=False)
              .tail(1))


def _trend_slope(values: pd.Series, window: int = 3) -> float:
    """Simple slope over last `window` points (€ or pct per month)."""
    vals = values.dropna().tail(window).values
    if len(vals) < 2:
        return np.nan
    x = np.arange(len(vals))
    return float(np.polyfit(x, vals, 1)[0])


def detect(df: pd.DataFrame) -> pd.DataFrame:
    """Scan all cost centers for risk signals on their most recent observation."""
    if "cost_center_id" not in df.columns or "period" not in df.columns:
        return pd.DataFrame()

    signals: list[dict] = []
    df_sorted = df.sort_values(["cost_center_id", "period"])

    for cc_id, grp in df_sorted.groupby("cost_center_id", sort=False):
        if grp.empty:
            continue
        latest = grp.iloc[-1]
        impact = abs(float(latest.get("cm_db", 0) or 0))

        # 1. Declining CM trend over last 3 months AND below plan
        slope = _trend_slope(grp["cm_db_pct"].astype(float))
        if pd.notna(slope) and slope < 0 and (latest.get("cm_vs_plan_delta", 0) or 0) < 0:
            signals.append(dict(
                cost_center_id=cc_id, period=latest["period"],
                signal="Declining CM trend",
                severity=_bucket(impact, 5_000, 25_000),
                detail=f"3M slope {slope:+.2%}/mo, below plan by "
                       f"{latest.get('cm_vs_plan_delta', 0):,.0f}€",
                impact_eur=impact,
            ))

        # 2. Absence rate spike vs own history
        abs_series = grp["absence_rate"].dropna()
        if len(abs_series) >= 3 and pd.notna(latest.get("absence_rate")):
            mu, sd = abs_series.iloc[:-1].mean(), abs_series.iloc[:-1].std()
            if sd and latest["absence_rate"] > mu + 2 * sd:
                signals.append(dict(
                    cost_center_id=cc_id, period=latest["period"],
                    signal="Absence spike",
                    severity=_bucket(impact, 5_000, 25_000),
                    detail=f"absence {latest['absence_rate']:.1%} vs avg {mu:.1%}",
                    impact_eur=impact,
                ))

        # 3. Productivity drop
        prod = latest.get("productivity_ratio")
        prod_slope = _trend_slope(grp["productivity_ratio"].astype(float))
        if pd.notna(prod) and prod < 0.70 and pd.notna(prod_slope) and prod_slope < 0:
            signals.append(dict(
                cost_center_id=cc_id, period=latest["period"],
                signal="Productivity drop",
                severity=_bucket(impact, 5_000, 25_000),
                detail=f"productivity {prod:.0%}, trend {prod_slope:+.2%}/mo",
                impact_eur=impact,
            ))

        # 4. Subcontractor creep vs planned ratio (BR)
        subc_share = latest.get("subcontractor_share")
        plan_subc = latest.get("plan_subcontractor_ratio")
        if pd.notna(subc_share) and pd.notna(plan_subc) and subc_share - plan_subc > 0.10:
            signals.append(dict(
                cost_center_id=cc_id, period=latest["period"],
                signal="Subcontractor creep",
                severity=_bucket(impact, 5_000, 25_000),
                detail=f"subcontractor share {subc_share:.0%} vs plan {plan_subc:.0%}",
                impact_eur=impact,
            ))

        # 5. Contract renewal risk (end within 90 days)
        ce = latest.get("contract_end")
        if pd.notna(ce):
            days = (ce - latest["period"]).days
            if 0 <= days <= 90:
                signals.append(dict(
                    cost_center_id=cc_id, period=latest["period"],
                    signal="Contract renewal risk",
                    severity="high" if impact > 25_000 else "medium",
                    detail=f"contract ends {ce.date()} (in {days}d)",
                    impact_eur=impact,
                ))

        # 6. Plan-gap widening
        plan_gap_series = grp["cm_vs_plan_delta"].dropna()
        if len(plan_gap_series) >= 2:
            if plan_gap_series.iloc[-1] < plan_gap_series.iloc[-2] < 0:
                signals.append(dict(
                    cost_center_id=cc_id, period=latest["period"],
                    signal="Plan gap widening",
                    severity=_bucket(abs(plan_gap_series.iloc[-1]), 5_000, 25_000),
                    detail=f"gap worsened "
                           f"{plan_gap_series.iloc[-2]:,.0f}€ → "
                           f"{plan_gap_series.iloc[-1]:,.0f}€",
                    impact_eur=abs(float(plan_gap_series.iloc[-1])),
                ))

    out = pd.DataFrame(signals)
    if out.empty:
        return out

    # Attach descriptive columns for UI
    latest_rows = _latest_per_cc(df)[["cost_center_id", "cost_center_name",
                                      "region", "customer_name", "service_type"]]
    out = out.merge(latest_rows, on="cost_center_id", how="left")
    out = out.sort_values(["severity", "impact_eur"],
                          ascending=[True, False],
                          key=lambda s: s.map({"high": 0, "medium": 1, "low": 2}) if s.name == "severity" else s)
    return out.reset_index(drop=True)


def _bucket(impact: float, low: float, high: float) -> str:
    if impact >= high:
        return "high"
    if impact >= low:
        return "medium"
    return "low"
