"""Facility overview + what-if simulator endpoints.

GET  /datasets/{id}/facility-overview?cc=...      — single-facility dashboard payload
POST /datasets/{id}/simulate-team-size             — thin wrapper over src.sim
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.deps import get_dataset
from backend.schemas import (
    ActionItemOut,
    DriverItemOut,
    FacilityOverviewResponse,
    SimulateTeamSizeRequest,
    SimulateTeamSizeResponse,
    SparklinePointOut,
)
from backend.services.dataset_store import DatasetEntry
from src import facility_overview as fov
from src import sim

router = APIRouter()


def _safe_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


@router.get("/datasets/{dataset_id}/facility-overview",
            response_model=FacilityOverviewResponse)
def get_facility_overview(
    entry: DatasetEntry = Depends(get_dataset),
    cc: str | None = Query(default=None, description="Cost center id override."),
    period: str | None = Query(default=None, description="ISO yyyy-mm-01."),
) -> FacilityOverviewResponse:
    period_ts: pd.Timestamp | None = None
    if period:
        try:
            period_ts = pd.Timestamp(period)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Bad period: {e}") from e

    payload = fov.build(entry.df, cost_center_id=cc, period=period_ts)
    if payload is None:
        raise HTTPException(status_code=404,
                            detail="No cost center available for the current dataset.")

    return FacilityOverviewResponse(
        cost_center_id=payload.cost_center_id,
        cost_center_name=payload.cost_center_name,
        region=payload.region,
        service_type=payload.service_type,
        period=payload.period,
        icon=payload.icon,
        status=payload.status,
        margin_pct=_safe_float(payload.margin_pct),
        margin_mom_delta=_safe_float(payload.margin_mom_delta),
        sparkline=[SparklinePointOut(**asdict(p)) for p in payload.sparkline],
        worst_drivers=[DriverItemOut(**asdict(d)) for d in payload.worst_drivers],
        recommended_actions=[ActionItemOut(**asdict(a)) for a in payload.recommended_actions],
        baseline_headcount=payload.baseline_headcount,
        team_size_suggestion=payload.team_size_suggestion,
    )


@router.post("/datasets/{dataset_id}/simulate-team-size",
             response_model=SimulateTeamSizeResponse)
def simulate_team_size(
    body: SimulateTeamSizeRequest,
    entry: DatasetEntry = Depends(get_dataset),
) -> SimulateTeamSizeResponse:
    df = entry.df
    cc_rows = df[df["cost_center_id"].astype(str) == str(body.cost_center_id)].sort_values("period")
    if cc_rows.empty:
        raise HTTPException(status_code=404,
                            detail=f"Unknown cost_center_id={body.cost_center_id}")

    if body.period:
        try:
            period_ts = pd.Timestamp(body.period)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Bad period: {e}") from e
        match = cc_rows[cc_rows["period"] == period_ts]
        row = match.iloc[0] if not match.empty else cc_rows.iloc[-1]
    else:
        row = cc_rows.iloc[-1]

    result = sim.simulate_team_size(
        row,
        new_headcount=float(body.new_headcount),
        baseline_headcount=body.baseline_headcount,
    )
    return SimulateTeamSizeResponse(
        baseline_headcount=result.baseline_headcount,
        new_headcount=result.new_headcount,
        baseline_margin=result.baseline_margin,
        new_margin=result.new_margin,
        delta_margin=result.delta_margin,
        productivity_gain_pct=result.productivity_gain_pct,
        new_cm_eur=result.new_cm_eur,
    )
