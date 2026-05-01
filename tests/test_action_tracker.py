"""Tests for src.action_tracker SQLite persistence."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.action_tracker import (  # noqa: E402
    list_for_contract,
    log_action,
    measure_outcome,
    update_status,
)


@pytest.fixture()
def db(tmp_path) -> Path:
    return tmp_path / "action_log.sqlite"


def test_log_and_list(db: Path) -> None:
    eid = log_action("CC-1", "labor_cost_audit", owner="ops",
                     estimated_impact=1_500.0, notes="initial",
                     baseline_cm_db=-500.0,
                     baseline_period=pd.Timestamp("2026-03-01"), db_path=db)
    assert isinstance(eid, int) and eid > 0
    df = list_for_contract("CC-1", db_path=db)
    assert len(df) == 1
    assert df.iloc[0]["action_id"] == "labor_cost_audit"
    assert df.iloc[0]["status"] == "proposed"
    assert df.iloc[0]["estimated_impact"] == pytest.approx(1_500.0)


def test_status_transitions(db: Path) -> None:
    eid = log_action("CC-1", "reduce_subcontractor_share", db_path=db)
    update_status(eid, "in_progress", db_path=db)
    update_status(eid, "done", notes="completed", db_path=db)
    df = list_for_contract("CC-1", db_path=db)
    assert df.iloc[0]["status"] == "done"
    assert df.iloc[0]["notes"] == "completed"


def test_invalid_status_rejected(db: Path) -> None:
    eid = log_action("CC-1", "labor_cost_audit", db_path=db)
    with pytest.raises(ValueError):
        update_status(eid, "not-a-status", db_path=db)  # type: ignore[arg-type]


def test_list_isolates_by_contract(db: Path) -> None:
    log_action("CC-1", "a", db_path=db)
    log_action("CC-2", "b", db_path=db)
    assert len(list_for_contract("CC-1", db_path=db)) == 1
    assert len(list_for_contract("CC-2", db_path=db)) == 1
    assert len(list_for_contract("CC-3", db_path=db)) == 0


def test_measure_outcome_writes_delta(db: Path) -> None:
    baseline_period = pd.Timestamp("2026-03-01")
    eid = log_action("CC-1", "labor_cost_audit", baseline_cm_db=-2_000.0,
                     baseline_period=baseline_period, db_path=db)
    df = pd.DataFrame({
        "cost_center_id": ["CC-1"] * 5,
        "period": pd.date_range("2026-03-01", periods=5, freq="MS"),
        "cm_db": [-2_000.0, -1_000.0, 0.0, 500.0, 1_000.0],
    })
    delta = measure_outcome(eid, df, db_path=db)
    assert delta is not None
    assert delta == pytest.approx(((-1_000.0 + 0.0 + 500.0) / 3) - (-2_000.0))
    row = list_for_contract("CC-1", db_path=db).iloc[0]
    assert row["realized_cm_delta"] == pytest.approx(delta)
    assert row["measured_at"] is not None


def test_measure_outcome_returns_none_without_enough_data(db: Path) -> None:
    eid = log_action("CC-1", "labor_cost_audit", baseline_cm_db=0.0,
                     baseline_period=pd.Timestamp("2026-03-01"), db_path=db)
    # only one month of post data but window wants >=1 (3//2 == 1), so this
    # is still enough; verify the too-short case with zero rows post-cutoff
    df = pd.DataFrame({
        "cost_center_id": ["CC-1"],
        "period": [pd.Timestamp("2026-03-01")],
        "cm_db": [0.0],
    })
    assert measure_outcome(eid, df, db_path=db) is None


def test_measure_outcome_unknown_entry(db: Path) -> None:
    assert measure_outcome(9999, pd.DataFrame(), db_path=db) is None
