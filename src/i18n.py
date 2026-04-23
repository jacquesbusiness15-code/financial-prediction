"""German string catalog for the WISAG Financial Co-Pilot UI."""
from __future__ import annotations

de: dict[str, str] = {
    # App-level
    "app.title": "WISAG Strategische Finanzvorschau",
    "app.subtitle": "KI-gestützter Deckungsbeitrags-Copilot — erkennt Abweichungen, erklärt das *Warum* und empfiehlt Maßnahmen.",
    "app.welcome": "Willkommen",
    "app.welcome_sub": "Ihr KI-gestützter Überblick über den Deckungsbeitrag.",

    # Navigation
    "nav.home": "Startseite",
    "nav.portfolio": "Portfolio-Übersicht",
    "nav.deepdive": "Detailanalyse",
    "nav.warnings": "Frühwarnungen",
    "nav.chat": "Co-Pilot Chat",
    "nav.plan_vs_actual": "Plan vs. Ist",
    "nav.open": "Öffnen",

    # Nav card descriptions
    "nav.portfolio.desc": "Alle Regionen auf einen Blick. Erkennen Sie Ausreißer in der Heatmap und die Top-Risiken.",
    "nav.deepdive.desc": "Eine Kostenstelle tief untersuchen. Die KI erklärt das Warum und schlägt Maßnahmen vor.",
    "nav.warnings.desc": "Proaktive Risikosignale für die nächsten 90 Tage — sortiert nach Euro-Wirkung.",
    "nav.chat.desc": "Stellen Sie Fragen in natürlicher Sprache. Der Co-Pilot antwortet auf Basis Ihrer Daten.",
    "nav.plan_vs_actual.desc": "Monatliche Abweichung zwischen Plan und Ist — mit farblich markierten Ausreißern.",

    # Sidebar
    "sidebar.filters": "Filter",
    "sidebar.settings": "Einstellungen",
    "sidebar.settings_help": "Datei-Upload, Schema-Prüfung und API-Status. Normalerweise nicht nötig.",
    "sidebar.data_source": "Datenquelle",
    "sidebar.upload": "Datensatz hochladen (optional)",
    "sidebar.upload_help": "Ohne Upload verwendet die App `data/Dataset_anoym.xlsx`.",
    "sidebar.api_status": "Claude-API",
    "sidebar.api_ok": "API-Schlüssel geladen",
    "sidebar.api_missing": "`ANTHROPIC_API_KEY` in `.env` setzen, um KI-Erklärungen zu aktivieren. Ohne Schlüssel verwendet die App eine einfache Vorlage.",

    # Filters
    "filter.region": "Region",
    "filter.region_only": "Region: **{r}** (einzige Region in den Daten)",
    "filter.service": "Dienstleistungsart",
    "filter.period": "Zeitraum",

    # KPIs
    "kpi.revenue": "Umsatz",
    "kpi.cm": "Deckungsbeitrag",
    "kpi.cm_planned": "Geplanter Deckungsbeitrag",
    "kpi.plan_gap": "Abweichung zum Plan",
    "kpi.cost_centers": "Kostenstellen",
    "kpi.anomalies": "Auffälligkeiten",
    "kpi.total_actual": "Ist-Deckungsbeitrag gesamt",
    "kpi.total_planned": "Plan-Deckungsbeitrag gesamt",
    "kpi.total_gap": "Gesamt-Abweichung",
    "kpi.worst_month": "Schlechtester Monat",
    "kpi.eur_at_stake": "Euro-Risiko (Top 10)",
    "kpi.high_severity": "Hohe Priorität",
    "kpi.medium_severity": "Mittlere Priorität",
    "kpi.low_severity": "Niedrige Priorität",

    # Portfolio Overview
    "portfolio.title": "Portfolio-Übersicht",
    "portfolio.subtitle": "Was läuft gut, was läuft schlecht — und was als nächstes zu tun ist.",
    "portfolio.heatmap_legend": "Rot = unter Plan · Grün = über Plan. Klicken und ziehen, um Zeiträume zu zoomen.",
    "portfolio.top_cc": "Größte Kostenstellen nach Umsatz",
    "portfolio.anomalies_title": "Top-Auffälligkeiten (nach Euro-Wirkung)",
    "portfolio.anomalies_empty": "Keine Auffälligkeiten mit den aktuellen Filtern gefunden.",
    "portfolio.anomalies_hint": "Öffnen Sie die **Detailanalyse** über die Seitenleiste und wählen Sie eine Kostenstelle, um Treiberanalyse und KI-Erklärung zu sehen.",
    "portfolio.how_to_read": "So lesen Sie diese Seite",
    "portfolio.how_to_read_body": (
        "- **Ampel** oben zeigt Plan-Erfüllung, Profitabilität und Risikolage auf einen Blick.\n"
        "- **Entwicklungs-Chart** zeigt, wie sich Umsatz, Ist- und Plan-DB Monat für Monat bewegen.\n"
        "- **Was läuft gut / Was läuft schlecht**: konkrete positive und negative Befunde — sortiert nach Euro-Wirkung.\n"
        "- **Empfohlene Maßnahmen**: konkrete nächste Schritte mit Direktlink in die passende Detail-Seite."
    ),
    "portfolio.evolution_title": "Entwicklung über die Zeit",
    "portfolio.evolution_caption": "Umsatz (Balken) sowie Ist- und Plan-Deckungsbeitrag (Linien) Monat für Monat.",
    "portfolio.good_title": "Was läuft gut",
    "portfolio.bad_title": "Was läuft schlecht",
    "portfolio.good_empty": "Aktuell keine positiven Auffälligkeiten im Filterbereich.",
    "portfolio.bad_empty": "Keine negativen Auffälligkeiten — Portfolio stabil.",
    "portfolio.actions_title": "Empfohlene Maßnahmen",
    "portfolio.actions_caption": "Konkrete nächste Schritte — abgeleitet aus den Risiko-Signalen oben.",
    "portfolio.actions_empty": "✓ Keine unmittelbaren Maßnahmen erforderlich — Portfolio in gutem Zustand.",
    "portfolio.traffic.plan": "Plan-Erfüllung",
    "portfolio.traffic.margin": "Profitabilität",
    "portfolio.traffic.risk": "Risikolage",
    "portfolio.traffic.plan.no_data": "Keine Plan-Daten verfügbar",
    "portfolio.traffic.plan.beat": "Plan übertroffen ({p})",
    "portfolio.traffic.plan.slightly": "Leicht unter Plan ({p})",
    "portfolio.traffic.plan.under": "Unter Plan ({p})",
    "portfolio.traffic.plan.deep": "Deutlich unter Plan ({p})",
    "portfolio.traffic.margin.healthy": "Marge {p} — gesund",
    "portfolio.traffic.margin.thin": "Marge {p} — dünn",
    "portfolio.traffic.margin.near_zero": "Marge {p} — nahe Null",
    "portfolio.traffic.margin.negative": "Marge {p} — negativ",
    "portfolio.traffic.risk.none": "Keine hochpriorisierten Risiken",
    "portfolio.traffic.risk.some": "{n} hochpriorisierte Risiken",

    # Facility-focus overview (strings below are ENGLISH to match the mock)
    "overview.back": "‹ Back to overview",
    "overview.period_label": "Period",
    "overview.export": "Export",
    "overview.margin": "Margin",
    "overview.change_mom": "Change vs last month",
    "overview.why_drop": "Why did the margin drop?",
    "overview.why_drop_sub": "Key factors vs last month",
    "overview.what_do": "What can we do?",
    "overview.what_do_sub": "Recommended actions",
    "overview.potential_impact": "Potential impact",
    "overview.view_all_drivers": "View all drivers ›",
    "overview.view_all_actions": "View all actions ›",
    "overview.whatif": "What if?",
    "overview.whatif_sub": "See how changes can impact margin",
    "overview.team_size": "Team size",
    "overview.employees": "employees",
    "overview.productivity_gain": "{p} productivity",
    "overview.new_margin": "New margin",
    "overview.vs_current": "{p} vs current",
    "overview.explore_more": "Explore more scenarios",
    "overview.explore_more_sub": "Test different combinations and see the potential impact.",
    "overview.data_updated": "Data last updated: {ts}",
    "overview.status.critical": "Critical",
    "overview.status.warn": "Watch",
    "overview.status.healthy": "Healthy",
    "overview.no_focus": "No cost center available in the current filter.",
    "overview.no_baseline": "No prior month available as a baseline.",

    # Custom sidebar nav (mock verbatim)
    "nav.overview_short": "Overview",
    "nav.analytics_short": "Analytics",
    "nav.forecasts_short": "Forecasts",
    "nav.scenarios_short": "Scenarios",
    "nav.reports_short": "Reports",
    "nav.alerts_short": "Alerts",
    "nav.settings_short": "Settings",
    "nav.ask_ai": "Ask AI",

    # Driver labels (English copy for the facility-focus cards)
    "driver.labor": "Higher labor costs",
    "driver.labor.sub": "Total labor costs increased",
    "driver.absence": "Increased absences",
    "driver.absence.sub": "More sick leaves and time off",
    "driver.training": "Training & onboarding",
    "driver.training.sub": "More new hires and training hours",
    "driver.subcontractor": "More subcontracting",
    "driver.subcontractor.sub": "Higher share of external services",
    "driver.material": "Higher material costs",
    "driver.material.sub": "Material consumption up",
    "driver.vehicle": "Higher vehicle costs",
    "driver.vehicle.sub": "Fleet and travel expenses up",
    "driver.revenue": "Revenue decline",
    "driver.revenue.sub": "Less billed revenue",
    "driver.revenue_up": "Revenue growth",
    "driver.revenue_up.sub": "More billed revenue",
    "driver.other": "Other cost movements",
    "driver.other.sub": "Sum of remaining cost lines",

    # Recommended-action labels (English)
    "action.shift.title": "Optimize shift scheduling",
    "action.shift.sub": "Reduce overtime and improve coverage",
    "action.absence.title": "Reduce absences",
    "action.absence.sub": "Strengthen retention and well-being programs",
    "action.onboarding.title": "Improve onboarding efficiency",
    "action.onboarding.sub": "Speed up productivity of new hires",
    "action.subcontractor.title": "Reduce subcontracting mix",
    "action.subcontractor.sub": "Grow in-house delivery, lower external cost",
    "action.pricing.title": "Review pricing & contract terms",
    "action.pricing.sub": "Renegotiate low-margin contracts",
    "action.productivity.title": "Boost productivity",
    "action.productivity.sub": "Improve process and shift utilization",
    "portfolio.worst_banner": (
        "🚨 **{month}** — Deckungsbeitrag eingebrochen auf **{cm}** "
        "(Kostenstelle {cc_id} · {cc_name}). {labor}{hours}. "
        "👉 Öffnen Sie die **Detailanalyse** für Treiberzerlegung und KI-Erklärung."
    ),
    "portfolio.dq_banner": (
        "📊 **Datenqualität — {month}:** Umsatz {rev} ist das {ratio:.1f}× des "
        "gleitenden 12-Monats-Mittels. {note}. "
        "Dieser Monat wird aus der Auffälligkeits-Rangliste ausgeschlossen, um Fehlalarme zu vermeiden."
    ),

    # Deep Dive
    "deepdive.title": "Detailanalyse",
    "deepdive.subtitle": "Kostenstelle auswählen → Treiberzerlegung und KI-Erklärung ansehen.",
    "deepdive.cost_center": "Kostenstelle",
    "deepdive.baseline": "Vergleichsbasis",
    "deepdive.baseline_prior_month": "vs. Vormonat",
    "deepdive.baseline_prior_year": "vs. Vorjahr",
    "deepdive.baseline_plan": "vs. Plan",
    "deepdive.period": "Analysezeitraum",
    "deepdive.no_data": "Keine Daten für diese Kostenstelle.",
    "deepdive.no_baseline": "Keine Vergleichsbasis für »{mode}« verfügbar. Bitte anderen Vergleich wählen.",
    "deepdive.timeline_title": "Deckungsbeitrag-Verlauf · Kostenstelle {cc}",
    "deepdive.waterfall_title": "ΔDB vs. {baseline} = {delta}",
    "deepdive.kpi_peers": "Kennzahlen im Vergleich zu regionalen Peers",
    "deepdive.kpi_peers_empty": "Nicht genügend Vergleichsdaten für Peers.",
    "deepdive.ai_title": "KI-Erklärung",
    "deepdive.ai_preview": "Die KI klassifiziert die Abweichung (operativ vs. Daten-Artefakt), nennt die Top-3-Ursachen und schlägt konkrete Maßnahmen vor.",
    "deepdive.ai_asking": "Frage Claude…",
    "deepdive.ai_hint": "Klicken Sie oben, um eine strukturierte Erklärung zu generieren.",
    "deepdive.download": "Als Kommentar herunterladen",
    "deepdive.residual_warn": "Hinweis: Ein Teil der Abweichung ({pct:.0%}) konnte nicht eindeutig einem Treiber zugeordnet werden. Die Treiberanalyse zeigt die wesentlichen Effekte, nicht alle Detail-Buchungen.",

    # Early Warnings
    "warnings.title": "Frühwarnungen",
    "warnings.subtitle": "Proaktive, regelbasierte Risikosignale auf den jüngsten Daten pro Kostenstelle.",
    "warnings.none": "✓ Keine Frühwarnungen mit den aktuellen Filtern.",
    "warnings.rules_title": "Welche Regeln prüfen wir?",
    "warnings.rules_body": (
        "- **DB-Trend rückläufig** — der Deckungsbeitrag sinkt seit 3 Monaten und liegt unter Plan.\n"
        "- **Krankenstand-Spitze** — Krankenstand > 2 σ über dem eigenen Durchschnitt.\n"
        "- **Produktivitätseinbruch** — Produktivität < 70 % und weiter fallend.\n"
        "- **Subunternehmer-Anstieg** — Subunternehmer-Anteil > 10 Prozentpunkte über Plan.\n"
        "- **Vertragsende in < 90 Tagen** — Renewal-Risiko bei laufenden Verträgen.\n"
        "- **Plan-Abweichung weitet sich** — die Lücke zum Plan vergrößert sich zwei Monate in Folge."
    ),
    "warnings.pick": "Warnung auswählen",
    "warnings.action_title": "Maßnahmenplan für eine ausgewählte Warnung",
    "warnings.ai_button": "KI-Maßnahmenplan anzeigen",
    "warnings.no_history": "Keine Historie verfügbar.",
    "warnings.not_enough_history": "Nicht genügend Historie für eine Vergleichsbasis.",

    # Signal labels (German)
    "signal.Declining CM trend": "DB-Trend rückläufig",
    "signal.Absence spike": "Krankenstand-Spitze",
    "signal.Productivity drop": "Produktivitätseinbruch",
    "signal.Subcontractor creep": "Subunternehmer-Anstieg",
    "signal.Contract renewal risk": "Vertragsende in Sicht",
    "signal.Plan gap widening": "Plan-Abweichung weitet sich",

    # Severity labels
    "severity.high": "Hoch",
    "severity.medium": "Mittel",
    "severity.low": "Niedrig",

    # Chat
    "chat.title": "Finanz-Co-Pilot Chat",
    "chat.subtitle": "Stellen Sie Fragen in natürlicher Sprache zu den gefilterten Daten.",
    "chat.try_asking": "Beispielfragen:",
    "chat.examples": (
        "- Welche Region hat aktuell den schwächsten Deckungsbeitrag und warum?\n"
        "- Ranking der 3 Kostenstellen mit der größten Plan-Abweichung — was haben sie gemeinsam?\n"
        "- Welche Dienstleistungsart trägt das größte absolute Margenrisiko?\n"
        "- Wenn die Produktivität im unteren Quartil um 10 % steigt — wie viel Deckungsbeitrag würde das freisetzen?"
    ),
    "chat.input_placeholder": "Frage an den Co-Pilot…",
    "chat.thinking": "Denke nach…",
    "chat.clear": "Chat zurücksetzen",

    # Plan vs Actual
    "pva.title": "Plan vs. Ist — monatliche Abweichung",
    "pva.subtitle": "Monatsvergleich von Ist- und Plan-Deckungsbeitrag mit Euro- und Prozent-Abweichung.",
    "pva.missing_cols": "Spalten `cm_planned` / `cm_db` fehlen — Abweichung kann nicht berechnet werden.",
    "pva.bar_title": "Monatliche DB-Abweichung (Ist − Plan, €)",
    "pva.chart_caption": "Monate mit Abweichung < −50 000 € sind rot, > +50 000 € grün.",
    "pva.table_title": "Abweichungstabelle pro Monat",
    "pva.col.month": "Monat",
    "pva.col.revenue": "Umsatz",
    "pva.col.planned": "Plan-DB",
    "pva.col.actual": "Ist-DB",
    "pva.col.gap_eur": "Abweichung €",
    "pva.col.gap_pct": "Abweichung %",
    "pva.table_caption": (
        "Zeilen sind **rot** hervorgehoben, wenn der Ist-DB den Plan um mehr als 50 k€ verfehlt hat; "
        "**grün**, wenn er den Plan um mehr als 50 k€ übertroffen hat. "
        "Große positive Ausreißer können auf Buchungs-Abgrenzungen hindeuten — siehe den Datenqualitäts-Hinweis auf der Portfolio-Übersicht."
    ),

    # Data source / errors
    "data.no_data_warn": "👈 **So starten Sie:** Legen Sie `Dataset_anoym.xlsx` im Ordner `data/` ab oder laden Sie die Datei über die Seitenleiste hoch.",
    "data.no_data_page": "Bitte laden Sie den Datensatz auf der Startseite.",
    "data.place_or_upload": "`Dataset_anoym.xlsx` im Ordner `./data/` ablegen oder oben hochladen.",
    "data.load_failed": "Laden fehlgeschlagen: {err}",
    "data.schema_ok": "✓ Schema: {m}/{t} Spalten erkannt",
    "data.schema_position": "⚠ Schema: {m}/{t} Spalten (Zuordnung über Spaltenposition — keine deutschen Überschriften gefunden). Export bitte mit Originalkopfzeile wiederholen.",
    "data.schema_error": "❌ Schema: {m}/{t} Spalten erkannt\n\nFehlende kritische Spalten: **{missing}**\n\nOhne diese Spalten kann die App nicht rechnen. Bitte Überschriften der Quelldatei prüfen.",
    "data.optional_missing": "{n} optionale Spalten fehlen",
    "data.extra_ignored": "{n} zusätzliche Spalten ignoriert",
    "data.stats": "{rows:,} Zeilen · {ccs} Kostenstellen · {pmin} → {pmax}",

    # Actions
    "action.generate_explanation": "KI-Erklärung anzeigen",
    "action.download": "Herunterladen",
    "action.open_deepdive": "Detailanalyse öffnen →",
    "action.details": "Details anzeigen",
}


def t(key: str, **fmt) -> str:
    """Translate a key. Unknown keys return the key itself (visible in UI to flag gaps)."""
    val = de.get(key, key)
    if fmt:
        try:
            return val.format(**fmt)
        except (KeyError, IndexError):
            return val
    return val
