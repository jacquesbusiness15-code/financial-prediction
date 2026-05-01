"""Feature-engineering edge cases for src.features.

Covers per-cost-center rolling windows, zero-denominator guards, and missing-
column fallbacks - the parts most likely to silently produce wrong numbers.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features import _safe_div, add_kpis, add_time_deltas  # noqa: E402


def _monthly_frame(cc_ids: list[str], n: int) -> pd.DataFrame:
    end = pd.Timestamp("2024-12-01")
    periods = [end - pd.DateOffset(months=(n - 1 - i)) for i in range(n)]
    rows = []
    for cc in cc_ids:
        for i, p in enumerate(periods):
            rows.append({
                "cost_center_id": cc,
                "period": p,
                "cm_db": 100.0 + i,
                "cm_db_pct": 10.0 + i,
                "revenue_total": 1000.0,
                "labor_cost_total": 500.0,
                "hours_actual": 100.0,
                "hours_productive": 80.0,
                "hours_training": 5.0,
                "labor_direct": 400.0,
                "vacation_cost": 20.0,
                "sick_cost": 10.0,
                "subcontractor_group": 0.0,
                "subcontractor_division": 0.0,
                "subcontractor_external": 0.0,
                "material_cost": 100.0,
                "vehicle_cost": 50.0,
                "travel_cost": 10.0,
                "quality_actual": 90.0,
                "quality_target": 95.0,
                "cm_planned": 120.0,
            })
    return pd.DataFrame(rows)


def test_safe_div_replaces_zero_denominator_with_nan():
    out = _safe_div(pd.Series([1.0, 2.0]), pd.Series([2.0, 0.0]))
    assert out.iloc[0] == pytest.approx(0.5)
    assert np.isnan(out.iloc[1])


def test_add_kpis_tolerates_missing_optional_columns():
    df = pd.DataFrame({"revenue_total": [1000.0], "labor_cost_total": [500.0]})
    out = add_kpis(df)
    # `_col` returns NaN-filled series when the column is missing; the KPIs
    # still exist on the frame rather than raising KeyError.
    assert "productivity_ratio" in out.columns
    assert "subcontractor_share" in out.columns
    # Denominator is 0 + 0 + 0 + 0 + 500 = 500; numerator subc is 0 -> share 0.
    assert out["subcontractor_share"].iloc[0] == 0.0
    # productivity_ratio uses hours columns which are absent -> NaN.
    assert np.isnan(out["productivity_ratio"].iloc[0])


def test_add_time_deltas_does_not_bleed_across_cost_centers():
    # Two contracts with disjoint histories should produce independent rolling
    # windows. A bug in `reset_index(level=0, drop=True)` would cross-contaminate.
    df = _monthly_frame(["A", "B"], n=6)
    out = add_time_deltas(df)
    # Each cost centre has 6 rows; the earliest row per centre must have NO
    # prior month, so MoM is NaN.
    per_cc_first = (out.sort_values("period")
                       .groupby("cost_center_id", observed=True).head(1))
    assert per_cc_first["cm_db_mom"].isna().all()
    # Rolling mean needs at least 3 points -> first two rows per centre NaN.
    first_two = (out.sort_values("period")
                    .groupby("cost_center_id", observed=True).head(2))
    assert first_two["cm_db_pct_roll6_mean"].isna().sum() >= 2


def test_add_time_deltas_yoy_is_nan_when_history_too_short():
    df = _monthly_frame(["A"], n=6)
    out = add_time_deltas(df)
    assert "cm_db_yoy" in out.columns
    assert out["cm_db_yoy"].isna().all()


def test_add_time_deltas_preserves_row_count():
    df = _monthly_frame(["A", "B", "C"], n=8)
    out = add_time_deltas(df)
    assert len(out) == len(df)
    # And row order is deterministic (sorted by cc, period).
    assert list(out["cost_center_id"]) == sorted(df["cost_center_id"].tolist())
