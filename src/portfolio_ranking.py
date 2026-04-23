"""Portfolio ranking: one row per contract, ranked by sustained unprofitability.

A "contract" is a `cost_center_id`. For each contract we compute:

- `current_cm_eur`     : latest month's `cm_db`
- `unprofitability_eur`: magnitude of average negative CM over the last 3
  months, i.e. `-mean(min(cm_db, 0))` across the tail. Positive months count
  as 0, so a single bad month is dampened but a sustained loss dominates.
- `first_unprofitable_period`, `months_unprofitable`: start + length of the
  *current* consecutive streak of negative-CM months (walk backward from the
  latest row while `cm_db < 0`).
- `top_reason_class`   : classified top negative driver from latest vs. prior
  month, or None if no prior month exists or no negative drivers.
- `cm_trend_pp`        : linear-regression slope of `cm_db_pct` over the last
  6 months, in percentage points per month. Tells you whether margin is
  structurally deteriorating even when revenue is flat.

The `@st.cache_data` decorator on `compute_rankings` memoizes results so
fragment reruns (tab switches, sort clicks, unrelated filter tweaks) reuse
the previous output when the input DataFrame is unchanged. The function
itself remains pure; the cache wrapper is the only Streamlit touch point.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from src import drivers
from src.facility_overview import (
    DRIVER_ICON,
    StatusLevel,
    classify_driver,
    sparkline_values,
    status_for,
)


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
    current_margin_pct: float | None
    margin_mom_pp: float | None  # Δ margin vs prior month in percentage points
    cm_trend_pp: float | None  # regression slope of cm_db_pct, pp per month (6m window)
    unprofitability_eur: float  # magnitude of avg negative CM over last 3 months
    first_unprofitable_period: pd.Timestamp | None
    months_unprofitable: int
    top_reason_class: str | None
    top_reason_title_key: str | None
    status: StatusLevel
    sparkline_periods: list[pd.Timestamp]
    sparkline_margins: list[float]
    sparkline_cm_eur: list[float]
    # Per-month MoM % change of cm_db over the 6 most recent pairs (so up to
    # 6 points). `sparkline_mom_periods[i]` is the "current" month for
    # `sparkline_cm_mom_pct[i]`. The LAST element equals `cm_mom_pct` — this
    # is what the row tooltip plots so that the chart's last-point height
    # visibly matches the Profitability "Trend vs last month" column.
    sparkline_cm_mom_pct: list[float]
    sparkline_mom_periods: list[pd.Timestamp]
    cm_mom_eur: float | None  # signed € delta: cm_now - cm_prev
    cm_mom_pct: float | None  # (cm_now - cm_prev) / abs(cm_prev); None if cm_prev == 0


def _as_str(row: pd.Series, col: str) -> str | None:
    if col not in row.index:
        return None
    v = row[col]
    if pd.isna(v):
        return None
    return str(v)


def _as_float(row: pd.Series, col: str) -> float:
    if col not in row.index:
        return 0.0
    v = row[col]
    try:
        return 0.0 if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return 0.0


def _cm_pct_series(history: pd.DataFrame) -> pd.Series:
    """Return `cm_db_pct` as a float Series in percentage-point units.

    Prefers the pre-computed `cm_db_pct` column; falls back to
    `cm_db / revenue_total * 100` where revenue is positive.
    """
    if "cm_db_pct" in history.columns:
        return pd.to_numeric(history["cm_db_pct"], errors="coerce")
    if "cm_db" in history.columns and "revenue_total" in history.columns:
        cm = pd.to_numeric(history["cm_db"], errors="coerce")
        rev = pd.to_numeric(history["revenue_total"], errors="coerce")
        return (cm / rev.where(rev > 0)) * 100.0
    return pd.Series(dtype=float)


def _cm_trend_pp(history: pd.DataFrame, window: int = 6) -> float | None:
    """Slope of contribution-margin percent over the last `window` months,
    expressed in **percentage points per month**. Returns ``None`` when
    fewer than 2 usable points are available. `history` must be sorted by
    `period` ascending (callers inside this module guarantee it).
    """
    if history.empty:
        return None
    tail = history.tail(window)
    y = _cm_pct_series(tail).to_numpy(dtype=float)
    y = y[~np.isnan(y)]
    if len(y) < 2:
        return None
    if np.all(y == y[0]):
        return 0.0
    x = np.arange(len(y), dtype=float)
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)


def _avg_negative_cm_3m(history: pd.DataFrame) -> float:
    """Magnitude (positive €) of the mean negative CM over the last 3 months.

    Positive months contribute 0; a single bad month is dampened but sustained
    losses dominate. Returns 0.0 when no usable `cm_db` values exist.
    """
    if history.empty or "cm_db" not in history.columns:
        return 0.0
    tail = history.tail(3)
    y = pd.to_numeric(tail["cm_db"], errors="coerce").to_numpy(dtype=float)
    y = y[~np.isnan(y)]
    if len(y) == 0:
        return 0.0
    return float(-np.mean(np.minimum(y, 0.0)))


def _compute_streak(history: pd.DataFrame) -> tuple[pd.Timestamp | None, int]:
    """Start date and length of the current consecutive negative-CM streak.

    Walks backward from the latest row while `cm_db < 0`. Returns
    ``(None, 0)`` if the latest row is not itself unprofitable.
    """
    if history.empty or "cm_db" not in history.columns:
        return None, 0
    ordered = history.reset_index(drop=True)
    cm = ordered["cm_db"]
    i = len(ordered) - 1
    if pd.isna(cm.iloc[i]) or cm.iloc[i] >= 0:
        return None, 0
    start_idx = i
    while start_idx - 1 >= 0:
        prev = cm.iloc[start_idx - 1]
        if pd.isna(prev) or prev >= 0:
            break
        start_idx -= 1
    return pd.Timestamp(ordered["period"].iloc[start_idx]), (i - start_idx + 1)


def _top_reason(history: pd.DataFrame) -> tuple[str, str] | None:
    """Return ``(class_key, title_key)`` of the biggest negative driver.

    Uses the latest row vs the prior row (MoM). Returns ``None`` if either
    row is missing or no negative driver was found.
    """
    if len(history) < 2:
        return None
    current = history.iloc[-1]
    prior = history.iloc[-2]
    all_drivers = drivers.decompose(current, prior)
    for d in sorted(all_drivers, key=lambda x: x.delta_eur):
        if d.delta_eur >= 0:
            break
        cls = classify_driver(d)
        if cls in DRIVER_ICON:
            _, title_key, _ = DRIVER_ICON[cls]
            return cls, title_key
    return None


@st.cache_data(show_spinner=False)
def compute_rankings(df: pd.DataFrame) -> list[ContractRanking]:
    """One `ContractRanking` per contract, sorted by unprofitability desc."""
    if df is None or df.empty or "cost_center_id" not in df.columns:
        return []

    # The loader already sorts by [cost_center_id, period]; re-sort defensively
    # once here so downstream per-group slicing can skip its own sort.
    df = df.sort_values(["cost_center_id", "period"])

    rankings: list[ContractRanking] = []
    for cc_id, hist in df.groupby("cost_center_id", sort=False, observed=True):
        if hist.empty:
            continue
        latest = hist.iloc[-1]

        rev = _as_float(latest, "revenue_total")
        cm = _as_float(latest, "cm_db")
        margin = (cm / rev) if rev else None

        prior = hist.iloc[-2] if len(hist) >= 2 else None
        margin_mom: float | None = None
        cm_mom_eur: float | None = None
        cm_mom_pct: float | None = None
        if prior is not None:
            prior_rev = _as_float(prior, "revenue_total")
            if prior_rev > 0 and rev > 0:
                prev_margin = _as_float(prior, "cm_db") / prior_rev
                margin_mom = (margin or 0) - prev_margin
            cm_prev_eur = _as_float(prior, "cm_db")
            cm_mom_eur = cm - cm_prev_eur
            if cm_prev_eur != 0:
                cm_mom_pct = (cm - cm_prev_eur) / abs(cm_prev_eur)

        cm_trend = _cm_trend_pp(hist, window=6)
        unprofit = _avg_negative_cm_3m(hist)

        streak_start, streak_len = _compute_streak(hist)
        reason = _top_reason(hist)

        tail = hist.tail(6)
        spark_periods = [pd.Timestamp(p) for p in tail["period"].tolist()]
        spark_margins = sparkline_values(tail, n=6)
        spark_cm_eur = [
            (float(v) if pd.notna(v) else 0.0)
            for v in tail.get("cm_db", pd.Series(dtype=float)).tolist()
        ]

        # MoM %-change series: pairwise on the last 7 rows so we get up to 6
        # points; each point is `(cm[i] - cm[i-1]) / abs(cm[i-1])`.
        mom_tail = hist.tail(7)
        mom_cm = [
            (float(v) if pd.notna(v) else 0.0)
            for v in mom_tail.get("cm_db", pd.Series(dtype=float)).tolist()
        ]
        mom_per = [pd.Timestamp(p) for p in mom_tail["period"].tolist()]
        spark_cm_mom_pct: list[float] = []
        spark_mom_periods: list[pd.Timestamp] = []
        for i in range(1, len(mom_cm)):
            prev_v = mom_cm[i - 1]
            if prev_v == 0:
                continue
            spark_cm_mom_pct.append((mom_cm[i] - prev_v) / abs(prev_v))
            spark_mom_periods.append(mom_per[i])

        rankings.append(ContractRanking(
            cost_center_id=str(cc_id),
            cost_center_name=_as_str(latest, "cost_center_name") or str(cc_id),
            customer_name=_as_str(latest, "customer_name"),
            region=_as_str(latest, "region"),
            industry=_as_str(latest, "industry"),
            entity=_as_str(latest, "entity"),
            latest_period=pd.Timestamp(latest["period"]) if pd.notna(latest.get("period")) else None,
            current_cm_eur=cm,
            current_margin_pct=margin,
            margin_mom_pp=margin_mom,
            cm_trend_pp=cm_trend,
            unprofitability_eur=unprofit,
            first_unprofitable_period=streak_start,
            months_unprofitable=streak_len,
            top_reason_class=reason[0] if reason else None,
            top_reason_title_key=reason[1] if reason else None,
            status=status_for(margin, margin_mom),
            sparkline_periods=spark_periods,
            sparkline_margins=spark_margins,
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
    """Post-ranking filter. Each arg is AND-combined; empty lists = no filter."""
    out = rankings
    if only_unprofitable:
        out = [r for r in out if r.unprofitability_eur > 0]
    if regions:
        rset = set(regions)
        out = [r for r in out if (r.region or "") in rset]
    if clients:
        cset = set(clients)
        out = [r for r in out if (r.customer_name or "") in cset]
    if industries:
        iset = set(industries)
        out = [r for r in out if (r.industry or "") in iset]
    if cost_centers:
        ccset = set(cost_centers)
        out = [r for r in out if r.cost_center_id in ccset]
    if reasons:
        rset = set(reasons)
        out = [r for r in out if (r.top_reason_class or "") in rset]
    if search:
        q = search.strip().lower()
        if q:
            out = [
                r for r in out
                if q in (r.cost_center_id.lower())
                or q in ((r.cost_center_name or "").lower())
                or q in ((r.customer_name or "").lower())
            ]
    return out


def totals(rankings: list[ContractRanking]) -> dict:
    """Aggregate stats for the KPI bar."""
    unprof = [r for r in rankings if r.unprofitability_eur > 0]
    total = float(sum(r.unprofitability_eur for r in unprof))
    longest: ContractRanking | None = None
    for r in unprof:
        if longest is None or r.months_unprofitable > longest.months_unprofitable:
            longest = r
    return {
        "total_unprofit_eur": total,
        "unprofit_count": len(unprof),
        "longest": longest,
    }
