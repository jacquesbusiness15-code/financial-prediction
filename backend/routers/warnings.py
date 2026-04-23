"""GET /datasets/{id}/early-warnings — rule-based risk signals."""
from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query

from backend.deps import get_dataset
from backend.schemas import WarningRow, WarningsResponse
from backend.services.dataset_store import DatasetEntry
from backend.services.filters import apply_filters
from src.early_warning import detect

router = APIRouter()


def _safe_float(v) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
        return 0.0 if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return 0.0


def _safe_str(v):
    if v is None:
        return None
    try:
        if isinstance(v, float) and np.isnan(v):
            return None
    except TypeError:
        pass
    if pd.isna(v):
        return None
    s = str(v)
    return s if s else None


@router.get("/datasets/{dataset_id}/early-warnings", response_model=WarningsResponse)
def get_warnings(
    entry: DatasetEntry = Depends(get_dataset),
    regions: list[str] | None = Query(default=None),
    services: list[str] | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> WarningsResponse:
    df = apply_filters(entry.df, regions, services, start, end)
    flagged = detect(df)

    rows: list[WarningRow] = []
    counts = {"high": 0, "medium": 0, "low": 0}
    total_impact = 0.0

    if not flagged.empty:
        for _, r in flagged.iterrows():
            period = r.get("period")
            impact = _safe_float(r.get("impact_eur"))
            total_impact += impact
            sev = str(r.get("severity", "low"))
            counts[sev] = counts.get(sev, 0) + 1
            rows.append(WarningRow(
                cost_center_id=str(r.get("cost_center_id", "")),
                cost_center_name=_safe_str(r.get("cost_center_name")),
                region=_safe_str(r.get("region")),
                customer_name=_safe_str(r.get("customer_name")),
                service_type=_safe_str(r.get("service_type")),
                period=period.strftime("%Y-%m") if hasattr(period, "strftime") else str(period),
                signal=str(r.get("signal", "")),
                severity=sev,
                detail=str(r.get("detail", "")),
                impact_eur=impact,
            ))

    return WarningsResponse(
        warnings=rows,
        counts=counts,
        total_impact_eur=total_impact,
    )
