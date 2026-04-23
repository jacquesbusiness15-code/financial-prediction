"""GET /datasets/{id}/plan-vs-actual — monthly CM Plan vs. Actual."""
from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query

from backend.deps import get_dataset
from backend.schemas import PlanVsActualMonth, PlanVsActualResponse
from backend.services.dataset_store import DatasetEntry
from backend.services.filters import apply_filters

router = APIRouter()


def _safe_float(v) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
        return 0.0 if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return 0.0


@router.get("/datasets/{dataset_id}/plan-vs-actual", response_model=PlanVsActualResponse)
def get_plan_vs_actual(
    entry: DatasetEntry = Depends(get_dataset),
    regions: list[str] | None = Query(default=None),
    services: list[str] | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> PlanVsActualResponse:
    df = apply_filters(entry.df, regions, services, start, end)
    if df.empty or "period" not in df.columns \
            or "cm_db" not in df.columns or "cm_planned" not in df.columns:
        return PlanVsActualResponse(months=[], total_actual=0.0,
                                    total_planned=0.0, total_gap=0.0,
                                    worst_month=None)

    agg = (df.groupby("period")
             .agg(revenue=("revenue_total", "sum"),
                  planned=("cm_planned", "sum"),
                  actual=("cm_db", "sum"))
             .reset_index()
             .sort_values("period"))
    agg["gap_eur"] = agg["actual"] - agg["planned"]
    agg["gap_pct"] = np.where(
        agg["planned"] != 0,
        agg["gap_eur"] / agg["planned"].replace(0, np.nan),
        np.nan,
    )

    months: list[PlanVsActualMonth] = []
    for _, r in agg.iterrows():
        p = r["period"]
        gap_pct = r.get("gap_pct")
        months.append(PlanVsActualMonth(
            period=p.strftime("%Y-%m") if hasattr(p, "strftime") else str(p),
            revenue=_safe_float(r.get("revenue")),
            planned=_safe_float(r.get("planned")),
            actual=_safe_float(r.get("actual")),
            gap_eur=_safe_float(r.get("gap_eur")),
            gap_pct=None if pd.isna(gap_pct) else _safe_float(gap_pct),
        ))

    worst = None
    if not agg.empty:
        worst_row = agg.loc[agg["gap_eur"].idxmin()]
        worst = worst_row["period"].strftime("%Y-%m") \
            if hasattr(worst_row["period"], "strftime") else str(worst_row["period"])

    return PlanVsActualResponse(
        months=months,
        total_actual=_safe_float(agg["actual"].sum()),
        total_planned=_safe_float(agg["planned"].sum()),
        total_gap=_safe_float(agg["gap_eur"].sum()),
        worst_month=worst,
    )
