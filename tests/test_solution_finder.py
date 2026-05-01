"""Tests for src.solution_finder diagnostics and recommendations."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmarks import CohortStats  # noqa: E402
from src.contract_metrics import ContractMetrics  # noqa: E402
from src.portfolio_ranking import ContractRanking  # noqa: E402
from src.solution_catalog import ACTIONS, ALL_ISSUE_CODES  # noqa: E402
from src.solution_finder import (  # noqa: E402
    MIN_ISSUE_SEVERITY,
    ActionRecommendation,
    Issue,
    diagnose,
    recommend,
)
from src.solution_impact import FORMULAS  # noqa: E402


def _cohort(**medians: float) -> CohortStats:
    return CohortStats(size=40, scope="global", medians=dict(medians),
                       p25={k: v * 0.9 for k, v in medians.items()},
                       p75={k: v * 1.1 for k, v in medians.items()})


def _ranking() -> ContractRanking:
    return ContractRanking(
        cost_center_id="CC-1", cost_center_name="Site 1", customer_name="Alpha",
        region="North", industry="FM", entity="Mandant1",
        latest_period=pd.Timestamp("2026-03-01"), current_cm_eur=-2_000.0,
        current_revenue_eur=40_000.0,
        current_margin_pct=-0.05, margin_mom_pp=-0.02, cm_trend_pp=-0.01,
        unprofitability_eur=2_000.0,
        first_unprofitable_period=pd.Timestamp("2025-11-01"),
        months_unprofitable=5, top_reason_class="labor",
        top_reason_title_key=None, status=None,
        sparkline_periods=[], sparkline_margins=[], sparkline_cm_eur=[],
        sparkline_cm_mom_pct=[], sparkline_mom_periods=[],
        cm_mom_eur=None, cm_mom_pct=None,
    )


def _metrics(**overrides) -> ContractMetrics:
    base = dict(
        base=_ranking(),
        unrent_now_eur=5_000.0, unrent_mom_delta_eur=0.0, unrent_6m_delta_eur=0.0,
        profitability_trend_dir="up", cm_mom_pct=-0.1,
        top_cost_category_now="labor", top_cost_category_now_eur=10_000.0,
        top_cost_increase_cat=None, top_cost_increase_pct=None,
        total_cost_increase_pct=None,
        hours_planned_minus_productive=200.0, ratio_mom_delta_pp=-2.0,
        ratio_6m_delta_pp=-3.0, hour_variance=None,
        contract_duration_months=24, cm_variance=None, is_long_term=True,
        revenue_variance=None,
        profitability_score=20.0, cost_structure_score=30.0,
        efficiency_score=25.0, stability_score=40.0, overall_score=28.75,
    )
    base.update(overrides)
    return ContractMetrics(**base)


def _bad_row(**overrides) -> pd.Series:
    base = {
        "cost_center_id": "CC-1",
        "period": pd.Timestamp("2026-03-01"),
        "revenue_total": 50_000.0,
        "revenue_hourly": 10_000.0,
        "cm_db": -2_000.0,
        "cm_planned": 5_000.0,
        "labor_cost_total": 30_000.0,
        "labor_ratio": 0.90,
        "plan_labor_cost_ratio": 0.75,
        "subcontractor_share": 0.40,
        "plan_subcontractor_ratio": 0.20,
        "subcontractor_total": 15_000.0,
        "subcontractor_group": 10_000.0,
        "subcontractor_division": 3_000.0,
        "subcontractor_external": 2_000.0,
        "productivity_ratio": 0.70,
        "hours_planned": 1_000.0,
        "hours_productive": 700.0,
        "labor_cost_per_productive_hour": 50.0,
        "absence_rate": 0.10,
        "quality_gap": -0.05,
        "contract_end": pd.NaT,
    }
    base.update(overrides)
    return pd.Series(base)


def _bad_history(n: int = 6) -> pd.DataFrame:
    periods = pd.date_range("2025-10-01", periods=n, freq="MS")
    return pd.DataFrame({
        "period": periods,
        "cost_center_id": ["CC-1"] * n,
        "cm_db": [-1_000.0 - 200 * i for i in range(n)],
        "cm_db_pct": [-0.02 - 0.005 * i for i in range(n)],
        "revenue_total": [50_000.0] * n,
        "labor_cost_total": [30_000.0] * n,
        "absence_rate": [0.05, 0.05, 0.05, 0.06, 0.08, 0.10][:n],
        "productivity_ratio": [0.85, 0.82, 0.80, 0.75, 0.72, 0.70][:n],
        "cm_vs_plan_delta": [-1_000 - 500 * i for i in range(n)],
    })


def test_every_impact_formula_exists_in_registry() -> None:
    for action in ACTIONS.values():
        assert action.impact_formula_id in FORMULAS, action.id


def test_every_issue_code_in_catalog_is_used() -> None:
    # Sanity: catalog and engine speak the same vocabulary.
    engine_codes = {
        "labor_overrun", "subcontractor_creep", "productivity_drop",
        "absence_spike", "quality_gap", "plan_gap_widening",
        "revenue_shortfall", "sustained_loss", "renewal_risk",
    }
    assert ALL_ISSUE_CODES.issubset(engine_codes)


def test_diagnose_on_clean_contract_returns_empty() -> None:
    row = _bad_row(labor_ratio=0.70, plan_labor_cost_ratio=0.75,
                   subcontractor_share=0.10, plan_subcontractor_ratio=0.20,
                   productivity_ratio=0.95, absence_rate=0.03,
                   quality_gap=0.01, cm_db=6_000.0)
    history = pd.DataFrame({
        "period": pd.date_range("2025-10-01", periods=3, freq="MS"),
        "cm_db": [5_000.0, 5_500.0, 6_000.0],
    })
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.05, labor_ratio=0.75)
    issues = diagnose(_metrics(), row, history, pd.DataFrame(), cohort)
    assert issues == []


def test_diagnose_surfaces_expected_codes() -> None:
    row = _bad_row()
    history = _bad_history()
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.04, labor_ratio=0.78)
    issues = diagnose(_metrics(), row, history, pd.DataFrame(), cohort)
    codes = {i.code for i in issues}
    expected = {"labor_overrun", "subcontractor_creep", "productivity_drop",
                "absence_spike", "quality_gap", "plan_gap_widening",
                "revenue_shortfall", "sustained_loss"}
    assert expected.issubset(codes)


def test_diagnose_orders_by_severity_descending() -> None:
    row = _bad_row()
    history = _bad_history()
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.04, labor_ratio=0.78)
    issues = diagnose(_metrics(), row, history, pd.DataFrame(), cohort)
    severities = [i.severity for i in issues]
    assert severities == sorted(severities, reverse=True)
    assert all(i.severity <= 1.0 for i in issues)


def test_recommend_respects_explicit_impact_floor() -> None:
    row = _bad_row()
    history = _bad_history()
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.04, labor_ratio=0.78)
    recs = recommend(_metrics(), row, history, pd.DataFrame(), cohort,
                     min_impact_eur=5_000.0)
    for r in recs:
        assert r.estimated_impact_eur_month >= 5_000.0 or r.category == "retention"


def test_recommend_severity_floor_drops_low_signal_issues() -> None:
    row = _bad_row(labor_ratio=0.76, plan_labor_cost_ratio=0.75,  # only 1pp over
                   subcontractor_share=0.21, plan_subcontractor_ratio=0.20,  # 1pp over
                   productivity_ratio=0.85, absence_rate=0.04,
                   quality_gap=0.01, cm_db=100.0, cm_planned=100.0)
    history = pd.DataFrame({
        "period": pd.date_range("2026-01-01", periods=3, freq="MS"),
        "cm_db": [100.0, 150.0, 100.0],
    })
    cohort = _cohort(productivity_ratio=0.86, absence_rate=0.04, labor_ratio=0.75)
    recs = recommend(_metrics(), row, history, pd.DataFrame(), cohort)
    # No issue passes the 0.2 severity floor -> no recommendations.
    assert recs == []


def test_recommend_returns_ranked_top_n() -> None:
    row = _bad_row()
    history = _bad_history()
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.04, labor_ratio=0.78)
    recs = recommend(_metrics(), row, history, pd.DataFrame(), cohort, top_n=3)
    assert 1 <= len(recs) <= 3
    quick = [r.quick_win_score for r in recs]
    assert quick == sorted(quick, reverse=True)
    for r in recs:
        assert 0 <= r.confidence <= 1.0
        assert r.owner_role
        assert r.estimated_impact_eur_month >= 0


def test_recommend_respects_mutual_exclusion() -> None:
    row = _bad_row()
    history = _bad_history()
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.04, labor_ratio=0.78)
    recs = recommend(_metrics(), row, history, pd.DataFrame(), cohort, top_n=5)
    ids = {r.action_id for r in recs}
    # reduce_scope and terminate_contract are mutually exclusive -> at most one
    assert not ({"reduce_scope", "terminate_contract"} <= ids)


def test_warnings_boost_severity() -> None:
    row = _bad_row()
    history = _bad_history()
    cohort = _cohort(productivity_ratio=0.90, absence_rate=0.04, labor_ratio=0.78)
    warnings = pd.DataFrame([{
        "cost_center_id": "CC-1",
        "signal": "Absence spike",
        "severity": "high",
        "detail": "absence 10% vs avg 4%",
        "impact_eur": 5_000.0,
    }])
    issues_no_warn = diagnose(_metrics(), row, history, pd.DataFrame(), cohort)
    issues_with_warn = diagnose(_metrics(), row, history, warnings, cohort)
    sev_no = next(i.severity for i in issues_no_warn if i.code == "absence_spike")
    sev_yes = next(i.severity for i in issues_with_warn if i.code == "absence_spike")
    assert sev_yes > sev_no


def test_recommend_empty_when_cohort_empty_and_no_plans() -> None:
    row = _bad_row(plan_labor_cost_ratio=0.0, plan_subcontractor_ratio=0.0,
                   cm_planned=0.0, cm_db=1_000.0, quality_gap=0.02)
    history = pd.DataFrame({
        "period": pd.date_range("2026-01-01", periods=3, freq="MS"),
        "cm_db": [500.0, 700.0, 1_000.0],
    })
    recs = recommend(_metrics(), row, history, pd.DataFrame(),
                     CohortStats(size=0, scope="global"))
    assert recs == []
