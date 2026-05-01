"""Display-layer tests for the Solutions panel formatters.

These tests exercise the pure helpers that format the tracked-actions table.
They do not instantiate a Streamlit session; the ``t()`` helper falls back to
German (``DEFAULT_LANG``) when no session is present, so German strings are
asserted directly.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import i18n  # noqa: E402
from src.solutions_panel import (  # noqa: E402
    _DASH,
    _fmt_created,
    _fmt_eur_or_dash,
    _fmt_realized,
    _safe_float,
    _safe_period,
    _tracked_to_table,
)


@pytest.fixture(autouse=True)
def _force_german_lang(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the language to German for deterministic assertions."""
    monkeypatch.setattr(i18n, "get_lang", lambda: "de")


# ---------------------------------------------------------------------------
# _fmt_eur_or_dash
# ---------------------------------------------------------------------------

def test_fmt_eur_or_dash_handles_nan_and_none() -> None:
    assert _fmt_eur_or_dash(None) == _DASH
    assert _fmt_eur_or_dash(float("nan")) == _DASH
    assert _fmt_eur_or_dash(pd.NA) == _DASH


def test_fmt_eur_or_dash_formats_thousands_with_dot() -> None:
    assert _fmt_eur_or_dash(1500) == "1.500 EUR"
    assert _fmt_eur_or_dash(-2_500.0) == "-2.500 EUR"
    assert _fmt_eur_or_dash(0) == "0 EUR"


def test_fmt_eur_or_dash_rejects_garbage() -> None:
    assert _fmt_eur_or_dash("not-a-number") == _DASH


# ---------------------------------------------------------------------------
# _fmt_realized
# ---------------------------------------------------------------------------

def test_fmt_realized_returns_not_ready_for_proposed() -> None:
    row = pd.Series({"status": "proposed", "realized_cm_delta": None})
    assert _fmt_realized(row) == "Noch nicht messbar"


def test_fmt_realized_returns_not_ready_for_in_progress() -> None:
    row = pd.Series({"status": "in_progress", "realized_cm_delta": float("nan")})
    assert _fmt_realized(row) == "Noch nicht messbar"


def test_fmt_realized_returns_pending_for_done_without_delta() -> None:
    row = pd.Series({"status": "done", "realized_cm_delta": None})
    assert _fmt_realized(row) == "Wird gemessen ..."


def test_fmt_realized_formats_eur_when_present_even_if_done() -> None:
    row = pd.Series({"status": "done", "realized_cm_delta": 1200.0})
    assert _fmt_realized(row) == "1.200 EUR"


def test_fmt_realized_formats_eur_for_any_status_when_delta_present() -> None:
    row = pd.Series({"status": "abandoned", "realized_cm_delta": -500.0})
    assert _fmt_realized(row) == "-500 EUR"


# ---------------------------------------------------------------------------
# _fmt_created
# ---------------------------------------------------------------------------

def test_fmt_created_formats_iso_to_ddmmyyyy() -> None:
    assert _fmt_created("2026-04-24T14:35:12") == "24.04.2026"


def test_fmt_created_handles_timestamp() -> None:
    assert _fmt_created(pd.Timestamp("2026-03-01")) == "01.03.2026"


def test_fmt_created_returns_dash_for_none_and_garbage() -> None:
    assert _fmt_created(None) == _DASH
    assert _fmt_created("not-a-date") == _DASH
    assert _fmt_created(pd.NaT) == _DASH


# ---------------------------------------------------------------------------
# _safe_float / _safe_period
# ---------------------------------------------------------------------------

def test_safe_float_returns_zero_for_none_nan_and_garbage() -> None:
    assert _safe_float(None) == 0.0
    assert _safe_float(float("nan")) == 0.0
    assert _safe_float(pd.NA) == 0.0
    assert _safe_float("not-a-number") == 0.0


def test_safe_float_passes_through_numerics() -> None:
    assert _safe_float(-1500) == -1500.0
    assert _safe_float(12.5) == 12.5


def test_safe_period_returns_none_for_missing_and_garbage() -> None:
    assert _safe_period(None) is None
    assert _safe_period(pd.NaT) is None
    assert _safe_period("not-a-date") is None


