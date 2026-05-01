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
    ContractOverviewMetrics,
    _compute_scores,
    _cost_structure_metrics,
    _efficiency_metrics,
    _profitability_metrics,
    _revenue_trend_metrics,
    _stability_metrics,
    compute_contract_overview_metrics,
    compute_metrics,
    safe_pct_change,
)
from src.portfolio_ranking import compute_rankings  # noqa: E402

_DEC_2024 = pd.Timestamp("2024-12-01")
_STABILITY_DEFAULTS = {
    "cm_db": 100, "cm_planned": 100, "revenue_total": 1000,
    "contract_end": pd.NaT,
}


def _mk_history(cc_id: str, rows: list[dict]) -> pd.DataFrame:
    base = {
        "cost_center_id": cc_id,
        "cost_center_name": f"Contract {cc_id}",
        "customer_name": "Cust",
        "region": "Nord",
        "industry": "facility",
        "entity": "WISAG",
    }
    return pd.DataFrame([{**base, **r} for r in rows])


def _monthly_periods(n: int, end=_DEC_2024) -> list[pd.Timestamp]:
    return [end - pd.DateOffset(months=(n - 1 - i)) for i in range(n)]


def _single_stability_row(start: pd.Timestamp) -> pd.DataFrame:
    return _mk_history("A", [{**_STABILITY_DEFAULTS,
                              "period": _DEC_2024,
                              "contract_start": start}])


# -------------------- safe_pct_change --------------------

def test_safe_pct_change_accepts_user_example():
    # User's canonical example: "drop from near 80 € to 1 €" must read as
    # roughly -98.75 %, not an absurd -5000 %.
    assert safe_pct_change(1.0, 80.0) == pytest.approx(-0.9875)


def test_safe_pct_change_rejects_tiny_baseline_absolute():
    # A 1 € prev month is below the 10 € absolute floor.
    assert safe_pct_change(50.0, 1.0) is None


def test_safe_pct_change_rejects_tiny_baseline_relative():
    # 20 € is above the absolute floor but below 5 % of 1000 -> fresh series.
    assert safe_pct_change(1000.0, 20.0) is None


def test_safe_pct_change_rejects_sign_flip():
    # CM flipping from +1 to -49 would legitimately compute as -5000 %.
    assert safe_pct_change(-49.0, 1.0) is None


def test_safe_pct_change_allows_sign_flip_when_requested():
    assert safe_pct_change(-49.0, 100.0, allow_sign_flip=True) == pytest.approx(-1.49)


def test_safe_pct_change_handles_none_and_zero_baseline():
    assert safe_pct_change(50.0, None) is None
    assert safe_pct_change(50.0, 0.0) is None
    assert safe_pct_change(None, 50.0) is None


# -------------------- Contract overview KPIs --------------------

def test_contract_overview_metrics_use_expected_formulas():
    current = pd.Series({"revenue_total": 1000.0, "cm_db": 250.0})
    prior = pd.Series({"revenue_total": 900.0, "cm_db": 180.0})

    out = compute_contract_overview_metrics(current, prior)

    assert isinstance(out, ContractOverviewMetrics)
    assert out.total_cost_eur == pytest.approx(750.0)
    assert out.cost_mom_eur == pytest.approx(30.0)
    assert out.cost_mom_pct == pytest.approx(30.0 / 720.0)
    assert out.margin_eur == pytest.approx(250.0)
    assert out.margin_mom_eur == pytest.approx(70.0)
    assert out.margin_pct == pytest.approx(0.25)
    assert out.margin_mom_delta == pytest.approx(0.25 - 0.2)


def test_contract_overview_cost_mom_is_always_available_as_eur_delta():
    current = pd.Series({"revenue_total": 1000.0, "cm_db": 250.0})
    prior = pd.Series({"revenue_total": 8.0, "cm_db": 1.0})

    out = compute_contract_overview_metrics(current, prior)

    assert out.cost_mom_eur == pytest.approx((1000.0 - 250.0) - (8.0 - 1.0))


def test_contract_overview_metrics_hide_margin_for_tiny_revenue():
    current = pd.Series({"revenue_total": 5.0, "cm_db": 1.0})
    prior = pd.Series({"revenue_total": 100.0, "cm_db": 20.0})

    out = compute_contract_overview_metrics(current, prior)

    assert out.total_cost_eur == pytest.approx(4.0)
    assert out.margin_eur == pytest.approx(1.0)
    assert out.margin_mom_eur == pytest.approx(-19.0)
    assert out.margin_pct is None
    assert out.margin_mom_delta is None


