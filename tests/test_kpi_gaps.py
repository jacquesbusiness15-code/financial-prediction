from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import drivers  # noqa: E402
from src.kpi_gaps import detect_gaps  # noqa: E402


def _row(**values) -> pd.Series:
    return pd.Series(values)


def test_labor_driver_surfaces_overtime_and_headcount_gaps() -> None:
    current = _row(
        labor_direct=220_000.0, labor_overhead=30_000.0,
        revenue_total=500_000.0, cm_db=10_000.0,
    )
    baseline = _row(
        labor_direct=150_000.0, labor_overhead=30_000.0,
        revenue_total=500_000.0, cm_db=80_000.0,
    )
    ds = drivers.decompose(current, baseline)
    observed = drivers.observed_delta(current, baseline)
    residual = drivers.residual(ds, observed)

    ids = [g.id for g in detect_gaps(current, ds, observed, residual, limit=6)]
    assert "overtime_hours" in ids
    assert "headcount_fte" in ids


def test_subcontractor_driver_surfaces_sub_gaps() -> None:
    current = _row(
        subcontractor_external=120_000.0, revenue_total=500_000.0, cm_db=5_000.0,
    )
    baseline = _row(
        subcontractor_external=40_000.0, revenue_total=500_000.0, cm_db=85_000.0,
    )
    ds = drivers.decompose(current, baseline)
    observed = drivers.observed_delta(current, baseline)
    residual = drivers.residual(ds, observed)

    ids = [g.id for g in detect_gaps(current, ds, observed, residual, limit=6)]
    assert "subcontractor_hours" in ids
    assert "subcontractor_reason" in ids


def test_plan_gap_fires_when_cm_planned_missing() -> None:
    current = _row(labor_direct=100.0, revenue_total=1000.0, cm_db=900.0)
    baseline = _row(labor_direct=90.0, revenue_total=1000.0, cm_db=910.0)
    ds = drivers.decompose(current, baseline)
    observed = drivers.observed_delta(current, baseline)
    residual = drivers.residual(ds, observed)

    ids = [g.id for g in detect_gaps(current, ds, observed, residual, limit=6)]
    assert "plan_values" in ids


def test_plan_gap_suppressed_when_cm_planned_present() -> None:
    current = _row(labor_direct=100.0, revenue_total=1000.0, cm_db=900.0,
                   cm_planned=950.0)
    baseline = _row(labor_direct=90.0, revenue_total=1000.0, cm_db=910.0,
                    cm_planned=950.0)
    ds = drivers.decompose(current, baseline)
    observed = drivers.observed_delta(current, baseline)
    residual = drivers.residual(ds, observed)

    ids = [g.id for g in detect_gaps(current, ds, observed, residual, limit=6)]
    assert "plan_values" not in ids


def test_large_residual_flags_missing_driver_gap() -> None:
    current = _row(labor_direct=100.0, revenue_total=1000.0, cm_db=500.0,
                   cm_planned=900.0, quality_actual=0.95)
    baseline = _row(labor_direct=90.0, revenue_total=1000.0, cm_db=910.0,
                    cm_planned=900.0, quality_actual=0.95)
    ds = drivers.decompose(current, baseline)
    observed = drivers.observed_delta(current, baseline)
    residual = drivers.residual(ds, observed)

    ids = [g.id for g in detect_gaps(current, ds, observed, residual, limit=6)]
    assert "missing_driver" in ids


def test_limit_is_respected() -> None:
    current = _row(
        labor_direct=220_000.0, subcontractor_external=120_000.0,
        vacation_cost=50_000.0, revenue_total=500_000.0, cm_db=10_000.0,
    )
    baseline = _row(
        labor_direct=150_000.0, subcontractor_external=40_000.0,
        vacation_cost=10_000.0, revenue_total=500_000.0, cm_db=300_000.0,
    )
    ds = drivers.decompose(current, baseline)
    observed = drivers.observed_delta(current, baseline)
    residual = drivers.residual(ds, observed)

    gaps = detect_gaps(current, ds, observed, residual, limit=3)
    assert len(gaps) <= 3
