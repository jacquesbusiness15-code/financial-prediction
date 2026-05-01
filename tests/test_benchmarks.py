"""Tests for src.benchmarks cohort aggregation."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmarks import (  # noqa: E402
    METRICS,
    MIN_COHORT_SIZE,
    CohortStats,
    cohort_stats,
    deltas_vs_cohort,
)


def _make_df(n_region_a: int = 30, n_region_b: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(n_region_a):
        rows.append({
            "region": "North",
            "industry": "FM",
            "service_type": "Cleaning",
            "labor_ratio": rng.uniform(0.6, 0.9),
            "subcontractor_share": rng.uniform(0.05, 0.25),
            "cm_db_pct": rng.uniform(0.05, 0.20),
            "productivity_ratio": rng.uniform(0.80, 0.95),
            "absence_rate": rng.uniform(0.02, 0.08),
            "quality_gap": rng.uniform(-0.03, 0.03),
        })
    for _ in range(n_region_b):
        rows.append({
            "region": "South",
            "industry": "FM",
            "service_type": "Cleaning",
            "labor_ratio": rng.uniform(0.6, 0.9),
            "subcontractor_share": rng.uniform(0.05, 0.25),
            "cm_db_pct": rng.uniform(0.05, 0.20),
            "productivity_ratio": rng.uniform(0.80, 0.95),
            "absence_rate": rng.uniform(0.02, 0.08),
            "quality_gap": rng.uniform(-0.03, 0.03),
        })
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_global_zero_cohort() -> None:
    stats = cohort_stats(pd.DataFrame())
    assert stats.size == 0
    assert stats.scope == "global"
    assert stats.medians == {}
    assert stats.adequacy() == 0.0


def test_happy_path_tight_cohort() -> None:
    df = _make_df()
    stats = cohort_stats(df, region="North", industry="FM", service_type="Cleaning")
    assert stats.scope == "region+industry+service"
    assert stats.size >= MIN_COHORT_SIZE
    for metric in METRICS:
        assert metric in stats.medians
        assert stats.p25[metric] <= stats.medians[metric] <= stats.p75[metric]


def test_fallback_when_cohort_too_thin() -> None:
    df = _make_df()
    stats = cohort_stats(df, region="South", industry="FM", service_type="Cleaning")
    # South has only 3 rows -> must fall back to a broader scope
    assert stats.scope != "region+industry+service"
    assert stats.size >= MIN_COHORT_SIZE


def test_fallback_to_global_when_filters_empty() -> None:
    df = _make_df()
    stats = cohort_stats(df, region="Mars", industry="None", service_type="None")
    assert stats.scope == "global"
    assert stats.size == len(df)


def test_adequacy_monotonic_with_size() -> None:
    small = CohortStats(size=5, scope="global")
    big = CohortStats(size=100, scope="global")
    assert small.adequacy() < big.adequacy()
    assert big.adequacy() == 1.0


def test_deltas_vs_cohort() -> None:
    df = _make_df()
    stats = cohort_stats(df, region="North", industry="FM", service_type="Cleaning")
    row = pd.Series({
        "labor_ratio": stats.medians["labor_ratio"] + 0.1,
        "subcontractor_share": stats.medians["subcontractor_share"] - 0.05,
        "productivity_ratio": np.nan,
    })
    deltas = deltas_vs_cohort(row, stats)
    assert pytest.approx(deltas["labor_ratio"], rel=1e-9) == 0.1
    assert pytest.approx(deltas["subcontractor_share"], rel=1e-9) == -0.05
    assert "productivity_ratio" not in deltas  # NaN values are dropped


def test_ignores_unknown_filters_gracefully() -> None:
    df = _make_df()
    stats = cohort_stats(df, region=None, industry=None, service_type=None)
    assert stats.size == len(df)
    assert stats.scope == "region+industry+service"  # all-None treated as no-filter
