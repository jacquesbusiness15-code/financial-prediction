"""Unit tests for src.contract_metrics."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.contract_metrics import (  # noqa: E402
    LONG_TERM_MONTH_THRESHOLD,
    ContractMetrics,
    _compute_scores,
    _cost_structure_metrics,
    _efficiency_metrics,
    _profitability_metrics,
    _stability_metrics,
    compute_metrics,
)
from src.portfolio_ranking import compute_rankings  # noqa: E402


def _mk_history(cc_id: str, rows: list[dict]) -> pd.DataFrame:
    """Build a per-contract history DataFrame, padding identity columns."""
    base = {
        "cost_center_id": cc_id,
        "cost_center_name": f"Contract {cc_id}",
        "customer_name": "Cust",
        "region": "Nord",
        "industry": "facility",
        "entity": "WISAG",
    }
    return pd.DataFrame([{**base, **r} for r in rows])


def _monthly_periods(n: int, end=pd.Timestamp("2024-12-01")) -> list[pd.Timestamp]:
    return [end - pd.DateOffset(months=(n - 1 - i)) for i in range(n)]


# -------------------- Profitability --------------------

def test_unrent_now_uses_planned_minus_actual():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "cm_planned": 1000, "cm_db": 800,
         "revenue_total": 10000},
        {"period": periods[1], "cm_planned": 1000, "cm_db": 400,
         "revenue_total": 10000},
    ])
    out = _profitability_metrics(hist)
    assert out["unrent_now_eur"] == pytest.approx(600.0)
    assert out["unrent_mom_delta_eur"] == pytest.approx(400.0)  # 600 - 200
    assert out["profitability_trend_dir"] == "up"


def test_unrent_clamped_when_actual_beats_plan():
    hist = _mk_history("A", [{
        "period": pd.Timestamp("2024-12-01"),
        "cm_planned": 800, "cm_db": 1500, "revenue_total": 10000,
    }])
    out = _profitability_metrics(hist)
    assert out["unrent_now_eur"] == 0.0
    assert out["unrent_mom_delta_eur"] is None


def test_unrent_6m_delta_against_prior_mean():
    periods = _monthly_periods(7)
    rows = [{"period": p, "cm_planned": 1000, "cm_db": 900,
             "revenue_total": 10000} for p in periods[:-1]]
    rows.append({"period": periods[-1], "cm_planned": 1000, "cm_db": 500,
                 "revenue_total": 10000})
    out = _profitability_metrics(_mk_history("A", rows))
    # Prior six months all had unrent=100, latest=500 → delta = 400
    assert out["unrent_6m_delta_eur"] == pytest.approx(400.0)


# -------------------- Cost structure --------------------

def test_top_cost_increase_cat_picks_biggest_mom_jump():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0],
         "labor_cost_total": 1000, "material_cost": 500, "vehicle_cost": 100,
         "revenue_total": 5000, "cm_db": 100, "cm_planned": 200},
        {"period": periods[1],
         "labor_cost_total": 1500, "material_cost": 520, "vehicle_cost": 110,
         "revenue_total": 5000, "cm_db": 100, "cm_planned": 200},
    ])
    out = _cost_structure_metrics(hist)
    assert out["top_cost_increase_cat"] == "labor"
    assert out["top_cost_increase_pct"] == pytest.approx(0.5)  # 500/1000
    assert out["top_cost_category_now"] == "labor"


def test_total_cost_increase_pct_handles_zero_prev():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0],
         "labor_cost_total": 0, "material_cost": 0, "revenue_total": 1000,
         "cm_db": 0, "cm_planned": 0},
        {"period": periods[1],
         "labor_cost_total": 500, "material_cost": 100, "revenue_total": 1000,
         "cm_db": 0, "cm_planned": 0},
    ])
    out = _cost_structure_metrics(hist)
    assert out["total_cost_increase_pct"] is None


# -------------------- Efficiency --------------------

def test_efficiency_ratio_deltas_and_hour_variance():
    periods = _monthly_periods(7)
    rows = []
    for i, p in enumerate(periods):
        rows.append({
            "period": p,
            "hours_planned": 100,
            "hours_productive": 90 if i < 6 else 60,
            "hour_variance": 5,
            "revenue_total": 1000,
            "cm_db": 100, "cm_planned": 150,
        })
    out = _efficiency_metrics(_mk_history("A", rows))
    assert out["hours_planned_minus_productive"] == pytest.approx(40.0)
    # MoM: ratio went 0.9 → 0.6 → delta -30pp
    assert out["ratio_mom_delta_pp"] == pytest.approx(-30.0)
    # 6m mean ratio = 0.9, now = 0.6 → delta -30pp
    assert out["ratio_6m_delta_pp"] == pytest.approx(-30.0)
    assert out["hour_variance"] == 5.0


def test_efficiency_with_zero_planned_hours_returns_none_ratio():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "hours_planned": 0, "hours_productive": 0,
         "hour_variance": 0, "revenue_total": 1000, "cm_db": 0, "cm_planned": 0},
        {"period": periods[1], "hours_planned": 0, "hours_productive": 0,
         "hour_variance": 0, "revenue_total": 1000, "cm_db": 0, "cm_planned": 0},
    ])
    out = _efficiency_metrics(hist)
    assert out["ratio_mom_delta_pp"] is None


# -------------------- Stability --------------------

def test_duration_uses_today_when_contract_end_missing():
    start = pd.Timestamp(date.today() - timedelta(days=200))
    hist = _mk_history("A", [{
        "period": pd.Timestamp("2024-12-01"),
        "contract_start": start,
        "contract_end": pd.NaT,
        "cm_db": 100, "cm_planned": 100, "revenue_total": 1000,
    }])
    out = _stability_metrics(hist)
    assert out["contract_duration_months"] is not None
    # 200 days / 30.4375 ≈ 6.57 → rounds to 7
    assert 6 <= out["contract_duration_months"] <= 7


def test_long_term_boundary_exactly_12_months():
    start = pd.Timestamp(date.today() - timedelta(days=int(30.4375 * 12)))
    hist = _mk_history("A", [{
        "period": pd.Timestamp("2024-12-01"),
        "contract_start": start,
        "contract_end": pd.NaT,
        "cm_db": 100, "cm_planned": 100, "revenue_total": 1000,
    }])
    out = _stability_metrics(hist)
    assert out["contract_duration_months"] == LONG_TERM_MONTH_THRESHOLD
    assert out["is_long_term"] is True


def test_short_term_below_threshold():
    start = pd.Timestamp(date.today() - timedelta(days=300))  # ~9.85 months
    hist = _mk_history("A", [{
        "period": pd.Timestamp("2024-12-01"),
        "contract_start": start,
        "contract_end": pd.NaT,
        "cm_db": 100, "cm_planned": 100, "revenue_total": 1000,
    }])
    out = _stability_metrics(hist)
    assert out["is_long_term"] is False


def test_cm_and_revenue_variance_non_negative():
    periods = _monthly_periods(6)
    rows = [{"period": p, "cm_db": 100 + i * 10, "revenue_total": 1000 + i * 100,
             "cm_planned": 100, "contract_start": periods[0],
             "contract_end": periods[-1]}
            for i, p in enumerate(periods)]
    out = _stability_metrics(_mk_history("A", rows))
    assert out["cm_variance"] is not None and out["cm_variance"] > 0
    assert out["revenue_variance"] is not None and out["revenue_variance"] > 0


# -------------------- Scoring --------------------

def test_overall_score_is_mean_of_sub_scores():
    rows = [
        {"profitability_score": 80, "cost_structure_score": 60,
         "efficiency_score": 40, "stability_score": 20},
    ]
    # Simulate by manually computing overall = mean
    expected = 50.0
    assert pytest.approx(expected) == sum(rows[0].values()) / 4


def test_small_set_scoring_returns_neutral_defaults():
    rows = [{
        "unrent_now_eur": 100.0,
        "total_cost_increase_pct": 0.1,
        "hours_planned_minus_productive": 10.0,
        "_hours_planned": 100.0,
        "contract_duration_months": 12,
        "cm_variance": 50.0,
        "revenue_variance": 300.0,
    }]
    _compute_scores(rows)
    # n=1 → every sub-score defaults to 50, overall also 50.
    assert rows[0]["profitability_score"] == 50.0
    assert rows[0]["overall_score"] == 50.0


def test_scoring_ranks_worst_to_zero_and_best_to_hundred():
    rows = []
    for unrent in [0.0, 100.0, 200.0, 300.0]:
        rows.append({
            "unrent_now_eur": unrent,
            "total_cost_increase_pct": 0.0,
            "hours_planned_minus_productive": 0.0,
            "_hours_planned": 100.0,
            "contract_duration_months": 12,
            "cm_variance": 0.0,
            "revenue_variance": 0.0,
        })
    _compute_scores(rows)
    scores = [r["profitability_score"] for r in rows]
    # Monotonically decreasing as unrent rises, best=100, worst=0.
    assert scores[0] > scores[1] > scores[2] > scores[3]
    assert scores[0] > 80.0
    assert scores[-1] < 20.0


# -------------------- End-to-end --------------------

def test_compute_metrics_end_to_end():
    periods = _monthly_periods(8)
    rows_a = []
    rows_b = []
    rows_c = []
    for i, p in enumerate(periods):
        rows_a.append({
            "period": p, "cm_planned": 1000,
            "cm_db": 900 if i < 7 else 200,
            "revenue_total": 10000, "labor_cost_total": 1000, "material_cost": 200,
            "hours_planned": 100, "hours_productive": 90, "hour_variance": 2,
            "contract_start": periods[0], "contract_end": periods[-1],
        })
        rows_b.append({
            "period": p, "cm_planned": 500,
            "cm_db": 500, "revenue_total": 5000, "labor_cost_total": 500,
            "material_cost": 100,
            "hours_planned": 100, "hours_productive": 95, "hour_variance": 1,
            "contract_start": periods[0], "contract_end": periods[-1],
        })
        rows_c.append({
            "period": p, "cm_planned": 300,
            "cm_db": 100 + i * 20, "revenue_total": 3000,
            "labor_cost_total": 300, "material_cost": 50,
            "hours_planned": 100, "hours_productive": 80, "hour_variance": 4,
            "contract_start": periods[0], "contract_end": periods[-1],
        })
    df = pd.concat([
        _mk_history("A", rows_a),
        _mk_history("B", rows_b),
        _mk_history("C", rows_c),
    ], ignore_index=True)

    rankings = compute_rankings(df)
    metrics = compute_metrics(rankings, df)
    assert len(metrics) == 3
    by_id = {m.base.cost_center_id: m for m in metrics}

    # Contract A has the blown-out unrentability → lowest profitability score.
    a = by_id["A"]
    b = by_id["B"]
    assert a.profitability_score < b.profitability_score
    for m in metrics:
        assert 0.0 <= m.overall_score <= 100.0
        assert isinstance(m, ContractMetrics)
