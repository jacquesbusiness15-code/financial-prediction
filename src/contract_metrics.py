"""Per-contract multi-dimensional metrics + 0-100 scoring.

Wraps the identity-centric `ContractRanking` from `src.portfolio_ranking` and
adds four category-specific metric bundles (profitability, cost structure,
efficiency, stability) plus a composite overall score. Scores are percentile-
ranked across the *visible* set so the "best" contract in the filtered view
gets 100 and the "worst" gets 0.

No Streamlit imports here — safe to unit-test.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from src.portfolio_ranking import ContractRanking, compute_rankings


# Cost-category columns used for "highest cost" / "highest MoM increase".
# Mirrors src/config.py COST_COLS_DB + COST_COLS_DB1_EXTRA + COST_COLS_DB2_EXTRA
# but grouped for display (we show one label per group, not per sub-column).
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


@dataclass
class ContractMetrics:
    base: ContractRanking

    # Profitability
    unrent_now_eur: float
    unrent_mom_delta_eur: float | None
    unrent_6m_delta_eur: float | None
    top_cost_increase_cat_mom: str | None
    profitability_trend_dir: str  # "up" | "down" | "flat"
    cm_mom_pct: float | None  # MoM change of actual cm_db as a ratio, e.g. -0.12

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


def _cost_category_value(row: pd.Series, cols: list[str]) -> float:
    total = 0.0
    for c in cols:
        if c in row.index:
            total += _safe_float(row[c])
    return total


def _category_totals(row: pd.Series) -> dict[str, float]:
    return {key: _cost_category_value(row, cols)
            for key, cols in COST_CATEGORY_COLUMNS.items()}


def _unrent(row: pd.Series) -> float:
    """Unrentability = max(planned CM - actual CM, 0). Positive = loss vs plan."""
    planned = _safe_float(row.get("cm_planned"))
    actual = _safe_float(row.get("cm_db"))
    return max(planned - actual, 0.0)


def _profitability_metrics(history: pd.DataFrame) -> dict:
    hist = history.sort_values("period") if "period" in history.columns else history
    if hist.empty:
        return {
            "unrent_now_eur": 0.0,
            "unrent_mom_delta_eur": None,
            "unrent_6m_delta_eur": None,
            "profitability_trend_dir": "flat",
            "cm_mom_pct": None,
        }
    latest = hist.iloc[-1]
    unrent_now = _unrent(latest)

    mom_delta: float | None = None
    cm_mom_pct: float | None = None
    if len(hist) >= 2:
        prev = hist.iloc[-2]
        mom_delta = unrent_now - _unrent(prev)
        cm_now = _safe_float(latest.get("cm_db"))
        cm_prev = _safe_float(prev.get("cm_db"))
        # Signed % change. Requires a non-zero baseline with the same sign
        # convention to be interpretable; fall back to None otherwise.
        if cm_prev != 0:
            cm_mom_pct = (cm_now - cm_prev) / abs(cm_prev)

    six_m_delta: float | None = None
    if len(hist) >= 2:
        prior = hist.iloc[:-1].tail(6)
        prior_vals = [_unrent(r) for _, r in prior.iterrows()]
        if prior_vals:
            six_m_delta = unrent_now - float(np.mean(prior_vals))

    if mom_delta is None or mom_delta == 0:
        trend_dir = "flat"
    elif mom_delta > 0:
        trend_dir = "up"  # worsening
    else:
        trend_dir = "down"  # improving

    return {
        "unrent_now_eur": unrent_now,
        "unrent_mom_delta_eur": mom_delta,
        "unrent_6m_delta_eur": six_m_delta,
        "profitability_trend_dir": trend_dir,
        "cm_mom_pct": cm_mom_pct,
    }


def _cost_structure_metrics(history: pd.DataFrame) -> dict:
    hist = history.sort_values("period") if "period" in history.columns else history
    if hist.empty:
        return {
            "top_cost_category_now": None,
            "top_cost_category_now_eur": 0.0,
            "top_cost_increase_cat": None,
            "top_cost_increase_pct": None,
            "total_cost_increase_pct": None,
            "top_cost_increase_cat_mom": None,
        }
    latest = hist.iloc[-1]
    now_totals = _category_totals(latest)

    top_cat_now = None
    top_cat_now_eur = 0.0
    for cat, val in now_totals.items():
        if val > top_cat_now_eur:
            top_cat_now = cat
            top_cat_now_eur = val

    prior = hist.iloc[-2] if len(hist) >= 2 else None
    top_inc_cat: str | None = None
    top_inc_pct: float | None = None
    total_pct: float | None = None

    if prior is not None:
        prev_totals = _category_totals(prior)
        biggest_delta_eur = 0.0
        for cat, now_val in now_totals.items():
            delta = now_val - prev_totals.get(cat, 0.0)
            if delta > biggest_delta_eur:
                biggest_delta_eur = delta
                top_inc_cat = cat
                prev = prev_totals.get(cat, 0.0)
                top_inc_pct = (delta / prev) if prev > 0 else None

        total_now = sum(now_totals.values())
        total_prev = sum(prev_totals.values())
        if total_prev > 0:
            total_pct = (total_now - total_prev) / total_prev

    return {
        "top_cost_category_now": top_cat_now,
        "top_cost_category_now_eur": top_cat_now_eur,
        "top_cost_increase_cat": top_inc_cat,
        "top_cost_increase_pct": top_inc_pct,
        "total_cost_increase_pct": total_pct,
        "top_cost_increase_cat_mom": top_inc_cat,
    }


def _efficiency_metrics(history: pd.DataFrame) -> dict:
    hist = history.sort_values("period") if "period" in history.columns else history
    if hist.empty:
        return {
            "hours_planned_minus_productive": None,
            "ratio_mom_delta_pp": None,
            "ratio_6m_delta_pp": None,
            "hour_variance": None,
        }
    latest = hist.iloc[-1]
    planned = _safe_float(latest.get("hours_planned"))
    productive = _safe_float(latest.get("hours_productive"))
    diff = planned - productive
    hour_var = latest.get("hour_variance")
    hour_var_f = _safe_float(hour_var, default=float("nan"))
    hour_variance = None if np.isnan(hour_var_f) else hour_var_f

    def ratio(row: pd.Series) -> float | None:
        p = _safe_float(row.get("hours_planned"))
        prod = _safe_float(row.get("hours_productive"))
        return (prod / p) if p > 0 else None

    now_ratio = ratio(latest)

    mom_pp: float | None = None
    if len(hist) >= 2:
        prev_ratio = ratio(hist.iloc[-2])
        if now_ratio is not None and prev_ratio is not None:
            mom_pp = (now_ratio - prev_ratio) * 100.0

    six_m_pp: float | None = None
    if len(hist) >= 2:
        prior = hist.iloc[:-1].tail(6)
        prior_ratios = [r for r in (ratio(row) for _, row in prior.iterrows())
                        if r is not None]
        if prior_ratios and now_ratio is not None:
            six_m_pp = (now_ratio - float(np.mean(prior_ratios))) * 100.0

    return {
        "hours_planned_minus_productive": diff,
        "ratio_mom_delta_pp": mom_pp,
        "ratio_6m_delta_pp": six_m_pp,
        "hour_variance": hour_variance,
    }


def _stability_metrics(history: pd.DataFrame) -> dict:
    hist = history.sort_values("period") if "period" in history.columns else history
    if hist.empty:
        return {
            "contract_duration_months": None,
            "cm_variance": None,
            "is_long_term": False,
            "revenue_variance": None,
        }
    latest = hist.iloc[-1]

    start = latest.get("contract_start")
    end = latest.get("contract_end")
    start_ts = pd.to_datetime(start, errors="coerce") if start is not None else pd.NaT
    end_ts = pd.to_datetime(end, errors="coerce") if end is not None else pd.NaT

    duration_months: int | None = None
    if pd.notna(start_ts):
        end_for_calc = end_ts if pd.notna(end_ts) else pd.Timestamp(date.today())
        delta_days = (end_for_calc - start_ts).days
        if delta_days >= 0:
            duration_months = int(round(delta_days / 30.4375))

    is_long = (duration_months is not None
               and duration_months >= LONG_TERM_MONTH_THRESHOLD)

    def variance(col: str) -> float | None:
        if col not in hist.columns:
            return None
        series = pd.to_numeric(hist[col], errors="coerce").dropna()
        if len(series) < 2:
            return None
        return float(series.std(ddof=0))

    return {
        "contract_duration_months": duration_months,
        "cm_variance": variance("cm_db"),
        "is_long_term": is_long,
        "revenue_variance": variance("revenue_total"),
    }


def _percentile_score(values: list[float], x: float | None,
                      higher_is_worse: bool) -> float:
    """0-100, 100 = best, 0 = worst.

    When `higher_is_worse` is True, the largest value in the set scores 0.
    When False, the largest value scores 100. NaN / None `x` returns the
    neutral default.
    """
    clean = [v for v in values if v is not None and not (isinstance(v, float)
                                                         and np.isnan(v))]
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return SMALL_SET_SCORE_DEFAULT
    if len(clean) < MIN_SET_FOR_PERCENTILE:
        return SMALL_SET_SCORE_DEFAULT
    n = len(clean)
    below = sum(1 for v in clean if v < x)
    equal = sum(1 for v in clean if v == x)
    # Mid-rank among ties, normalised to 0..1 then scaled to 0..100.
    rank_pct = 100.0 * (below + 0.5 * equal) / n
    return (100.0 - rank_pct) if higher_is_worse else rank_pct


def _compute_scores(rows: list[dict]) -> list[dict]:
    """Add the five score fields to each row in-place, return the list."""
    unrent_vals = [r["unrent_now_eur"] for r in rows]
    total_cost_vals = [r["total_cost_increase_pct"] for r in rows]

    def eff_badness(r: dict) -> float | None:
        diff = r["hours_planned_minus_productive"]
        if diff is None:
            return None
        hp = r.get("_hours_planned") or 0.0
        if hp <= 0:
            return None
        return abs(diff) / hp

    eff_vals = [eff_badness(r) for r in rows]
    duration_vals = [r["contract_duration_months"] for r in rows]
    cm_var_vals = [r["cm_variance"] for r in rows]
    rev_var_vals = [r["revenue_variance"] for r in rows]

    for r in rows:
        prof = _percentile_score(unrent_vals, r["unrent_now_eur"],
                                 higher_is_worse=True)
        cost = _percentile_score(total_cost_vals, r["total_cost_increase_pct"],
                                 higher_is_worse=True)
        eff = _percentile_score(eff_vals, eff_badness(r), higher_is_worse=True)

        dur_score = _percentile_score(duration_vals,
                                      r["contract_duration_months"],
                                      higher_is_worse=False)
        cmv_score = _percentile_score(cm_var_vals, r["cm_variance"],
                                      higher_is_worse=True)
        rv_score = _percentile_score(rev_var_vals, r["revenue_variance"],
                                     higher_is_worse=True)
        stab = float(np.mean([dur_score, cmv_score, rv_score]))

        overall = float(np.mean([prof, cost, eff, stab]))

        r["profitability_score"] = round(prof, 1)
        r["cost_structure_score"] = round(cost, 1)
        r["efficiency_score"] = round(eff, 1)
        r["stability_score"] = round(stab, 1)
        r["overall_score"] = round(overall, 1)

    return rows


def compute_metrics(rankings: list[ContractRanking],
                    df: pd.DataFrame) -> list[ContractMetrics]:
    """Build a ContractMetrics per ranking using the per-contract history in `df`.

    `df` is the full (optionally filtered) dataset from which `rankings` was
    built. We look up each contract's history by `cost_center_id` so metrics
    can consult every row the UI considers visible.
    """
    if not rankings:
        return []
    if df is None or df.empty or "cost_center_id" not in df.columns:
        return []

    grouped = {str(cc): hist for cc, hist in df.groupby("cost_center_id",
                                                        sort=False)}

    intermediate: list[dict] = []
    for r in rankings:
        hist = grouped.get(str(r.cost_center_id), pd.DataFrame())
        prof = _profitability_metrics(hist)
        cost = _cost_structure_metrics(hist)
        eff = _efficiency_metrics(hist)
        stab = _stability_metrics(hist)

        hp_latest = 0.0
        if not hist.empty and "hours_planned" in hist.columns:
            last_hp = hist.sort_values("period").iloc[-1].get("hours_planned")
            hp_latest = _safe_float(last_hp)

        intermediate.append({
            "base": r,
            **prof, **cost, **eff, **stab,
            "_hours_planned": hp_latest,
        })

    _compute_scores(intermediate)

    out: list[ContractMetrics] = []
    for row in intermediate:
        row.pop("_hours_planned", None)
        out.append(ContractMetrics(**row))
    return out


__all__ = [
    "ContractMetrics",
    "COST_CATEGORY_COLUMNS",
    "LONG_TERM_MONTH_THRESHOLD",
    "compute_metrics",
]


# Re-export for test convenience.
_ = compute_rankings  # keep import used
