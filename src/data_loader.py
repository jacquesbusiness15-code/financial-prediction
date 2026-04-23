"""Load the WISAG dataset and return a clean, typed DataFrame + a SchemaReport.

Primary strategy: match German header names via HEADER_MAP (robust to column
reorders). Fallback: rename by Excel column position via COLUMN_MAP (used only
when no headers are recognized — keeps legacy files working).
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
    col_letter_to_index,
)

NUMERIC_PREFIXES = ("revenue_", "cost", "subcontractor_", "internal_service_",
                    "travel_", "labor_", "training_", "vacation_", "sick_",
                    "material_", "vehicle_", "hours_", "cm_", "hour_variance",
                    "cost_variance", "quality_", "plan_", "contracted_")

# Columns that match a numeric prefix by accident (e.g. start with "cost")
# but are actually string identifiers — never coerce these.
NON_NUMERIC_EXCEPTIONS = {
    "cost_center_id", "cost_center_name", "cost_center_name_ext",
    "customer_name", "customer_id", "customer_name_secondary",
    "contracted_fixed_price",  # this one IS numeric, keep. (placeholder)
}
# Trim the placeholder entry back out — keep only true string cols.
NON_NUMERIC_EXCEPTIONS.discard("contracted_fixed_price")


@dataclass
class SchemaReport:
    matched: list[str] = field(default_factory=list)
    unmapped_input: list[str] = field(default_factory=list)
    missing_expected: list[str] = field(default_factory=list)
    strategy: str = "header"  # "header" | "position"

    @property
    def missing_critical(self) -> list[str]:
        return [c for c in CRITICAL_SEMANTIC_COLS if c in self.missing_expected]

    @property
    def ok(self) -> bool:
        return not self.missing_critical

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


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if c in NON_NUMERIC_EXCEPTIONS:
            continue
        if any(c.startswith(p) or c == p for p in NUMERIC_PREFIXES) \
                or c in ("year", "month", "accrual_adjustment"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _add_period(df: pd.DataFrame) -> pd.DataFrame:
    if "year" in df.columns and "month" in df.columns:
        df["period"] = pd.to_datetime(
            dict(year=df["year"].astype("Int64"),
                 month=df["month"].astype("Int64"),
                 day=1),
            errors="coerce",
        )
    for c in ("contract_start", "contract_end"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", format="mixed")
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
      - `.../pubhtml`            → `.../pub?output=csv`
      - `.../edit?...gid=N`      → `.../export?format=csv&gid=N`
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
    columns matched, which were missing, and which strategy (header vs
    position) was used.
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

    df = _coerce_numeric(df)
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
