"""German + English string catalogs for the WISAG Financial Co-Pilot UI."""
from __future__ import annotations

DEFAULT_LANG = "de"

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
    "sidebar.language": "Sprache",

    # Language switcher options
    "lang.de": "Deutsch",
    "lang.en": "Englisch",

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


en: dict[str, str] = {
    # App-level
    "app.title": "WISAG Strategic Financial Forecast",
    "app.subtitle": "AI-powered contribution-margin copilot — detects variances, explains the *why*, and recommends actions.",
    "app.welcome": "Welcome",
    "app.welcome_sub": "Your AI-powered contribution-margin overview.",

    # Navigation
    "nav.home": "Home",
    "nav.portfolio": "Portfolio overview",
    "nav.deepdive": "Deep dive",
    "nav.warnings": "Early warnings",
    "nav.chat": "Copilot chat",
    "nav.plan_vs_actual": "Plan vs. actual",
    "nav.open": "Open",

    # Nav card descriptions
    "nav.portfolio.desc": "All regions at a glance. Spot outliers in the heatmap and the top risks.",
    "nav.deepdive.desc": "Investigate a cost center in depth. The AI explains the why and suggests actions.",
    "nav.warnings.desc": "Proactive risk signals for the next 90 days — sorted by euro impact.",
    "nav.chat.desc": "Ask questions in natural language. The copilot answers based on your data.",
    "nav.plan_vs_actual.desc": "Monthly variance between plan and actual — with outliers color-coded.",

    # Sidebar
    "sidebar.filters": "Filters",
    "sidebar.settings": "Settings",
    "sidebar.settings_help": "File upload, schema check and API status. Usually not needed.",
    "sidebar.data_source": "Data source",
    "sidebar.upload": "Upload dataset (optional)",
    "sidebar.upload_help": "Without an upload the app uses `data/Dataset_anoym.xlsx`.",
    "sidebar.api_status": "Claude API",
    "sidebar.api_ok": "API key loaded",
    "sidebar.api_missing": "Set `ANTHROPIC_API_KEY` in `.env` to enable AI explanations. Without a key the app falls back to a simple template.",
    "sidebar.language": "Language",

    # Language switcher options
    "lang.de": "German",
    "lang.en": "English",

    # Filters
    "filter.region": "Region",
    "filter.region_only": "Region: **{r}** (only region in the data)",
    "filter.service": "Service type",
    "filter.period": "Period",

    # KPIs
    "kpi.revenue": "Revenue",
    "kpi.cm": "Contribution margin",
    "kpi.cm_planned": "Planned contribution margin",
    "kpi.plan_gap": "Gap vs. plan",
    "kpi.cost_centers": "Cost centers",
    "kpi.anomalies": "Anomalies",
    "kpi.total_actual": "Total actual contribution margin",
    "kpi.total_planned": "Total planned contribution margin",
    "kpi.total_gap": "Total gap",
    "kpi.worst_month": "Worst month",
    "kpi.eur_at_stake": "Euro at stake (top 10)",
    "kpi.high_severity": "High priority",
    "kpi.medium_severity": "Medium priority",
    "kpi.low_severity": "Low priority",

    # Portfolio Overview
    "portfolio.title": "Portfolio overview",
    "portfolio.subtitle": "What's going well, what's going poorly — and what to do next.",
    "portfolio.heatmap_legend": "Red = below plan · Green = above plan. Click and drag to zoom into periods.",
    "portfolio.top_cc": "Largest cost centers by revenue",
    "portfolio.anomalies_title": "Top anomalies (by euro impact)",
    "portfolio.anomalies_empty": "No anomalies found with the current filters.",
    "portfolio.anomalies_hint": "Open **Deep dive** from the sidebar and pick a cost center to see driver decomposition and AI explanation.",
    "portfolio.how_to_read": "How to read this page",
    "portfolio.how_to_read_body": (
        "- **Traffic lights** at the top show plan attainment, profitability and risk posture at a glance.\n"
        "- **Evolution chart** shows how revenue, actual and planned CM move month by month.\n"
        "- **What's going well / What's going poorly**: concrete positive and negative findings — sorted by euro impact.\n"
        "- **Recommended actions**: concrete next steps with a direct link into the relevant detail page."
    ),
    "portfolio.evolution_title": "Evolution over time",
    "portfolio.evolution_caption": "Revenue (bars) and actual/planned contribution margin (lines), month by month.",
    "portfolio.good_title": "What's going well",
    "portfolio.bad_title": "What's going poorly",
    "portfolio.good_empty": "No positive anomalies in the current filter.",
    "portfolio.bad_empty": "No negative anomalies — portfolio stable.",
    "portfolio.actions_title": "Recommended actions",
    "portfolio.actions_caption": "Concrete next steps — derived from the risk signals above.",
    "portfolio.actions_empty": "✓ No immediate actions required — portfolio in good shape.",
    "portfolio.traffic.plan": "Plan attainment",
    "portfolio.traffic.margin": "Profitability",
    "portfolio.traffic.risk": "Risk posture",
    "portfolio.traffic.plan.no_data": "No plan data available",
    "portfolio.traffic.plan.beat": "Plan beaten ({p})",
    "portfolio.traffic.plan.slightly": "Slightly below plan ({p})",
    "portfolio.traffic.plan.under": "Below plan ({p})",
    "portfolio.traffic.plan.deep": "Well below plan ({p})",
    "portfolio.traffic.margin.healthy": "Margin {p} — healthy",
    "portfolio.traffic.margin.thin": "Margin {p} — thin",
    "portfolio.traffic.margin.near_zero": "Margin {p} — near zero",
    "portfolio.traffic.margin.negative": "Margin {p} — negative",
    "portfolio.traffic.risk.none": "No high-priority risks",
    "portfolio.traffic.risk.some": "{n} high-priority risks",

    # Facility-focus overview (already English — copied verbatim)
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

    # Custom sidebar nav (already English)
    "nav.overview_short": "Overview",
    "nav.analytics_short": "Analytics",
    "nav.forecasts_short": "Forecasts",
    "nav.scenarios_short": "Scenarios",
    "nav.reports_short": "Reports",
    "nav.alerts_short": "Alerts",
    "nav.settings_short": "Settings",
    "nav.ask_ai": "Ask AI",

    # Driver labels (already English)
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

    # Recommended-action labels (already English)
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
        "🚨 **{month}** — contribution margin dropped to **{cm}** "
        "(cost center {cc_id} · {cc_name}). {labor}{hours}. "
        "👉 Open **Deep dive** for driver decomposition and AI explanation."
    ),
    "portfolio.dq_banner": (
        "📊 **Data quality — {month}:** revenue {rev} is {ratio:.1f}× the trailing "
        "12-month average. {note}. "
        "This month is excluded from the anomaly ranking to avoid false alerts."
    ),

    # Deep Dive
    "deepdive.title": "Deep dive",
    "deepdive.subtitle": "Pick a cost center → see driver decomposition and AI explanation.",
    "deepdive.cost_center": "Cost center",
    "deepdive.baseline": "Baseline",
    "deepdive.baseline_prior_month": "vs. prior month",
    "deepdive.baseline_prior_year": "vs. prior year",
    "deepdive.baseline_plan": "vs. plan",
    "deepdive.period": "Analysis period",
    "deepdive.no_data": "No data for this cost center.",
    "deepdive.no_baseline": "No baseline available for \"{mode}\". Please pick a different comparison.",
    "deepdive.timeline_title": "Contribution margin timeline · cost center {cc}",
    "deepdive.waterfall_title": "ΔCM vs. {baseline} = {delta}",
    "deepdive.kpi_peers": "KPIs vs. regional peers",
    "deepdive.kpi_peers_empty": "Not enough comparison data for peers.",
    "deepdive.ai_title": "AI explanation",
    "deepdive.ai_preview": "The AI classifies the variance (operational vs. data artifact), names the top 3 root causes and suggests concrete actions.",
    "deepdive.ai_asking": "Asking Claude…",
    "deepdive.ai_hint": "Click above to generate a structured explanation.",
    "deepdive.download": "Download as comment",
    "deepdive.residual_warn": "Note: part of the variance ({pct:.0%}) could not be cleanly attributed to a driver. The driver analysis shows the main effects, not every individual booking.",

    # Early Warnings
    "warnings.title": "Early warnings",
    "warnings.subtitle": "Proactive, rule-based risk signals on the latest data per cost center.",
    "warnings.none": "✓ No early warnings with the current filters.",
    "warnings.rules_title": "Which rules do we check?",
    "warnings.rules_body": (
        "- **CM trend declining** — contribution margin has fallen for 3 months and sits below plan.\n"
        "- **Absence spike** — absence rate > 2 σ above its own average.\n"
        "- **Productivity drop** — productivity < 70 % and still falling.\n"
        "- **Subcontractor creep** — subcontractor share > 10 percentage points above plan.\n"
        "- **Contract ending in < 90 days** — renewal risk on active contracts.\n"
        "- **Plan gap widening** — the gap to plan grows two months in a row."
    ),
    "warnings.pick": "Pick a warning",
    "warnings.action_title": "Action plan for the selected warning",
    "warnings.ai_button": "Show AI action plan",
    "warnings.no_history": "No history available.",
    "warnings.not_enough_history": "Not enough history for a baseline.",

    # Signal labels
    "signal.Declining CM trend": "Declining CM trend",
    "signal.Absence spike": "Absence spike",
    "signal.Productivity drop": "Productivity drop",
    "signal.Subcontractor creep": "Subcontractor creep",
    "signal.Contract renewal risk": "Contract renewal risk",
    "signal.Plan gap widening": "Plan gap widening",

    # Severity labels
    "severity.high": "High",
    "severity.medium": "Medium",
    "severity.low": "Low",

    # Chat
    "chat.title": "Financial copilot chat",
    "chat.subtitle": "Ask questions in natural language about the filtered data.",
    "chat.try_asking": "Try asking:",
    "chat.examples": (
        "- Which region currently has the weakest contribution margin, and why?\n"
        "- Ranking of the 3 cost centers with the largest plan gap — what do they have in common?\n"
        "- Which service type carries the largest absolute margin risk?\n"
        "- If productivity in the bottom quartile rises by 10 %, how much contribution margin would that free up?"
    ),
    "chat.input_placeholder": "Ask the copilot…",
    "chat.thinking": "Thinking…",
    "chat.clear": "Reset chat",

    # Plan vs Actual
    "pva.title": "Plan vs. actual — monthly variance",
    "pva.subtitle": "Monthly comparison of actual and planned contribution margin with euro and percent variance.",
    "pva.missing_cols": "Columns `cm_planned` / `cm_db` missing — variance cannot be computed.",
    "pva.bar_title": "Monthly CM variance (actual − plan, €)",
    "pva.chart_caption": "Months with variance < −50,000 € are red, > +50,000 € green.",
    "pva.table_title": "Monthly variance table",
    "pva.col.month": "Month",
    "pva.col.revenue": "Revenue",
    "pva.col.planned": "Planned CM",
    "pva.col.actual": "Actual CM",
    "pva.col.gap_eur": "Gap €",
    "pva.col.gap_pct": "Gap %",
    "pva.table_caption": (
        "Rows are highlighted **red** when actual CM missed plan by more than 50 k€; "
        "**green** when it beat plan by more than 50 k€. "
        "Large positive outliers may indicate booking accruals — see the data-quality note on the Portfolio overview."
    ),

    # Data source / errors
    "data.no_data_warn": "👈 **Getting started:** drop `Dataset_anoym.xlsx` into the `data/` folder or upload the file via the sidebar.",
    "data.no_data_page": "Please load the dataset on the home page.",
    "data.place_or_upload": "Drop `Dataset_anoym.xlsx` into `./data/` or upload it above.",
    "data.load_failed": "Load failed: {err}",
    "data.schema_ok": "✓ Schema: {m}/{t} columns detected",
    "data.schema_position": "⚠ Schema: {m}/{t} columns (mapped by column position — no German headers found). Please re-export with the original header row.",
    "data.schema_error": "❌ Schema: {m}/{t} columns detected\n\nMissing critical columns: **{missing}**\n\nWithout these columns the app cannot compute. Please check the source file's headers.",
    "data.optional_missing": "{n} optional columns missing",
    "data.extra_ignored": "{n} extra columns ignored",
    "data.stats": "{rows:,} rows · {ccs} cost centers · {pmin} → {pmax}",

    # Actions
    "action.generate_explanation": "Show AI explanation",
    "action.download": "Download",
    "action.open_deepdive": "Open deep dive →",
    "action.details": "Show details",
}


SUPPORTED: dict[str, dict[str, str]] = {"de": de, "en": en}


def get_lang() -> str:
    """Return the active UI language, defaulting to German.

    Imports streamlit lazily so this module stays import-cheap and works
    outside of a Streamlit script context (e.g. unit tests).
    """
    try:
        import streamlit as st
        return st.session_state.get("lang", DEFAULT_LANG)
    except Exception:  # noqa: BLE001
        return DEFAULT_LANG


def t(key: str, **fmt) -> str:
    """Translate a key in the active language.

    Falls back to German if the key is missing in the active catalog, and to
    the key itself if missing in German too (so gaps stay visible in the UI).
    """
    catalog = SUPPORTED.get(get_lang(), de)
    val = catalog.get(key) or de.get(key, key)
    if fmt:
        try:
            return val.format(**fmt)
        except (KeyError, IndexError):
            return val
    return val
