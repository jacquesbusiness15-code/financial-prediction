"""SQLite-backed log of Solution Finder actions per contract.

The tracker stores proposed / in-progress / done / abandoned actions so
the team has a history of what was tried and what the realised CM delta
was afterwards. Streamlit re-runs every user interaction, so the
connection is opened per call (never held across reruns) and WAL journal
mode is used to keep Windows file locks from blocking concurrent reads.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal, Optional

import pandas as pd


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


Status = Literal["proposed", "in_progress", "done", "abandoned"]
VALID_STATUSES: frozenset[str] = frozenset({
    "proposed", "in_progress", "done", "abandoned",
})

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "action_log.sqlite"

OUTCOME_WINDOW_MONTHS = 3


_SCHEMA = """
CREATE TABLE IF NOT EXISTS action_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id         TEXT    NOT NULL,
    action_id           TEXT    NOT NULL,
    created_at          TEXT    NOT NULL,
    owner               TEXT,
    estimated_impact    REAL,
    status              TEXT    NOT NULL DEFAULT 'proposed',
    notes               TEXT,
    baseline_cm_db      REAL,
    baseline_period     TEXT,
    realized_cm_delta   REAL,
    measured_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_action_log_contract ON action_log(contract_id);
CREATE INDEX IF NOT EXISTS idx_action_log_status   ON action_log(status);
"""


@contextmanager
def _connect(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_action(
    contract_id: str,
    action_id: str,
    owner: Optional[str] = None,
    estimated_impact: Optional[float] = None,
    notes: str = "",
    baseline_cm_db: Optional[float] = None,
    baseline_period: Optional[pd.Timestamp] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Insert a new proposed-status action; return the row id."""
    created = _now_iso()
    baseline_iso = _iso(baseline_period)
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO action_log(
                contract_id, action_id, created_at, owner, estimated_impact,
                status, notes, baseline_cm_db, baseline_period
            ) VALUES (?, ?, ?, ?, ?, 'proposed', ?, ?, ?)
            """,
            (str(contract_id), str(action_id), created, owner,
             _maybe_float(estimated_impact), notes, _maybe_float(baseline_cm_db),
             baseline_iso),
        )
        return int(cur.lastrowid)


def update_status(
    entry_id: int,
    status: Status,
    notes: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status!r}")
    with _connect(db_path) as conn:
        if notes is None:
            conn.execute("UPDATE action_log SET status = ? WHERE id = ?",
                         (status, int(entry_id)))
        else:
            conn.execute(
                "UPDATE action_log SET status = ?, notes = ? WHERE id = ?",
                (status, notes, int(entry_id)),
            )


def list_for_contract(
    contract_id: str,
    db_path: Optional[Path] = None,
) -> pd.DataFrame:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, contract_id, action_id, created_at, owner,
                   estimated_impact, status, notes, baseline_cm_db,
                   baseline_period, realized_cm_delta, measured_at
            FROM action_log
            WHERE contract_id = ?
            ORDER BY created_at DESC
            """,
            (str(contract_id),),
        ).fetchall()
    columns = ["id", "contract_id", "action_id", "created_at", "owner",
               "estimated_impact", "status", "notes", "baseline_cm_db",
               "baseline_period", "realized_cm_delta", "measured_at"]
    return pd.DataFrame(rows, columns=columns)


def measure_outcome(
    entry_id: int,
    df: pd.DataFrame,
    db_path: Optional[Path] = None,
    window_months: int = OUTCOME_WINDOW_MONTHS,
) -> Optional[float]:
    """Compute realized cm_db delta vs baseline for the window after created_at.

    Reads the entry's contract id + baseline, aggregates cm_db over the
    ``window_months`` months strictly after ``baseline_period`` (or the
    creation timestamp if baseline is missing) from ``df`` and writes the
    delta plus ``measured_at`` back into the row. Returns the delta if
    enough post-action data exists, otherwise None.
    """
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT contract_id, baseline_cm_db, baseline_period, created_at "
            "FROM action_log WHERE id = ?",
            (int(entry_id),),
        ).fetchone()
        if row is None:
            return None
        contract_id, baseline_cm_db, baseline_period, created_at = row

    if df is None or df.empty or "cost_center_id" not in df.columns:
        return None

    hist = df[df["cost_center_id"].astype(str) == str(contract_id)].copy()
    if hist.empty or "period" not in hist.columns or "cm_db" not in hist.columns:
        return None
    hist["period"] = pd.to_datetime(hist["period"], errors="coerce")

    cutoff = pd.to_datetime(baseline_period or created_at, errors="coerce")
    if pd.isna(cutoff):
        return None
    end = cutoff + pd.DateOffset(months=window_months)
    post = hist[(hist["period"] > cutoff) & (hist["period"] <= end)]
    if len(post) < max(1, window_months // 2):
        return None

    mean_post = float(pd.to_numeric(post["cm_db"], errors="coerce").mean())
    baseline = _maybe_float(baseline_cm_db)
    if baseline is None:
        baseline_row = hist[hist["period"] == cutoff]
        if baseline_row.empty:
            return None
        baseline = float(pd.to_numeric(
            baseline_row["cm_db"], errors="coerce").mean())

    delta = mean_post - baseline
    measured = _now_iso()
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE action_log SET realized_cm_delta = ?, measured_at = ? "
            "WHERE id = ?",
            (float(delta), measured, int(entry_id)),
        )
    return float(delta)


def _iso(period: Optional[pd.Timestamp]) -> Optional[str]:
    if period is None:
        return None
    ts = pd.to_datetime(period, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.isoformat()


def _maybe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f
