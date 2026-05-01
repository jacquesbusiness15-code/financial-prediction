"""Deterministic intent layer for the financial co-pilot.

For ranking-style questions ("welcher Vertrag hat die höchsten Kosten?"), the
LLM has been observed to confuse cost (revenue minus margin) with negative
margin. This module short-circuits those questions: detect the metric and the
direction, sort the dataframe in Python, and format a verified answer.

Everything else still falls through to the free-form LLM chat path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

# ---------------------------------------------------------------------------
# Intent model
# ---------------------------------------------------------------------------

# Canonical metrics. Each maps to either a raw column on the dataframe or to
# the derived `cost_total = revenue_total - cm_db`. Add new entries here when a
# new ranking dimension becomes useful.
METRIC_COLUMN: dict[str, str] = {
    "cost_total": "cost_total",
    "revenue": "revenue_total",
    "cm_db": "cm_db",
    "cm_db_pct": "cm_db_pct",
    "labor_cost": "labor_cost_total",
    "material_cost": "material_cost",
    "vehicle_cost": "vehicle_cost",
}

# Default sort direction is ASCENDING when direction == "bottom", DESCENDING
# when direction == "top".
_MAX_N = 10


@dataclass
class RankingIntent:
    metric: str
    direction: str  # "top" or "bottom"
    n: int = 1


@dataclass
class RankingAnswer:
    intent: RankingIntent
    period: pd.Timestamp | None
    rows: list[dict]  # each: id, name, customer, region, value, revenue, cm, cost
    metric_label_de: str
    metric_label_en: str


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

# Direction tokens. The order matters: "höchster Verlust" should still parse
# as "biggest loss" (direction=bottom on cm_db), so the loss/Verlust rule
# below is allowed to override the direction.
_TOP_RX = re.compile(
    r"\b(h(ö|oe)chst\w*|gr(ö|oe)(ss|ß)t\w*|teuerst\w*|meist\w*|maxim\w*|"
    r"highest|largest|biggest|most|top|best\w*)\b",
    re.IGNORECASE,
)
_BOTTOM_RX = re.compile(
    r"\b(niedrigst\w*|kleinst\w*|geringst\w*|wenigst\w*|minim\w*|schlecht\w*|"
    r"lowest|smallest|fewest|least|worst)\b",
    re.IGNORECASE,
)

# Metric lexicons (DE then EN). First match wins, so put the more specific
# ones (labor, material, vehicle) before the generic "kosten".
_METRIC_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("labor_cost", re.compile(r"\b(personalkosten|lohnkosten|labor\s*cost|wages?)\b", re.I)),
    ("material_cost", re.compile(r"\b(materialkosten|material\s*cost)\b", re.I)),
    ("vehicle_cost", re.compile(r"\b(fahrzeugkosten|kfz[- ]?kosten|vehicle\s*cost)\b", re.I)),
    ("revenue", re.compile(r"\b(umsatz|umsatzes|erl(ö|oe)se?|revenue|sales|turnover)\b", re.I)),
    ("cm_db_pct", re.compile(r"\b(margen?prozent|marge\s*in\s*prozent|margin\s*percent|db[-\s]?%|margin\s*%)\b", re.I)),
    # cost_total: catch "Kosten", "Aufwand", "Ausgaben". Excludes Personalkosten /
    # Materialkosten / Fahrzeugkosten which are handled above.
    ("cost_total", re.compile(r"\b(gesamtkosten|kosten|aufwand|aufwendungen|ausgaben|expenses?|cost)\b", re.I)),
    # cm_db: positive-margin and negative-margin (loss) variants both map here;
    # the direction is set by the loss-detector below.
    ("cm_db", re.compile(
        r"\b(deckungsbeitrag|\bdb\b|marge|gewinn|margin|profit|"
        r"verlust|verluste|loss|losses)\b", re.I)),
]

# Loss detector: any of these tokens forces direction=bottom on the cm_db
# metric (asking for "biggest loss" means most negative margin).
_LOSS_RX = re.compile(r"\b(verlust\w*|loss|losses|negativ\w*\s+(marge|db|deckungsbeitrag))\b", re.I)

# Contract-scope tokens: at least one is required so that we don't hijack
# generic questions like "wie hoch sind die Kosten?".
_SCOPE_RX = re.compile(
    r"\b(vertrag|vertr(ä|ae)ge|kostenstelle|kostenstellen|kunde|kunden|"
    r"contract|contracts|cost\s*center|customer|customers|kst|kst-id)\b",
    re.IGNORECASE,
)

# "Top 3", "die 5 teuersten", "top-10"
_N_RX = re.compile(
    r"\b(?:top[\s-]*|die\s+|den\s+|the\s+)?(\d{1,2})\s+"
    r"(?:gr(ö|oe)(ss|ß)t\w*|h(ö|oe)chst\w*|teuerst\w*|niedrigst\w*|kleinst\w*|"
    r"top\w*|best\w*|worst|schlecht\w*|"
    r"vertr|kostenstellen|contracts?|customers?|kunden)",
    re.IGNORECASE,
)
_N_RX_LEAD = re.compile(r"\btop[\s-]*(\d{1,2})\b", re.IGNORECASE)


def detect_ranking_intent(text: str, lang: str = "de") -> RankingIntent | None:
    """Return a RankingIntent if `text` looks like a top-N question, else None.

    Detection requires:
      1. a direction word (höchste / niedrigste / top / lowest / ...),
      2. a metric word (Kosten, Umsatz, Marge, ...),
      3. a contract-scope noun (Vertrag, Kostenstelle, ...).
    """
    del lang  # rules are bilingual; lang only matters for formatting.
    if not text:
        return None
    t = text.strip()
    if not _SCOPE_RX.search(t):
        return None

    metric: str | None = None
    for name, pat in _METRIC_RULES:
        if pat.search(t):
            metric = name
            break
    if metric is None:
        return None

    has_top = bool(_TOP_RX.search(t))
    has_bottom = bool(_BOTTOM_RX.search(t))
    has_loss = bool(_LOSS_RX.search(t))

    # If the user said "Verlust" / "loss", they want the most negative cm_db.
    if metric == "cm_db" and has_loss:
        direction = "bottom"
    elif has_top and not has_bottom:
        direction = "top"
    elif has_bottom and not has_top:
        direction = "bottom"
    elif has_top and has_bottom:
        # Ambiguous — bail to the LLM.
        return None
    else:
        # No direction word at all → not a ranking question.
        return None

    # Extract N (default 1, capped at _MAX_N).
    n = 1
    m = _N_RX.search(t) or _N_RX_LEAD.search(t)
    if m:
        try:
            n = max(1, min(_MAX_N, int(m.group(1))))
        except (TypeError, ValueError):
            n = 1

    return RankingIntent(metric=metric, direction=direction, n=n)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

_MIN_REVENUE_FOR_PCT = 10.0


def answer_ranking(intent: RankingIntent, df: pd.DataFrame) -> RankingAnswer:
    """Compute the top-N answer for `intent` against the latest period of `df`."""
    label_de, label_en = _metric_labels(intent.metric)
    empty = RankingAnswer(intent=intent, period=None, rows=[],
                          metric_label_de=label_de, metric_label_en=label_en)
    if df is None or df.empty or "period" not in df.columns:
        return empty

    latest = df["period"].max()
    if pd.isna(latest):
        return empty
    slice_ = df[df["period"] == latest].copy()
    if slice_.empty:
        return empty

    # Always derive cost_total so the cost ranking has a column to sort on
    # even when the source frame doesn't expose one directly.
    if "revenue_total" in slice_.columns and "cm_db" in slice_.columns:
        slice_["cost_total"] = (
            pd.to_numeric(slice_["revenue_total"], errors="coerce")
            - pd.to_numeric(slice_["cm_db"], errors="coerce")
        )

    key_col = METRIC_COLUMN.get(intent.metric)
    if key_col is None or key_col not in slice_.columns:
        return RankingAnswer(intent=intent, period=pd.Timestamp(latest), rows=[],
                             metric_label_de=label_de, metric_label_en=label_en)

    slice_[key_col] = pd.to_numeric(slice_[key_col], errors="coerce")
    slice_ = slice_.dropna(subset=[key_col])

    # cm_db_pct should not rank tiny-revenue noise to the top.
    if intent.metric == "cm_db_pct" and "revenue_total" in slice_.columns:
        slice_ = slice_[pd.to_numeric(slice_["revenue_total"], errors="coerce")
                        >= _MIN_REVENUE_FOR_PCT]

    if slice_.empty:
        return RankingAnswer(intent=intent, period=pd.Timestamp(latest), rows=[],
                             metric_label_de=label_de, metric_label_en=label_en)

    ascending = (intent.direction == "bottom")
    sorted_ = slice_.sort_values(key_col, ascending=ascending).head(intent.n)

    rows: list[dict] = []
    for _, row in sorted_.iterrows():
        rev = _safe_float(row.get("revenue_total"))
        cm = _safe_float(row.get("cm_db"))
        cost = (rev - cm) if rev is not None and cm is not None else None
        value = _safe_float(row.get(key_col))
        rows.append({
            "id": _safe_str(row.get("cost_center_id")),
            "name": _safe_str(row.get("cost_center_name")),
            "customer": _safe_str(row.get("customer_name")),
            "region": _safe_str(row.get("region")),
            "value": value,
            "revenue_eur": rev,
            "cm_eur": cm,
            "cost_eur": cost,
        })

    return RankingAnswer(
        intent=intent, period=pd.Timestamp(latest), rows=rows,
        metric_label_de=label_de, metric_label_en=label_en,
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

# Mirrors the in-app glossary terms (src/glossary.py) so the chat output
# matches tooltips and KPI labels.
_METRIC_LABELS: dict[str, tuple[str, str]] = {
    "cost_total": ("Gesamtkosten", "total cost"),
    "revenue": ("Umsatz", "revenue"),
    "cm_db": ("Deckungsbeitrag", "contribution margin"),
    "cm_db_pct": ("Deckungsbeitrag in %", "contribution margin %"),
    "labor_cost": ("Personalkosten", "labor cost"),
    "material_cost": ("Materialkosten", "material cost"),
    "vehicle_cost": ("Fahrzeugkosten", "vehicle cost"),
}

_DIRECTION_LABELS_DE: dict[tuple[str, str], str] = {
    ("top", "cost_total"): "höchsten Gesamtkosten",
    ("bottom", "cost_total"): "niedrigsten Gesamtkosten",
    ("top", "revenue"): "höchsten Umsatz",
    ("bottom", "revenue"): "niedrigsten Umsatz",
    ("top", "cm_db"): "höchsten Deckungsbeitrag",
    ("bottom", "cm_db"): "niedrigsten Deckungsbeitrag (grössten Verlust)",
    ("top", "cm_db_pct"): "höchste Marge in Prozent",
    ("bottom", "cm_db_pct"): "niedrigste Marge in Prozent",
    ("top", "labor_cost"): "höchsten Personalkosten",
    ("bottom", "labor_cost"): "niedrigsten Personalkosten",
    ("top", "material_cost"): "höchsten Materialkosten",
    ("bottom", "material_cost"): "niedrigsten Materialkosten",
    ("top", "vehicle_cost"): "höchsten Fahrzeugkosten",
    ("bottom", "vehicle_cost"): "niedrigsten Fahrzeugkosten",
}

_DIRECTION_LABELS_EN: dict[tuple[str, str], str] = {
    ("top", "cost_total"): "highest total cost",
    ("bottom", "cost_total"): "lowest total cost",
    ("top", "revenue"): "highest revenue",
    ("bottom", "revenue"): "lowest revenue",
    ("top", "cm_db"): "highest contribution margin",
    ("bottom", "cm_db"): "lowest contribution margin (biggest loss)",
    ("top", "cm_db_pct"): "highest margin %",
    ("bottom", "cm_db_pct"): "lowest margin %",
    ("top", "labor_cost"): "highest labor cost",
    ("bottom", "labor_cost"): "lowest labor cost",
    ("top", "material_cost"): "highest material cost",
    ("bottom", "material_cost"): "lowest material cost",
    ("top", "vehicle_cost"): "highest vehicle cost",
    ("bottom", "vehicle_cost"): "lowest vehicle cost",
}

# German months to keep the period stamp readable to a controller.
_MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def format_ranking_answer(answer: RankingAnswer, lang: str = "de") -> str:
    if lang == "en":
        return _format_en(answer)
    return _format_de(answer)


def _format_de(answer: RankingAnswer) -> str:
    if not answer.rows:
        return ("Für die aktuelle Periode liegen keine Werte vor, die diese Frage "
                "beantworten könnten. Prüfen Sie die Filter oder die Datenquelle.")

    period = _period_de(answer.period)
    headline = _DIRECTION_LABELS_DE.get(
        (answer.intent.direction, answer.intent.metric),
        f"Top-{answer.intent.n} nach {answer.metric_label_de}",
    )

    if answer.intent.n == 1:
        title = f"**Vertrag mit {headline}** ({period})"
        body = _row_line_de(answer.rows[0], answer.intent.metric)
        out = f"{title}\n{body}"
    else:
        title = f"**Top {len(answer.rows)} Verträge nach {answer.metric_label_de}** ({period})"
        lines = [f"{i + 1}. {_row_line_de(r, answer.intent.metric)}"
                 for i, r in enumerate(answer.rows)]
        out = title + "\n" + "\n".join(lines)

    if answer.intent.metric == "cost_total":
        out += ("\n\n*Hinweis: Gesamtkosten = Umsatz minus Deckungsbeitrag. Der "
                "Vertrag mit dem grössten Verlust ist meist ein anderer — fragen "
                "Sie nach dem niedrigsten Deckungsbeitrag.*")
    return out


def _format_en(answer: RankingAnswer) -> str:
    if not answer.rows:
        return ("No values are available for the current period to answer this "
                "question. Please check the filters or data source.")

    period = _period_en(answer.period)
    headline = _DIRECTION_LABELS_EN.get(
        (answer.intent.direction, answer.intent.metric),
        f"top {answer.intent.n} by {answer.metric_label_en}",
    )

    if answer.intent.n == 1:
        title = f"**Contract with the {headline}** ({period})"
        body = _row_line_en(answer.rows[0], answer.intent.metric)
        out = f"{title}\n{body}"
    else:
        title = f"**Top {len(answer.rows)} contracts by {answer.metric_label_en}** ({period})"
        lines = [f"{i + 1}. {_row_line_en(r, answer.intent.metric)}"
                 for i, r in enumerate(answer.rows)]
        out = title + "\n" + "\n".join(lines)

    if answer.intent.metric == "cost_total":
        out += ("\n\n*Note: Total cost = revenue − contribution margin. The "
                "biggest-loss contract is usually a different one — ask for the "
                "'lowest contribution margin' to get that.*")
    return out


def _row_line_de(row: dict, metric: str) -> str:
    name = row.get("name") or row.get("id") or "?"
    cust = f" — {row['customer']}" if row.get("customer") else ""
    rev = _eur_de(row.get("revenue_eur"))
    cm = _eur_de(row.get("cm_eur"), signed=True)
    cost = _eur_de(row.get("cost_eur"))
    pct = _pct_de(row.get("value")) if metric == "cm_db_pct" else None

    if metric == "cost_total":
        return (f"KST `{row.get('id', '?')}` — *{name}*{cust} — "
                f"Gesamtkosten **{cost}** (Umsatz {rev}, DB {cm}).")
    if metric == "revenue":
        return (f"KST `{row.get('id', '?')}` — *{name}*{cust} — "
                f"Umsatz **{rev}** (DB {cm}, Gesamtkosten {cost}).")
    if metric == "cm_db":
        return (f"KST `{row.get('id', '?')}` — *{name}*{cust} — "
                f"DB **{cm}** (Umsatz {rev}, Gesamtkosten {cost}).")
    if metric == "cm_db_pct":
        return (f"KST `{row.get('id', '?')}` — *{name}*{cust} — "
                f"Marge **{pct}** (Umsatz {rev}, DB {cm}).")
    value = _eur_de(row.get("value"))
    return (f"KST `{row.get('id', '?')}` — *{name}*{cust} — "
            f"**{value}** (Umsatz {rev}, DB {cm}, Gesamtkosten {cost}).")


def _row_line_en(row: dict, metric: str) -> str:
    name = row.get("name") or row.get("id") or "?"
    cust = f" — {row['customer']}" if row.get("customer") else ""
    rev = _eur_en(row.get("revenue_eur"))
    cm = _eur_en(row.get("cm_eur"), signed=True)
    cost = _eur_en(row.get("cost_eur"))
    pct = _pct_en(row.get("value")) if metric == "cm_db_pct" else None

    if metric == "cost_total":
        return (f"`{row.get('id', '?')}` — *{name}*{cust} — "
                f"total cost **{cost}** (revenue {rev}, CM {cm}).")
    if metric == "revenue":
        return (f"`{row.get('id', '?')}` — *{name}*{cust} — "
                f"revenue **{rev}** (CM {cm}, total cost {cost}).")
    if metric == "cm_db":
        return (f"`{row.get('id', '?')}` — *{name}*{cust} — "
                f"CM **{cm}** (revenue {rev}, total cost {cost}).")
    if metric == "cm_db_pct":
        return (f"`{row.get('id', '?')}` — *{name}*{cust} — "
                f"margin **{pct}** (revenue {rev}, CM {cm}).")
    value = _eur_en(row.get("value"))
    return (f"`{row.get('id', '?')}` — *{name}*{cust} — "
            f"**{value}** (revenue {rev}, CM {cm}, total cost {cost}).")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _metric_labels(metric: str) -> tuple[str, str]:
    return _METRIC_LABELS.get(metric, (metric, metric))


def _safe_float(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value) -> str | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    s = str(value).strip()
    return s or None


def _eur_de(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    sign = "+" if signed and value > 0 else ""
    formatted = f"{value:,.0f}".replace(",", ".")
    return f"{sign}{formatted} €"


def _eur_en(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}€{value:,.0f}"


def _pct_de(value: float | None) -> str:
    if value is None:
        return "n/a"
    formatted = f"{value:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} %"


def _pct_en(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.1f}%"


def _period_de(period: pd.Timestamp | None) -> str:
    if period is None:
        return "Stand aktuell"
    try:
        return f"Stand {_MONTHS_DE[period.month - 1]} {period.year}"
    except (AttributeError, IndexError, ValueError):
        return "Stand aktuell"


def _period_en(period: pd.Timestamp | None) -> str:
    if period is None:
        return "current period"
    try:
        return period.strftime("as of %B %Y")
    except (AttributeError, ValueError):
        return "current period"
