"""Parquet cache for the enriched WISAG dataset.

Keyed by (sha1(source_bytes)[:12], SCHEMA_VERSION) so contract bumps
invalidate every existing cache. URL loads skip the cache (no stable hash).
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

_REPORT_FIELDS = ("matched", "unmapped_input", "missing_expected",
                  "strategy", "dtype_mismatches")


def _cache_key(path: Path) -> str:
    return f"{hashlib.sha1(path.read_bytes()).hexdigest()[:12]}-{SCHEMA_VERSION}"


def _paths_for(key: str) -> tuple[Path, Path]:
    return CACHE_DIR / f"{key}.parquet", CACHE_DIR / f"{key}.report.json"


def _report_to_dict(report: SchemaReport) -> dict:
    d = {f: getattr(report, f) for f in _REPORT_FIELDS}
    d["dtype_mismatches"] = [list(m) for m in report.dtype_mismatches]
    return d


def _report_from_dict(d: dict) -> SchemaReport:
    return SchemaReport(
        matched=list(d.get("matched", [])),
        unmapped_input=list(d.get("unmapped_input", [])),
        missing_expected=list(d.get("missing_expected", [])),
        strategy=str(d.get("strategy", "header")),
        dtype_mismatches=[tuple(m) for m in d.get("dtype_mismatches", [])],
    )


def _drop_cache_files(*paths: Path) -> None:
    for p in paths:
        p.unlink(missing_ok=True)


def load_or_build_cache(path: str | Path,
                        sheet: str | int = 0
                        ) -> tuple[pd.DataFrame, SchemaReport]:
    src = str(path)
    # URL or missing file: delegate to load() so the user sees canonical errors.
    if _is_url(src) or not Path(src).exists():
        df, report = load(src, sheet=sheet)
        return enrich(df), report

    p = Path(src)
    key = _cache_key(p)
    parquet_path, report_path = _paths_for(key)

    if parquet_path.exists() and report_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            report = _report_from_dict(json.loads(report_path.read_text("utf-8")))
            return df, report
        except (OSError, ValueError, json.JSONDecodeError):
            _drop_cache_files(parquet_path, report_path)

    df, report = load(src, sheet=sheet)
    # Skip enrich + parquet write for schema-invalid datasets: the caller shows
    # an error and the file will be purged, so the work would be wasted.
    if not report.ok:
        return df, report
    df = enrich(df)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(parquet_path, engine="pyarrow", index=False)
        report_path.write_text(json.dumps(_report_to_dict(report)), encoding="utf-8")
    except (OSError, ValueError, ImportError):
        # Parquet engine missing or write failed: skip caching, app still works.
        _drop_cache_files(parquet_path, report_path)
    return df, report


def clear_cache() -> int:
    if not CACHE_DIR.exists():
        return 0
    removed = 0
    for f in CACHE_DIR.iterdir():
        if f.is_file():
            f.unlink()
            removed += 1
    return removed