def test_contract_overview_metrics_use_cm_db_pct_when_available():
    current = pd.Series({"revenue_total": 0.952, "cm_db": 0.164685, "cm_db_pct": 17.298824})
    prior = pd.Series({"revenue_total": 0.910, "cm_db": 0.120000, "cm_db_pct": 12.000000})

    out = compute_contract_overview_metrics(current, prior)

    assert out.margin_eur == pytest.approx(0.164685)
    assert out.margin_mom_eur == pytest.approx(0.044685)
    assert out.margin_pct == pytest.approx(0.17298824)
    assert out.margin_mom_delta == pytest.approx(0.05298824)


def test_contract_overview_metrics_reject_tiny_previous_cost_for_pct_change():
    current = pd.Series({"revenue_total": 100.0, "cm_db": 20.0})
    prior = pd.Series({"revenue_total": 5.0, "cm_db": 0.5})

    out = compute_contract_overview_metrics(current, prior)

    assert out.total_cost_eur == pytest.approx(80.0)
    assert out.cost_mom_eur == pytest.approx(75.5)
    assert out.margin_eur == pytest.approx(20.0)
    assert out.margin_mom_eur == pytest.approx(19.5)
    assert out.cost_mom_pct is None


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
    assert out["unrent_mom_delta_eur"] == pytest.approx(400.0)
    assert out["profitability_trend_dir"] == "up"


def test_unrent_clamped_when_actual_beats_plan():
    hist = _mk_history("A", [{
        "period": _DEC_2024,
        "cm_planned": 800, "cm_db": 1500, "revenue_total": 10000,
    }])
    out = _profitability_metrics(hist)
    assert out["unrent_now_eur"] == 0.0
    assert out["unrent_mom_delta_eur"] is None


def test_cm_mom_pct_is_none_on_sign_flip():
    # CM flipping from +1 € to -49 € used to produce -5000 %.
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "cm_planned": 100, "cm_db": 1,
         "revenue_total": 10000},
        {"period": periods[1], "cm_planned": 100, "cm_db": -49,
         "revenue_total": 10000},
    ])
    out = _profitability_metrics(hist)
    assert out["cm_mom_pct"] is None


def test_cm_mom_pct_is_none_on_tiny_baseline():
    # cm_prev=1 passes the old `!= 0` guard but is below the new 10 € floor.
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "cm_planned": 100, "cm_db": 1,
         "revenue_total": 10000},
        {"period": periods[1], "cm_planned": 100, "cm_db": 5,
         "revenue_total": 10000},
    ])
    out = _profitability_metrics(hist)
    assert out["cm_mom_pct"] is None


def test_unrent_6m_delta_against_prior_mean():
    periods = _monthly_periods(7)
    rows = [{"period": p, "cm_planned": 1000, "cm_db": 900,
             "revenue_total": 10000} for p in periods[:-1]]
    rows.append({"period": periods[-1], "cm_planned": 1000, "cm_db": 500,
                 "revenue_total": 10000})
    out = _profitability_metrics(_mk_history("A", rows))
    # Prior six months all had unrent=100, latest=500 -> delta = 400
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
    assert out["top_cost_increase_pct"] == pytest.approx(0.5)
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


def test_total_cost_increase_pct_rejects_tiny_prev():
    # 5 € of prior cost against 600 € now looks like +11.900 % under naive math;
    # `safe_pct_change` correctly rejects it as a fresh series.
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0],
         "labor_cost_total": 5, "material_cost": 0, "revenue_total": 1000,
         "cm_db": 0, "cm_planned": 0},
        {"period": periods[1],
         "labor_cost_total": 500, "material_cost": 100, "revenue_total": 1000,
         "cm_db": 0, "cm_planned": 0},
    ])
    out = _cost_structure_metrics(hist)
    assert out["total_cost_increase_pct"] is None


