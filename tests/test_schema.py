"""Schema contract tests for the WISAG dataset.

These guard the two invariants the loader promises:

1. Every semantic name in HEADER_MAP has a dtype declaration in SCHEMA, and
   the two stay in sync.
2. Loading `data/Dataset_anoym.xlsx` produces a SchemaReport with `ok=True`
   and the expected critical columns, derived columns, and dtypes.

If any of these fail, the cached parquet at `data/.cache/` is invalid too -
clear it with `src.data_cache.clear_cache()` before re-running.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    CRITICAL_SEMANTIC_COLS,
    HEADER_MAP,
    SCHEMA,
    SCHEMA_VERSION,
)
from src.data_cache import load_or_build_cache, clear_cache  # noqa: E402
from src.data_loader import load  # noqa: E402
from src.features import enrich  # noqa: E402

DATASET = ROOT / "data" / "Dataset_anoym.xlsx"

EXPECTED_DERIVED_COLS = frozenset({
    # from add_kpis
    "productivity_ratio", "absence_rate", "training_intensity",
    "cost_total_db2", "subcontractor_total", "subcontractor_share",
    "labor_cost_per_productive_hour", "labor_ratio", "quality_gap",
    "cm_vs_plan_delta", "cm_vs_plan_pct",
    # from add_time_deltas (6 base cols x 3 suffixes = 18 derived)
    "cm_db_mom", "cm_db_yoy", "cm_db_mom_pct",
    "cm_db_pct_mom", "cm_db_pct_yoy", "cm_db_pct_mom_pct",
    "cm_db1_mom", "cm_db1_yoy", "cm_db1_mom_pct",
    "cm_db2_mom", "cm_db2_yoy", "cm_db2_mom_pct",
    "revenue_total_mom", "revenue_total_yoy", "revenue_total_mom_pct",
    "labor_cost_total_mom", "labor_cost_total_yoy", "labor_cost_total_mom_pct",
    # rolling stats
    "cm_db_pct_roll6_mean", "cm_db_pct_roll6_std",
    # from data_quality.annotate
    "dq_accrual_flag",
    # built in the loader
    "period",
})


def _skip_if_no_dataset() -> None:
    if not DATASET.exists():
        pytest.skip(f"Dataset not present at {DATASET}")


def test_schema_version_is_string() -> None:
    assert isinstance(SCHEMA_VERSION, str) and SCHEMA_VERSION


def test_header_map_covers_schema() -> None:
    """Every SCHEMA key must be a semantic value in HEADER_MAP and vice versa."""
    header_values = set(HEADER_MAP.values())
    schema_keys = set(SCHEMA.keys())
    assert header_values == schema_keys, {
        "in_header_not_schema": sorted(header_values - schema_keys),
        "in_schema_not_header": sorted(schema_keys - header_values),
    }


def test_critical_columns_are_in_schema() -> None:
    for c in CRITICAL_SEMANTIC_COLS:
        assert c in SCHEMA, f"critical column {c!r} missing from SCHEMA"


def test_load_produces_ok_report() -> None:
    _skip_if_no_dataset()
    _, report = load(str(DATASET))
    assert report.strategy == "header"
    assert report.missing_critical == []
    assert report.critical_dtype_mismatches == []
    assert report.ok is True


def test_loader_applies_schema_dtypes() -> None:
    _skip_if_no_dataset()
    df, _ = load(str(DATASET))
    # Spot-check one column per dtype family.
    assert df["year"].dtype.name == "Int64"
    assert df["revenue_total"].dtype.name == "float64"
    assert str(df["cost_center_id"].dtype) == "category"
    assert str(df["cost_center_name"].dtype) == "string"
    assert df["contract_start"].dtype.name == "datetime64[ns]"


def test_enrich_produces_expected_derived_columns() -> None:
    _skip_if_no_dataset()
    df, _ = load(str(DATASET))
    out = enrich(df)
    missing = EXPECTED_DERIVED_COLS - set(out.columns)
    assert not missing, f"enrich missed: {sorted(missing)}"


def test_parquet_roundtrip_is_stable() -> None:
    """Second call must come from cache and produce identical rows/columns."""
    _skip_if_no_dataset()
    clear_cache()  # start from a known cold state
    df_cold, report_cold = load_or_build_cache(str(DATASET))
    df_warm, report_warm = load_or_build_cache(str(DATASET))

    assert len(df_cold) == len(df_warm)
    assert list(df_cold.columns) == list(df_warm.columns)
    assert report_cold.ok is True
    assert report_warm.ok is True
    assert report_cold.strategy == report_warm.strategy

    # Values must match, but parquet may round-trip categoricals as strings.
    pd.testing.assert_frame_equal(
        df_cold.reset_index(drop=True),
        df_warm.reset_index(drop=True),
        check_dtype=False,
        check_categorical=False,
    )


def test_cache_key_changes_with_schema_version(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_if_no_dataset()
    from src import data_cache

    original = data_cache.SCHEMA_VERSION
    monkeypatch.setattr(data_cache, "SCHEMA_VERSION", original + "-test")

    key_a = data_cache._cache_key(DATASET)
    monkeypatch.setattr(data_cache, "SCHEMA_VERSION", original + "-other")
    key_b = data_cache._cache_key(DATASET)

    assert key_a != key_b
    assert key_a.endswith("-test")
    assert key_b.endswith("-other")
