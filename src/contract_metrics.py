"""Per-contract multi-dimensional metrics + 0-100 scoring.

Wraps the identity-centric `ContractRanking` from `src.portfolio_ranking` and
adds four category-specific bundles (profitability, cost structure, efficiency,
stability) plus a composite overall score. Scores are percentile-ranked across
the *visible* set so the best filtered contract gets 100 and the worst gets 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from src.portfolio_ranking import ContractRanking, compute_rankings


# Cost categories for "highest cost" / "highest MoM increase" widgets.
COST_CATEGORY_COLUMNS: dict[str, list[str]] = {
    "labor": ["labor_cost_total"],
    "subcontractor": [
        "subcontractor_group",
        "subcontractor_division",
        "subcontractor_external",
    ],
    "internal_service": ["internal_service_el1", "internal_service_el2"],
    "travel": ["travel_cost"],
    "material": ["material_cost"],
    "vehicle": ["vehicle_cost"],
}

LONG_TERM_MONTH_THRESHOLD = 12
SMALL_SET_SCORE_DEFAULT = 50.0
MIN_SET_FOR_PERCENTILE = 3

_EMPTY_PROFITABILITY = {
    "unrent_now_eur": 0.0,
    "unrent_mom_delta_eur": None,
    "unrent_6m_delta_eur": None,
    "profitability_trend_dir": "flat",
    "cm_mom_pct": None,
}
_EMPTY_COST_STRUCTURE = {
    "top_cost_category_now": None,
    "top_cost_category_now_eur": 0.0,
    "top_cost_increase_cat": None,
    "top_cost_increase_pct": None,
    "total_cost_increase_pct": None,
}
_EMPTY_EFFICIENCY = {
    "hours_planned_minus_productive": None,
    "ratio_mom_delta_pp": None,
    "ratio_6m_delta_pp": None,
    "hour_variance": None,
    "eff_badness": None,
}
_EMPTY_STABILITY = {
    "contract_duration_months": None,
    "cm_variance": None,
    "is_long_term": False,
    "revenue_variance": None,
}
_EMPTY_REVENUE_TREND = {
    "revenue_mom_delta_eur": None,
    "revenue_6m_delta_eur": None,
    "top_revenue_decline_cat": None,
    "top_revenue_decline_eur": None,
    "revenue_trend_dir": "no_data",
}

# Revenue stream keys shared with i18n ("revenue_stream.<key>"). Order drives
# tie-breaking when two streams drop by exactly the same amount.
REVENUE_STREAM_COLUMNS: list[tuple[str, str]] = [
    ("fixed",  "revenue_fixed"),
    ("hourly", "revenue_hourly"),
    ("other",  "revenue_other"),
]

# Epsilon for the "flat" trend band: revenue that moved less than this in both
# relative and absolute terms is treated as unchanged. Prevents a 5 EUR drop on
# a 500k EUR contract from rendering as "Rückläufig".
_REVENUE_TREND_REL_EPS = 0.005   # 0.5 % of the larger-of-current-or-prior
_REVENUE_TREND_ABS_EPS = 50.0    # never call a sub-50 EUR move a real trend


@dataclass
class ContractOverviewMetrics:
    total_cost_eur: float | None
    cost_mom_pct: float | None
    cost_mom_eur: float | None
    margin_eur: float | None
    margin_mom_eur: float | None
    margin_pct: float | None
    margin_mom_delta: float | None


@dataclass
class ContractMetrics:
    base: ContractRanking

    # Profitability
    unrent_now_eur: float
    unrent_mom_delta_eur: float | None
    unrent_6m_delta_eur: float | None
    profitability_trend_dir: str
    cm_mom_pct: float | None

    # Cost structure
    top_cost_category_now: str | None
    top_cost_category_now_eur: float
    top_cost_increase_cat: str | None
    top_cost_increase_pct: float | None
    total_cost_increase_pct: float | None

    # Efficiency
    hours_planned_minus_productive: float | None
    ratio_mom_delta_pp: float | None
    ratio_6m_delta_pp: float | None
    hour_variance: float | None

    # Stability
    contract_duration_months: int | None
    cm_variance: float | None
    is_long_term: bool
    revenue_variance: float | None

    # Revenue trend
    revenue_mom_delta_eur: float | None
    revenue_6m_delta_eur: float | None
    top_revenue_decline_cat: str | None
    top_revenue_decline_eur: float | None
    revenue_trend_dir: str

    # Scores (0-100, higher = better)
    profitability_score: float
    cost_structure_score: float
    efficiency_score: float
    stability_score: float
    overall_score: float


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _maybe_float(value) -> float | None:
    """Like `_safe_float` but returns `None` instead of defaulting on missing."""
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# `cm_db_pct` is expected in percent (e.g. 17.0 for 17 %). Some upstream feeds
# accidentally store it as a ratio (0.17). Anything whose magnitude is at or
# below this bound is treated as already-ratio and forces the fallback path.
_CM_DB_PCT_RATIO_UPPER_BOUND = 1.5


def _row_margin_pct(
    row: pd.Series | None,
    *,
    min_revenue_eur: float = 10.0,
) -> float | None:
    if row is None:
        return None

    cm_pct_raw = row.get("cm_db_pct")
    try:
        if cm_pct_raw is not None and not pd.isna(cm_pct_raw):
            cm_pct_val = float(cm_pct_raw)
            if abs(cm_pct_val) > _CM_DB_PCT_RATIO_UPPER_BOUND:
                return cm_pct_val / 100.0
    except (TypeError, ValueError):
        pass

    revenue = _maybe_float(row.get("revenue_total"))
    cm = _maybe_float(row.get("cm_db"))
    if revenue is None or cm is None:
        return None
    if revenue >= min_revenue_eur:
        return cm / revenue
    return None


def compute_contract_overview_metrics(
    current_row: pd.Series,
    prior_row: pd.Series | None = None,
    *,
    min_revenue_eur: float = 10.0,
) -> ContractOverviewMetrics:
    """Compute the four hero metrics for the contract detail overview.

    Formulas:
      * total cost = revenue_total - cm_db
      * cost vs previous month = total_cost_current - total_cost_previous
      * margin = cm_db
      * change vs previous month = cm_db_current - cm_db_previous

    Any metric whose inputs are missing returns ``None`` rather than being
    silently treated as zero — the UI can then render ``—`` instead of a
    misleading ``0 €``.
    """
    revenue_now = _maybe_float(current_row.get("revenue_total"))
    cm_now = _maybe_float(current_row.get("cm_db"))
    total_cost_now = (revenue_now - cm_now) if (revenue_now is not None
                                                and cm_now is not None) else None
    margin_now_eur = cm_now
    margin_now = _row_margin_pct(current_row, min_revenue_eur=min_revenue_eur)

    cost_mom_pct: float | None = None
    cost_mom_eur: float | None = None
    margin_mom_eur: float | None = None
    margin_mom_delta: float | None = None

    if prior_row is not None:
        revenue_prev = _maybe_float(prior_row.get("revenue_total"))
        cm_prev = _maybe_float(prior_row.get("cm_db"))
        total_cost_prev = (revenue_prev - cm_prev) if (revenue_prev is not None
                                                       and cm_prev is not None) else None
        margin_prev = _row_margin_pct(prior_row, min_revenue_eur=min_revenue_eur)

        if total_cost_now is not None and total_cost_prev is not None:
            cost_mom_eur = total_cost_now - total_cost_prev
            cost_mom_pct = safe_pct_change(total_cost_now, total_cost_prev)
        if margin_now_eur is not None and cm_prev is not None:
            margin_mom_eur = margin_now_eur - cm_prev
        if margin_now is not None and margin_prev is not None:
            margin_mom_delta = margin_now - margin_prev

    return ContractOverviewMetrics(
        total_cost_eur=total_cost_now,
        cost_mom_pct=cost_mom_pct,
        cost_mom_eur=cost_mom_eur,
        margin_eur=margin_now_eur,
        margin_mom_eur=margin_mom_eur,
        margin_pct=margin_now,
        margin_mom_delta=margin_mom_delta,
    )


def safe_pct_change(
    current: float | None,
    baseline: float | None,
    *,
    min_ratio: float = 0.05,
    min_abs_eur: float = 10.0,
    allow_sign_flip: bool = False,
) -> float | None:
    """Standard percentage change, gated against meaningless denominators.

    Returns ``(current - baseline) / abs(baseline)`` when the change is
    quantitatively meaningful, otherwise ``None``. Callers are expected to
    fall back to a EUR delta or "no data" when the result is ``None``.

    A baseline is rejected when any of the following hold:
      * ``baseline`` is missing, NaN, or exactly zero;
      * ``|baseline| < min_abs_eur`` (absolute floor — e.g. 1 € prev month);
      * ``|baseline| < min_ratio * max(|baseline|, |current|)`` (relative
        floor — a fresh series disguised as a change);
      * ``current`` and ``baseline`` have opposite signs and
        ``allow_sign_flip`` is ``False`` (treating a sign flip as a %
        change produces absurd values like -5000 %).
    """
    if current is None or baseline is None:
        return None
    try:
        if pd.isna(current) or pd.isna(baseline):
            return None
    except TypeError:
        return None
    cur = float(current)
    base = float(baseline)
    if base == 0.0:
        return None
    abs_base = abs(base)
    if abs_base < min_abs_eur:
        return None
    if abs_base < min_ratio * max(abs_base, abs(cur)):
        return None
    if not allow_sign_flip and (cur * base) < 0.0:
        return None
    return (cur - base) / abs_base


def _sorted_history(history: pd.DataFrame) -> pd.DataFrame:
    if "period" in history.columns:
        return history.sort_values("period")
    return history


def _cost_category_value(row: pd.Series, cols: list[str]) -> float:
    return sum(_safe_float(row[c]) for c in cols if c in row.index)


def _category_totals(row: pd.Series) -> dict[str, float]:
    return {key: _cost_category_value(row, cols)
            for key, cols in COST_CATEGORY_COLUMNS.items()}


def _unrent(row: pd.Series) -> float:
    """Unrentability = max(planned CM - actual CM, 0). Positive = loss vs plan."""
    planned = _safe_float(row.get("cm_planned"))
    actual = _safe_float(row.get("cm_db"))
    return max(planned - actual, 0.0)


def _productive_ratio(row: pd.Series) -> float | None:
    planned = _safe_float(row.get("hours_planned"))
    productive = _safe_float(row.get("hours_productive"))
    return (productive / planned) if planned > 0 else None


def _profitability_metrics(history: pd.DataFrame) -> dict:
    hist = _sorted_history(history)
    if hist.empty:
        return dict(_EMPTY_PROFITABILITY)
    latest = hist.iloc[-1]
    unrent_now = _unrent(latest)

    mom_delta: float | None = None
    cm_mom_pct: float | None = None
    six_m_delta: float | None = None

    if len(hist) >= 2:
        prev = hist.iloc[-2]
        mom_delta = unrent_now - _unrent(prev)
        cm_prev = _safe_float(prev.get("cm_db"))
        cm_mom_pct = safe_pct_change(
            _safe_float(latest.get("cm_db")), cm_prev,
        )

        prior = hist.iloc[:-1].tail(6)
        if not prior.empty:
            six_m_delta = unrent_now - float(np.mean([_unrent(r) for _, r in prior.iterrows()]))

    if mom_delta is None or mom_delta == 0:
        trend_dir = "flat"
    else:
        trend_dir = "up" if mom_delta > 0 else "down"

    return {
        "unrent_now_eur": unrent_now,
        "unrent_mom_delta_eur": mom_delta,
        "unrent_6m_delta_eur": six_m_delta,
        "profitability_trend_dir": trend_dir,
        "cm_mom_pct": cm_mom_pct,
    }


def _cost_structure_metrics(history: pd.DataFrame) -> dict:
    hist = _sorted_history(history)
    if hist.empty:
        return dict(_EMPTY_COST_STRUCTURE)
    now_totals = _category_totals(hist.iloc[-1])

    top_cat_now: str | None = None
    top_cat_now_eur = 0.0
    for cat, val in now_totals.items():
        if val > top_cat_now_eur:
            top_cat_now, top_cat_now_eur = cat, val

    top_inc_cat: str | None = None
    top_inc_pct: float | None = None
    total_pct: float | None = None

    if len(hist) >= 2:
        prev_totals = _category_totals(hist.iloc[-2])
        biggest_delta = 0.0
        for cat, now_val in now_totals.items():
            prev = prev_totals.get(cat, 0.0)
            delta = now_val - prev
            if delta > biggest_delta:
                biggest_delta = delta
                top_inc_cat = cat
                top_inc_pct = safe_pct_change(now_val, prev)

        total_now = sum(now_totals.values())
        total_prev = sum(prev_totals.values())
        total_pct = safe_pct_change(total_now, total_prev)

    return {
        "top_cost_category_now": top_cat_now,
        "top_cost_category_now_eur": top_cat_now_eur,
        "top_cost_increase_cat": top_inc_cat,
        "top_cost_increase_pct": top_inc_pct,
        "total_cost_increase_pct": total_pct,
    }


def _efficiency_metrics(history: pd.DataFrame) -> dict:
    hist = _sorted_history(history)
    if hist.empty:
        return dict(_EMPTY_EFFICIENCY)
    latest = hist.iloc[-1]
    planned_latest = _safe_float(latest.get("hours_planned"))
    diff = planned_latest - _safe_float(latest.get("hours_productive"))

    hour_var_f = _safe_float(latest.get("hour_variance"), default=float("nan"))
    hour_variance = None if np.isnan(hour_var_f) else hour_var_f

    now_ratio = _productive_ratio(latest)
    mom_pp: float | None = None
    six_m_pp: float | None = None

    if len(hist) >= 2 and now_ratio is not None:
        prev_ratio = _productive_ratio(hist.iloc[-2])
        if prev_ratio is not None:
            mom_pp = (now_ratio - prev_ratio) * 100.0

        prior = hist.iloc[:-1].tail(6)
        prior_ratios = [r for r in (_productive_ratio(row) for _, row in prior.iterrows())
                        if r is not None]
        if prior_ratios:
            six_m_pp = (now_ratio - float(np.mean(prior_ratios))) * 100.0

    # Self-contained badness signal: fraction of planned hours NOT delivered
    # productively. Positive = bad. Keeps `_compute_scores` free of temp keys.
    eff_badness: float | None = None
    if planned_latest > 0:
        eff_badness = abs(diff) / planned_latest

    return {
        "hours_planned_minus_productive": diff,
        "ratio_mom_delta_pp": mom_pp,
        "ratio_6m_delta_pp": six_m_pp,
        "hour_variance": hour_variance,
        "eff_badness": eff_badness,
    }


def _variance(hist: pd.DataFrame, col: str) -> float | None:
    if col not in hist.columns:
        return None
    series = pd.to_numeric(hist[col], errors="coerce").dropna()
    if len(series) < 2:
        return None
    return float(series.std(ddof=0))


def _stability_metrics(history: pd.DataFrame) -> dict:
    hist = _sorted_history(history)
    if hist.empty:
        return dict(_EMPTY_STABILITY)
    latest = hist.iloc[-1]

    start_ts = pd.to_datetime(latest.get("contract_start"), errors="coerce")
    end_ts = pd.to_datetime(latest.get("contract_end"), errors="coerce")

    duration_months: int | None = None
    if pd.notna(start_ts):
        end_for_calc = end_ts if pd.notna(end_ts) else pd.Timestamp(date.today())
        delta_days = (end_for_calc - start_ts).days
        if delta_days >= 0:
            duration_months = int(round(delta_days / 30.4375))

    return {
        "contract_duration_months": duration_months,
        "cm_variance": _variance(hist, "cm_db"),
        "is_long_term": duration_months is not None and duration_months >= LONG_TERM_MONTH_THRESHOLD,
        "revenue_variance": _variance(hist, "revenue_total"),
    }


def _revenue_total(row: pd.Series) -> float:
    """Revenue for a single period. Prefer `revenue_total`, fall back to the
    sum of the three stream columns when the total is missing."""
    total = _maybe_float(row.get("revenue_total"))
    if total is not None:
        return total
    return sum(_safe_float(row.get(col)) for _key, col in REVENUE_STREAM_COLUMNS)


def _revenue_trend_metrics(history: pd.DataFrame) -> dict:
    hist = _sorted_history(history)
    if hist.empty:
        return dict(_EMPTY_REVENUE_TREND)
    latest = hist.iloc[-1]
    rev_now = _revenue_total(latest)

    mom_delta: float | None = None
    six_m_delta: float | None = None
    top_cat: str | None = None
    top_delta: float | None = None
    trend_dir = "no_data"

    if len(hist) >= 2:
        prev = hist.iloc[-2]
        rev_prev = _revenue_total(prev)
        mom_delta = rev_now - rev_prev

        # Classify "flat" vs "up"/"down": the movement must clear BOTH the
        # absolute floor AND the relative floor, otherwise it's noise.
        scale = max(abs(rev_now), abs(rev_prev))
        rel_eps = scale * _REVENUE_TREND_REL_EPS
        if abs(mom_delta) < max(_REVENUE_TREND_ABS_EPS, rel_eps):
            trend_dir = "flat"
        else:
            trend_dir = "down" if mom_delta < 0 else "up"

        # Top declining stream: biggest (most negative) per-stream MoM delta.
        worst = 0.0
        for key, col in REVENUE_STREAM_COLUMNS:
            if col not in hist.columns:
                continue
            delta = _safe_float(latest.get(col)) - _safe_float(prev.get(col))
            # Tie-break by list order (stable when equal): strict `<` only.
            if delta < worst:
                worst = delta
                top_cat = key
                top_delta = delta

        prior = hist.iloc[:-1].tail(6)
        if not prior.empty:
            six_m_delta = rev_now - float(np.mean(
                [_revenue_total(r) for _, r in prior.iterrows()]
            ))

    return {
        "revenue_mom_delta_eur": mom_delta,
        "revenue_6m_delta_eur": six_m_delta,
        "top_revenue_decline_cat": top_cat,
        "top_revenue_decline_eur": top_delta,
        "revenue_trend_dir": trend_dir,
    }


def _percentile_score(values: list[float], x: float | None,
                      higher_is_worse: bool) -> float:
    """0-100, 100 = best, 0 = worst. Mid-rank among ties."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return SMALL_SET_SCORE_DEFAULT
    clean = [v for v in values
             if v is not None and not (isinstance(v, float) and np.isnan(v))]
    n = len(clean)
    if n < MIN_SET_FOR_PERCENTILE:
        return SMALL_SET_SCORE_DEFAULT
    below = sum(1 for v in clean if v < x)
    equal = sum(1 for v in clean if v == x)
    rank_pct = 100.0 * (below + 0.5 * equal) / n
    return (100.0 - rank_pct) if higher_is_worse else rank_pct


