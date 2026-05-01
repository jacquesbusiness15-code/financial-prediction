"""Peer cohort benchmarks for contract diagnostics.

Aggregates per-cohort median / p25 / p75 for the operational KPIs that the
Solution Finder relies on. Falls back through three scopes when the cohort
is too thin so downstream consumers always receive a populated CohortStats
object together with the scope and size they were computed from.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

try:  # keep import-safe outside Streamlit runtime (tests, CLI)
    import streamlit as st
    _cache = st.cache_data
except Exception:  # pragma: no cover - Streamlit is optional at import time
    def _cache(*_args, **_kwargs):
        def _decorator(fn):
            return fn
        return _decorator


METRICS: tuple[str, ...] = (
    "labor_ratio",
    "subcontractor_share",
    "cm_db_pct",
    "productivity_ratio",
    "absence_rate",
    "quality_gap",
)

MIN_COHORT_SIZE = 5


@dataclass(frozen=True)
class CohortStats:
    size: int
    scope: str
    medians: dict[str, float] = field(default_factory=dict)
    p25: dict[str, float] = field(default_factory=dict)
    p75: dict[str, float] = field(default_factory=dict)

    def adequacy(self) -> float:
        """Cohort adequacy factor in [0, 1] used by confidence scoring."""
        return float(min(1.0, self.size / 20.0))


def _aggregate(frame: pd.DataFrame) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    medians: dict[str, float] = {}
    p25: dict[str, float] = {}
    p75: dict[str, float] = {}
    for metric in METRICS:
        if metric not in frame.columns:
            continue
        series = pd.to_numeric(frame[metric], errors="coerce").dropna()
        if series.empty:
            continue
        medians[metric] = float(series.median())
        p25[metric] = float(series.quantile(0.25))
        p75[metric] = float(series.quantile(0.75))
    return medians, p25, p75


def _filter(df: pd.DataFrame, **filters: Optional[str]) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for key, value in filters.items():
        if value is None or key not in df.columns:
            continue
        mask &= df[key].astype("string") == str(value)
    return df.loc[mask]


@_cache(show_spinner=False)
def cohort_stats(
    df: pd.DataFrame,
    region: Optional[str] = None,
    industry: Optional[str] = None,
    service_type: Optional[str] = None,
) -> CohortStats:
    """Return cohort median/p25/p75 for the operational KPIs.

    Falls back from region+industry+service to industry+service to global
    whenever the current cohort has fewer than ``MIN_COHORT_SIZE`` rows with
    at least one of the target metrics populated.
    """
    if df is None or df.empty:
        return CohortStats(size=0, scope="global")

    scope_chain: tuple[tuple[str, dict[str, Optional[str]]], ...] = (
        ("region+industry+service",
         {"region": region, "industry": industry, "service_type": service_type}),
        ("industry+service",
         {"industry": industry, "service_type": service_type}),
        ("industry",
         {"industry": industry}),
        ("global", {}),
    )

    for scope, filters in scope_chain:
        frame = _filter(df, **filters)
        if frame.empty:
            continue
        medians, p25, p75 = _aggregate(frame)
        if not medians:
            continue
        if len(frame) < MIN_COHORT_SIZE and scope != "global":
            continue
        return CohortStats(size=int(len(frame)), scope=scope,
                           medians=medians, p25=p25, p75=p75)

    # final attempt: global aggregation even if the chain above skipped it
    medians, p25, p75 = _aggregate(df)
    return CohortStats(size=int(len(df)), scope="global",
                       medians=medians, p25=p25, p75=p75)


def deltas_vs_cohort(row: pd.Series, cohort: CohortStats) -> dict[str, float]:
    """Per-metric signed delta of the row vs cohort median."""
    out: dict[str, float] = {}
    for metric in METRICS:
        if metric not in cohort.medians:
            continue
        value = row.get(metric, np.nan)
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if np.isnan(value):
            continue
        out[metric] = value - cohort.medians[metric]
    return out
