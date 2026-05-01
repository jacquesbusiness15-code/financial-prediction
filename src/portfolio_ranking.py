"""Portfolio ranking: one row per contract, ranked by sustained unprofitability.

A contract is a `cost_center_id`. `unprofitability_eur` is the magnitude of the
mean negative CM across the last 3 months (positive months count as 0), so a
single bad month is dampened but a sustained loss dominates. `cm_trend_pp` is
the regression slope of `cm_db_pct` over the last 6 months.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import streamlit as st

from src import drivers

if TYPE_CHECKING:
    # Type-only; real imports happen inside functions to avoid a cycle
    # (facility_overview -> contract_metrics -> portfolio_ranking -> facility_overview).
    from src.facility_overview import StatusLevel


@dataclass
class ContractRanking:
    cost_center_id: str
    cost_center_name: str
    customer_name: str | None
    region: str | None
    industry: str | None
    entity: str | None
    latest_period: pd.Timestamp | None
    current_cm_eur: float
    current_revenue_eur: float
    current_margin_pct: float | None
    margin_mom_pp: float | None
    cm_trend_pp: float | None
    unprofitability_eur: float
    first_unprofitable_period: pd.Timestamp | None
    months_unprofitable: int
    top_reason_class: str | None
    top_reason_title_key: str | None
    status: StatusLevel
    sparkline_periods: list[pd.Timestamp]
    sparkline_margins: list[float]
    sparkline_cm_eur: list[float]
    sparkline_cm_mom_pct: list[float]
    sparkline_mom_periods: list[pd.Timestamp]
    cm_mom_eur: float | None
    cm_mom_pct: float | None


def _as_str(row: pd.Series, col: str) -> str | None:
    if col not in row.index:
        return None
    v = row[col]
    return None if pd.isna(v) else str(v)


def _as_float(row: pd.Series, col: str) -> float:
    if col not in row.index:
        return 0.0
    v = row[col]
    try:
        return 0.0 if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return 0.0


def _cm_pct_series(history: pd.DataFrame) -> pd.Series:
    """Return `cm_db_pct` as floats; fall back to cm_db/revenue_total * 100."""
    if "cm_db_pct" in history.columns:
        return pd.to_numeric(history["cm_db_pct"], errors="coerce")
    if "cm_db" in history.columns and "revenue_total" in history.columns:
        cm = pd.to_numeric(history["cm_db"], errors="coerce")
        rev = pd.to_numeric(history["revenue_total"], errors="coerce")
        return (cm / rev.where(rev > 0)) * 100.0
    return pd.Series(dtype=float)


def _cm_trend_pp(history: pd.DataFrame, window: int = 6) -> float | None:
    """Slope of CM% (pp/month) over the trailing `window`; None if <2 points."""
    if history.empty:
        return None
    y = _cm_pct_series(history.tail(window)).to_numpy(dtype=float)
    y = y[~np.isnan(y)]
    if len(y) < 2:
        return None
    if np.all(y == y[0]):
        return 0.0
    slope, _ = np.polyfit(np.arange(len(y), dtype=float), y, 1)
    return float(slope)


def _avg_negative_cm_3m(history: pd.DataFrame) -> float:
    if history.empty or "cm_db" not in history.columns:
        return 0.0
    y = pd.to_numeric(history.tail(3)["cm_db"], errors="coerce").to_numpy(dtype=float)
    y = y[~np.isnan(y)]
    if len(y) == 0:
        return 0.0
    return float(-np.mean(np.minimum(y, 0.0)))


def _compute_streak(history: pd.DataFrame) -> tuple[pd.Timestamp | None, int]:
    """Start and length of the current consecutive negative-CM streak.

    Returns ``(None, 0)`` if the latest row isn't itself unprofitable.
    """
    if history.empty or "cm_db" not in history.columns:
        return None, 0
    ordered = history.reset_index(drop=True)
    cm = ordered["cm_db"]
    end = len(ordered) - 1
    if pd.isna(cm.iloc[end]) or cm.iloc[end] >= 0:
        return None, 0
    start = end
    while start > 0:
        prev = cm.iloc[start - 1]
        if pd.isna(prev) or prev >= 0:
            break
        start -= 1
    return pd.Timestamp(ordered["period"].iloc[start]), end - start + 1


def _top_reason(history: pd.DataFrame) -> tuple[str, str] | None:
    """Return (class_key, title_key) of the biggest negative MoM driver."""
    from src.facility_overview import DRIVER_ICON, classify_driver
    if len(history) < 2:
        return None
    decomposed = drivers.decompose(history.iloc[-1], history.iloc[-2])
    for d in sorted(decomposed, key=lambda x: x.delta_eur):
        if d.delta_eur >= 0:
            break
        cls = classify_driver(d)
        if cls in DRIVER_ICON:
            _, title_key, _ = DRIVER_ICON[cls]
            return cls, title_key
    return None


def _floats_from(series: pd.Series) -> list[float]:
    return [(float(v) if pd.notna(v) else 0.0) for v in series.tolist()]


@st.cache_data(show_spinner=False)
def compute_rankings(df: pd.DataFrame) -> list[ContractRanking]:
    """One `ContractRanking` per contract, sorted by unprofitability desc."""
    from src.facility_overview import sparkline_values, status_for
    if df is None or df.empty or "cost_center_id" not in df.columns:
        return []

    df = df.sort_values(["cost_center_id", "period"])

    rankings: list[ContractRanking] = []
    for cc_id, hist in df.groupby("cost_center_id", sort=False, observed=True):
        if hist.empty:
            continue
        latest = hist.iloc[-1]
        rev = _as_float(latest, "revenue_total")
        cm = _as_float(latest, "cm_db")
        margin = (cm / rev) if rev else None

        margin_mom: float | None = None
        cm_mom_eur: float | None = None
        cm_mom_pct: float | None = None
        if len(hist) >= 2:
            prior = hist.iloc[-2]
            prior_rev = _as_float(prior, "revenue_total")
            if prior_rev > 0 and rev > 0:
                margin_mom = (margin or 0) - _as_float(prior, "cm_db") / prior_rev
            cm_prev = _as_float(prior, "cm_db")
            cm_mom_eur = cm - cm_prev
            if cm_prev != 0:
                cm_mom_pct = (cm - cm_prev) / abs(cm_prev)

        tail = hist.tail(6)
        spark_periods = [pd.Timestamp(p) for p in tail["period"].tolist()]
        spark_cm_eur = _floats_from(tail.get("cm_db", pd.Series(dtype=float)))

        # MoM series: pairwise over last 7 rows yields up to 6 points.
        mom_tail = hist.tail(7)
        mom_cm = _floats_from(mom_tail.get("cm_db", pd.Series(dtype=float)))
        mom_per = [pd.Timestamp(p) for p in mom_tail["period"].tolist()]
        spark_cm_mom_pct: list[float] = []
        spark_mom_periods: list[pd.Timestamp] = []
        for i in range(1, len(mom_cm)):
            prev_v = mom_cm[i - 1]
            if prev_v == 0:
                continue
            spark_cm_mom_pct.append((mom_cm[i] - prev_v) / abs(prev_v))
            spark_mom_periods.append(mom_per[i])

        reason = _top_reason(hist)
        streak_start, streak_len = _compute_streak(hist)
        latest_period = (pd.Timestamp(latest["period"])
                         if pd.notna(latest.get("period")) else None)

        rankings.append(ContractRanking(
            cost_center_id=str(cc_id),
            cost_center_name=_as_str(latest, "cost_center_name") or str(cc_id),
            customer_name=_as_str(latest, "customer_name"),
            region=_as_str(latest, "region"),
            industry=_as_str(latest, "industry"),
            entity=_as_str(latest, "entity"),
            latest_period=latest_period,
            current_cm_eur=cm,
            current_revenue_eur=rev,
            current_margin_pct=margin,
            margin_mom_pp=margin_mom,
            cm_trend_pp=_cm_trend_pp(hist, window=6),
            unprofitability_eur=_avg_negative_cm_3m(hist),
            first_unprofitable_period=streak_start,
            months_unprofitable=streak_len,
            top_reason_class=reason[0] if reason else None,
            top_reason_title_key=reason[1] if reason else None,
            status=status_for(margin, margin_mom),
            sparkline_periods=spark_periods,
            sparkline_margins=sparkline_values(tail, n=6),
            sparkline_cm_eur=spark_cm_eur,
            sparkline_cm_mom_pct=spark_cm_mom_pct,
            sparkline_mom_periods=spark_mom_periods,
            cm_mom_eur=cm_mom_eur,
            cm_mom_pct=cm_mom_pct,
        ))

    rankings.sort(key=lambda r: r.unprofitability_eur, reverse=True)
    return rankings


def filter_rankings(
    rankings: list[ContractRanking],
    *,
    regions: list[str] | None = None,
    clients: list[str] | None = None,
    industries: list[str] | None = None,
    cost_centers: list[str] | None = None,
    reasons: list[str] | None = None,
    search: str | None = None,
    only_unprofitable: bool = True,
) -> list[ContractRanking]:
    """Post-ranking filter. Each arg is AND-combined; empty lists == no filter."""
    out = rankings
    if only_unprofitable:
        out = [r for r in out if r.unprofitability_eur > 0]

    for values, getter in (
        (regions, lambda r: r.region or ""),
        (clients, lambda r: r.customer_name or ""),
        (industries, lambda r: r.industry or ""),
        (cost_centers, lambda r: r.cost_center_id),
        (reasons, lambda r: r.top_reason_class or ""),
    ):
        if values:
            allowed = set(values)
            out = [r for r in out if getter(r) in allowed]

    if search:
        q = search.strip().lower()
        if q:
            out = [
                r for r in out
                if q in r.cost_center_id.lower()
                or q in (r.cost_center_name or "").lower()
                or q in (r.customer_name or "").lower()
            ]
    return out


def totals(rankings: list[ContractRanking]) -> dict:
    """Aggregate stats for the KPI bar."""
    unprof = [r for r in rankings if r.unprofitability_eur > 0]
    longest = max(unprof, key=lambda r: r.months_unprofitable, default=None)
    return {
        "total_unprofit_eur": float(sum(r.unprofitability_eur for r in unprof)),
        "unprofit_count": len(unprof),
        "longest": longest,
    }