def _compute_scores(rows: list[dict]) -> list[dict]:
    """Add the five score fields to each row in-place, return the list.

    Expects each row to already carry the ``eff_badness`` key produced by
    ``_efficiency_metrics``. Missing → treated as an unranked row (default 50).
    """
    unrent_vals = [r["unrent_now_eur"] for r in rows]
    total_cost_vals = [r["total_cost_increase_pct"] for r in rows]
    eff_vals = [r.get("eff_badness") for r in rows]
    duration_vals = [r["contract_duration_months"] for r in rows]
    cm_var_vals = [r["cm_variance"] for r in rows]
    rev_var_vals = [r["revenue_variance"] for r in rows]

    for r in rows:
        prof = _percentile_score(unrent_vals, r["unrent_now_eur"], True)
        cost = _percentile_score(total_cost_vals, r["total_cost_increase_pct"], True)
        eff = _percentile_score(eff_vals, r.get("eff_badness"), True)
        dur_score = _percentile_score(duration_vals, r["contract_duration_months"], False)
        cmv_score = _percentile_score(cm_var_vals, r["cm_variance"], True)
        rv_score = _percentile_score(rev_var_vals, r["revenue_variance"], True)
        stab = float(np.mean([dur_score, cmv_score, rv_score]))
        overall = float(np.mean([prof, cost, eff, stab]))

        r["profitability_score"] = round(prof, 1)
        r["cost_structure_score"] = round(cost, 1)
        r["efficiency_score"] = round(eff, 1)
        r["stability_score"] = round(stab, 1)
        r["overall_score"] = round(overall, 1)

    return rows