def test_safe_period_normalizes_strings_and_timestamps() -> None:
    assert _safe_period("2026-03-01") == pd.Timestamp("2026-03-01")
    assert _safe_period(pd.Timestamp("2026-03-01")) == pd.Timestamp("2026-03-01")


# ---------------------------------------------------------------------------
# _tracked_to_table
# ---------------------------------------------------------------------------

def _make_tracked_row(**over) -> dict:
    base: dict = {
        "id": 1,
        "contract_id": "CC-1",
        "action_id": "labor_cost_audit",
        "created_at": "2026-04-24T14:35:12",
        "owner": "ops",
        "estimated_impact": 1_500.0,
        "status": "proposed",
        "notes": "",
        "baseline_cm_db": -500.0,
        "baseline_period": "2026-03-01",
        "realized_cm_delta": None,
        "measured_at": None,
    }
    base.update(over)
    return base


def test_tracked_to_table_empty_is_passthrough() -> None:
    empty = pd.DataFrame(columns=["action_id", "status", "estimated_impact",
                                  "realized_cm_delta", "owner", "created_at"])
    out = _tracked_to_table(empty)
    assert out.empty


def test_tracked_to_table_has_expected_columns_and_no_raw_status() -> None:
    tracked = pd.DataFrame([_make_tracked_row()])
    out = _tracked_to_table(tracked)

    assert list(out.columns) == [
        "Massnahme", "Status", "Wirkung (EUR/Monat)",
        "Realisiert (EUR/Monat)", "Verantwortlich", "Erstellt",
    ]
    # Header must NOT be the old 'Sicherheit' label.
    assert "Sicherheit" not in out.columns


def test_tracked_to_table_formats_values_and_status() -> None:
    tracked = pd.DataFrame([
        _make_tracked_row(status="proposed", realized_cm_delta=None,
                          estimated_impact=1_500.0,
                          created_at="2026-04-24T14:35:12"),
        _make_tracked_row(id=2, status="done", realized_cm_delta=320.0,
                          estimated_impact=900.0,
                          created_at="2026-02-01T09:00:00"),
    ])
    out = _tracked_to_table(tracked)

    # Row 1 - proposed, no realized delta yet
    assert out.iloc[0]["Status"] == "Vorgeschlagen"
    assert out.iloc[0]["Wirkung (EUR/Monat)"] == "1.500 EUR"
    assert out.iloc[0]["Realisiert (EUR/Monat)"] == "Noch nicht messbar"
    assert out.iloc[0]["Erstellt"] == "24.04.2026"
    assert out.iloc[0]["Verantwortlich"] == "Betrieb"

    # Row 2 - done, realized delta present
    assert out.iloc[1]["Status"] == "Abgeschlossen"
    assert out.iloc[1]["Wirkung (EUR/Monat)"] == "900 EUR"
    assert out.iloc[1]["Realisiert (EUR/Monat)"] == "320 EUR"
    assert out.iloc[1]["Erstellt"] == "01.02.2026"


def test_tracked_to_table_handles_unknown_owner_and_nan_impact() -> None:
    tracked = pd.DataFrame([
        _make_tracked_row(owner="mystery_role", estimated_impact=math.nan),
    ])
    out = _tracked_to_table(tracked)

    # Unknown owner roles pass through as the raw string so no information
    # is silently dropped; known roles are translated instead.
    assert out.iloc[0]["Verantwortlich"] == "mystery_role"
    assert out.iloc[0]["Wirkung (EUR/Monat)"] == _DASH


def test_tracked_to_table_blank_owner_shows_empty_string() -> None:
    tracked = pd.DataFrame([_make_tracked_row(owner=None)])
    out = _tracked_to_table(tracked)
    assert out.iloc[0]["Verantwortlich"] == ""


def test_tracked_to_table_done_without_delta_shows_pending() -> None:
    tracked = pd.DataFrame([
        _make_tracked_row(status="done", realized_cm_delta=float("nan")),
    ])
    out = _tracked_to_table(tracked)
    assert out.iloc[0]["Realisiert (EUR/Monat)"] == "Wird gemessen ..."