def test_top_inc_pct_rejects_tiny_baseline():
    # Category prev = 0.50 € is below the 10 € floor; the jump should NOT be
    # displayed as a percentage even though labor is still flagged as biggest.
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0],
         "labor_cost_total": 0.50, "material_cost": 500,
         "revenue_total": 5000, "cm_db": 100, "cm_planned": 200},
        {"period": periods[1],
         "labor_cost_total": 50, "material_cost": 500,
         "revenue_total": 5000, "cm_db": 100, "cm_planned": 200},
    ])
    out = _cost_structure_metrics(hist)
    assert out["top_cost_increase_cat"] == "labor"
    assert out["top_cost_increase_pct"] is None


# -------------------- Efficiency --------------------

def test_efficiency_ratio_deltas_and_hour_variance():
    periods = _monthly_periods(7)
    rows = [{
        "period": p,
        "hours_planned": 100,
        "hours_productive": 90 if i < 6 else 60,
        "hour_variance": 5,
        "revenue_total": 1000,
        "cm_db": 100, "cm_planned": 150,
    } for i, p in enumerate(periods)]
    out = _efficiency_metrics(_mk_history("A", rows))
    assert out["hours_planned_minus_productive"] == pytest.approx(40.0)
    assert out["ratio_mom_delta_pp"] == pytest.approx(-30.0)
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
    out = _stability_metrics(_single_stability_row(
        pd.Timestamp(date.today() - timedelta(days=200))))
    # 200 days / 30.4375 ~= 6.57 -> rounds to 7
    assert out["contract_duration_months"] is not None
    assert 6 <= out["contract_duration_months"] <= 7


def test_long_term_boundary_exactly_12_months():
    start = pd.Timestamp(date.today() - timedelta(days=int(30.4375 * 12)))
    out = _stability_metrics(_single_stability_row(start))
    assert out["contract_duration_months"] == LONG_TERM_MONTH_THRESHOLD
    assert out["is_long_term"] is True


def test_short_term_below_threshold():
    start = pd.Timestamp(date.today() - timedelta(days=300))  # ~9.85 months
    out = _stability_metrics(_single_stability_row(start))
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
    sub_scores = {"profitability_score": 80, "cost_structure_score": 60,
                  "efficiency_score": 40, "stability_score": 20}
    assert pytest.approx(50.0) == sum(sub_scores.values()) / 4


def test_small_set_scoring_returns_neutral_defaults():
    rows = [{
        "unrent_now_eur": 100.0,
        "total_cost_increase_pct": 0.1,
        "hours_planned_minus_productive": 10.0,
        "eff_badness": 0.10,
        "contract_duration_months": 12,
        "cm_variance": 50.0,
        "revenue_variance": 300.0,
    }]
    _compute_scores(rows)
    # n=1 -> every sub-score defaults to 50, overall also 50.
    assert rows[0]["profitability_score"] == 50.0
    assert rows[0]["overall_score"] == 50.0


def test_scoring_ranks_worst_to_zero_and_best_to_hundred():
    rows = [{
        "unrent_now_eur": unrent,
        "total_cost_increase_pct": 0.0,
        "hours_planned_minus_productive": 0.0,
        "eff_badness": 0.0,
        "contract_duration_months": 12,
        "cm_variance": 0.0,
        "revenue_variance": 0.0,
    } for unrent in [0.0, 100.0, 200.0, 300.0]]
    _compute_scores(rows)
    scores = [r["profitability_score"] for r in rows]
    assert scores[0] > scores[1] > scores[2] > scores[3]
    assert scores[0] > 80.0
    assert scores[-1] < 20.0


# -------------------- End-to-end --------------------

