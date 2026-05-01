"""Tests for src.copilot_intent.

The headline regression: when the user asks for the contract with the highest
cost, the answer must be the highest revenue_total - cm_db, NOT the most
negative cm_db. The two are different concepts and were previously confused
by the LLM. The fixture below makes them deliberately disjoint.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.copilot_intent import (  # noqa: E402
    METRIC_COLUMN,
    RankingIntent,
    answer_ranking,
    detect_ranking_intent,
    format_ranking_answer,
)


_LATEST = pd.Timestamp("2026-03-01")
_PRIOR = pd.Timestamp("2026-02-01")


def _df() -> pd.DataFrame:
    """Three contracts, latest period, designed so 'highest cost' and
    'biggest loss' are different rows."""
    rows = [
        # Big profitable contract: highest cost (4_950_000) but positive CM.
        {"cost_center_id": "BIG", "cost_center_name": "Big Customer",
         "customer_name": "Mueller GmbH", "region": "West",
         "period": _LATEST, "revenue_total": 5_000_000.0, "cm_db": 50_000.0,
         "labor_cost_total": 2_000_000.0, "material_cost": 100_000.0,
         "vehicle_cost": 50_000.0, "cm_db_pct": 1.0},
        # Mid contract: middle of the pack.
        {"cost_center_id": "MID", "cost_center_name": "Mid Customer",
         "customer_name": "Schmitz AG", "region": "Nord",
         "period": _LATEST, "revenue_total": 200_000.0, "cm_db": 20_000.0,
         "labor_cost_total": 100_000.0, "material_cost": 5_000.0,
         "vehicle_cost": 2_000.0, "cm_db_pct": 10.0},
        # Loser: very negative CM, but tiny revenue → cost is only 30k,
        # nowhere near the BIG contract's cost.
        {"cost_center_id": "LOS", "cost_center_name": "Loser Site",
         "customer_name": "Beispiel KG", "region": "Sued",
         "period": _LATEST, "revenue_total": 10_000.0, "cm_db": -20_000.0,
         "labor_cost_total": 25_000.0, "material_cost": 1_000.0,
         "vehicle_cost": 500.0, "cm_db_pct": -200.0},
    ]
    # A prior period so period filtering has something to discard.
    prior_rows = [
        {**r, "period": _PRIOR, "revenue_total": r["revenue_total"] * 0.9,
         "cm_db": r["cm_db"] * 0.9} for r in rows
    ]
    return pd.DataFrame(rows + prior_rows)


# -------------------- detect_ranking_intent --------------------


def test_detect_highest_cost_question_de():
    out = detect_ranking_intent("Welcher Vertrag hat die höchsten Kosten?", "de")
    assert out is not None
    assert out.metric == "cost_total"
    assert out.direction == "top"
    assert out.n == 1


def test_detect_highest_cost_question_en():
    out = detect_ranking_intent("Which contract has the highest cost?", "en")
    assert out is not None
    assert out.metric == "cost_total"
    assert out.direction == "top"


def test_detect_biggest_loss_question_de():
    out = detect_ranking_intent("Welcher Vertrag macht den größten Verlust?", "de")
    assert out is not None
    assert out.metric == "cm_db"
    # "größter Verlust" → most negative CM → bottom direction.
    assert out.direction == "bottom"


def test_detect_top_n_revenue_de():
    out = detect_ranking_intent("Top 3 Verträge nach Umsatz", "de")
    assert out is not None
    assert out.metric == "revenue"
    assert out.direction == "top"
    assert out.n == 3


def test_detect_lowest_margin_de():
    out = detect_ranking_intent("Kostenstelle mit der niedrigsten Marge", "de")
    assert out is not None
    assert out.metric == "cm_db"
    assert out.direction == "bottom"


def test_detect_labor_cost_specific_de():
    out = detect_ranking_intent(
        "Welcher Vertrag hat die höchsten Personalkosten?", "de")
    assert out is not None
    # Personalkosten must NOT collapse into the generic cost_total bucket.
    assert out.metric == "labor_cost"
    assert out.direction == "top"


def test_detect_returns_none_for_open_ended():
    assert detect_ranking_intent("Wie geht es uns dieses Jahr?", "de") is None


def test_detect_returns_none_without_contract_scope():
    # No "Vertrag" / "Kostenstelle" → don't hijack a portfolio question.
    assert detect_ranking_intent("Wie hoch sind die Kosten?", "de") is None


def test_detect_returns_none_without_direction():
    assert detect_ranking_intent("Was sind die Kosten von Vertrag X?", "de") is None


def test_detect_caps_n_at_ten():
    out = detect_ranking_intent("Top 99 Verträge nach Umsatz", "de")
    assert out is not None
    assert out.n == 10


# -------------------- answer_ranking --------------------


def test_metric_column_map_covers_all_metrics():
    # Defensive: every metric used by the formatter must have a column mapping.
    from src.copilot_intent import _METRIC_LABELS  # noqa: PLC0415
    for metric in _METRIC_LABELS:
        assert metric in METRIC_COLUMN, metric


def test_highest_cost_returns_big_profitable_contract():
    """Headline regression: 'highest cost' is BIG, NOT the most-negative-CM LOS."""
    intent = RankingIntent(metric="cost_total", direction="top", n=1)
    answer = answer_ranking(intent, _df())
    assert len(answer.rows) == 1
    assert answer.rows[0]["id"] == "BIG"
    # The cost cited is exactly revenue - cm_db.
    assert answer.rows[0]["cost_eur"] == pytest.approx(4_950_000.0)
    # And it's NOT the loser.
    assert answer.rows[0]["id"] != "LOS"


def test_biggest_loss_returns_los_not_big():
    intent = RankingIntent(metric="cm_db", direction="bottom", n=1)
    answer = answer_ranking(intent, _df())
    assert answer.rows[0]["id"] == "LOS"
    assert answer.rows[0]["cm_eur"] == pytest.approx(-20_000.0)


def test_highest_cost_and_biggest_loss_are_different_contracts():
    cost = answer_ranking(
        RankingIntent("cost_total", "top", 1), _df()).rows[0]["id"]
    loss = answer_ranking(
        RankingIntent("cm_db", "bottom", 1), _df()).rows[0]["id"]
    assert cost != loss


def test_top_3_by_revenue_orders_descending():
    intent = RankingIntent(metric="revenue", direction="top", n=3)
    answer = answer_ranking(intent, _df())
    assert [r["id"] for r in answer.rows] == ["BIG", "MID", "LOS"]


def test_only_latest_period_is_ranked():
    intent = RankingIntent(metric="cost_total", direction="top", n=1)
    answer = answer_ranking(intent, _df())
    # The prior period had revenue scaled by 0.9, so cost would have been
    # 4_455_000 — must not appear.
    assert answer.rows[0]["cost_eur"] == pytest.approx(4_950_000.0)


def test_empty_dataframe_returns_empty_answer():
    answer = answer_ranking(
        RankingIntent("cost_total", "top", 1), pd.DataFrame())
    assert answer.rows == []


def test_unknown_metric_returns_empty_answer():
    intent = RankingIntent(metric="not_a_real_metric", direction="top", n=1)
    answer = answer_ranking(intent, _df())
    assert answer.rows == []


# -------------------- format_ranking_answer --------------------


def test_german_format_calls_out_cost_disambiguation():
    intent = RankingIntent(metric="cost_total", direction="top", n=1)
    answer = answer_ranking(intent, _df())
    out = format_ranking_answer(answer, lang="de")
    assert "Big Customer" in out
    # The disambiguation hint must be present so the user is not misled.
    assert "Verlust" in out or "Deckungsbeitrag" in out
    assert "höchsten" in out.lower() or "gesamtkosten" in out.lower()


def test_german_format_handles_empty():
    empty = answer_ranking(
        RankingIntent("cost_total", "top", 1), pd.DataFrame())
    out = format_ranking_answer(empty, lang="de")
    assert "keine Werte" in out.lower() or "keine werte" in out.lower()


def test_english_format_for_revenue_top3():
    intent = RankingIntent(metric="revenue", direction="top", n=3)
    answer = answer_ranking(intent, _df())
    out = format_ranking_answer(answer, lang="en")
    # Order preserved, all three names appear, headline mentions revenue.
    assert "revenue" in out.lower()
    assert "Big Customer" in out and "Mid Customer" in out and "Loser Site" in out