@st.cache_data(show_spinner=False, max_entries=32)
def compute_metrics(rankings: list[ContractRanking],
                    df: pd.DataFrame) -> list[ContractMetrics]:
    """Build a ContractMetrics per ranking using per-contract history in `df`."""
    if not rankings:
        return []
    if df is None or df.empty or "cost_center_id" not in df.columns:
        return []

    grouped = {str(cc): hist
               for cc, hist in df.groupby("cost_center_id", sort=False)}

    intermediate: list[dict] = []
    for r in rankings:
        hist = grouped.get(str(r.cost_center_id), pd.DataFrame())
        intermediate.append({
            "base": r,
            **_profitability_metrics(hist),
            **_cost_structure_metrics(hist),
            **_efficiency_metrics(hist),
            **_stability_metrics(hist),
            **_revenue_trend_metrics(hist),
        })

    _compute_scores(intermediate)

    out: list[ContractMetrics] = []
    for row in intermediate:
        row.pop("eff_badness", None)
        out.append(ContractMetrics(**row))
    return out


__all__ = [
    "ContractMetrics",
    "ContractOverviewMetrics",
    "COST_CATEGORY_COLUMNS",
    "LONG_TERM_MONTH_THRESHOLD",
    "REVENUE_STREAM_COLUMNS",
    "compute_contract_overview_metrics",
    "compute_metrics",
    "compute_rankings",
    "safe_pct_change",
]
