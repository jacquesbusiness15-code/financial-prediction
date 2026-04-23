"""GET /datasets/{id}/portfolio — KPIs, heatmap, top cost centers, top anomalies."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query

from backend.deps import get_dataset
from backend.schemas import (
    AnomalyRow,
    HeatmapPayload,
    KpiBlock,
    PortfolioResponse,
    TopCostCenter,
)
from backend.services.dataset_store import DatasetEntry
from backend.services.filters import apply_filters
from src.anomaly import detect, top_n

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
    """Return str(v) unless v is None / NaN / empty."""
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


def _build_heatmap(df: pd.DataFrame, top_n: int = 20) -> HeatmapPayload:
    if df.empty or "cm_db_pct" not in df.columns:
        return HeatmapPayload(row_dim="region", rows=[], columns=[], z=[])

    row_dim = "region" if df.get("region", pd.Series()).nunique() > 1 else "cost_center"

    if row_dim == "region" and "region" in df.columns:
        pivot = (df.groupby(["region", "period"])["cm_db_pct"]
                   .mean()
                   .reset_index()
                   .pivot(index="region", columns="period", values="cm_db_pct"))
    else:
        if "cost_center_id" not in df.columns:
            return HeatmapPayload(row_dim="region", rows=[], columns=[], z=[])
        rev_rank = (df.groupby("cost_center_id")["revenue_total"]
                      .sum().nlargest(top_n).index)
        sub = df[df["cost_center_id"].isin(rev_rank)].copy()
        sub["cc_label"] = sub["cost_center_id"].astype(str)
        if "cost_center_name" in sub.columns:
            sub["cc_label"] = (sub["cost_center_id"].astype(str) + " · "
                               + sub["cost_center_name"].fillna("").astype(str).str.slice(0, 25))
        pivot = (sub.groupby(["cc_label", "period"])["cm_db_pct"]
                    .mean()
                    .reset_index()
                    .pivot(index="cc_label", columns="period", values="cm_db_pct"))
        row_dim = "cost_center"

    pivot = pivot.sort_index()
    columns = [p.strftime("%Y-%m") for p in pivot.columns]
    rows = [str(r) for r in pivot.index.tolist()]
    z = [[_safe_float(v) for v in row] for row in pivot.values]
    return HeatmapPayload(row_dim=row_dim, rows=rows, columns=columns, z=z)


def _top_cost_centers(df: pd.DataFrame, n: int = 8) -> list[TopCostCenter]:
    if "cost_center_id" not in df.columns or df.empty:
        return []
    grouped = (df.groupby("cost_center_id")
                 .agg(cost_center_name=("cost_center_name", "first")
                      if "cost_center_name" in df.columns else ("cost_center_id", "first"),
                      region=("region", "first") if "region" in df.columns else ("cost_center_id", "first"),
                      revenue_total=("revenue_total", "sum"),
                      cm_db=("cm_db", "sum")))
    grouped["cm_db_pct"] = grouped["cm_db"] / grouped["revenue_total"].replace(0, np.nan)
    grouped = grouped.sort_values("revenue_total", ascending=False).head(n)

    out: list[TopCostCenter] = []
    for cc_id, row in grouped.iterrows():
        out.append(TopCostCenter(
            cost_center_id=str(cc_id),
            cost_center_name=_safe_str(row.get("cost_center_name")),
            region=_safe_str(row.get("region")),
            revenue_total=_safe_float(row.get("revenue_total")) or 0.0,
            cm_db=_safe_float(row.get("cm_db")) or 0.0,
            cm_db_pct=_safe_float(row.get("cm_db_pct")),
        ))
    return out


def _anomaly_rows(df: pd.DataFrame, n: int = 8) -> list[AnomalyRow]:
    top = top_n(df, n=n)
    if top.empty:
        return []
    out: list[AnomalyRow] = []
    for _, r in top.iterrows():
        period = r.get("period")
        out.append(AnomalyRow(
            period=period.strftime("%Y-%m") if hasattr(period, "strftime") else str(period),
            region=_safe_str(r.get("region")),
            cost_center_id=str(r.get("cost_center_id", "")),
            cost_center_name=_safe_str(r.get("cost_center_name")),
            customer_name=_safe_str(r.get("customer_name")),
            service_type=_safe_str(r.get("service_type")),
            cm_db=_safe_float(r.get("cm_db")),
            cm_db_pct=_safe_float(r.get("cm_db_pct")),
            labor_ratio=_safe_float(r.get("labor_ratio")),
            cm_db_mom=_safe_float(r.get("cm_db_mom")),
            cm_db_yoy=_safe_float(r.get("cm_db_yoy")),
            cm_vs_plan_delta=_safe_float(r.get("cm_vs_plan_delta")),
            impact_eur=_safe_float(r.get("impact_eur")) or 0.0,
            severity=str(r.get("severity", "low")),
            anomaly_reasons=str(r.get("anomaly_reasons", "")),
        ))
    return out


@router.get("/datasets/{dataset_id}/portfolio", response_model=PortfolioResponse)
def get_portfolio(
    entry: DatasetEntry = Depends(get_dataset),
    regions: list[str] | None = Query(default=None),
    services: list[str] | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> PortfolioResponse:
    df = apply_filters(entry.df, regions, services, start, end)

    flagged = detect(df)
    kpis = KpiBlock(
        revenue=_safe_float(df.get("revenue_total", pd.Series(0)).sum()) or 0.0,
        cm_db=_safe_float(df.get("cm_db", pd.Series(0)).sum()) or 0.0,
        cm_planned=_safe_float(df.get("cm_planned", pd.Series(0)).sum()) or 0.0,
        plan_gap=_safe_float(
            df.get("cm_db", pd.Series(0)).sum()
            - df.get("cm_planned", pd.Series(0)).sum()
        ) or 0.0,
        cost_centers=int(df["cost_center_id"].nunique()) if "cost_center_id" in df.columns else 0,
        anomalies_count=int(len(flagged)),
    )

    return PortfolioResponse(
        kpis=kpis,
        heatmap=_build_heatmap(df),
        top_cost_centers=_top_cost_centers(df, n=8),
        top_anomalies=_anomaly_rows(df, n=8),
    )