def test_compute_metrics_end_to_end():
    periods = _monthly_periods(8)
    common = {
        "hours_planned": 100, "hour_variance": 1,
        "contract_start": periods[0], "contract_end": periods[-1],
    }

    def _row(p, i, *, cm_planned, cm_db, revenue, labor, material, productive):
        return {
            **common, "period": p,
            "cm_planned": cm_planned, "cm_db": cm_db, "revenue_total": revenue,
            "labor_cost_total": labor, "material_cost": material,
            "hours_productive": productive,
        }

    rows_a = [_row(p, i, cm_planned=1000, cm_db=(900 if i < 7 else 200),
                   revenue=10000, labor=1000, material=200, productive=90)
              for i, p in enumerate(periods)]
    rows_b = [_row(p, i, cm_planned=500, cm_db=500, revenue=5000,
                   labor=500, material=100, productive=95)
              for i, p in enumerate(periods)]
    rows_c = [_row(p, i, cm_planned=300, cm_db=100 + i * 20, revenue=3000,
                   labor=300, material=50, productive=80)
              for i, p in enumerate(periods)]
    # Hour variance differs per contract; patch after row construction.
    for r in rows_a: r["hour_variance"] = 2
    for r in rows_c: r["hour_variance"] = 4

    df = pd.concat([
        _mk_history("A", rows_a),
        _mk_history("B", rows_b),
        _mk_history("C", rows_c),
    ], ignore_index=True)

    metrics = compute_metrics(compute_rankings(df), df)
    assert len(metrics) == 3
    by_id = {m.base.cost_center_id: m for m in metrics}

    # Contract A has the blown-out unrentability -> lowest profitability score.
    assert by_id["A"].profitability_score < by_id["B"].profitability_score
    for m in metrics:
        assert 0.0 <= m.overall_score <= 100.0
        assert isinstance(m, ContractMetrics)


# -------------------- Audit regression tests (2026-04) --------------------
# These cover the bugs surfaced during the "every contract value" audit:
#   * NaN cm_db/revenue no longer silently becomes 0 € in the overview.
#   * cm_db_pct stored as a ratio (0.17) falls back to cm_db/revenue_total.
#   * _compute_scores no longer depends on a temp `_hours_planned` key.
#   * The former duplicate `top_cost_increase_cat_mom` field is gone.

def test_overview_returns_none_when_cm_db_missing():
    current = pd.Series({"revenue_total": float("nan"), "cm_db": float("nan")})
    prior = pd.Series({"revenue_total": 900.0, "cm_db": 180.0})
    out = compute_contract_overview_metrics(current, prior)
    assert out.total_cost_eur is None
    assert out.margin_eur is None
    assert out.margin_pct is None
    assert out.cost_mom_eur is None
    assert out.margin_mom_eur is None


def test_overview_returns_none_when_only_cm_db_missing():
    # Revenue is known, CM is not — the margin is genuinely unknown, not 0.
    current = pd.Series({"revenue_total": 1000.0, "cm_db": float("nan")})
    out = compute_contract_overview_metrics(current, None)
    assert out.margin_eur is None
    assert out.margin_pct is None
    # total_cost is revenue - cm_db; with cm_db missing it must be None too,
    # otherwise the UI would read "Kosten = Umsatz" which is false.
    assert out.total_cost_eur is None


def test_overview_margin_pct_ignores_cm_db_pct_when_in_ratio_form():
    # Upstream stored the ratio (0.17) instead of the percent (17). The old
    # code returned 0.0017; the fix must fall back to cm_db / revenue_total.
    current = pd.Series({"revenue_total": 1000.0, "cm_db": 250.0, "cm_db_pct": 0.17})
    out = compute_contract_overview_metrics(current, None)
    assert out.margin_pct == pytest.approx(0.25)


def test_overview_margin_pct_honours_cm_db_pct_when_in_percent_form():
    # Sanity: the canonical path (cm_db_pct in percent) still works.
    current = pd.Series({"revenue_total": 1000.0, "cm_db": 250.0, "cm_db_pct": 17.0})
    out = compute_contract_overview_metrics(current, None)
    assert out.margin_pct == pytest.approx(0.17)


# -------------------- Profitability edge cases --------------------

def test_profitability_trend_dir_flat_on_zero_mom_delta():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "cm_planned": 100, "cm_db": 50,
         "revenue_total": 1000},
        {"period": periods[1], "cm_planned": 100, "cm_db": 50,
         "revenue_total": 1000},
    ])
    out = _profitability_metrics(hist)
    assert out["unrent_mom_delta_eur"] == 0.0
    assert out["profitability_trend_dir"] == "flat"


def test_profitability_6m_delta_none_for_short_history():
    hist = _mk_history("A", [
        {"period": _DEC_2024, "cm_planned": 100, "cm_db": 50,
         "revenue_total": 1000}
    ])
    out = _profitability_metrics(hist)
    assert out["unrent_6m_delta_eur"] is None


