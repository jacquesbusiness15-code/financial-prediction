"""Shared DataFrame filter logic — extracted from app.py:_sidebar_filters."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd


def parse_iso(s: str | None) -> pd.Timestamp | None:
    if s is None or s == "":
        return None
    try:
        return pd.Timestamp(datetime.fromisoformat(s))
    except ValueError:
        return None


def apply_filters(
    df: pd.DataFrame,
    regions: Iterable[str] | None = None,
    services: Iterable[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """Return a copy filtered by region/service/period inclusively."""
    mask = pd.Series(True, index=df.index)

    if regions:
        regions = list(regions)
        if "region" in df.columns and regions:
            mask &= df["region"].isin(regions)

    if services:
        services = list(services)
        if "service_type" in df.columns and services:
            mask &= df["service_type"].isin(services)

    start_ts = parse_iso(start)
    end_ts = parse_iso(end)
    if "period" in df.columns:
        if start_ts is not None:
            mask &= df["period"] >= start_ts
        if end_ts is not None:
            mask &= df["period"] <= end_ts

    return df[mask].copy()
