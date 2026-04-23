"""In-process LRU cache for loaded DataFrames.

Replaces Streamlit's `@st.cache_data`. A dataset is identified by the SHA-1
of its source string (path or URL) so re-loading the same source reuses the
cached DataFrame without going back to the network or Excel engine.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.data_loader import SchemaReport, load, summary
from src.features import enrich


MAX_ENTRIES = 8
TTL_SECONDS = 30 * 60


@dataclass
class DatasetEntry:
    dataset_id: str
    source: str
    df: pd.DataFrame
    schema_report: SchemaReport
    summary: dict
    loaded_at: float


class DatasetStore:
    """Thread-safe LRU cache keyed by dataset_id (hash of source)."""

    def __init__(self, max_entries: int = MAX_ENTRIES, ttl_seconds: int = TTL_SECONDS):
        self._entries: "OrderedDict[str, DatasetEntry]" = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_entries
        self._ttl = ttl_seconds

    @staticmethod
    def _id_for(source: str) -> str:
        return hashlib.sha1(source.encode("utf-8")).hexdigest()[:16]

    def _evict_stale(self) -> None:
        now = time.time()
        expired = [k for k, v in self._entries.items()
                   if now - v.loaded_at > self._ttl]
        for k in expired:
            self._entries.pop(k, None)

    def get(self, dataset_id: str) -> Optional[DatasetEntry]:
        with self._lock:
            self._evict_stale()
            entry = self._entries.get(dataset_id)
            if entry is not None:
                self._entries.move_to_end(dataset_id)  # LRU bump
            return entry

    def load_from_source(self, source: str) -> DatasetEntry:
        dataset_id = self._id_for(source)
        with self._lock:
            self._evict_stale()
            cached = self._entries.get(dataset_id)
            if cached is not None:
                self._entries.move_to_end(dataset_id)
                return cached

        # Heavy work outside the lock.
        raw_df, report = load(source)
        enriched = enrich(raw_df)
        stats = summary(enriched)

        entry = DatasetEntry(
            dataset_id=dataset_id,
            source=source,
            df=enriched,
            schema_report=report,
            summary=stats,
            loaded_at=time.time(),
        )

        with self._lock:
            self._entries[dataset_id] = entry
            self._entries.move_to_end(dataset_id)
            while len(self._entries) > self._max:
                self._entries.popitem(last=False)
        return entry


# Module-level singleton
_store = DatasetStore()


def get_store() -> DatasetStore:
    return _store