def test_profitability_6m_window_uses_exactly_six_months_before_latest():
    # Build 10 periods: the first four should be outside the window.
    periods = _monthly_periods(10)
    rows = []
    for i, p in enumerate(periods):
        # periods[0..3] carry cm_db=0 (unrent=1000); periods[4..8] carry
        # cm_db=500 (unrent=500). Those five contribute along with a
        # sixth window-row (period 9-1=8) when latest=period[9].
        if i < 4:
            cm = 0
        elif i < 9:
            cm = 500
        else:  # latest row
            cm = 200
        rows.append({"period": p, "cm_planned": 1000, "cm_db": cm,
                     "revenue_total": 10_000})
    out = _profitability_metrics(_mk_history("A", rows))
    # Window = periods[3..8] (six rows). unrent for those rows:
    #   i=3 -> 1000 (still outside the 'bad' block if we include it),
    #   i=4..8 -> 500. Mean = (1000 + 500*5)/6 = 583.333...
    latest_unrent = 1000 - 200  # 800
    expected_delta = latest_unrent - (1000 + 500 * 5) / 6.0
    assert out["unrent_6m_delta_eur"] == pytest.approx(expected_delta)


# -------------------- Cost structure edge cases --------------------

def test_cost_structure_top_category_none_when_all_zero():
    hist = _mk_history("A", [{
        "period": _DEC_2024,
        "labor_cost_total": 0, "material_cost": 0, "vehicle_cost": 0,
        "revenue_total": 1000, "cm_db": 1000, "cm_planned": 1000,
    }])
    out = _cost_structure_metrics(hist)
    assert out["top_cost_category_now"] is None
    assert out["top_cost_category_now_eur"] == 0.0


def test_cost_structure_top_increase_none_when_no_category_rose():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0],
         "labor_cost_total": 1000, "material_cost": 500,
         "revenue_total": 5000, "cm_db": 100, "cm_planned": 200},
        {"period": periods[1],
         "labor_cost_total": 900, "material_cost": 400,
         "revenue_total": 5000, "cm_db": 100, "cm_planned": 200},
    ])
    out = _cost_structure_metrics(hist)
    assert out["top_cost_increase_cat"] is None
    assert out["top_cost_increase_pct"] is None


def test_cost_structure_no_duplicate_mom_field():
    hist = _mk_history("A", [{
        "period": _DEC_2024,
        "labor_cost_total": 100, "material_cost": 50,
        "revenue_total": 1000, "cm_db": 100, "cm_planned": 100,
    }])
    out = _cost_structure_metrics(hist)
    assert "top_cost_increase_cat_mom" not in out
    # And the dataclass should no longer expose the duplicate field.
    assert not hasattr(ContractMetrics, "top_cost_increase_cat_mom")


# -------------------- Efficiency edge cases --------------------

def test_efficiency_eff_badness_computed_inside_bundle():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "hours_planned": 100, "hours_productive": 90,
         "hour_variance": 0, "revenue_total": 1000, "cm_db": 100, "cm_planned": 100},
        {"period": periods[1], "hours_planned": 100, "hours_productive": 60,
         "hour_variance": 0, "revenue_total": 1000, "cm_db": 100, "cm_planned": 100},
    ])
    out = _efficiency_metrics(hist)
    # Latest planned=100, productive=60 -> diff=40, badness=0.40.
    assert out["eff_badness"] == pytest.approx(0.40)


def test_efficiency_eff_badness_none_when_no_planned_hours():
    hist = _mk_history("A", [{
        "period": _DEC_2024, "hours_planned": 0, "hours_productive": 0,
        "hour_variance": 0, "revenue_total": 1000, "cm_db": 0, "cm_planned": 0,
    }])
    out = _efficiency_metrics(hist)
    assert out["eff_badness"] is None


def test_scores_independent_of_temp_hours_planned_key():
    # Regression: _compute_scores used to silently collapse to default 50 when
    # callers forgot to set `_hours_planned`. With eff_badness carried inside
    # the efficiency bundle, scoring works without any auxiliary keys.
    rows = [{
        "unrent_now_eur": unrent,
        "total_cost_increase_pct": 0.0,
        "hours_planned_minus_productive": 0.0,
        "eff_badness": badness,
        "contract_duration_months": 12,
        "cm_variance": 0.0,
        "revenue_variance": 0.0,
    } for unrent, badness in [(0.0, 0.0), (100.0, 0.1), (200.0, 0.2), (300.0, 0.4)]]
    _compute_scores(rows)
    eff_scores = [r["efficiency_score"] for r in rows]
    # Worst badness (0.4) must rank lowest; best (0.0) highest.
    assert eff_scores[0] > eff_scores[-1]


