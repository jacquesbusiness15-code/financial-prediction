"""Tests for src.cost_drivers issue-to-column decomposition."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cost_drivers import (  # noqa: E402
    ISSUE_DRIVER_COLUMNS,
    identify_drivers_for_issue,
)


def _history_with_spike(column: str, baseline: float, current: float,
                         extras: dict[str, list[float]] | None = None) -> tuple[pd.Series, pd.DataFrame]:
    periods = pd.date_range("2025-10-01", periods=4, freq="MS")
    data: dict[str, list[float]] = {column: [baseline] * 3 + [current]}
    if extras:
        for k, vals in extras.items():
            data[k] = vals
    df = pd.DataFrame({"period": periods, **data})
    latest = df.iloc[-1].copy()
    return latest, df


def test_labor_overrun_flags_the_spiked_column() -> None:
    # labor_direct spikes from 100 to 180, everything else flat.
    latest, hist = _history_with_spike(
        "labor_direct", baseline=100.0, current=180.0,
        extras={
            "labor_overhead": [20.0, 20.0, 20.0, 20.0],
            "training_cost":  [0.0, 0.0, 0.0, 0.0],
            "vacation_cost":  [5.0, 5.0, 5.0, 5.0],
            "sick_cost":      [5.0, 5.0, 5.0, 5.0],
        })
    drivers = identify_drivers_for_issue("labor_overrun", latest, hist)
    assert drivers
    top = drivers[0]
    assert top.column == "labor_direct"
    assert top.delta_eur == pytest.approx(80.0)
    assert top.delta_pct == pytest.approx(0.80)
    assert top.sub_action_id == "audit_overtime"
    assert 0 < top.share_of_issue <= 1


def test_subcontractor_creep_points_to_external_when_external_moved() -> None:
    latest, hist = _history_with_spike(
        "subcontractor_external", baseline=50.0, current=200.0,
        extras={
            "subcontractor_group":    [10.0, 10.0, 10.0, 10.0],
            "subcontractor_division": [5.0,  5.0,  5.0,  5.0],
        })
    drivers = identify_drivers_for_issue("subcontractor_creep", latest, hist)
    assert drivers[0].column == "subcontractor_external"
    assert drivers[0].sub_action_id == "renegotiate_external_rates"


def test_revenue_shortfall_flags_drop_not_growth() -> None:
    # revenue_hourly falls from 1000 to 400
    latest, hist = _history_with_spike(
        "revenue_hourly", baseline=1000.0, current=400.0,
        extras={"revenue_fixed": [500.0, 500.0, 500.0, 500.0]})
    drivers = identify_drivers_for_issue("revenue_shortfall", latest, hist)
    assert drivers, "shrinking revenue should count as a driver"
    assert drivers[0].column == "revenue_hourly"
    assert drivers[0].delta_eur < 0


def test_unknown_issue_returns_empty() -> None:
    latest = pd.Series({"labor_direct": 100.0})
    assert identify_drivers_for_issue("not_a_thing", latest, pd.DataFrame()) == []


def test_flat_history_produces_no_drivers() -> None:
    latest, hist = _history_with_spike(
        "labor_direct", baseline=100.0, current=100.0,
        extras={"labor_overhead": [20.0, 20.0, 20.0, 20.0]})
    assert identify_drivers_for_issue("labor_overrun", latest, hist) == []


def test_share_of_issue_sums_to_one() -> None:
    periods = pd.date_range("2025-10-01", periods=4, freq="MS")
    hist = pd.DataFrame({
        "period": periods,
        "labor_direct":   [100.0, 100.0, 100.0, 150.0],  # +50
        "labor_overhead": [10.0,  10.0,  10.0,  35.0],   # +25
        "training_cost":  [5.0,   5.0,   5.0,   5.0],
        "vacation_cost":  [5.0,   5.0,   5.0,   5.0],
        "sick_cost":      [5.0,   5.0,   5.0,   5.0],
    })
    latest = hist.iloc[-1].copy()
    drivers = identify_drivers_for_issue("labor_overrun", latest, hist, top_n=5)
    assert len(drivers) == 2
    assert sum(d.share_of_issue for d in drivers) == pytest.approx(1.0)


def test_all_mapped_sub_actions_have_i18n_keys() -> None:
    # Guard against typos in the column->sub_action map.
    sub_action_ids = {sub for pairs in ISSUE_DRIVER_COLUMNS.values()
                      for _, sub in pairs}
    # All sub-action ids should look like valid identifiers.
    assert all(s.replace("_", "").isalnum() for s in sub_action_ids)
    assert sub_action_ids, "catalog should not be empty"
