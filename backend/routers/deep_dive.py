"""GET /datasets/{id}/deep-dive/{cost_center_id} — full cost-center breakdown."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.deps import get_dataset
from backend.schemas import (
    DeepDiveResponse,
    DriverOut,
    HistoryStats,
    PeerKpi,
    TimelinePoint,
    WaterfallRow,
)
from backend.services.dataset_store import DatasetEntry
from src.benchmarks import history_for, history_stats, kpi_vs_peers
from src.drivers import (
    build_plan_baseline,
    decompose,
    observed_delta,
    pick_baseline,
    residual,
    to_waterfall_df,
)

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


def _safe_str(v) -> Optional[str]:
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


def _baseline_label(mode: str) -> str:
    return {"mom": "Vormonat", "yoy": "Vorjahr", "plan": "Plan"}.get(mode, mode)


@router.get("/datasets/{dataset_id}/deep-dive/{cost_center_id}",
            response_model=DeepDiveResponse)
def get_deep_dive(
    cost_center_id: str,
    entry: DatasetEntry = Depends(get_dataset),
    mode: str = Query(default="mom", pattern="^(mom|yoy|plan)$"),
    period: str | None = Query(
        default=None,
        description="ISO date yyyy-mm-01. Defaults to the latest period for this cost center.",
    ),
) -> DeepDiveResponse:
    df = entry.df
    cc_rows = df[df["cost_center_id"].astype(str) == str(cost_center_id)].sort_values("period")
    if cc_rows.empty:
        raise HTTPException(status_code=404,
                            detail=f"No rows for cost_center_id={cost_center_id}")

    if period:
        try:
            current_period = pd.Timestamp(period)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Bad period: {e}") from e
        current_rows = cc_rows[cc_rows["period"] == current_period]
        if current_rows.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No row at period={period} for cost_center_id={cost_center_id}",
            )
        current = current_rows.iloc[0]
    else:
        current = cc_rows.iloc[-1]
        current_period = current["period"]

    if mode == "plan":
        if "cm_planned" not in df.columns or pd.isna(current.get("cm_planned")):
            raise HTTPException(
                status_code=404,
                detail="No plan value available for this row.",
            )
        baseline = build_plan_baseline(current)
    else:
        baseline = pick_baseline(cc_rows, current_period, mode=mode)
        if baseline is None:
            raise HTTPException(
                status_code=404,
                detail=f"No baseline available for mode={mode}.",
            )

    drivers = decompose(current, baseline)
    obs = observed_delta(current, baseline)
    modeled = sum(d.delta_eur for d in drivers)
    res = residual(drivers, obs)
    wf = to_waterfall_df(drivers, obs, top_k=8)

    history = history_for(df, cost_center_id, window_months=24)
    timeline = [
        TimelinePoint(
            period=p.strftime("%Y-%m-%d") if hasattr(p, "strftime") else str(p),
            cm_db=_safe_float(row.get("cm_db")),
            cm_planned=_safe_float(row.get("cm_planned")),
        )
        for p, row in zip(history["period"], history.to_dict("records"))
    ]

    peers_df = kpi_vs_peers(df, current)
    peers = [PeerKpi(**p) for p in peers_df.to_dict("records")] if not peers_df.empty else []

    stats = history_stats(df, cost_center_id)

    return DeepDiveResponse(
        cost_center_id=str(cost_center_id),
        cost_center_name=_safe_str(current.get("cost_center_name")),
        region=_safe_str(current.get("region")),
        service_type=_safe_str(current.get("service_type")),
        period=current_period.strftime("%Y-%m-%d"),
        baseline_label=_baseline_label(mode),
        observed_delta=_safe_float(obs) or 0.0,
        modeled_delta=_safe_float(modeled) or 0.0,
        residual=_safe_float(res) or 0.0,
        residual_pct=_safe_float(res / obs) if obs else None,
        drivers=[DriverOut(**d.as_dict()) for d in drivers],
        waterfall=[WaterfallRow(**r) for r in wf.to_dict("records")],
        timeline=timeline,
        kpis_vs_peers=peers,
        history_stats=HistoryStats(**{k: _safe_float(v) for k, v in stats.items()}),
        labor_ratio=_safe_float(current.get("labor_ratio")),
        cm_current=_safe_float(current.get("cm_db")) or 0.0,
        cm_baseline=_safe_float(baseline.get("cm_db")) or 0.0,
        cm_current_pct=_safe_float(current.get("cm_db_pct")),
        hour_variance=_safe_float(current.get("hour_variance")),
        dq_accrual_flag=bool(current.get("dq_accrual_flag", False)),
        manager_comment=_safe_str(current.get("manager_comment")),
    )
