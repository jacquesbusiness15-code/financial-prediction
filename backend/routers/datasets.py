"""POST /datasets — load from URL/path; GET /datasets/{id}/summary."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_dataset
from backend.schemas import (
    DatasetFacets,
    DatasetSummary,
    LoadDatasetRequest,
    LoadDatasetResponse,
    SchemaReportOut,
)
from backend.services.dataset_store import DatasetEntry, get_store

router = APIRouter()


def _iso(ts) -> str | None:
    if ts is None:
        return None
    try:
        return ts.date().isoformat() if hasattr(ts, "date") else str(ts)
    except Exception:  # noqa: BLE001
        return None


def _facets(df) -> DatasetFacets:
    regions = sorted([r for r in df.get("region", []).dropna().unique()]) \
        if "region" in df.columns else []
    services = sorted([s for s in df.get("service_type", []).dropna().unique()]) \
        if "service_type" in df.columns else []
    period_min = df["period"].min() if "period" in df.columns else None
    period_max = df["period"].max() if "period" in df.columns else None
    return DatasetFacets(
        regions=regions,
        services=services,
        period_min=_iso(period_min),
        period_max=_iso(period_max),
    )


def _entry_to_response(entry: DatasetEntry) -> LoadDatasetResponse:
    r = entry.schema_report
    stats = entry.summary.copy()
    stats["period_min"] = _iso(stats.get("period_min"))
    stats["period_max"] = _iso(stats.get("period_max"))
    return LoadDatasetResponse(
        dataset_id=entry.dataset_id,
        summary=DatasetSummary(**{k: stats.get(k) for k in DatasetSummary.model_fields}),
        schema_report=SchemaReportOut(
            matched=r.matched,
            unmapped_input=r.unmapped_input,
            missing_expected=r.missing_expected,
            missing_critical=r.missing_critical,
            strategy=r.strategy,
            expected_total=r.expected_total,
            ok=r.ok,
        ),
        facets=_facets(entry.df),
    )


@router.post("/datasets", response_model=LoadDatasetResponse)
def post_dataset(req: LoadDatasetRequest) -> LoadDatasetResponse:
    try:
        entry = get_store().load_from_source(req.source)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Load failed: {e}") from e
    return _entry_to_response(entry)


@router.get("/datasets/{dataset_id}/summary", response_model=LoadDatasetResponse)
def get_summary(entry: DatasetEntry = Depends(get_dataset)) -> LoadDatasetResponse:
    return _entry_to_response(entry)
