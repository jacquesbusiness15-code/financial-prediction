"""Persistent parquet cache for the fully-enriched WISAG dataset.

The raw `.xlsx` parse is the slowest step in the data pipeline (~2 s for the
anonymised 2 MB dataset). Every page rerun currently replays that work from
cache memory, but cold starts (first load of a new Streamlit session) have to
reparse Excel plus re-run every feature-engineering step.

This module caches the full post-`enrich` frame to a parquet file keyed by
`(sha1(source_bytes)[:12], SCHEMA_VERSION)`. The schema version is part of the
key so changing the contract in `src.config` automatically invalidates every
old cache. URL loads (Google Sheets) are not cached - there's no stable hash
for them - they fall through to the live `load + enrich` path.

Cache location: `data/.cache/{key}.parquet` plus a sidecar
`{key}.report.json` that stores the SchemaReport for the build.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.config import SCHEMA_VERSION
from src.data_loader import SchemaReport, load, _is_url
from src.features import enrich

CACHE_DIR = Path("data") / ".cache"


def _source_digest(path: Path) -> str:
    h = hashlib.sha1(path.read_bytes()).hexdigest()
    return h[:12]


def _cache_key(path: Path) -> str:
    return f"{_source_digest(path)}-{SCHEMA_VERSION}"


def _paths_for(key: str) -> tuple[Path, Path]:
    return CACHE_DIR / f"{key}.parquet", CACHE_DIR / f"{key}.report.json"


def _report_to_dict(report: SchemaReport) -> dict:
    return {
        "matched": report.matched,
        "unmapped_input": report.unmapped_input,
        "missing_expected": report.missing_expected,
        "strategy": report.strategy,
        "dtype_mismatches": [list(m) for m in report.dtype_mismatches],
    }


def _report_from_dict(d: dict) -> SchemaReport:
    return SchemaReport(
        matched=list(d.get("matched", [])),
        unmapped_input=list(d.get("unmapped_input", [])),
        missing_expected=list(d.get("missing_expected", [])),
        strategy=str(d.get("strategy", "header")),
        dtype_mismatches=[tuple(m) for m in d.get("dtype_mismatches", [])],
    )


def load_or_build_cache(path: str | Path,
                        sheet: str | int = 0
                        ) -> tuple[pd.DataFrame, SchemaReport]:
    """Return the enriched dataframe + SchemaReport for `path`.

    Caches to `data/.cache/` on first build. URLs bypass the cache. Any
    parquet-read failure falls through to a fresh build (and overwrites the
    stale cache).
    """
    src = str(path)
    if _is_url(src):
        df, report = load(src, sheet=sheet)
        return enrich(df), report

    p = Path(src)
    if not p.exists():
        # Re-raise via load() so the user sees the canonical message.
        df, report = load(src, sheet=sheet)
        return enrich(df), report

    key = _cache_key(p)
    parquet_path, report_path = _paths_for(key)

    if parquet_path.exists() and report_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            report = _report_from_dict(json.loads(report_path.read_text("utf-8")))
            return df, report
        except Exception:  # noqa: BLE001
            # Corrupt cache - fall through to rebuild.
            parquet_path.unlink(missing_ok=True)
            report_path.unlink(missing_ok=True)

    df, report = load(src, sheet=sheet)
    df = enrich(df)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(parquet_path, engine="pyarrow", index=False)
        report_path.write_text(json.dumps(_report_to_dict(report)), encoding="utf-8")
    except Exception:  # noqa: BLE001
        # If parquet engine is missing, silently skip caching. The app still
        # works - just without the cold-start speedup.
        parquet_path.unlink(missing_ok=True)
        report_path.unlink(missing_ok=True)
    return df, report


def clear_cache() -> int:
    """Delete every cached build. Returns the number of files removed."""
    if not CACHE_DIR.exists():
        return 0
    removed = 0
    for f in CACHE_DIR.iterdir():
        if f.is_file():
            f.unlink()
            removed += 1
    return removed
