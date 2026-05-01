"""Tests for src.solution_impact euro-impact formulas."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmarks import CohortStats  # noqa: E402
from src.solution_catalog import ACTIONS  # noqa: E402
from src.solution_impact import (  # noqa: E402
    ASSUMPTION_ABSENCE_RECOVERY,
    ASSUMPTION_LABOR_SAVINGS,
    ASSUMPTION_PRICE_PASSTHROUGH,
    ASSUMPTION_PRODUCTIVITY_GAIN,
    ASSUMPTION_QUALITY_PENALTY,
    ASSUMPTION_RENEG_RECOVERY,
    ASSUMPTION_SUBC_RECOVERY,
    FORMULAS,
    IMPACT_REVENUE_CAP_SHARE,
    simulate,
)


def _cohort(**medians: float) -> CohortStats:
    return CohortStats(size=40, scope="global", medians=dict(medians),
                       p25={k: v * 0.9 for k, v in medians.items()},
                       p75={k: v * 1.1 for k, v in medians.items()})


def test_catalog_formulas_resolve() -> None:
    for action in ACTIONS.values():
        assert action.impact_formula_id in FORMULAS, action.id


def test_reduce_subcontractor_share_happy_path() -> None:
    row = pd.Series({
        "subcontractor_share": 0.40,
        "plan_subcontractor_ratio": 0.25,
        "subcontractor_total": 10_000.0,
        "revenue_total": 100_000.0,
    })
    expected = (0.40 - 0.25) * ASSUMPTION_SUBC_RECOVERY * 10_000.0  # 750
    got = simulate("reduce_subcontractor_share", row, _cohort())
    assert got == pytest.approx(expected)


def test_reduce_subcontractor_share_zero_when_at_plan() -> None:
    row = pd.Series({
        "subcontractor_share": 0.20,
        "plan_subcontractor_ratio": 0.25,
        "subcontractor_total": 10_000.0,
        "revenue_total": 100_000.0,
    })
    assert simulate("reduce_subcontractor_share", row, _cohort()) == 0.0


def test_labor_cost_audit() -> None:
    row = pd.Series({
        "labor_ratio": 0.90,
        "plan_labor_cost_ratio": 0.75,
        "revenue_total": 50_000.0,
    })
    expected = (0.90 - 0.75) * 50_000.0 * ASSUMPTION_LABOR_SAVINGS  # 1125
    got = simulate("labor_cost_audit", row, _cohort())
    assert got == pytest.approx(expected)


def test_productivity_improvement() -> None:
    row = pd.Series({
        "hours_planned": 1_000.0,
        "hours_productive": 800.0,
        "labor_cost_per_productive_hour": 50.0,
        "revenue_total": 200_000.0,
    })
    expected = 200.0 * 50.0 * ASSUMPTION_PRODUCTIVITY_GAIN  # 1000
    got = simulate("productivity_improvement", row, _cohort())
    assert got == pytest.approx(expected)


def test_reprice_hourly_uses_peer_gap() -> None:
    row = pd.Series({
        "revenue_hourly": 10_000.0,
        "labor_ratio": 0.95,
        "revenue_total": 50_000.0,
    })
    cohort = _cohort(labor_ratio=0.80)
    expected = 10_000.0 * (0.95 - 0.80) * ASSUMPTION_PRICE_PASSTHROUGH  # 750
    got = simulate("reprice_hourly", row, cohort)
    assert got == pytest.approx(expected)


def test_reprice_hourly_zero_when_cohort_missing() -> None:
    row = pd.Series({"revenue_hourly": 10_000.0, "labor_ratio": 0.95,
                     "revenue_total": 50_000.0})
    assert simulate("reprice_hourly", row, _cohort()) == 0.0


def test_absence_intervention() -> None:
    row = pd.Series({
        "absence_rate": 0.10,
        "labor_cost_total": 20_000.0,
        "revenue_total": 50_000.0,
    })
    cohort = _cohort(absence_rate=0.04)
    expected = (0.10 - 0.04) * 20_000.0 * ASSUMPTION_ABSENCE_RECOVERY  # 480
    got = simulate("absence_intervention", row, cohort)
    assert got == pytest.approx(expected)


def test_quality_remediation() -> None:
    row = pd.Series({
        "quality_gap": -0.05,
        "revenue_total": 100_000.0,
    })
    expected = 0.05 * 100_000.0 * ASSUMPTION_QUALITY_PENALTY  # 150
    got = simulate("quality_remediation", row, _cohort())
    assert got == pytest.approx(expected)


def test_renegotiate_price() -> None:
    row = pd.Series({
        "cm_planned": 5_000.0,
        "cm_db": -1_000.0,
        "revenue_total": 50_000.0,
    })
    expected = (5_000.0 - (-1_000.0)) * ASSUMPTION_RENEG_RECOVERY  # 3600
    got = simulate("renegotiate_price", row, _cohort())
    assert got == pytest.approx(expected)


def test_stop_bleed_only_when_cm_negative() -> None:
    neg = pd.Series({"cm_db": -2_000.0, "revenue_total": 50_000.0})
    pos = pd.Series({"cm_db": 3_000.0, "revenue_total": 50_000.0})
    assert simulate("stop_bleed", neg, _cohort()) == pytest.approx(2_000.0)
    assert simulate("stop_bleed", pos, _cohort()) == 0.0


def test_renewal_outreach_returns_revenue() -> None:
    row = pd.Series({"revenue_total": 25_000.0})
    assert simulate("renewal_outreach", row, _cohort()) == pytest.approx(25_000.0)


def test_training_investment() -> None:
    row = pd.Series({
        "productivity_ratio": 0.70,
        "hours_productive": 500.0,
        "labor_cost_per_productive_hour": 40.0,
        "revenue_total": 200_000.0,
    })
    cohort = _cohort(productivity_ratio=0.90)
    expected = (0.90 - 0.70) * 500.0 * 40.0  # 4000
    got = simulate("training_investment", row, cohort)
    assert got == pytest.approx(expected)


def test_impact_is_clamped_to_revenue_cap() -> None:
    row = pd.Series({
        "subcontractor_share": 0.80,
        "plan_subcontractor_ratio": 0.0,
        "subcontractor_total": 1_000_000.0,
        "revenue_total": 10_000.0,
    })
    got = simulate("reduce_subcontractor_share", row, _cohort())
    assert got == pytest.approx(10_000.0 * IMPACT_REVENUE_CAP_SHARE)


def test_impact_never_negative() -> None:
    row = pd.Series({
        "labor_ratio": 0.5,
        "plan_labor_cost_ratio": 0.8,
        "revenue_total": 10_000.0,
    })
    assert simulate("labor_cost_audit", row, _cohort()) == 0.0


def test_simulate_unknown_formula_raises() -> None:
    with pytest.raises(KeyError):
        simulate("does_not_exist", pd.Series({"revenue_total": 1.0}), _cohort())
