"""Load the WISAG dataset into a typed DataFrame plus SchemaReport.

Header matching via HEADER_MAP is primary; position-based renaming via
COLUMN_MAP is the legacy fallback. Dtypes come from SCHEMA; any silent NA
introduced on a critical column fails SchemaReport.ok.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

from src.config import COLUMN_MAP, CRITICAL_SEMANTIC_COLS, HEADER_MAP, SCHEMA


@dataclass
class SchemaReport:
    matched: list[str] = field(default_factory=list)
    unmapped_input: list[str] = field(default_factory=list)
    missing_expected: list[str] = field(default_factory=list)
    strategy: str = "header"  # "header" | "position"
    # (column, expected_dtype, observed_sample) for columns where coercion lost rows
    dtype_mismatches: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def missing_critical(self) -> list[str]:
        missing = set(self.missing_expected)
        return [c for c in CRITICAL_SEMANTIC_COLS if c in missing]

    @property
    def critical_dtype_mismatches(self) -> list[tuple[str, str, str]]:
        critical = set(CRITICAL_SEMANTIC_COLS)
        return [m for m in self.dtype_mismatches if m[0] in critical]

    @property
    def ok(self) -> bool:
        return not self.missing_critical and not self.critical_dtype_mismatches

    @property
    def expected_total(self) -> int:
        return len(HEADER_MAP)


def _rename_by_header(df: pd.DataFrame) -> tuple[pd.DataFrame, SchemaReport]:
    rename: dict[str, str] = {}
    unmapped: list[str] = []
    for col in df.columns:
        key = str(col).strip()
        if key in HEADER_MAP:
            rename[col] = HEADER_MAP[key]
        else:
            unmapped.append(str(col))
    df = df.rename(columns=rename)
    mapped_semantic = set(rename.values())
    return df, SchemaReport(
        matched=list(rename.values()),
        unmapped_input=unmapped,
        missing_expected=[v for v in HEADER_MAP.values() if v not in mapped_semantic],
        strategy="header",
    )


def _rename_by_position(df: pd.DataFrame) -> tuple[pd.DataFrame, SchemaReport]:
    # COLUMN_MAP is insertion-ordered by Excel letter (A, B, ..., BU) so its
    # values are already in positional order.
    position_names = list(COLUMN_MAP.values())
    new_names = [position_names[i] if i < len(position_names) else f"col_{i}"
                 for i in range(len(df.columns))]
    df = df.copy()
    df.columns = new_names
    mapped_set = set(new_names) - {n for n in new_names if n.startswith("col_")}
    return df, SchemaReport(
        matched=[n for n in new_names if not n.startswith("col_")],
        unmapped_input=[n for n in new_names if n.startswith("col_")],
        missing_expected=[v for v in HEADER_MAP.values() if v not in mapped_set],
        strategy="position",
    )


def _coerce_series(s: pd.Series, dtype: str) -> pd.Series:
    if dtype == "Int64":
        return pd.to_numeric(s, errors="coerce").astype("Int64")
    if dtype == "float64":
        return pd.to_numeric(s, errors="coerce").astype("float64")
    if dtype == "string":
        return s.astype("string")
    if dtype == "category":
        # Normalize via string first so category values compare consistently.
        return s.astype("string").astype("category")
    if dtype == "datetime64[ns]":
        return pd.to_datetime(s, errors="coerce")
    if dtype == "boolean":
        return pd.to_numeric(s, errors="coerce").fillna(0).astype("bool")
    raise ValueError(f"Unsupported dtype in SCHEMA: {dtype!r}")


def _coerce_dtypes(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, str, str]]]:
    df = df.copy()
    mismatches: list[tuple[str, str, str]] = []
    lossy_dtypes = {"Int64", "float64", "datetime64[ns]"}
    for col, (dtype, _group) in SCHEMA.items():
        if col not in df.columns:
            continue
        original = df[col]
        try:
            coerced = _coerce_series(original, dtype)
        except (ValueError, TypeError) as e:
            mismatches.append((col, dtype, f"coercion error: {e}"))
            continue
        if dtype in lossy_dtypes:
            lost = original.notna() & coerced.isna()
            if lost.any():
                bad = str(original[lost].iloc[0])
                sample = bad if len(bad) <= 40 else bad[:37] + "..."
                mismatches.append((col, dtype, sample))
        df[col] = coerced
    return df, mismatches


def _add_period(df: pd.DataFrame) -> pd.DataFrame:
    if "year" in df.columns and "month" in df.columns:
        df["period"] = pd.to_datetime(
            {"year": df["year"], "month": df["month"], "day": 1},
            errors="coerce",
        )
    return df


_xlsx_engine_cached: str | None = None


def _xlsx_engine() -> str:
    # calamine (Rust-backed) parses XLSX 5-20x faster than openpyxl via pandas;
    # falls back if python-calamine isn't installed.
    global _xlsx_engine_cached
    if _xlsx_engine_cached is None:
        try:
            import python_calamine  # noqa: F401
            _xlsx_engine_cached = "calamine"
        except ImportError:
            _xlsx_engine_cached = "openpyxl"
    return _xlsx_engine_cached


def _sniff_delimiter(path: Path, encoding: str) -> str:
    try:
        with path.open("r", encoding=encoding) as f:
            sample = f.read(8192)
    except (OSError, UnicodeDecodeError):
        return ","
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def _read_any(path: Path, sheet: str | int) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, sheet_name=sheet, engine=_xlsx_engine(), header=0)
    if suffix != ".csv":
        raise ValueError(f"Unsupported file type: {suffix!r} (expected .xlsx, .xls, or .csv)")
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8", "utf-8-sig", "iso-8859-1", "cp1252"):
        try:
            return pd.read_csv(path, sep=_sniff_delimiter(path, encoding), encoding=encoding)
        except UnicodeDecodeError as e:
            last_error = e
            continue
    raise last_error  # type: ignore[misc]


def _is_url(s: str) -> bool:
    return s.lower().startswith(("http://", "https://"))


def _to_csv_url(url: str) -> str:
    """Convert a Google Sheets share/publish URL into a direct CSV-export URL."""
    if "docs.google.com/spreadsheets" not in url:
        return url
    gid_match = re.search(r"[?&#]gid=(\d+)", url)
    gid_param = f"&gid={gid_match.group(1)}" if gid_match else ""
    if "/pubhtml" in url:
        base = url.split("/pubhtml", 1)[0]
        return f"{base}/pub?output=csv{gid_param}"
    m = re.search(r"/spreadsheets/d/(e/)?([^/?#]+)", url)
    if not m:
        return url
    prefix, sheet_id = m.group(1) or "", m.group(2)
    if prefix:
        return f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv{gid_param}"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv{gid_param}"


def load(path: str | Path, sheet: str | int = 0) -> tuple[pd.DataFrame, SchemaReport]:
    """Load and type-clean the WISAG dataset from a local file or URL."""
    src = str(path)
    if _is_url(src):
        raw = pd.read_csv(_to_csv_url(src))
    else:
        p = Path(src)
        if not p.exists():
            raise FileNotFoundError(
                f"Dataset not found at {p}. Place Dataset_anoym.xlsx in ./data/ "
                "or paste a Google Sheets URL in the sidebar."
            )
        raw = _read_any(p, sheet)

    df, report = _rename_by_header(raw)
    if not report.matched:
        df, report = _rename_by_position(raw)

    df, report.dtype_mismatches = _coerce_dtypes(df)
    df = _add_period(df)
    if "period" in df.columns and "cost_center_id" in df.columns:
        df = df.sort_values(["cost_center_id", "period"]).reset_index(drop=True)
    return df, report


def summary(df: pd.DataFrame) -> dict:
    out: dict = {"rows": len(df), "columns": len(df.columns)}
    if "period" in df.columns:
        out["period_min"] = df["period"].min()
        out["period_max"] = df["period"].max()
    for col, key in (("region", "regions"), ("cost_center_id", "cost_centers")):
        if col in df.columns:
            out[key] = int(df[col].nunique())
    for col, key in (("revenue_total", "revenue_total"), ("cm_db", "cm_db_total")):
        if col in df.columns:
            out[key] = float(df[col].sum())
    return out
