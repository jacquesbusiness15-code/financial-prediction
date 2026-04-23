"""Load the WISAG dataset and return a clean, typed DataFrame + a SchemaReport.

Primary strategy: match German header names via HEADER_MAP (robust to column
reorders). Fallback: rename by Excel column position via COLUMN_MAP (used only
when no headers are recognized - keeps legacy files working).

Dtype coercion is schema-driven: every mapped column is coerced to the dtype
declared in `src.config.SCHEMA`. Rows whose source value cannot be coerced
(non-null in, null out) are counted; any such loss on a critical column is
reported as a dtype mismatch and fails `SchemaReport.ok`.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

from src.config import (
    COLUMN_MAP,
    CRITICAL_SEMANTIC_COLS,
    HEADER_MAP,
    SCHEMA,
    col_letter_to_index,
)


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
        return [c for c in CRITICAL_SEMANTIC_COLS if c in self.missing_expected]

    @property
    def critical_dtype_mismatches(self) -> list[tuple[str, str, str]]:
        return [m for m in self.dtype_mismatches if m[0] in CRITICAL_SEMANTIC_COLS]

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
    mapped_semantic = list(rename.values())
    return df, SchemaReport(
        matched=mapped_semantic,
        unmapped_input=unmapped,
        missing_expected=[v for v in HEADER_MAP.values() if v not in mapped_semantic],
        strategy="header",
    )


def _rename_by_position(df: pd.DataFrame) -> tuple[pd.DataFrame, SchemaReport]:
    new_names: list[str] = []
    for i, _ in enumerate(df.columns):
        letter = next((ltr for ltr in COLUMN_MAP
                       if col_letter_to_index(ltr) == i), None)
        new_names.append(COLUMN_MAP[letter] if letter else f"col_{i}")
    df = df.copy()
    df.columns = new_names
    mapped = [n for n in new_names if not n.startswith("col_")]
    return df, SchemaReport(
        matched=mapped,
        unmapped_input=[n for n in new_names if n.startswith("col_")],
        missing_expected=[v for v in HEADER_MAP.values() if v not in mapped],
        strategy="position",
    )


def _coerce_series(s: pd.Series, dtype: str) -> pd.Series:
    """Coerce `s` to `dtype`. Invalid values become NA/NaN/NaT."""
    if dtype == "Int64":
        return pd.to_numeric(s, errors="coerce").astype("Int64")
    if dtype == "float64":
        return pd.to_numeric(s, errors="coerce").astype("float64")
    if dtype == "string":
        return s.astype("string")
    if dtype == "category":
        # Normalize to string first so categorical values compare consistently.
        return s.astype("string").astype("category")
    if dtype == "datetime64[ns]":
        return pd.to_datetime(s, errors="coerce")
    if dtype == "boolean":
        return pd.to_numeric(s, errors="coerce").fillna(0).astype("bool")
    raise ValueError(f"Unsupported dtype in SCHEMA: {dtype!r}")


def _sample_bad_value(original: pd.Series, coerced: pd.Series) -> str:
    """Pick the first source value that failed to coerce, for error reporting."""
    mask = original.notna() & coerced.isna()
    if not mask.any():
        return ""
    bad = original[mask].iloc[0]
    text = str(bad)
    return text if len(text) <= 40 else text[:37] + "..."


def _coerce_dtypes(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, str, str]]]:
    """Apply SCHEMA dtypes. Return the coerced frame + a list of mismatches."""
    df = df.copy()
    mismatches: list[tuple[str, str, str]] = []
    for col, (dtype, _group) in SCHEMA.items():
        if col not in df.columns:
            continue
        original = df[col]
        try:
            coerced = _coerce_series(original, dtype)
        except Exception as e:  # noqa: BLE001
            mismatches.append((col, dtype, f"coercion error: {e}"))
            continue
        # Detect rows where coercion silently dropped data.
        if dtype in ("Int64", "float64", "datetime64[ns]"):
            pre = int(original.notna().sum())
            post = int(coerced.notna().sum())
            if post < pre:
                mismatches.append((col, dtype, _sample_bad_value(original, coerced)))
        df[col] = coerced
    return df, mismatches


def _add_period(df: pd.DataFrame) -> pd.DataFrame:
    if "year" in df.columns and "month" in df.columns:
        df["period"] = pd.to_datetime(
            dict(year=df["year"].astype("Int64"),
                 month=df["month"].astype("Int64"),
                 day=1),
            errors="coerce",
        )
    return df


def _read_any(path: Path, sheet: str | int) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        encodings = ("utf-8", "utf-8-sig", "iso-8859-1", "cp1252")
        last_error: Exception | None = None
        for encoding in encodings:
            try:
                raw = path.read_text(encoding=encoding)
                sample = raw[:8192]
                delimiter = ","
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                    delimiter = dialect.delimiter
                except csv.Error:
                    pass
                return pd.read_csv(io.StringIO(raw), sep=delimiter)
            except UnicodeDecodeError as e:
                last_error = e
        if last_error is not None:
            raise last_error
        return pd.read_csv(path)
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, sheet_name=sheet, engine="openpyxl", header=0)
    raise ValueError(f"Unsupported file type: {suffix!r} (expected .xlsx, .xls, or .csv)")


def _is_url(s: str) -> bool:
    return s.lower().startswith(("http://", "https://"))


def _to_csv_url(url: str) -> str:
    """Convert a Google Sheets view/publish URL into a direct CSV export URL.

    Handles:
      - `.../pubhtml`            -> `.../pub?output=csv`
      - `.../edit?...gid=N`      -> `.../export?format=csv&gid=N`
    Other URLs are returned unchanged (assumed to already serve CSV).
    """
    if "docs.google.com/spreadsheets" not in url:
        return url
    if "/pubhtml" in url:
        base = url.split("/pubhtml", 1)[0]
        gid_match = re.search(r"[?&#]gid=(\d+)", url)
        gid_param = f"&gid={gid_match.group(1)}" if gid_match else ""
        return f"{base}/pub?output=csv{gid_param}"
    m = re.search(r"/spreadsheets/d/(e/)?([^/?#]+)", url)
    if m:
        prefix, sheet_id = m.group(1) or "", m.group(2)
        gid_match = re.search(r"[?&#]gid=(\d+)", url)
        gid_param = f"&gid={gid_match.group(1)}" if gid_match else ""
        if prefix:
            return f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv{gid_param}"
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv{gid_param}"
    return url


def load(path: str | Path, sheet: str | int = 0) -> tuple[pd.DataFrame, SchemaReport]:
    """Load and type-clean the WISAG dataset from a local file or URL.

    Accepts:
      - a local `.xlsx` / `.xls` / `.csv` file path
      - an `http(s)` URL pointing at a CSV (Google Sheets share/publish links
        are auto-converted to their CSV-export form)

    Returns (dataframe, schema_report). The report tells the caller which
    columns matched, which were missing, which dtype coercions lost data, and
    which strategy (header vs position) was used.
    """
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

    df, mismatches = _coerce_dtypes(df)
    report.dtype_mismatches = mismatches
    df = _add_period(df)
    if "period" in df.columns and "cost_center_id" in df.columns:
        df = df.sort_values(["cost_center_id", "period"]).reset_index(drop=True)
    return df, report


def summary(df: pd.DataFrame) -> dict:
    out: dict = {"rows": len(df), "columns": len(df.columns)}
    if "period" in df.columns:
        out["period_min"] = df["period"].min()
        out["period_max"] = df["period"].max()
    if "region" in df.columns:
        out["regions"] = int(df["region"].nunique())
    if "cost_center_id" in df.columns:
        out["cost_centers"] = int(df["cost_center_id"].nunique())
    if "revenue_total" in df.columns:
        out["revenue_total"] = float(df["revenue_total"].sum())
    if "cm_db" in df.columns:
        out["cm_db_total"] = float(df["cm_db"].sum())
    return out