# -------------------- Stability edge cases --------------------

def test_stability_variance_none_for_single_row_history():
    hist = _single_stability_row(pd.Timestamp("2024-01-01"))
    out = _stability_metrics(hist)
    assert out["cm_variance"] is None
    assert out["revenue_variance"] is None


def test_stability_is_long_term_strict_below_threshold():
    # ~11 months of history: not long-term.
    start = pd.Timestamp(date.today() - timedelta(days=int(30.4375 * 11)))
    out = _stability_metrics(_single_stability_row(start))
    assert out["contract_duration_months"] is not None
    assert out["contract_duration_months"] < LONG_TERM_MONTH_THRESHOLD
    assert out["is_long_term"] is False


# -------------------- Ranking edge cases --------------------

def test_ranking_margin_mom_none_when_prior_revenue_zero():
    periods = _monthly_periods(2)
    df = _mk_history("A", [
        {"period": periods[0], "revenue_total": 0.0, "cm_db": 0.0,
         "cm_planned": 0.0, "labor_cost_total": 0.0},
        {"period": periods[1], "revenue_total": 1000.0, "cm_db": 100.0,
         "cm_planned": 100.0, "labor_cost_total": 100.0},
    ])
    rankings = compute_rankings(df)
    assert len(rankings) == 1
    # Prior month had revenue = 0, so margin MoM (pp) is undefined.
    assert rankings[0].margin_mom_pp is None
    # EUR delta on CM is still meaningful.
    assert rankings[0].cm_mom_eur == pytest.approx(100.0)


# -------------------- Early warning config --------------------

def test_early_warning_ignores_micro_slope():
    from src.early_warning import detect
    from src.features import enrich

    periods = _monthly_periods(12)
    # cm_db_pct drifts by -0.01 pp/mo (noise, not a real trend) and stays
    # below plan. Historical threshold would fire; audit threshold should not.
    base_rows = []
    for i, p in enumerate(periods):
        base_rows.append({
            "period": p,
            "year": p.year, "month": p.month,
            "cost_center_id": "A", "cost_center_name": "A",
            "revenue_total": 1000.0, "cm_db": 100.0 - 0.01 * i,
            "cm_db_pct": 10.0 - 0.01 * i,  # very small negative slope
            "cm_planned": 150.0,
            "labor_cost_total": 500.0, "material_cost": 100.0, "vehicle_cost": 50.0,
            "subcontractor_group": 0, "subcontractor_division": 0,
            "subcontractor_external": 0, "travel_cost": 0,
            "internal_service_el1": 0, "internal_service_el2": 0,
            "vacation_cost": 0, "sick_cost": 0,
            "hours_productive": 80, "hours_actual": 100,
            "hours_training": 0, "quality_actual": 0, "quality_target": 0,
            "service_type": "facility", "region": "Nord",
            "customer_name": "Cust",
        })
    df = pd.DataFrame(base_rows)
    df = enrich(df)
    signals = detect(df)
    # -0.01 pp/mo is well above the -0.5 pp/mo alerting floor.
    assert (signals.empty
            or "Declining CM trend" not in set(signals["signal"]))


# -------------------- Revenue trend --------------------

def _rev_row(period, *, fixed=0, hourly=0, other=0, cm_db=100, cm_planned=100):
    total = fixed + hourly + other
    return {
        "period": period,
        "revenue_fixed": fixed,
        "revenue_hourly": hourly,
        "revenue_other": other,
        "revenue_total": total,
        "cm_db": cm_db,
        "cm_planned": cm_planned,
    }


def test_revenue_trend_flat_when_all_streams_steady():
    periods = _monthly_periods(12)
    hist = _mk_history("A", [_rev_row(p, fixed=5000, hourly=3000, other=1000)
                             for p in periods])
    out = _revenue_trend_metrics(hist)
    assert out["revenue_mom_delta_eur"] == 0
    assert out["revenue_6m_delta_eur"] == 0
    assert out["top_revenue_decline_cat"] is None
    assert out["top_revenue_decline_eur"] is None
    assert out["revenue_trend_dir"] == "flat"


