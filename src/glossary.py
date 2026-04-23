"""Finance-term tooltips in German. Used via `help=` in Streamlit widgets."""
from __future__ import annotations

de_glossary: dict[str, str] = {
    "revenue": "Umsatz: Gesamterlöse im gewählten Zeitraum aus allen aktiven Kostenstellen.",
    "cm_db": (
        "Deckungsbeitrag (DB): Umsatz minus variable Kosten. Zeigt, wie viel Marge "
        "die Kostenstelle zum Gesamtergebnis beiträgt."
    ),
    "cm_planned": "Geplanter Deckungsbeitrag: der im Jahresplan hinterlegte Zielwert.",
    "plan_gap": (
        "Abweichung zum Plan: Differenz zwischen tatsächlichem DB und geplantem DB. "
        "Negativ bedeutet: unter Plan."
    ),
    "cost_centers": "Anzahl aktiver Kostenstellen im gewählten Zeitraum und Filter.",
    "anomalies": (
        "Auffälligkeiten: Perioden und Kostenstellen, die aufgrund von Regeln oder "
        "Statistik aus dem Rahmen fallen (z. B. negativer DB, Plan-Miss > 15 %)."
    ),
    "waterfall": (
        "Treiberanalyse: Zerlegt die DB-Veränderung in ihre Ursachen "
        "(z. B. Personalkosten, Subunternehmer, Umsatz). Balken nach oben = positiver Effekt."
    ),
    "residual": (
        "Restgröße: der nicht eindeutig zugeordnete Anteil der Abweichung — meist unter 5 %. "
        "Liegt er darüber, zeigt die App eine Warnung an."
    ),
    "labor_ratio": "Personalquote: Personalkosten geteilt durch Umsatz. Hoch = margenbelastend.",
    "productivity": "Produktivität: Ist-Stunden im Verhältnis zu den Plan-Stunden (100 % = auf Plan).",
    "absence_rate": "Krankenstand: Anteil der krankheitsbedingten Ausfallzeit an den Gesamtstunden.",
    "subcontractor_share": "Subunternehmer-Anteil: Anteil der Subunternehmer-Kosten an den Gesamtkosten.",
    "heatmap": (
        "Heatmap: Farbliche Darstellung der DB-Marge pro Region und Monat. "
        "Rot = unter Plan, Grün = über Plan."
    ),
    "severity": (
        "Priorität: Hoch = sofortige Aufmerksamkeit (> 25 k€ Wirkung), "
        "Mittel = prüfen (5–25 k€), Niedrig = beobachten."
    ),
    "impact_eur": "Euro-Wirkung: geschätztes finanzielles Volumen, das von diesem Signal betroffen ist.",
    "cm_pct": "Deckungsbeitrag in Prozent: DB geteilt durch Umsatz.",
    "peer_comparison": (
        "Peer-Vergleich: Vergleich der ausgewählten Kostenstelle mit dem Median "
        "aller Kostenstellen derselben Region."
    ),
}


def g(key: str) -> str:
    """Look up a tooltip. Returns an empty string for unknown keys."""
    return de_glossary.get(key, "")
