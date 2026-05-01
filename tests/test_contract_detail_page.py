from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.contract_detail_page import _default_period_index  # noqa: E402


def test_default_period_index_prefers_latest_row_with_margin_value() -> None:
    focus = pd.DataFrame([
        {"period": pd.Timestamp("2026-01-01"), "revenue_total": 100.0, "cm_db_pct": 20.0},
        {"period": pd.Timestamp("2026-02-01"), "revenue_total": 150.0, "cm_db_pct": 15.0},
        {"period": pd.Timestamp("2026-03-01"), "revenue_total": 0.0, "cm_db_pct": pd.NA},
    ])

    assert _default_period_index(focus) == 1