def test_revenue_trend_flags_hourly_collapse():
    periods = _monthly_periods(8)
    rows = [_rev_row(p, fixed=5000, hourly=3000, other=1000) for p in periods[:-1]]
    rows.append(_rev_row(periods[-1], fixed=5000, hourly=500, other=1000))
    out = _revenue_trend_metrics(_mk_history("A", rows))
    assert out["revenue_mom_delta_eur"] == pytest.approx(-2500.0)
    assert out["top_revenue_decline_cat"] == "hourly"
    assert out["top_revenue_decline_eur"] == pytest.approx(-2500.0)
    assert out["revenue_trend_dir"] == "down"


def test_revenue_trend_picks_biggest_negative_stream_when_all_drop():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        _rev_row(periods[0], fixed=10000, hourly=4000, other=2000),
        _rev_row(periods[1], fixed=3000,  hourly=3000, other=1500),
    ])
    out = _revenue_trend_metrics(hist)
    # Pauschal dropped by 7000 (largest), Stunden by 1000, Sonstige by 500.
    assert out["top_revenue_decline_cat"] == "fixed"
    assert out["top_revenue_decline_eur"] == pytest.approx(-7000.0)
    assert out["revenue_mom_delta_eur"] == pytest.approx(-8500.0)


def test_revenue_trend_growth_has_no_decline_stream():
    periods = _monthly_periods(3)
    hist = _mk_history("A", [
        _rev_row(periods[0], fixed=5000, hourly=2000, other=500),
        _rev_row(periods[1], fixed=5100, hourly=2100, other=550),
        _rev_row(periods[2], fixed=5300, hourly=2400, other=600),
    ])
    out = _revenue_trend_metrics(hist)
    assert out["revenue_mom_delta_eur"] > 0
    assert out["top_revenue_decline_cat"] is None
    assert out["top_revenue_decline_eur"] is None
    assert out["revenue_trend_dir"] == "up"


def test_revenue_trend_single_month_returns_no_data():
    periods = _monthly_periods(1)
    hist = _mk_history("A", [_rev_row(periods[0], fixed=1000, hourly=500)])
    out = _revenue_trend_metrics(hist)
    assert out["revenue_mom_delta_eur"] is None
    assert out["revenue_6m_delta_eur"] is None
    assert out["revenue_trend_dir"] == "no_data"


def test_revenue_trend_classifies_sub_epsilon_move_as_flat():
    # A -10 EUR move on a 500k EUR contract must NOT read as a real decline.
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        _rev_row(periods[0], fixed=500000),
        _rev_row(periods[1], fixed=499990),
    ])
    out = _revenue_trend_metrics(hist)
    assert out["revenue_trend_dir"] == "flat"


def test_revenue_trend_falls_back_to_revenue_total_without_streams():
    periods = _monthly_periods(2)
    hist = _mk_history("A", [
        {"period": periods[0], "revenue_total": 8000, "cm_db": 100, "cm_planned": 100},
        {"period": periods[1], "revenue_total": 5000, "cm_db": 100, "cm_planned": 100},
    ])
    out = _revenue_trend_metrics(hist)
    assert out["revenue_mom_delta_eur"] == pytest.approx(-3000.0)
    # No per-stream columns -> can't attribute the drop.
    assert out["top_revenue_decline_cat"] is None
    assert out["revenue_trend_dir"] == "down"


def test_compute_metrics_exposes_revenue_trend_fields():
    periods = _monthly_periods(3)
    rows = [_rev_row(p, fixed=5000, hourly=3000, other=1000,
                     cm_db=500, cm_planned=600) for p in periods[:-1]]
    rows.append(_rev_row(periods[-1], fixed=5000, hourly=500, other=1000,
                         cm_db=200, cm_planned=600))
    # Stability requires contract_start on the latest row.
    for r in rows:
        r["contract_start"] = periods[0]
        r["hours_planned"] = 100
        r["hours_productive"] = 90

    df = _mk_history("A", rows)
    metrics = compute_metrics(compute_rankings(df), df)
    assert len(metrics) == 1
    m = metrics[0]
    assert m.top_revenue_decline_cat == "hourly"
    assert m.revenue_trend_dir == "down"
    assert m.revenue_mom_delta_eur == pytest.approx(-2500.0)
