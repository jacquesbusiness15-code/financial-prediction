"""German + English string catalogs for the WISAG Financial Co-Pilot UI."""
from __future__ import annotations

DEFAULT_LANG = "de"

de: dict[str, str] = {
    # App-level
    "app.title": "WISAG Finanz-Copilot",
    "app.subtitle": "Ihre KI für Marge, Risiken und Maßnahmen.",
    "app.welcome": "Willkommen zurück",
    "app.welcome_sub": "Ihr Überblick auf einen Blick.",

    # Navigation
    "nav.home": "Startseite",
    "nav.portfolio": "Überblick",
    "nav.deepdive": "Details",
    "nav.warnings": "Warnungen",
    "nav.chat": "KI fragen",
    "nav.plan_vs_actual": "Plan vs. Ist",
    "nav.open": "Öffnen",

    # Nav card descriptions (kept for the legacy nav_card; nav_tile doesn't use them)
    "nav.portfolio.desc": "Alle Standorte auf einen Blick.",
    "nav.deepdive.desc": "Einen Standort genau ansehen.",
    "nav.warnings.desc": "Risiken nach Euro-Wirkung.",
    "nav.chat.desc": "Fragen in eigenen Worten stellen.",
    "nav.plan_vs_actual.desc": "Monat für Monat: Ist vs. Plan.",

    # Topbar / settings popover
    "topbar.back_home": "Zurück zur Übersicht",
    "topbar.settings": "Einstellungen",
    "topbar.settings_tip": "Datenquelle und API-Status",

    # Landing status card
    "landing.status_title": "Portfolio-Status",
    "landing.status_sub": "Stand heute",
    "landing.status_margin": "Marge",
    "landing.status_gap": "vs. Plan",
    "landing.cta_overview": "Überblick",
    "landing.cta_details": "Details",
    "landing.cta_alerts": "Warnungen",

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
    "kpi.cm": "Marge",
    "kpi.cm_planned": "Plan-Marge",
    "kpi.plan_gap": "vs. Plan",
    "kpi.cost_centers": "Standorte",
    "kpi.anomalies": "Auffälligkeiten",
    "kpi.total_actual": "Ist gesamt",
    "kpi.total_planned": "Plan gesamt",
    "kpi.total_gap": "Abweichung",
    "kpi.worst_month": "Schwächster Monat",
    "kpi.eur_at_stake": "€ im Risiko",
    "kpi.high_severity": "Hoch",
    "kpi.medium_severity": "Mittel",
    "kpi.low_severity": "Niedrig",

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
    "portfolio.actions_empty": "Keine unmittelbaren Maßnahmen erforderlich — Portfolio in gutem Zustand.",
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

    # Facility-focus overview
    "overview.back": "‹ Zurück zur Übersicht",
    "overview.section_title": "Überblick",
    "overview.cat.revenue": "Gesamtumsatz",
    "overview.cat.costs": "Gesamtkosten",
    "overview.cat.cm": "Gesamt-Deckungsbeitrag",
    "overview.trend_sub": "Letzte 12 Monate — mit Regressionslinie",
    "overview.period_label": "Zeitraum",
    "overview.export": "Exportieren",
    "overview.margin": "Marge",
    "overview.change_mom": "Veränderung ggü. Vormonat",
    "overview.cost_total": "Gesamtkosten",
    "overview.cost_mom": "Kosten vs. Vormonat",
    "overview.why_drop": "Warum ist die Marge gefallen?",
    "overview.why_drop_sub": "Wichtigste Faktoren ggü. Vormonat",
    "overview.cost_causes_title": "Was hat die Kosten erhöht?",
    "overview.cost_causes_sub": "Größte Kostensteigerungen zum Vormonat",
    "overview.what_do": "Was können wir tun?",
    "overview.what_do_sub": "Empfohlene Maßnahmen",
    "overview.solutions_title": "Maßnahmen zur Kostensenkung",
    "overview.solutions_sub": "Geschätzter Margeneffekt und Begründung",
    "overview.potential_impact": "Potenzielle Wirkung",
    "overview.view_all_drivers": "Alle Treiber anzeigen ›",
    "overview.view_all_actions": "Alle Maßnahmen anzeigen ›",
    "overview.whatif": "Was wäre wenn?",
    "overview.whatif_sub": "So wirken sich Änderungen auf die Marge aus",
    "overview.team_size": "Teamgröße",
    "overview.employees": "Mitarbeitende",
    "overview.productivity_gain": "{p} Produktivität",
    "overview.new_margin": "Neue Marge",
    "overview.vs_current": "{p} ggü. aktuell",
    "overview.explore_more": "Weitere Szenarien testen",
    "overview.explore_more_sub": "Verschiedene Kombinationen testen und die potenzielle Wirkung sehen.",
    "overview.data_updated": "Daten zuletzt aktualisiert: {ts}",
    "overview.status.critical": "Kritisch",
    "overview.status.warn": "Beobachten",
    "overview.status.healthy": "Gesund",
    "overview.no_focus": "Keine Kostenstelle im aktuellen Filter verfügbar.",
    "overview.no_baseline": "Kein Vormonat als Vergleichsbasis verfügbar.",
    "overview.evolution_title": "Margen-Trend",
    "overview.evolution_sub": "Letzte 6 Monate — Deckungsbeitrag %",

    # Custom sidebar nav
    "nav.overview_short": "Übersicht",
    "nav.analytics_short": "Analyse",
    "nav.forecasts_short": "Prognosen",
    "nav.scenarios_short": "Szenarien",
    "nav.reports_short": "Berichte",
    "nav.alerts_short": "Warnungen",
    "nav.settings_short": "Einstellungen",
    "nav.ask_ai": "KI fragen",

    # Driver labels (facility-focus cards)
    "driver.labor": "Höhere Personalkosten",
    "driver.labor.sub": "Personalkosten insgesamt gestiegen",
    "driver.labor.cause": "Überstunden, Schichtzuschläge oder Personalaufbau haben die Lohnkosten erhöht.",
    "driver.absence": "Mehr Ausfallzeiten",
    "driver.absence.sub": "Mehr Kranken- und Urlaubstage",
    "driver.absence.cause": "Kranken- und Urlaubskosten sind diesen Monat gestiegen.",
    "driver.training": "Schulung & Einarbeitung",
    "driver.training.sub": "Mehr Neueinstellungen und Schulungsstunden",
    "driver.training.cause": "Höhere Ausbildungs- und Einarbeitungskosten als im Vormonat.",
    "driver.subcontractor": "Mehr Fremdleistungen",
    "driver.subcontractor.sub": "Höherer Anteil externer Leistungen",
    "driver.subcontractor.cause": "Mehr Leistungen an Nachunternehmer zu höherem Satz.",
    "driver.material": "Höhere Materialkosten",
    "driver.material.sub": "Materialverbrauch gestiegen",
    "driver.material.cause": "Verbrauchsmaterial und Materialeinsatz sind gestiegen.",
    "driver.vehicle": "Höhere Fahrzeugkosten",
    "driver.vehicle.sub": "Fuhrpark- und Reisekosten gestiegen",
    "driver.vehicle.cause": "Fuhrpark, Kraftstoff oder Reisekosten sind gestiegen.",
    "driver.revenue": "Umsatzrückgang",
    "driver.revenue.sub": "Weniger abgerechneter Umsatz",
    "driver.revenue_up": "Umsatzwachstum",
    "driver.revenue_up.sub": "Mehr abgerechneter Umsatz",
    "driver.other": "Sonstige Kostenbewegungen",
    "driver.other.sub": "Summe verbleibender Kostenarten",
    "driver.other.cause": "Kleinere Kostenpositionen haben in Summe die Gesamtkosten erhöht.",

    # Recommended-action labels
    "action.shift.title": "Schichtplanung optimieren",
    "action.shift.sub": "Überstunden senken und Abdeckung verbessern",
    "action.shift.why": "Schichten an den Bedarf anpassen reduziert unproduktive Lohnstunden.",
    "action.absence.title": "Ausfallzeiten reduzieren",
    "action.absence.sub": "Bindungs- und Gesundheitsprogramme stärken",
    "action.absence.why": "Weniger Ausfälle halten die Arbeit im Plan ohne Überstunden.",
    "action.onboarding.title": "Einarbeitung effizienter gestalten",
    "action.onboarding.sub": "Produktivität neuer Mitarbeitender schneller heben",
    "action.onboarding.why": "Schnellere Einarbeitung verkürzt bezahlte, aber unproduktive Zeit.",
    "action.subcontractor.title": "Fremdleistungsanteil senken",
    "action.subcontractor.sub": "Eigenleistung ausbauen, externe Kosten senken",
    "action.subcontractor.why": "Eigenleistung statt Nachunternehmer vermeidet deren Aufschläge.",
    "action.pricing.title": "Preise und Vertragskonditionen prüfen",
    "action.pricing.sub": "Margenschwache Verträge nachverhandeln",
    "action.pricing.why": "Abrechnung an Ist-Kosten ausrichten schützt die Vertragsmarge.",
    "action.productivity.title": "Produktivität steigern",
    "action.productivity.sub": "Prozesse und Schichtauslastung verbessern",
    "action.productivity.why": "Höherer Output je Lohnstunde senkt die Stückkosten.",
    "portfolio.worst_banner": (
        "**{month}** — Deckungsbeitrag eingebrochen auf **{cm}** "
        "(Kostenstelle {cc_id} · {cc_name}). {labor}{hours}. "
        "Öffnen Sie die **Detailanalyse** für Treiberzerlegung und KI-Erklärung."
    ),
    "portfolio.dq_banner": (
        "**Datenqualität — {month}:** Umsatz {rev} ist das {ratio:.1f}× des "
        "gleitenden 12-Monats-Mittels. {note}. "
        "Dieser Monat wird aus der Auffälligkeits-Rangliste ausgeschlossen, um Fehlalarme zu vermeiden."
    ),

    # Deep Dive
    "deepdive.title": "Details",
    "deepdive.subtitle": "Standort wählen · Was sich verändert hat · Maßnahmen.",
    "deepdive.cost_center": "Standort",
    "deepdive.baseline": "Vergleich",
    "deepdive.baseline_prior_month": "Vormonat",
    "deepdive.baseline_prior_year": "Vorjahr",
    "deepdive.baseline_plan": "Plan",
    "deepdive.period": "Zeitraum",
    "deepdive.no_data": "Keine Daten für diesen Standort.",
    "deepdive.no_baseline": "Kein Vergleich »{mode}« verfügbar.",
    "deepdive.timeline_title": "Margen-Verlauf",
    "deepdive.waterfall_title": "Was sich verändert hat · {delta}",
    "deepdive.kpi_peers": "Vergleich mit der Region",
    "deepdive.kpi_peers_empty": "Nicht genügend Vergleichsdaten.",
    "deepdive.ai_title": "KI-Erklärung",
    "deepdive.ai_preview": "Top-Ursachen und Maßnahmen in Klartext.",
    "deepdive.ai_asking": "Frage Claude…",
    "deepdive.ai_hint": "Klicken Sie oben, um eine Erklärung zu generieren.",
    "deepdive.download": "Als Kommentar herunterladen",
    "deepdive.residual_warn": "Hinweis: {pct:.0%} der Veränderung konnte keinem einzelnen Faktor zugeordnet werden.",
    "deepdive.section_changed": "Was sich verändert hat",
    "deepdive.section_peers": "Vergleich mit der Region",
    "deepdive.peer_median_label": "Peer-Median: {v}",
    "deepdive.show_details": "Details anzeigen",

    # Early Warnings
    "warnings.title": "Warnungen",
    "warnings.subtitle": "Risiken, sortiert nach Euro-Wirkung.",
    "warnings.none": "Keine Warnungen mit den aktuellen Filtern.",
    "warnings.pick": "Warnung wählen",
    "warnings.action_title": "Maßnahmen für diese Warnung",
    "warnings.ai_button": "Maßnahmen anzeigen",
    "warnings.no_history": "Keine Historie verfügbar.",
    "warnings.not_enough_history": "Nicht genügend Historie für einen Vergleich.",
    "warnings.at_risk": "€ im Risiko",

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
    "chat.title": "Ask AI",
    "chat.subtitle": "Fragen Sie in eigenen Worten.",
    "chat.try_asking": "Beispiele",
    "chat.chip_weakest": "Wo ist die Marge am schwächsten — und warum?",
    "chat.chip_plan_gap": "Top-3 Standorte mit der größten Plan-Abweichung",
    "chat.chip_productivity": "Was bringt +10 % Produktivität im unteren Quartil?",
    "chat.input_placeholder": "Ihre Frage…",
    "chat.thinking": "Denke nach…",
    "chat.clear": "Chat zurücksetzen",

    # Floating copilot dock
    "copilot.placeholder": "Frag zu deinen Verträgen…",
    "copilot.mic_hint": "Wispr-Flow-Taste drücken zum Diktieren",
    "copilot.empty_greeting": "Hallo. Fragen Sie mich zu Ihrem Portfolio.",
    "copilot.send": "Senden",
    "copilot.mic": "Diktieren",
    "copilot.read_aloud": "Vorlesen",
    "copilot.stop_reading": "Vorlesen stoppen",
    "copilot.error_no_key": "Anthropic-API-Key fehlt. ANTHROPIC_API_KEY in .env setzen.",

    # Plan vs Actual
    "pva.title": "Ist vs. Plan",
    "pva.subtitle": "Monat für Monat.",
    "pva.missing_cols": "Spalten fehlen — Abweichung kann nicht berechnet werden.",
    "pva.bar_title": "Ist vs. Plan pro Monat",
    "pva.bar_sub": "Grün = über Plan · Rot = unter Plan",
    "pva.table_title": "Monatsvergleich",
    "pva.col.month": "Monat",
    "pva.col.revenue": "Umsatz",
    "pva.col.planned": "Plan",
    "pva.col.actual": "Ist",
    "pva.col.gap_eur": "Differenz",
    "pva.col.gap_pct": "Differenz %",
    "pva.legend.beat": "Über Plan (> +50 k€)",
    "pva.legend.miss": "Unter Plan (< −50 k€)",

    # Upload page (shown when no dataset is present yet)
    "upload.title": "Datensatz hochladen",
    "upload.subtitle": "Laden Sie Ihre WISAG-Exportdatei, um den Co-Pilot zu starten. Marge, Treiber und Warnungen werden automatisch berechnet.",
    "upload.cta": "Datei auswählen oder hierher ziehen",
    "upload.cta_help": "Unterstützte Formate: .xlsx, .xls, .csv",
    "upload.requirements_title": "Was wir erwarten",
    "upload.requirements_sub": "Damit die Analyse funktioniert, sollte die Datei diese Merkmale haben.",
    "upload.req_xlsx.title": "Excel- oder CSV-Export",
    "upload.req_xlsx.sub": ".xlsx, .xls oder .csv — direkt aus Ihrem ERP.",
    "upload.req_headers.title": "Originale Spaltenüberschriften",
    "upload.req_headers.sub": "Deutsche Kopfzeilen wie Jahr, Monat, KST, Ges_Ums, DB.",
    "upload.req_period.title": "Monatliche Datensätze",
    "upload.req_period.sub": "Mindestens zwei Monate pro Kostenstelle für Vergleiche.",
    "upload.success": "Datensatz geladen — Dashboard wird aktualisiert.",
    "upload.schema_failed": "Schemaprüfung fehlgeschlagen: {msg}",
    "upload.sample_hint": "Kein Datensatz zur Hand? Legen Sie `Dataset_anoym.xlsx` im Ordner `data/` ab.",

    # Data source / errors
    "data.no_data_warn": "**So starten Sie:** Legen Sie `Dataset_anoym.xlsx` im Ordner `data/` ab oder laden Sie die Datei über die Seitenleiste hoch.",
    "data.no_data_page": "Bitte laden Sie den Datensatz auf der Startseite.",
    "data.place_or_upload": "`Dataset_anoym.xlsx` im Ordner `./data/` ablegen oder oben hochladen.",
    "data.load_failed": "Laden fehlgeschlagen: {err}",
    "data.schema_ok": "Schema: {m}/{t} Spalten erkannt",
    "data.schema_position": "Schema: {m}/{t} Spalten (Zuordnung über Spaltenposition — keine deutschen Überschriften gefunden). Export bitte mit Originalkopfzeile wiederholen.",
    "data.schema_error": "Schema: {m}/{t} Spalten erkannt\n\nFehlende kritische Spalten: **{missing}**\n\nOhne diese Spalten kann die App nicht rechnen. Bitte Überschriften der Quelldatei prüfen.",
    "data.optional_missing": "{n} optionale Spalten fehlen",
    "data.extra_ignored": "{n} zusätzliche Spalten ignoriert",
    "data.stats": "{rows:,} Zeilen · {ccs} Kostenstellen · {pmin} → {pmax}",

    # Actions
    "action.generate_explanation": "KI-Erklärung anzeigen",
    "action.download": "Herunterladen",
    "action.open_deepdive": "Detailanalyse öffnen →",
    "action.details": "Details anzeigen",

    # --- Analytics page ---
    "analytics.title": "Analytics",
    "analytics.subtitle": "Portfolio-Überblick: Heatmap, Anomalien und Umsatztreiber.",
    "analytics.kpi.revenue": "Gesamtumsatz",
    "analytics.kpi.margin": "Portfolio-Marge",
    "analytics.kpi.sites": "Kostenstellen",
    "analytics.kpi.anomalies": "Anomalien",
    "analytics.heatmap.title": "Margen-Heatmap",
    "analytics.heatmap.sub": "CM% nach Region × Monat.",
    "analytics.heatmap.empty": "Nicht genug Daten für die Heatmap.",
    "analytics.anomalies.title": "Top-Anomalien",
    "analytics.anomalies.sub": "Gefiltert und geordnet nach €-Wirkung.",
    "analytics.anomalies.empty": "Keine Anomalien erkannt.",
    "analytics.leaders.title": "Umsatzführer",
    "analytics.leaders.sub": "Stärkster Umsatzzuwachs ggü. Vormonat.",
    "analytics.laggards.title": "Umsatzverlierer",
    "analytics.laggards.sub": "Größter Umsatzrückgang ggü. Vormonat.",

    # --- Forecasts page ---
    "forecasts.title": "Prognosen",
    "forecasts.subtitle": "Einfache Trendprojektion der Marge auf Basis historischer Daten.",
    "forecasts.horizon": "Horizont",
    "forecasts.horizon.3": "3 Monate",
    "forecasts.horizon.6": "6 Monate",
    "forecasts.horizon.12": "12 Monate",
    "forecasts.scope": "Bereich",
    "forecasts.scope.portfolio": "Portfolio",
    "forecasts.scope.cost_center": "Einzelne Kostenstelle",
    "forecasts.chart.title": "Margenverlauf & Projektion",
    "forecasts.chart.sub": "Historie (blau) + Prognose mit Vertrauensband.",
    "forecasts.trajectory.title": "Erwartete Entwicklung je Kostenstelle",
    "forecasts.trajectory.sub": "Erwartete Δ Marge über den Horizont.",
    "forecasts.col.cost_center": "Kostenstelle",
    "forecasts.col.current": "Aktuelle Marge",
    "forecasts.col.projected": "Projizierte Marge",
    "forecasts.col.delta": "Δ Marge",
    "forecasts.col.direction": "Tendenz",
    "forecasts.direction.up": "steigend",
    "forecasts.direction.flat": "stabil",
    "forecasts.direction.down": "fallend",
    "forecasts.methodology.title": "Methodik",
    "forecasts.methodology.body": "Lineare Regression auf den letzten 12 Monaten plus einfacher Saison-Mittelwert. Keine ML-Prognose — diese Ansicht ist bewusst einfach und dient als Orientierung, nicht als Entscheidungsgrundlage.",
    "forecasts.empty": "Nicht genügend Historie für eine Prognose.",

    # --- Scenarios page ---
    "scenarios.title": "Szenarien",
    "scenarios.subtitle": "Mehrere Hebel gleichzeitig bewegen und die Margenwirkung sehen.",
    "scenarios.picker.label": "Kostenstelle",
    "scenarios.levers.title": "Hebel",
    "scenarios.levers.sub": "Regler bewegen — alle Werte sind Deltas gegenüber dem aktuellen Monat.",
    "scenarios.lever.headcount": "Mitarbeitende",
    "scenarios.lever.headcount.help": "Absolute Zahl Mitarbeitender für das neue Szenario.",
    "scenarios.lever.absence": "Ausfallquote Δ",
    "scenarios.lever.absence.help": "Prozentpunkte-Veränderung der Ausfallquote.",
    "scenarios.lever.rate": "Abrechnungssatz Δ",
    "scenarios.lever.rate.help": "Prozentuale Veränderung des durchschnittlichen Abrechnungssatzes.",
    "scenarios.lever.subco": "Fremdleistungsanteil Δ",
    "scenarios.lever.subco.help": "Prozentpunkte-Veränderung des Subunternehmer-Anteils.",
    "scenarios.reset": "Zurücksetzen",
    "scenarios.result.title": "Ergebnis",
    "scenarios.result.new_margin": "Neue Marge",
    "scenarios.result.delta_margin": "Δ Marge",
    "scenarios.result.delta_cm": "Δ Deckungsbeitrag",
    "scenarios.waterfall.title": "Beiträge je Hebel",
    "scenarios.waterfall.sub": "So viel Margenwirkung hat jeder Hebel.",
    "scenarios.waterfall.empty": "Noch kein Hebel bewegt.",

    # --- Reports page ---
    "reports.title": "Berichte",
    "reports.subtitle": "Plan vs. Ist und exportierbare Snapshots.",
    "reports.scope": "Bereich",
    "reports.scope.portfolio": "Portfolio",
    "reports.scope.region": "Region",
    "reports.scope.cost_center": "Kostenstelle",
    "reports.range.from": "Von",
    "reports.range.to": "Bis",
    "reports.pva.title": "Plan vs. Ist",
    "reports.pva.sub": "Monatliche Gegenüberstellung von Plan und tatsächlichem Umsatz.",
    "reports.pva.col.month": "Monat",
    "reports.pva.col.revenue": "Umsatz",
    "reports.pva.col.plan": "Plan",
    "reports.pva.col.actual": "Ist",
    "reports.pva.col.gap_eur": "Lücke €",
    "reports.pva.col.gap_pct": "Lücke %",
    "reports.waterfall.title": "Treiber (Ist vs. Plan)",
    "reports.waterfall.sub": "Beiträge der einzelnen Treiber zur Gesamtabweichung.",
    "reports.export.title": "Export",
    "reports.export.sub": "Aktuelle Auswahl als Datei herunterladen.",
    "reports.export.csv": "CSV herunterladen",
    "reports.export.xlsx": "Excel herunterladen",

    # --- Alerts page ---
    "alerts.title": "Warnungen",
    "alerts.subtitle": "Frühwarnungen aus Regeln und Statistik, geordnet nach €-Wirkung.",
    "alerts.filter.severity": "Schweregrad",
    "alerts.filter.severity.all": "Alle",
    "alerts.filter.severity.high": "Hoch",
    "alerts.filter.severity.medium": "Mittel",
    "alerts.filter.severity.low": "Niedrig",
    "alerts.filter.scope": "Bereich",
    "alerts.filter.scope.all": "Alle Kostenstellen",
    "alerts.filter.scope.region": "Aktuelle Region",
    "alerts.empty": "Aktuell keine aktiven Warnungen — alles im grünen Bereich.",
    "alerts.count": "{n} Warnung(en)",
    "alerts.detail.title": "Details",
    "alerts.detail.ai_title": "Empfohlener Maßnahmenplan",
    "alerts.detail.ai_wait": "Claude analysiert…",
    "alerts.detail.ai_fallback": "Keine KI verfügbar — Vorlage wird verwendet.",
    "alerts.detail.open_scenario": "In Szenarien öffnen →",
    "alerts.detail.close": "Schließen",

    # --- Settings page ---
    "settings.title": "Einstellungen",
    "settings.subtitle": "Sprache, Datenquelle und Cache verwalten.",
    "settings.language.title": "Sprache",
    "settings.language.sub": "Beeinflusst alle Seiten sofort.",
    "settings.data.title": "Datenquelle",
    "settings.data.sub": "Aktuell geladene Datei und Statistiken.",
    "settings.data.path": "Pfad",
    "settings.data.rows": "Zeilen",
    "settings.data.modified": "Zuletzt geändert",
    "settings.data.upload": "Neuen Datensatz hochladen",
    "settings.cache.title": "Cache",
    "settings.cache.sub": "Alle zwischengespeicherten Berechnungen und Daten verwerfen.",
    "settings.cache.clear": "Cache leeren",
    "settings.cache.cleared": "Cache geleert.",
    "settings.about.title": "Über",
    "settings.about.sub": "App-Informationen.",
    "settings.about.version": "Version",
    "settings.about.commit": "Commit",
    "settings.about.web": "Next.js-Frontend unter `web/`",

    # --- Portfolio ranking table (new landing view) ---
    "portfolio.header": "Verträge",
    "portfolio.header_sub": "Verträge nach Unrentabilität — am stärksten unrentable oben.",
    "portfolio.search_placeholder": "Vertrag, Kunde oder Kostenstelle suchen…",
    "portfolio.filters": "Filter",
    "portfolio.filters_reset": "Filter zurücksetzen",
    "portfolio.filter_region": "Region",
    "portfolio.filter_month": "Zeitraum",
    "portfolio.filter_client": "Kunde",
    "portfolio.filter_branch": "Branche",
    "portfolio.filter_reason": "Grund",
    "portfolio.filter_cost_center": "Kostenstelle",
    "portfolio.show_profitable": "Auch rentable Verträge anzeigen",
    "portfolio.kpi_total_unprofit": "Gesamte Unrentabilität",
    "portfolio.kpi_total_unprofit_sub": "Summe über sichtbare Verträge",
    "portfolio.kpi_longest_unprofit": "Längste Unrentabilität",
    "portfolio.kpi_longest_unprofit_sub": "{name} · seit {since}",
    "portfolio.kpi_longest_unit": "{n} Monate",
    "portfolio.kpi_longest_unit_one": "{n} Monat",
    "portfolio.kpi_none": "—",
    "portfolio.table_contract": "Vertrag",
    "portfolio.table_client": "Kunde",
    "portfolio.table_region": "Region",
    "portfolio.table_branch": "Branche",
    "portfolio.table_cost_center": "Kostenstelle",
    "portfolio.table_unprofit": "Unrentabilität (€)",
    "portfolio.table_since": "Unrentabel seit",
    "portfolio.table_months": "Monate",
    "portfolio.table_reason": "Größter Grund",
    "portfolio.col_contract": "Vertrag",
    "portfolio.col_biggest_unprofit": "Größte Unrentabilität",
    "portfolio.col_longest_unprofit": "Längste Unrentabilität",
    "portfolio.col_biggest_reason": "Größter Grund",
    "portfolio.col_trend": "DB-Trend",
    "portfolio.col_trend_sub": "pp/Monat (6M)",
    "portfolio.tooltip_sub": "Deckungsbeitrag — Veränderung ggü. Vormonat (%)",
    "portfolio.empty_all_profitable": "Keine unrentablen Verträge mit diesen Filtern — alle Verträge im grünen Bereich.",
    "portfolio.empty_no_contracts": "Keine Verträge im aktuellen Filter.",
    "portfolio.open_contract_hint": "Zeile anklicken, um einen Vertrag im Detail zu öffnen.",
    "portfolio.open_contract": "Vertrag öffnen",

    # --- Contracts category tabs (Overall / Profitability / Revenue / Cost / Efficiency / Stability) ---
    "contracts.tab.overall": "Gesamt",
    "contracts.tab.profitability": "Rentabilität",
    "contracts.tab.revenue_trend": "Umsatzentwicklung",
    "contracts.tab.cost_structure": "Kostenstruktur",
    "contracts.tab.efficiency": "Effizienz",
    "contracts.tab.stability": "Stabilität",

    # Overall tab columns
    "contracts.col.score_profitability": "Rentabilität",
    "contracts.col.score_cost": "Kostenstruktur",
    "contracts.col.score_efficiency": "Effizienz",
    "contracts.col.score_stability": "Stabilität",
    "contracts.col.score_overall": "Gesamtbewertung",

    # Profitability tab columns
    "contracts.col.unrent_mom": "Unrentabilität ggü. Vormonat",
    "contracts.col.unrent_6m": "Unrentabilität ggü. 6 Monaten",
    "contracts.col.top_cost_increase_cat": "Kostenart mit grösstem Anstieg",
    "contracts.col.trend_mom": "Trend ggü. Vormonat",

    # Revenue trend tab columns
    "contracts.col.revenue_mom": "Umsatz ggü. Vormonat",
    "contracts.col.revenue_6m": "Umsatz ggü. 6 Monaten",
    "contracts.col.top_decline_stream": "Schwächster Umsatzstrom",
    "contracts.col.revenue_trend": "Umsatztrend",
    "contracts.col.revenue_trend.down": "Rückläufig",
    "contracts.col.revenue_trend.flat": "Stabil",
    "contracts.col.revenue_trend.up": "Steigend",
    "contracts.col.revenue_trend.no_data": "—",

    # Revenue stream labels
    "revenue_stream.fixed": "Pauschal",
    "revenue_stream.hourly": "Stunden",
    "revenue_stream.other": "Sonstige",

    # Cost structure tab columns
    "contracts.col.top_cost_cat": "Höchste Kosten",
    "contracts.col.cost_highest_increase": "Stärkster Kostenanstieg",
    "contracts.col.cost_highest_increase_pct": "Anstieg (%)",
    "contracts.col.total_cost_increase_pct": "Gesamtkostenanstieg (%)",

    # Efficiency tab columns
    "contracts.col.hours_plan_minus_prod": "Soll − Produktivstunden",
    "contracts.col.ratio_mom": "Verhältnis ggü. Vormonat",
    "contracts.col.ratio_6m": "Verhältnis ggü. 6 Monaten",
    "contracts.col.hour_variance": "Stundenabweichung",

    # Stability tab columns
    "contracts.col.duration": "Laufzeit",
    "contracts.col.cm_variance": "DB-Varianz",
    "contracts.col.long_short": "Laufzeittyp",
    "contracts.col.revenue_variance": "Umsatzvarianz",

    # Shared labels
    "contracts.duration_months": "{n} Monate",
    "contracts.long_term": "Langfristig",
    "contracts.short_term": "Kurzfristig",
    "contracts.no_data": "—",
    "contracts.trend_up": "verschlechtert",
    "contracts.trend_down": "verbessert",
    "contracts.trend_flat": "stabil",

    # Cost category labels
    "cost_cat.labor": "Personal",
    "cost_cat.subcontractor": "Fremdleistung",
    "cost_cat.internal_service": "Interne Leistung",
    "cost_cat.travel": "Fahrkosten",
    "cost_cat.material": "Material",
    "cost_cat.vehicle": "Fahrzeug",

    # Short reason labels (for filter chips + table cell)
    "reason.labor": "Personal",
    "reason.absence": "Ausfallzeiten",
    "reason.training": "Einarbeitung",
    "reason.subcontractor": "Fremdleistung",
    "reason.material": "Material",
    "reason.vehicle": "Fuhrpark",
    "reason.revenue": "Umsatz",
    "reason.other": "Sonstiges",
    "reason.none": "—",

    # Solution Finder
    "solutions.title": "Empfohlene Massnahmen",
    "solutions.subtitle": "Top-Massnahmen nach Euro-Wirkung pro Aufwand",
    "solutions.col.action": "Massnahme",
    "solutions.col.why": "Begruendung",
    "solutions.col.impact": "Wirkung (EUR/Monat)",
    "solutions.col.owner": "Verantwortlich",
    "solutions.col.timeframe": "Zeitrahmen (Wochen)",
    "solutions.col.confidence": "Sicherheit",
    "solutions.col.category": "Kategorie",
    "solutions.owner.ops": "Betrieb",
    "solutions.owner.sales": "Vertrieb",
    "solutions.owner.regional_manager": "Regionalleitung",
    "solutions.status.proposed": "Vorgeschlagen",
    "solutions.status.in_progress": "In Umsetzung",
    "solutions.status.done": "Abgeschlossen",
    "solutions.status.abandoned": "Verworfen",
    "solutions.btn.mark_proposed": "Als vorgeschlagen markieren",
    "solutions.btn.mark_in_progress": "In Umsetzung",
    "solutions.btn.mark_done": "Abschliessen",
    "solutions.btn.mark_abandoned": "Verwerfen",
    "solutions.confidence.low": "niedrig",
    "solutions.confidence.med": "mittel",
    "solutions.confidence.high": "hoch",
    "solutions.empty": "Keine Massnahmen noetig.",
    "solutions.cohort_note": "Benchmark: {scope}, n={size}",
    "solutions.llm_narrative_title": "Kunden-Skript",
    "solutions.llm_unavailable": "KI-Skript nicht verfuegbar (kein API-Schluessel).",
    "solutions.assumption_hint": "Annahme: {pct:.0f}% des ermittelten Potenzials",
    "solutions.tracked_title": "Laufende Massnahmen",
    "solutions.tracked_empty": "Noch keine Massnahme verfolgt.",
    "solutions.realized_column": "Realisiert (EUR/Monat)",
    "solutions.col.status": "Status",
    "solutions.col.created": "Erstellt",
    "solutions.track_confirmed": "Massnahme '{title}' wird verfolgt.",
    "solutions.realized_pending": "Wird gemessen ...",
    "solutions.realized_not_ready": "Noch nicht messbar",
    "solutions.category.cost": "Kosten",
    "solutions.category.revenue": "Umsatz",
    "solutions.category.scope": "Scope",
    "solutions.category.retention": "Kundenbindung",
    "solutions.category.quality": "Qualitaet",
    "solutions.log_action": "Verfolgen",

    # Issue labels (short, used in the Why column)
    "issue.labor_overrun": "Personalquote ueber Plan",
    "issue.subcontractor_creep": "Fremdleistung ueber Plan",
    "issue.productivity_drop": "Produktivitaet unter Cohort-Median",
    "issue.absence_spike": "Ausfallzeiten ueber Cohort-Median",
    "issue.quality_gap": "Qualitaetsziel verfehlt",
    "issue.plan_gap_widening": "Marge weicht vom Plan ab",
    "issue.revenue_shortfall": "Umsatz unter Planniveau",
    "issue.sustained_loss": "Mehrere Monate negativer DB",
    "issue.renewal_risk": "Vertragsende in Sicht",

    # Action titles + descriptions
    "action.renegotiate_price.title": "Preis nachverhandeln",
    "action.renegotiate_price.description": "Rahmenvertrag mit dem Kunden ueberpruefen und Anpassung an Plan-Marge anstreben.",
    "action.reprice_hourly.title": "Stundensätze anpassen",
    "action.reprice_hourly.description": "Stundensätze naeher am Cohort-Median anheben, Kundenabstimmung erforderlich.",
    "action.audit_subcontractors.title": "Subunternehmer-Audit",
    "action.audit_subcontractors.description": "Subunternehmer-Rechnungen sichten, Kostentreiber und Doppelabrechnungen eliminieren.",
    "action.reduce_subcontractor_share.title": "Subunternehmer-Anteil senken",
    "action.reduce_subcontractor_share.description": "Eigenpersonal ausbauen oder Auftragsmix verschieben, um Subunternehmer-Quote zu reduzieren.",
    "action.labor_cost_audit.title": "Personalkosten-Audit",
    "action.labor_cost_audit.description": "Einsatzplanung, Ueberstunden und Einweisungszeiten pruefen und zum Plan ausrichten.",
    "action.productivity_improvement.title": "Produktivitaet verbessern",
    "action.productivity_improvement.description": "Einsatzablauf, Routenfuehrung und Werkzeuge ueberpruefen, um produktive Stunden zu heben.",
    "action.absence_intervention.title": "Ausfallzeiten reduzieren",
    "action.absence_intervention.description": "Gespraeche mit Teamleitung fuehren, Gesundheitsschutz und Einsatzplanung anpassen.",
    "action.reduce_scope.title": "Leistung reduzieren",
    "action.reduce_scope.description": "Mit dem Kunden Scope-Reduktion vereinbaren, verlustbringende Leistungen ausklammern.",
    "action.terminate_contract.title": "Vertrag beenden",
    "action.terminate_contract.description": "Kuendigung vorbereiten, wenn Gegenmassnahmen keine nachhaltige Marge herstellen.",
    "action.renewal_outreach.title": "Verlaengerung anbahnen",
    "action.renewal_outreach.description": "Kundenkontakt vor Vertragsende aufnehmen, neue Konditionen verhandeln.",
    "action.training_investment.title": "Schulungen ausbauen",
    "action.training_investment.description": "Einarbeitungsprogramm anpassen, um Produktivitaetsluecke zum Cohort-Median zu schliessen.",
    "action.quality_remediation.title": "Qualitaet nachbessern",
    "action.quality_remediation.description": "Nacharbeiten priorisieren, SLA-Gespraeche fuehren, Pruefplan verschaerfen.",

    # Cost-driver sub-actions (attached to a specific data column).
    "sub_action.audit_overtime.title": "Ueberstunden + Direktlohn-Einsatz pruefen",
    "sub_action.reduce_labor_overhead.title": "Lohnnebenkosten / Zuschlaege nachrechnen",
    "sub_action.shorten_onboarding.title": "Einarbeitungsdauer kuerzen",
    "sub_action.stagger_vacations.title": "Urlaubsplanung entzerren",
    "sub_action.absence_intervention.title": "Krankenstand gezielt ansprechen",
    "sub_action.renegotiate_external_rates.title": "Externe Subunternehmer-Saetze nachverhandeln",
    "sub_action.rebalance_group_sourcing.title": "Konzern-Sourcing neu verteilen",
    "sub_action.rebalance_division_sourcing.title": "Sparten-Sourcing neu verteilen",
    "sub_action.reduce_break_overrun.title": "Pausenzeiten kontrollieren",
    "sub_action.labor_cost_audit.title": "Personalkosten-Audit",
    "sub_action.procurement_review.title": "Materialeinkauf pruefen",
    "sub_action.fleet_audit.title": "Fuhrpark / Routen pruefen",
    "sub_action.travel_policy_review.title": "Reiserichtlinie pruefen",
    "sub_action.reprice_hourly_detail.title": "Stundensätze hochstufen",
    "sub_action.renegotiate_fixed_price.title": "Pauschale nachverhandeln",
    "sub_action.renewal_outreach_detail.title": "Vorzeitige Verlaengerungsgespraeche",

    # Column labels used in the driver table.
    "column.labor_direct": "Direktlohn",
    "column.labor_overhead": "Lohnnebenkosten",
    "column.training_cost": "Einarbeitung",
    "column.vacation_cost": "Urlaubskosten",
    "column.sick_cost": "Krankenkosten",
    "column.subcontractor_external": "Subunternehmer extern",
    "column.subcontractor_group": "Subunternehmer Konzern",
    "column.subcontractor_division": "Subunternehmer Sparte",
    "column.hours_break": "Pausenstunden",
    "column.hours_training": "Einarbeitungsstunden",
    "column.labor_cost_total": "Personalkosten gesamt",
    "column.subcontractor_services_total": "Subunternehmer gesamt",
    "column.material_cost": "Material",
    "column.vehicle_cost": "Fuhrpark",
    "column.travel_cost": "Reisekosten",
    "column.revenue_hourly": "Umsatz Stundenabrechnung",
    "column.revenue_fixed": "Umsatz Pauschale",
    "column.revenue_total": "Umsatz gesamt",

    # Driver evidence table headers.
    "solutions.col.driver": "Ursache (Datenspalte)",
    "solutions.col.driver_delta": "Abweichung",
    "solutions.col.driver_fix": "Konkrete Massnahme",
    "solutions.driver_share": "{pct:.0f}% der Luecke",
    "solutions.drivers_title": "Treiber + konkrete Fixes",
    "solutions.drivers_empty": "Keine eindeutigen Kostentreiber erkannt.",

    # Panel intro + KPI strip
    "solutions.intro_title": "Wie diese Liste entsteht",
    "solutions.intro_body": (
        "Drei Fragen beantwortet die Seite automatisch:\n\n"
        "**1. Was ist das Problem?** Regelbasierte Diagnose aus Plan-"
        "Abweichung, Cohort-Vergleich und den Fruehwarnsignalen.\n\n"
        "**2. Welche Datenspalte ist schuld?** Kostenspalten "
        "(Direktlohn, Subunternehmer extern, Krankenkosten, ...) "
        "werden gegen ihren eigenen 3-Monats-Schnitt verglichen. "
        "Die staerkste Abweichung gewinnt.\n\n"
        "**3. Was tun?** Jede Datenspalte hat eine konkrete Handlung "
        "hinterlegt (Direktlohn hoch -> Ueberstunden pruefen). "
        "Der EUR-Betrag ist konservativ und auf 30% vom Monatsumsatz "
        "bzw. den Monatsverlust begrenzt."
    ),
    "solutions.kpi_title": "Kernzahlen des Monats",
    "solutions.kpi_cm": "Deckungsbeitrag (Ist)",
    "solutions.kpi_cm_plan": "Deckungsbeitrag (Plan)",
    "solutions.kpi_gap": "Luecke zum Plan",
    "solutions.kpi_revenue": "Umsatz",
    "solutions.kpi_score": "Gesamtscore",

    # Per-action card: three-question layout.
    "solutions.q1_title": "Was wir tun",
    "solutions.q2_title": "Warum das hilft",
    "solutions.q3_title": "Was es bringt",
    "solutions.q3_math_title": "So wird der Betrag berechnet",
    "solutions.q3_cap_note": (
        "Nach Kappung: auf **{capped}/Monat** gedeckelt "
        "(Max. 30% vom Monatsumsatz oder der Monatsverlust)."
    ),
    "solutions.q3_outcome_cost": (
        "Bei Umsetzung sinken die betroffenen Kosten um rund "
        "**{impact}/Monat**. Bei gleichem Umsatz steigt der "
        "Deckungsbeitrag des Vertrags um denselben Betrag."
    ),
    "solutions.q3_outcome_revenue": (
        "Bei Umsetzung steigt der Umsatz um rund "
        "**{impact}/Monat**. Bei gleichen Kosten wandert der "
        "komplette Betrag in die Marge."
    ),
    "solutions.q3_outcome_retention": (
        "Bei erfolgreicher Verlaengerung bleiben rund "
        "**{impact}/Monat** Umsatz im Portfolio erhalten."
    ),
    "solutions.q3_outcome_scope": (
        "Nach Scope-Reduktion oder Vertragsende entfaellt der "
        "monatliche Verlust von rund **{impact}/Monat**."
    ),
    "solutions.meta_owner": "Verantwortlich: **{owner}**",
    "solutions.meta_timeframe": "Zeitrahmen: **{weeks} Wochen**",
    "solutions.meta_confidence": "Aussagekraft: **{conf}**",
    "solutions.ready_to_track": "Bereit zum Verfolgen?",
    "solutions.no_drivers_text": (
        "Keine einzelne Datenspalte dominiert diese Luecke. "
        "Die Massnahme wirkt breit auf die Kostenstruktur."
    ),

    # "What we will do" lead sentence per action.
    "what_prose.renegotiate_price": "Mit dem Kunden einen neuen Rahmenpreis verhandeln, der die aktuelle Leistung fair bewertet.",
    "what_prose.reprice_hourly": "Stundensätze beim Kunden anheben, bis die Personalquote auf Cohort-Niveau liegt.",
    "what_prose.audit_subcontractors": "Subunternehmer-Rechnungen der letzten 3 Monate pruefen und Unstimmigkeiten zurueckfordern.",
    "what_prose.reduce_subcontractor_share": "Leistungen Schritt fuer Schritt von Subunternehmern ins Eigenpersonal ueberfuehren.",
    "what_prose.labor_cost_audit": "Personalkosten-Struktur systematisch durchgehen (Ueberstunden, Schichtplanung, Einarbeitung) und zum Plan ausrichten.",
    "what_prose.productivity_improvement": "Ablauf vor Ort eine Woche beobachten, Stoerungen finden und Quick-Fixes in 14 Tagen umsetzen.",
    "what_prose.absence_intervention": "Krankenstand ueber Gespraeche mit Teamleitung und Praeventionsmassnahmen aktiv senken.",
    "what_prose.reduce_scope": "Mit dem Kunden Scope-Reduktion oder Pauschalanpassung vereinbaren und im Vertragsanhang festhalten.",
    "what_prose.terminate_contract": "Vertrag geordnet kuendigen; Kuendigungsfristen und Personalbindung vorab klaeren.",
    "what_prose.renewal_outreach": "90-120 Tage vor Vertragsende in die Verlaengerungsverhandlung gehen.",
    "what_prose.training_investment": "Gezielten Schulungsplan aufsetzen, um die Produktivitaetsluecke zum Cohort-Median zu schliessen.",
    "what_prose.quality_remediation": "Nacharbeitsplan mit Teams priorisieren und SLA-Review-Termin mit dem Kunden setzen.",

    # "Why this helps" short prose per action.
    "why_prose.renegotiate_price": (
        "Der Vertrag bringt weniger Deckungsbeitrag als geplant. "
        "Eine Preisanpassung bringt Umsatz und Marge wieder auf das "
        "urspruenglich kalkulierte Niveau, ohne am operativen Ablauf "
        "etwas zu aendern."
    ),
    "why_prose.reprice_hourly": (
        "Die Personalquote liegt ueber dem, was vergleichbare "
        "Vertraege verlangen. Eine Anhebung der Stundensätze gleicht "
        "den Unterschied aus, ohne Eingriff in die Einsatzplanung."
    ),
    "why_prose.audit_subcontractors": (
        "Subunternehmer-Rechnungen enthalten oft Doppelabrechnungen, "
        "Zuschlaege jenseits des Vertrags oder falsche Stundensätze. "
        "Ein Audit findet diese Posten und holt sie zurueck."
    ),
    "why_prose.reduce_subcontractor_share": (
        "Zu viel Arbeit laeuft ueber Subunternehmer, die teurer sind "
        "als Eigenpersonal. Verlagern ins eigene Team senkt die "
        "Kostenbasis dauerhaft."
    ),
    "why_prose.labor_cost_audit": (
        "Die Personalkosten liegen ueber Plan. Ursache sind meist "
        "Ueberstunden, falsche Schichten oder nicht eingebuchte "
        "Einarbeitung. Ein strukturiertes Audit findet die Treiber "
        "und bringt sie zum Plan zurueck."
    ),
    "why_prose.productivity_improvement": (
        "Produktive Stunden liegen unter Soll. Eine Woche "
        "Ablaufbeobachtung deckt Werkzeug-, Routen- oder "
        "Koordinationsprobleme auf. Kleine Fixes heben die "
        "Produktivitaet messbar."
    ),
    "why_prose.absence_intervention": (
        "Der Krankenstand liegt deutlich ueber dem Cohort-Schnitt. "
        "Jeder Prozentpunkt Ausfall erzeugt Ersatz- und "
        "Ueberstunden-Kosten. Gezielte Gespraeche senken die Quote "
        "in wenigen Wochen."
    ),
    "why_prose.reduce_scope": (
        "Der Vertrag ist im aktuellen Zuschnitt nicht rentabel. "
        "Leistungen aus dem Scope zu nehmen stoppt den Verlust, "
        "ohne den Kunden zu verlieren."
    ),
    "why_prose.terminate_contract": (
        "Keine Gegenmassnahme stellt eine nachhaltige Marge her. "
        "Jede weitere Vertragslaufzeit kostet Geld. Geordnete "
        "Kuendigung stoppt den Verlust und macht Personal fuer "
        "rentable Auftraege frei."
    ),
    "why_prose.renewal_outreach": (
        "Der Vertrag endet in den naechsten Monaten. Ohne Aktion "
        "entfaellt der komplette Umsatz. Frueher Kundenkontakt "
        "sichert die Verlaengerung mit besseren Konditionen."
    ),
    "why_prose.training_investment": (
        "Die Produktivitaet liegt unter dem Cohort-Median, weil die "
        "Einarbeitung nicht passt. Gezielte Schulungen schliessen "
        "die Luecke zu vergleichbaren Standorten."
    ),
    "why_prose.quality_remediation": (
        "Das Qualitaetsziel wird verfehlt. Unbehandelt drohen "
        "SLA-Pauschalen, Nacharbeit und Kundenverlust. Pruefplan "
        "und SLA-Review halten den Vertrag stabil."
    ),

    # KPI gap detector (contract detail page card + LLM context)
    "gaps.section_title": "Welche Kennzahlen fehlen fuer eine schaerfere Diagnose?",
    "gaps.section_sub": "Diese Datenpunkte wuerden die Ursachenanalyse belastbarer machen.",
    "gaps.section_hint": "Fehlende Daten",
    "gaps.empty": "Die verfuegbaren Daten reichen fuer die Hauptursachen aus.",
    "gaps.overtime_hours.title": "Ueberstunden-Stunden",
    "gaps.overtime_hours.reason": "Ohne Ueberstunden-Stunden laesst sich nicht zwischen Mehrarbeit und Personalaufbau unterscheiden.",
    "gaps.headcount_fte.title": "Kopfzahl / FTE",
    "gaps.headcount_fte.reason": "Mit FTE-Zahlen laesst sich die Kostenveraenderung pro Kopf berechnen.",
    "gaps.absence_reason.title": "Ausfallgrund-Aufschluesselung",
    "gaps.absence_reason.reason": "Trennt einmalige Ausfaelle (Grippewelle) von strukturellen Problemen.",
    "gaps.subcontractor_hours.title": "Subunternehmer-Stunden",
    "gaps.subcontractor_hours.reason": "Erlaubt den Vergleich des externen Stundensatzes mit dem internen.",
    "gaps.subcontractor_reason.title": "Einsatzgrund Subunternehmer",
    "gaps.subcontractor_reason.reason": "Ueberlauf oder Spezialleistung? Je nach Grund sind andere Massnahmen sinnvoll.",
    "gaps.billable_hours.title": "Abgerechnete Stunden",
    "gaps.billable_hours.reason": "Trennt Preis- vom Mengeneffekt bei einer Umsatzbewegung.",
    "gaps.price_per_hour.title": "Stundenpreis",
    "gaps.price_per_hour.reason": "Zeigt, ob der Umsatzrueckgang aus Preis- oder Mengenreduktion kommt.",
    "gaps.customer_churn.title": "Kundenabgaenge",
    "gaps.customer_churn.reason": "Einmaliger Kundenverlust vs. allgemeiner Nachfragerueckgang haben verschiedene Konsequenzen.",
    "gaps.quality_kpi.title": "Qualitaets-Kennzahl",
    "gaps.quality_kpi.reason": "Zeigt, ob Kostensenkungen die Servicequalitaet gefaehrden.",
    "gaps.plan_values.title": "Planwerte (geplanter DB)",
    "gaps.plan_values.reason": "Kein Abgleich mit Plan moeglich; nur Vormonatsvergleich verfuegbar.",
    "gaps.missing_driver.title": "Weitere Kostenarten",
    "gaps.missing_driver.reason": "Unerklaerte Restgroesse ist materiell - eine oder mehrere Kostenpositionen fehlen im Modell.",
}


