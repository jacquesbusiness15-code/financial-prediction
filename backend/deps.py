"""FastAPI dependency: resolve dataset_id → DataFrame + schema report."""
from __future__ import annotations

from fastapi import HTTPException, Path

from backend.services.dataset_store import DatasetEntry, get_store


def get_dataset(dataset_id: str = Path(..., min_length=4)) -> DatasetEntry:
    entry = get_store().get(dataset_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown dataset_id={dataset_id!r}. "
                "POST /api/datasets to (re)load a source and receive a fresh id."
            ),
        )
    return entry