en: dict[str, str] = {
    # App-level
    "app.title": "WISAG Finance Copilot",
    "app.subtitle": "Your AI for margin, risks and actions.",
    "app.welcome": "Welcome back",
    "app.welcome_sub": "Your portfolio at a glance.",

    # Navigation
    "nav.home": "Home",
    "nav.portfolio": "Overview",
    "nav.deepdive": "Details",
    "nav.warnings": "Alerts",
    "nav.chat": "Ask AI",
    "nav.plan_vs_actual": "Plan vs. actual",
    "nav.open": "Open",

    # Nav card descriptions
    "nav.portfolio.desc": "All sites at a glance.",
    "nav.deepdive.desc": "Inspect one site closely.",
    "nav.warnings.desc": "Risks ranked by euro impact.",
    "nav.chat.desc": "Ask questions in your own words.",
    "nav.plan_vs_actual.desc": "Month-by-month actual vs. plan.",

    # Topbar / settings popover
    "topbar.back_home": "Back to overview",
    "topbar.settings": "Settings",
    "topbar.settings_tip": "Data source and API status",

    # Landing status card
    "landing.status_title": "Portfolio status",
    "landing.status_sub": "As of today",
    "landing.status_margin": "Margin",
    "landing.status_gap": "vs. plan",
    "landing.cta_overview": "Overview",
    "landing.cta_details": "Details",
    "landing.cta_alerts": "Alerts",

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
    "kpi.cm": "Margin",
    "kpi.cm_planned": "Planned margin",
    "kpi.plan_gap": "vs. plan",
    "kpi.cost_centers": "Sites",
    "kpi.anomalies": "Anomalies",
    "kpi.total_actual": "Actual",
    "kpi.total_planned": "Planned",
    "kpi.total_gap": "Gap",
    "kpi.worst_month": "Weakest month",
    "kpi.eur_at_stake": "€ at risk",
    "kpi.high_severity": "High",
    "kpi.medium_severity": "Medium",
    "kpi.low_severity": "Low",

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
    "portfolio.actions_empty": "No immediate actions required — portfolio in good shape.",
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
    "overview.section_title": "Overview",
    "overview.cat.revenue": "Total Revenue",
    "overview.cat.costs": "Total Costs",
    "overview.cat.cm": "Total Contribution Margin",
    "overview.trend_sub": "Last 12 months — with regression line",
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
    "overview.evolution_title": "Margin trend",
    "overview.evolution_sub": "Last 6 months — contribution margin %",
    "overview.cost_total": "Total cost",
    "overview.cost_mom": "Cost vs last month",
    "overview.cost_causes_title": "What drove cost up?",
    "overview.cost_causes_sub": "Top cost categories that rose vs last month",
    "overview.solutions_title": "Actions that cut this cost",
    "overview.solutions_sub": "Estimated margin impact and why each step reduces cost",

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
    "driver.labor.cause": "Overtime, shift premiums, or headcount growth raised the labour bill.",
    "driver.absence": "Increased absences",
    "driver.absence.sub": "More sick leaves and time off",
    "driver.absence.cause": "Sick leave and vacation costs climbed this month.",
    "driver.training": "Training & onboarding",
    "driver.training.sub": "More new hires and training hours",
    "driver.training.cause": "Heavier onboarding or training spend versus last month.",
    "driver.subcontractor": "More subcontracting",
    "driver.subcontractor.sub": "Higher share of external services",
    "driver.subcontractor.cause": "More work routed to subcontractors at a higher rate.",
    "driver.material": "Higher material costs",
    "driver.material.sub": "Material consumption up",
    "driver.material.cause": "Consumables and materials ordered or consumed rose.",
    "driver.vehicle": "Higher vehicle costs",
    "driver.vehicle.sub": "Fleet and travel expenses up",
    "driver.vehicle.cause": "Fleet use, fuel, or travel expense increased.",
    "driver.revenue": "Revenue decline",
    "driver.revenue.sub": "Less billed revenue",
    "driver.revenue_up": "Revenue growth",
    "driver.revenue_up.sub": "More billed revenue",
    "driver.other": "Other cost movements",
    "driver.other.sub": "Sum of remaining cost lines",
    "driver.other.cause": "Smaller cost categories combined to push the total up.",

    # Recommended-action labels (already English)
    "action.shift.title": "Optimize shift scheduling",
    "action.shift.sub": "Reduce overtime and improve coverage",
    "action.shift.why": "Matching shifts to demand trims idle paid hours.",
    "action.absence.title": "Reduce absences",
    "action.absence.sub": "Strengthen retention and well-being programs",
    "action.absence.why": "Reducing absences keeps work inside the plan without overtime.",
    "action.onboarding.title": "Improve onboarding efficiency",
    "action.onboarding.sub": "Speed up productivity of new hires",
    "action.onboarding.why": "Faster ramp-up shortens paid-but-unproductive time.",
    "action.subcontractor.title": "Reduce subcontracting mix",
    "action.subcontractor.sub": "Grow in-house delivery, lower external cost",
    "action.subcontractor.why": "Bringing work in-house avoids subcontractor markup.",
    "action.pricing.title": "Review pricing & contract terms",
    "action.pricing.sub": "Renegotiate low-margin contracts",
    "action.pricing.why": "Aligning billing to actual cost protects the contract margin.",
    "action.productivity.title": "Boost productivity",
    "action.productivity.sub": "Improve process and shift utilization",
    "action.productivity.why": "Higher output per paid hour lowers unit cost.",
    "portfolio.worst_banner": (
        "**{month}** — contribution margin dropped to **{cm}** "
        "(cost center {cc_id} · {cc_name}). {labor}{hours}. "
        "Open **Deep dive** for driver decomposition and AI explanation."
    ),
    "portfolio.dq_banner": (
        "**Data quality — {month}:** revenue {rev} is {ratio:.1f}× the trailing "
        "12-month average. {note}. "
        "This month is excluded from the anomaly ranking to avoid false alerts."
    ),

    # Deep Dive
    "deepdive.title": "Details",
    "deepdive.subtitle": "Pick a site · what changed · actions.",
    "deepdive.cost_center": "Site",
    "deepdive.baseline": "Compare to",
    "deepdive.baseline_prior_month": "Last month",
    "deepdive.baseline_prior_year": "Last year",
    "deepdive.baseline_plan": "Plan",
    "deepdive.period": "Period",
    "deepdive.no_data": "No data for this site.",
    "deepdive.no_baseline": "No baseline for \"{mode}\".",
    "deepdive.timeline_title": "Margin over time",
    "deepdive.waterfall_title": "What changed · {delta}",
    "deepdive.kpi_peers": "Compared to the region",
    "deepdive.kpi_peers_empty": "Not enough comparison data.",
    "deepdive.ai_title": "AI explanation",
    "deepdive.ai_preview": "Top causes and actions in plain language.",
    "deepdive.ai_asking": "Asking Claude…",
    "deepdive.ai_hint": "Click above to generate an explanation.",
    "deepdive.download": "Download as comment",
    "deepdive.residual_warn": "Note: {pct:.0%} of the change couldn't be mapped to a single factor.",
    "deepdive.section_changed": "What changed",
    "deepdive.section_peers": "Compared to the region",
    "deepdive.peer_median_label": "Peer median: {v}",
    "deepdive.show_details": "Show details",

    # Early Warnings
    "warnings.title": "Alerts",
    "warnings.subtitle": "Risks, sorted by euro impact.",
    "warnings.none": "No alerts with the current filters.",
    "warnings.pick": "Pick an alert",
    "warnings.action_title": "Actions for this alert",
    "warnings.ai_button": "Show actions",
    "warnings.no_history": "No history available.",
    "warnings.not_enough_history": "Not enough history for a baseline.",
    "warnings.at_risk": "€ at risk",

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
    "chat.title": "Ask AI",
    "chat.subtitle": "Ask anything in your own words.",
    "chat.try_asking": "Examples",
    "chat.chip_weakest": "Where is the margin weakest — and why?",
    "chat.chip_plan_gap": "Top-3 sites missing plan the most",
    "chat.chip_productivity": "What does +10% productivity unlock?",
    "chat.input_placeholder": "Your question…",
    "chat.thinking": "Thinking…",
    "chat.clear": "Reset chat",

    # Floating copilot dock
    "copilot.placeholder": "Ask about your contracts…",
    "copilot.mic_hint": "Press your Wispr Flow key to dictate",
    "copilot.empty_greeting": "Hi. Ask me anything about your portfolio.",
    "copilot.send": "Send",
    "copilot.mic": "Dictate",
    "copilot.read_aloud": "Read aloud",
    "copilot.stop_reading": "Stop reading",
    "copilot.error_no_key": "Anthropic API key missing. Set ANTHROPIC_API_KEY in .env.",

    # Plan vs Actual
    "pva.title": "Actual vs. plan",
    "pva.subtitle": "Month by month.",
    "pva.missing_cols": "Columns missing — variance cannot be computed.",
    "pva.bar_title": "Actual vs. plan by month",
    "pva.bar_sub": "Green = above plan · Red = below plan",
    "pva.table_title": "Monthly breakdown",
    "pva.col.month": "Month",
    "pva.col.revenue": "Revenue",
    "pva.col.planned": "Plan",
    "pva.col.actual": "Actual",
    "pva.col.gap_eur": "Difference",
    "pva.col.gap_pct": "Difference %",
    "pva.legend.beat": "Above plan (> +50 k€)",
    "pva.legend.miss": "Below plan (< −50 k€)",

    # Upload page (shown when no dataset is present yet)
    "upload.title": "Upload your dataset",
    "upload.subtitle": "Drop your WISAG export file to start the Co-Pilot. Margin, drivers and alerts are computed automatically.",
    "upload.cta": "Choose a file or drop it here",
    "upload.cta_help": "Supported formats: .xlsx, .xls, .csv",
    "upload.requirements_title": "What we expect",
    "upload.requirements_sub": "For the analysis to work, the file should meet these requirements.",
    "upload.req_xlsx.title": "Excel or CSV export",
    "upload.req_xlsx.sub": ".xlsx, .xls or .csv — straight from your ERP.",
    "upload.req_headers.title": "Original column headers",
    "upload.req_headers.sub": "German headers such as Jahr, Monat, KST, Ges_Ums, DB.",
    "upload.req_period.title": "Monthly records",
    "upload.req_period.sub": "At least two months per cost center for comparisons.",
    "upload.success": "Dataset loaded — refreshing the dashboard.",
    "upload.schema_failed": "Schema check failed: {msg}",
    "upload.sample_hint": "No dataset at hand? Drop `Dataset_anoym.xlsx` into the `data/` folder.",

    # Data source / errors
    "data.no_data_warn": "**Getting started:** drop `Dataset_anoym.xlsx` into the `data/` folder or upload the file via the sidebar.",
    "data.no_data_page": "Please load the dataset on the home page.",
    "data.place_or_upload": "Drop `Dataset_anoym.xlsx` into `./data/` or upload it above.",
    "data.load_failed": "Load failed: {err}",
    "data.schema_ok": "Schema: {m}/{t} columns detected",
    "data.schema_position": "Schema: {m}/{t} columns (mapped by column position — no German headers found). Please re-export with the original header row.",
    "data.schema_error": "Schema: {m}/{t} columns detected\n\nMissing critical columns: **{missing}**\n\nWithout these columns the app cannot compute. Please check the source file's headers.",
    "data.optional_missing": "{n} optional columns missing",
    "data.extra_ignored": "{n} extra columns ignored",
    "data.stats": "{rows:,} rows · {ccs} cost centers · {pmin} → {pmax}",

    # Actions
    "action.generate_explanation": "Show AI explanation",
    "action.download": "Download",
    "action.open_deepdive": "Open deep dive →",
    "action.details": "Show details",

    # --- Analytics page ---
    "analytics.title": "Analytics",
    "analytics.subtitle": "Portfolio overview: heatmap, anomalies and revenue movers.",
    "analytics.kpi.revenue": "Total revenue",
    "analytics.kpi.margin": "Portfolio margin",
    "analytics.kpi.sites": "Cost centers",
    "analytics.kpi.anomalies": "Anomalies",
    "analytics.heatmap.title": "Margin heatmap",
    "analytics.heatmap.sub": "CM% by region × month.",
    "analytics.heatmap.empty": "Not enough data for the heatmap.",
    "analytics.anomalies.title": "Top anomalies",
    "analytics.anomalies.sub": "Filtered and ranked by € impact.",
    "analytics.anomalies.empty": "No anomalies detected.",
    "analytics.leaders.title": "Revenue leaders",
    "analytics.leaders.sub": "Largest revenue gains vs. prior month.",
    "analytics.laggards.title": "Revenue laggards",
    "analytics.laggards.sub": "Largest revenue drops vs. prior month.",

    # --- Forecasts page ---
    "forecasts.title": "Forecasts",
    "forecasts.subtitle": "Simple margin trend projection based on historical data.",
    "forecasts.horizon": "Horizon",
    "forecasts.horizon.3": "3 months",
    "forecasts.horizon.6": "6 months",
    "forecasts.horizon.12": "12 months",
    "forecasts.scope": "Scope",
    "forecasts.scope.portfolio": "Portfolio",
    "forecasts.scope.cost_center": "Single cost center",
    "forecasts.chart.title": "Margin history & projection",
    "forecasts.chart.sub": "History (blue) + forecast with confidence band.",
    "forecasts.trajectory.title": "Expected trajectory per cost center",
    "forecasts.trajectory.sub": "Expected Δ margin across the horizon.",
    "forecasts.col.cost_center": "Cost center",
    "forecasts.col.current": "Current margin",
    "forecasts.col.projected": "Projected margin",
    "forecasts.col.delta": "Δ margin",
    "forecasts.col.direction": "Direction",
    "forecasts.direction.up": "rising",
    "forecasts.direction.flat": "flat",
    "forecasts.direction.down": "falling",
    "forecasts.methodology.title": "Methodology",
    "forecasts.methodology.body": "Linear regression on the last 12 months plus a simple seasonal mean. Not an ML forecast — this view is deliberately simple and is meant as guidance, not a decision rule.",
    "forecasts.empty": "Not enough history to forecast.",

    # --- Scenarios page ---
    "scenarios.title": "Scenarios",
    "scenarios.subtitle": "Move several levers at once and see the margin effect.",
    "scenarios.picker.label": "Cost center",
    "scenarios.levers.title": "Levers",
    "scenarios.levers.sub": "Move the sliders — all values are deltas vs. the current month.",
    "scenarios.lever.headcount": "Headcount",
    "scenarios.lever.headcount.help": "Absolute number of staff in the new scenario.",
    "scenarios.lever.absence": "Absence rate Δ",
    "scenarios.lever.absence.help": "Percentage-point change of the absence rate.",
    "scenarios.lever.rate": "Billing rate Δ",
    "scenarios.lever.rate.help": "Percent change of the average billing rate.",
    "scenarios.lever.subco": "Subcontractor share Δ",
    "scenarios.lever.subco.help": "Percentage-point change of the subcontractor share.",
    "scenarios.reset": "Reset",
    "scenarios.result.title": "Result",
    "scenarios.result.new_margin": "New margin",
    "scenarios.result.delta_margin": "Δ margin",
    "scenarios.result.delta_cm": "Δ contribution margin",
    "scenarios.waterfall.title": "Contribution per lever",
    "scenarios.waterfall.sub": "How much margin effect each lever produces.",
    "scenarios.waterfall.empty": "No lever moved yet.",

    # --- Reports page ---
    "reports.title": "Reports",
    "reports.subtitle": "Plan vs. actual and exportable snapshots.",
    "reports.scope": "Scope",
    "reports.scope.portfolio": "Portfolio",
    "reports.scope.region": "Region",
    "reports.scope.cost_center": "Cost center",
    "reports.range.from": "From",
    "reports.range.to": "To",
    "reports.pva.title": "Plan vs. actual",
    "reports.pva.sub": "Monthly comparison of plan and actual revenue.",
    "reports.pva.col.month": "Month",
    "reports.pva.col.revenue": "Revenue",
    "reports.pva.col.plan": "Plan",
    "reports.pva.col.actual": "Actual",
    "reports.pva.col.gap_eur": "Gap €",
    "reports.pva.col.gap_pct": "Gap %",
    "reports.waterfall.title": "Drivers (actual vs. plan)",
    "reports.waterfall.sub": "Contribution of each driver to the total variance.",
    "reports.export.title": "Export",
    "reports.export.sub": "Download the current selection as a file.",
    "reports.export.csv": "Download CSV",
    "reports.export.xlsx": "Download Excel",

    # --- Alerts page ---
    "alerts.title": "Alerts",
    "alerts.subtitle": "Early warnings from rules and statistics, ranked by € impact.",
    "alerts.filter.severity": "Severity",
    "alerts.filter.severity.all": "All",
    "alerts.filter.severity.high": "High",
    "alerts.filter.severity.medium": "Medium",
    "alerts.filter.severity.low": "Low",
    "alerts.filter.scope": "Scope",
    "alerts.filter.scope.all": "All cost centers",
    "alerts.filter.scope.region": "Current region",
    "alerts.empty": "No active warnings — everything is in the green zone.",
    "alerts.count": "{n} alert(s)",
    "alerts.detail.title": "Details",
    "alerts.detail.ai_title": "Recommended action plan",
    "alerts.detail.ai_wait": "Claude is analyzing…",
    "alerts.detail.ai_fallback": "No AI available — using template.",
    "alerts.detail.open_scenario": "Open in Scenarios →",
    "alerts.detail.close": "Close",

    # --- Settings page ---
    "settings.title": "Settings",
    "settings.subtitle": "Manage language, data source and cache.",
    "settings.language.title": "Language",
    "settings.language.sub": "Affects all pages immediately.",
    "settings.data.title": "Data source",
    "settings.data.sub": "Currently loaded file and stats.",
    "settings.data.path": "Path",
    "settings.data.rows": "Rows",
    "settings.data.modified": "Last modified",
    "settings.data.upload": "Upload new dataset",
    "settings.cache.title": "Cache",
    "settings.cache.sub": "Clear all memoized computations and data.",
    "settings.cache.clear": "Clear cache",
    "settings.cache.cleared": "Cache cleared.",
    "settings.about.title": "About",
    "settings.about.sub": "App info.",
    "settings.about.version": "Version",
    "settings.about.commit": "Commit",
    "settings.about.web": "Next.js frontend under `web/`",

    # --- Portfolio ranking table (new landing view) ---
    "portfolio.header": "Contracts",
    "portfolio.header_sub": "Contracts ranked by unprofitability — most unprofitable on top.",
    "portfolio.search_placeholder": "Search contract, client or cost center…",
    "portfolio.filters": "Filters",
    "portfolio.filters_reset": "Reset filters",
    "portfolio.filter_region": "Region",
    "portfolio.filter_month": "Months",
    "portfolio.filter_client": "Client",
    "portfolio.filter_branch": "Branch",
    "portfolio.filter_reason": "Reason",
    "portfolio.filter_cost_center": "Cost center",
    "portfolio.show_profitable": "Show profitable contracts too",
    "portfolio.kpi_total_unprofit": "Total unprofitability",
    "portfolio.kpi_total_unprofit_sub": "Sum across visible contracts",
    "portfolio.kpi_longest_unprofit": "Longest unprofitability",
    "portfolio.kpi_longest_unprofit_sub": "{name} · since {since}",
    "portfolio.kpi_longest_unit": "{n} months",
    "portfolio.kpi_longest_unit_one": "{n} month",
    "portfolio.kpi_none": "—",
    "portfolio.table_contract": "Contract",
    "portfolio.table_client": "Client",
    "portfolio.table_region": "Region",
    "portfolio.table_branch": "Branch",
    "portfolio.table_cost_center": "Cost center",
    "portfolio.table_unprofit": "Unprofitability (€)",
    "portfolio.table_since": "Unprofitable since",
    "portfolio.table_months": "Months",
    "portfolio.table_reason": "Biggest reason",
    "portfolio.col_contract": "Contract",
    "portfolio.col_biggest_unprofit": "Biggest unprofitability",
    "portfolio.col_longest_unprofit": "Longest unprofitability",
    "portfolio.col_biggest_reason": "Biggest reason",
    "portfolio.col_trend": "CM trend",
    "portfolio.col_trend_sub": "pp/month (6m)",
    "portfolio.tooltip_sub": "Contribution margin — month-over-month change (%)",
    "portfolio.empty_all_profitable": "No unprofitable contracts with these filters — everything is in the green zone.",
    "portfolio.empty_no_contracts": "No contracts match the current filters.",
    "portfolio.open_contract_hint": "Click a row to open the contract detail view.",
    "portfolio.open_contract": "Open contract",

    # --- Contracts category tabs (Overall / Profitability / Revenue / Cost / Efficiency / Stability) ---
    "contracts.tab.overall": "Overall",
    "contracts.tab.profitability": "Profitability",
    "contracts.tab.revenue_trend": "Revenue trend",
    "contracts.tab.cost_structure": "Cost structure",
    "contracts.tab.efficiency": "Efficiency",
    "contracts.tab.stability": "Stability",

    # Overall tab columns
    "contracts.col.score_profitability": "Profitability",
    "contracts.col.score_cost": "Cost structure",
    "contracts.col.score_efficiency": "Efficiency",
    "contracts.col.score_stability": "Stability",
    "contracts.col.score_overall": "Overall score",

    # Profitability tab columns
    "contracts.col.unrent_mom": "Unrentability vs last month",
    "contracts.col.unrent_6m": "Unrentability vs last 6 months",
    "contracts.col.top_cost_increase_cat": "Cost category with biggest increase",
    "contracts.col.trend_mom": "Trend vs last month",

    # Revenue trend tab columns
    "contracts.col.revenue_mom": "Revenue vs last month",
    "contracts.col.revenue_6m": "Revenue vs last 6 months",
    "contracts.col.top_decline_stream": "Weakest revenue stream",
    "contracts.col.revenue_trend": "Revenue direction",
    "contracts.col.revenue_trend.down": "Declining",
    "contracts.col.revenue_trend.flat": "Stable",
    "contracts.col.revenue_trend.up": "Growing",
    "contracts.col.revenue_trend.no_data": "—",

    # Revenue stream labels
    "revenue_stream.fixed": "Fixed-price",
    "revenue_stream.hourly": "Hourly",
    "revenue_stream.other": "Other",

    # Cost structure tab columns
    "contracts.col.top_cost_cat": "Highest cost",
    "contracts.col.cost_highest_increase": "Biggest cost increase",
    "contracts.col.cost_highest_increase_pct": "Increase (%)",
    "contracts.col.total_cost_increase_pct": "Total cost increase (%)",

    # Efficiency tab columns
    "contracts.col.hours_plan_minus_prod": "Planned - productive hours",
    "contracts.col.ratio_mom": "Ratio vs last month",
    "contracts.col.ratio_6m": "Ratio vs last 6 months",
    "contracts.col.hour_variance": "Hour variance",

    # Stability tab columns
    "contracts.col.duration": "Duration",
    "contracts.col.cm_variance": "CM variance",
    "contracts.col.long_short": "Long / short term",
    "contracts.col.revenue_variance": "Revenue variance",

    # Shared labels
    "contracts.duration_months": "{n} months",
    "contracts.long_term": "Long-term",
    "contracts.short_term": "Short-term",
    "contracts.no_data": "—",
    "contracts.trend_up": "worsening",
    "contracts.trend_down": "improving",
    "contracts.trend_flat": "flat",

    # Cost category labels
    "cost_cat.labor": "Labor",
    "cost_cat.subcontractor": "Subcontractor",
    "cost_cat.internal_service": "Internal service",
    "cost_cat.travel": "Travel",
    "cost_cat.material": "Material",
    "cost_cat.vehicle": "Vehicle",

    # Short reason labels (for filter chips + table cell)
    "reason.labor": "Labor",
    "reason.absence": "Absences",
    "reason.training": "Training",
    "reason.subcontractor": "Subcontractor",
    "reason.material": "Material",
    "reason.vehicle": "Vehicle",
    "reason.revenue": "Revenue",
    "reason.other": "Other",
    "reason.none": "—",

    # Solution Finder
    "solutions.title": "Recommended Actions",
    "solutions.subtitle": "Top actions ranked by euro impact per unit of effort",
    "solutions.col.action": "Action",
    "solutions.col.why": "Why",
    "solutions.col.impact": "Impact (EUR/month)",
    "solutions.col.owner": "Owner",
    "solutions.col.timeframe": "Timeframe (weeks)",
    "solutions.col.confidence": "Confidence",
    "solutions.col.category": "Category",
    "solutions.owner.ops": "Operations",
    "solutions.owner.sales": "Sales",
    "solutions.owner.regional_manager": "Regional Manager",
    "solutions.status.proposed": "Proposed",
    "solutions.status.in_progress": "In progress",
    "solutions.status.done": "Done",
    "solutions.status.abandoned": "Abandoned",
    "solutions.btn.mark_proposed": "Mark as proposed",
    "solutions.btn.mark_in_progress": "Mark in progress",
    "solutions.btn.mark_done": "Mark done",
    "solutions.btn.mark_abandoned": "Mark abandoned",
    "solutions.confidence.low": "low",
    "solutions.confidence.med": "medium",
    "solutions.confidence.high": "high",
    "solutions.empty": "No actions needed.",
    "solutions.cohort_note": "Benchmark: {scope}, n={size}",
    "solutions.llm_narrative_title": "Customer-ready talking points",
    "solutions.llm_unavailable": "AI script unavailable (no API key).",
    "solutions.assumption_hint": "Assumption: {pct:.0f}% of identified potential",
    "solutions.tracked_title": "Tracked actions",
    "solutions.tracked_empty": "No action tracked yet.",
    "solutions.realized_column": "Realized (EUR/month)",
    "solutions.col.status": "Status",
    "solutions.col.created": "Created",
    "solutions.track_confirmed": "Tracking action '{title}'.",
    "solutions.realized_pending": "Measuring ...",
    "solutions.realized_not_ready": "Not yet measurable",
    "solutions.category.cost": "Cost",
    "solutions.category.revenue": "Revenue",
    "solutions.category.scope": "Scope",
    "solutions.category.retention": "Retention",
    "solutions.category.quality": "Quality",
    "solutions.log_action": "Track",

    # Issue labels
    "issue.labor_overrun": "Labor ratio above plan",
    "issue.subcontractor_creep": "Subcontractor share above plan",
    "issue.productivity_drop": "Productivity below peer median",
    "issue.absence_spike": "Absence rate above peer median",
    "issue.quality_gap": "Quality target missed",
    "issue.plan_gap_widening": "Margin widening vs plan",
    "issue.revenue_shortfall": "Revenue short of plan level",
    "issue.sustained_loss": "Sustained negative CM months",
    "issue.renewal_risk": "Renewal deadline approaching",

    # Action titles + descriptions
    "action.renegotiate_price.title": "Renegotiate price",
    "action.renegotiate_price.description": "Revisit the master contract with the customer and realign toward plan CM.",
    "action.reprice_hourly.title": "Reprice hourly rates",
    "action.reprice_hourly.description": "Lift hourly rates closer to the cohort median; customer alignment required.",
    "action.audit_subcontractors.title": "Subcontractor audit",
    "action.audit_subcontractors.description": "Review subcontractor invoices; eliminate cost drivers and duplicate billings.",
    "action.reduce_subcontractor_share.title": "Reduce subcontractor share",
    "action.reduce_subcontractor_share.description": "Grow in-house staff or shift order mix to lower the subcontractor ratio.",
    "action.labor_cost_audit.title": "Labor cost audit",
    "action.labor_cost_audit.description": "Review staffing, overtime and training hours; bring them back to plan.",
    "action.productivity_improvement.title": "Productivity improvement",
    "action.productivity_improvement.description": "Revisit deployment flow, routing and tooling to raise productive hours.",
    "action.absence_intervention.title": "Absence intervention",
    "action.absence_intervention.description": "Coach team leaders, adjust health/safety and staffing rotation.",
    "action.reduce_scope.title": "Reduce scope",
    "action.reduce_scope.description": "Agree scope reduction with the customer; carve out unprofitable services.",
    "action.terminate_contract.title": "Terminate contract",
    "action.terminate_contract.description": "Prepare termination if countermeasures cannot restore margin sustainably.",
    "action.renewal_outreach.title": "Renewal outreach",
    "action.renewal_outreach.description": "Engage the customer before contract end; negotiate new terms.",
    "action.training_investment.title": "Training investment",
    "action.training_investment.description": "Adapt onboarding to close the productivity gap vs cohort median.",
    "action.quality_remediation.title": "Quality remediation",
    "action.quality_remediation.description": "Prioritise rework, run SLA meetings, tighten inspection plan.",

    # Cost-driver sub-actions
    "sub_action.audit_overtime.title": "Audit overtime + direct-labor deployment",
    "sub_action.reduce_labor_overhead.title": "Recheck labor overhead / surcharges",
    "sub_action.shorten_onboarding.title": "Shorten onboarding duration",
    "sub_action.stagger_vacations.title": "Stagger holiday planning",
    "sub_action.absence_intervention.title": "Targeted absence intervention",
    "sub_action.renegotiate_external_rates.title": "Renegotiate external subcontractor rates",
    "sub_action.rebalance_group_sourcing.title": "Rebalance group-internal sourcing",
    "sub_action.rebalance_division_sourcing.title": "Rebalance division-internal sourcing",
    "sub_action.reduce_break_overrun.title": "Tighten break-time control",
    "sub_action.labor_cost_audit.title": "Labor cost audit",
    "sub_action.procurement_review.title": "Procurement review",
    "sub_action.fleet_audit.title": "Fleet / routing audit",
    "sub_action.travel_policy_review.title": "Travel policy review",
    "sub_action.reprice_hourly_detail.title": "Uplift hourly rates",
    "sub_action.renegotiate_fixed_price.title": "Renegotiate fixed price",
    "sub_action.renewal_outreach_detail.title": "Early renewal conversation",

    # Column labels
    "column.labor_direct": "Direct labor",
    "column.labor_overhead": "Labor overhead",
    "column.training_cost": "Training",
    "column.vacation_cost": "Vacation",
    "column.sick_cost": "Sick leave",
    "column.subcontractor_external": "Subcontractor external",
    "column.subcontractor_group": "Subcontractor group",
    "column.subcontractor_division": "Subcontractor division",
    "column.hours_break": "Break hours",
    "column.hours_training": "Training hours",
    "column.labor_cost_total": "Labor cost total",
    "column.subcontractor_services_total": "Subcontractor total",
    "column.material_cost": "Material",
    "column.vehicle_cost": "Vehicle",
    "column.travel_cost": "Travel",
    "column.revenue_hourly": "Revenue - Hourly",
    "column.revenue_fixed": "Revenue - Fixed",
    "column.revenue_total": "Revenue - Total",

    # Driver evidence table
    "solutions.col.driver": "Root cause (data column)",
    "solutions.col.driver_delta": "Delta",
    "solutions.col.driver_fix": "Concrete fix",
    "solutions.driver_share": "{pct:.0f}% of the gap",
    "solutions.drivers_title": "Drivers + concrete fixes",
    "solutions.drivers_empty": "No clear cost drivers identified.",

    # Panel intro + KPI strip
    "solutions.intro_title": "How this list is built",
    "solutions.intro_body": (
        "Three questions are answered automatically:\n\n"
        "**1. What is the problem?** Rule-based diagnosis from plan "
        "deviation, peer-cohort comparison and early-warning signals.\n\n"
        "**2. Which data column is to blame?** Cost columns (direct "
        "labor, external subcontractor, sick cost, ...) are compared to "
        "their own 3-month average. The largest deviation wins.\n\n"
        "**3. What to do?** Each data column is mapped to a concrete "
        "action (direct labor up -> audit overtime). The EUR figure is "
        "conservative and capped at 30% of monthly revenue or the "
        "monthly loss."
    ),
    "solutions.kpi_title": "Key numbers this month",
    "solutions.kpi_cm": "Contribution margin (actual)",
    "solutions.kpi_cm_plan": "Contribution margin (plan)",
    "solutions.kpi_gap": "Gap to plan",
    "solutions.kpi_revenue": "Revenue",
    "solutions.kpi_score": "Overall score",

    # Per-action card: three-question layout
    "solutions.q1_title": "What we'll do",
    "solutions.q2_title": "Why this helps",
    "solutions.q3_title": "What it's worth",
    "solutions.q3_math_title": "How the number was calculated",
    "solutions.q3_cap_note": (
        "After cap: limited to **{capped}/month** "
        "(max 30% of monthly revenue or the monthly loss)."
    ),
    "solutions.q3_outcome_cost": (
        "If executed, the affected costs drop by about "
        "**{impact}/month**. At the same revenue, the contract's "
        "contribution margin rises by the same amount."
    ),
    "solutions.q3_outcome_revenue": (
        "If executed, revenue rises by about **{impact}/month**. "
        "At the same cost base, the full amount flows into margin."
    ),
    "solutions.q3_outcome_retention": (
        "On successful renewal, roughly **{impact}/month** of revenue "
        "stays in the portfolio."
    ),
    "solutions.q3_outcome_scope": (
        "After scope reduction or termination, the monthly loss of "
        "about **{impact}/month** is stopped."
    ),
    "solutions.meta_owner": "Owner: **{owner}**",
    "solutions.meta_timeframe": "Timeframe: **{weeks} weeks**",
    "solutions.meta_confidence": "Confidence: **{conf}**",
    "solutions.ready_to_track": "Ready to track?",
    "solutions.no_drivers_text": (
        "No single data column dominates this gap. "
        "The action applies broadly to the cost structure."
    ),

    # "What we will do" lead sentence per action
    "what_prose.renegotiate_price": "Negotiate a new master price with the customer that fairly reflects the current service.",
    "what_prose.reprice_hourly": "Lift hourly rates with the customer until labor ratio is on par with the cohort.",
    "what_prose.audit_subcontractors": "Review subcontractor invoices from the last 3 months and claim back any discrepancies.",
    "what_prose.reduce_subcontractor_share": "Progressively move services from subcontractors to in-house staff.",
    "what_prose.labor_cost_audit": "Walk the labor-cost structure systematically (overtime, shifts, onboarding) and realign to plan.",
    "what_prose.productivity_improvement": "Observe operations on site for one week, identify friction points and ship a quick-fix within 14 days.",
    "what_prose.absence_intervention": "Cut the absence rate through team-lead conversations and prevention measures.",
    "what_prose.reduce_scope": "Agree a scope reduction or fixed-price adjustment with the customer and amend the contract annex.",
    "what_prose.terminate_contract": "Terminate the contract in an orderly way; check notice periods and staff redeployment up-front.",
    "what_prose.renewal_outreach": "Start renewal negotiations 90-120 days before contract end.",
    "what_prose.training_investment": "Run a targeted training plan to close the productivity gap vs cohort median.",
    "what_prose.quality_remediation": "Prioritise a rework plan with teams and set an SLA review meeting with the customer.",

    # "Why this helps" short prose per action
    "why_prose.renegotiate_price": (
        "The contract delivers less contribution margin than planned. "
        "A price adjustment brings revenue and margin back to the "
        "originally calculated level without changing operations."
    ),
    "why_prose.reprice_hourly": (
        "The labor ratio is above what comparable contracts command. "
        "Lifting hourly rates closes the gap without touching "
        "deployment planning."
    ),
    "why_prose.audit_subcontractors": (
        "Subcontractor invoices often contain duplicate billings, "
        "unauthorised surcharges or wrong hourly rates. An audit "
        "finds these and claims them back."
    ),
    "why_prose.reduce_subcontractor_share": (
        "Too much work runs through subcontractors, who are more "
        "expensive than in-house staff. Shifting services in-house "
        "lowers the cost base sustainably."
    ),
    "why_prose.labor_cost_audit": (
        "Labor cost is above plan. The cause is usually overtime, "
        "wrong shift planning or unbooked onboarding. A structured "
        "audit finds the drivers and brings them back to plan."
    ),
    "why_prose.productivity_improvement": (
        "Productive hours are below target. A week of on-site "
        "observation reveals tooling, routing or coordination "
        "issues. Small fixes move productivity measurably."
    ),
    "why_prose.absence_intervention": (
        "The absence rate is well above cohort. Each percentage "
        "point of absence creates substitute and overtime cost. "
        "Focused conversations reduce the rate within weeks."
    ),
    "why_prose.reduce_scope": (
        "The contract is not profitable in its current shape. "
        "Removing specific services stops the bleed without "
        "losing the customer."
    ),
    "why_prose.terminate_contract": (
        "No countermeasure can restore a sustainable margin. Every "
        "additional month costs money. Orderly termination stops "
        "the loss and frees staff for profitable contracts."
    ),
    "why_prose.renewal_outreach": (
        "The contract ends in the next months. Without action the "
        "full revenue disappears. Early customer contact secures "
        "renewal on better terms."
    ),
    "why_prose.training_investment": (
        "Productivity is below cohort median because onboarding "
        "does not fit. Targeted training closes the gap to "
        "comparable sites."
    ),
    "why_prose.quality_remediation": (
        "The quality target is missed. Untreated, SLA penalties, "
        "rework and customer loss loom. An inspection plan and "
        "SLA review stabilise the contract."
    ),

    # KPI gap detector
    "gaps.section_title": "Which KPIs would sharpen this diagnosis?",
    "gaps.section_sub": "These data points would make the root-cause analysis more conclusive.",
    "gaps.section_hint": "Missing data",
    "gaps.empty": "The available data is sufficient for the main causes.",
    "gaps.overtime_hours.title": "Overtime hours",
    "gaps.overtime_hours.reason": "Without overtime hours we cannot separate extra work from headcount growth.",
    "gaps.headcount_fte.title": "Headcount / FTE",
    "gaps.headcount_fte.reason": "FTE figures let us compute cost change per head.",
    "gaps.absence_reason.title": "Absence reason breakdown",
    "gaps.absence_reason.reason": "Separates one-off absences (flu wave) from structural issues.",
    "gaps.subcontractor_hours.title": "Subcontractor hours",
    "gaps.subcontractor_hours.reason": "Lets us compare the external hourly rate with the internal one.",
    "gaps.subcontractor_reason.title": "Subcontractor usage reason",
    "gaps.subcontractor_reason.reason": "Overflow or specialty work? Different root causes need different actions.",
    "gaps.billable_hours.title": "Billable hours",
    "gaps.billable_hours.reason": "Separates price from volume effect on a revenue move.",
    "gaps.price_per_hour.title": "Price per hour",
    "gaps.price_per_hour.reason": "Shows whether the revenue shift comes from price or volume.",
    "gaps.customer_churn.title": "Customer churn",
    "gaps.customer_churn.reason": "A one-off customer loss and a broad demand decline imply different responses.",
    "gaps.quality_kpi.title": "Quality KPI",
    "gaps.quality_kpi.reason": "Shows whether cost cuts are eroding service quality.",
    "gaps.plan_values.title": "Plan values (planned CM)",
    "gaps.plan_values.reason": "No plan comparison possible; only a prior-month baseline is available.",
    "gaps.missing_driver.title": "Additional cost categories",
    "gaps.missing_driver.reason": "Unexplained residual is material - one or more cost lines are missing from the model.",
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
