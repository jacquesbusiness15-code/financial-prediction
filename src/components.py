"""Reusable UI primitives for the WISAG Financial Co-Pilot."""
from __future__ import annotations

from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.glossary import g
from src.i18n import t
from src.styles import inject_global_css
from src.theme import SEVERITY_COLORS

LOGO_PATH = Path("assets/wisag_logo.svg")


@lru_cache(maxsize=1)
def _logo_svg() -> str:
    """Return raw SVG string, sized and inline-embeddable, or empty if missing."""
    if not LOGO_PATH.exists():
        return ""
    try:
        return LOGO_PATH.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


def _render_logo(width_px: int = 140) -> None:
    svg = _logo_svg()
    if not svg:
        return
    # Strip the XML/DOCTYPE prologue — browsers render inline <svg> fine without it.
    idx = svg.find("<svg")
    if idx > 0:
        svg = svg[idx:]
    st.markdown(
        f"<div style='width:{width_px}px;margin-bottom:8px;'>{svg}</div>",
        unsafe_allow_html=True,
    )


def setup_page(page_title_key: str, icon: str | None = None) -> None:
    """Call once at the very top of each page (before any st.* output).

    Wraps st.set_page_config + CSS injection so every page has a consistent frame.
    """
    page_icon = icon or "📊"
    st.set_page_config(
        page_title=t(page_title_key),
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_css()


def page_header(title_key: str, subtitle_key: str | None = None,
                icon: str | None = None) -> None:
    """Standard top-of-page block. Shows the WISAG logo + title + optional subtitle."""
    _render_logo(width_px=140)
    title = (f"{icon}  " if icon else "") + t(title_key)
    st.markdown(f"<h1 style='margin-bottom:0.2rem'>{escape(title)}</h1>",
                unsafe_allow_html=True)
    if subtitle_key:
        st.caption(t(subtitle_key))


def language_switcher() -> None:
    """Render a compact DE/EN language toggle in the sidebar.

    Binds to st.session_state["lang"] via the widget `key`, so changes are
    picked up automatically by i18n.get_lang() on the next rerun.
    """
    if "lang" not in st.session_state:
        st.session_state["lang"] = "de"
    with st.sidebar:
        st.radio(
            t("sidebar.language"),
            options=["de", "en"],
            key="lang",
            format_func=lambda code: t(f"lang.{code}"),
            horizontal=True,
            label_visibility="collapsed",
        )


def sidebar_logo() -> None:
    """Render the logo and language switcher at the top of the sidebar."""
    with st.sidebar:
        _render_logo(width_px=120)
    language_switcher()


# ---------------------------------------------------------------------------
# Custom sidebar nav — icon + label + optional badge + sticky Ask-AI CTA
# ---------------------------------------------------------------------------

_NAV_ITEMS: list[tuple[str, str, str]] = [
    # (icon, i18n_label_key, page_path) — mirrors the reference mock's 7 items.
    ("🏠", "nav.overview_short",   "pages/1_Portfolio_Overview.py"),
    ("📊", "nav.analytics_short",  "pages/2_Deep_Dive.py"),
    ("🔮", "nav.forecasts_short",  "pages/5_Plan_vs_Actual.py"),
    ("🧪", "nav.scenarios_short",  "pages/4_Copilot_Chat.py"),
    ("📄", "nav.reports_short",    "pages/5_Plan_vs_Actual.py"),
    ("🔔", "nav.alerts_short",     "pages/3_Early_Warnings.py"),
    ("⚙", "nav.settings_short",    "app.py"),
]


def sidebar_nav(active_path: str, alerts_count: int = 0) -> None:
    """Render an icon+label nav in the sidebar using real `st.page_link`s.

    The visual treatment (hover/active background, icon sizing, the red alert
    count on the Frühwarnungen item, the orange Ask-AI CTA at the bottom) is
    delivered entirely by CSS targeting Streamlit's `stPageLink` test-ids.
    `alerts_count` > 0 surfaces as " • N" appended to the Alerts label, which
    CSS then rewrites into a pill via `::after`/content — but for portability
    we just append the count inline so it's visible without custom styling.
    """
    if not hasattr(st, "page_link"):
        return  # very old Streamlit — skip the custom nav gracefully

    with st.sidebar:
        st.markdown("<div class='wisag-sidebar-nav'>", unsafe_allow_html=True)
        for icon, key, path in _NAV_ITEMS:
            label = t(key)
            if key == "nav.alerts_short" and alerts_count > 0:
                label = f"{label}  •  {alerts_count}"
            st.page_link(path, label=f"{icon}  {label}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Ask-AI CTA — styled via the `.wisag-askai` wrapper class.
        st.markdown("<div class='wisag-askai'>", unsafe_allow_html=True)
        st.page_link("pages/4_Copilot_Chat.py",
                     label=f"✨  {t('nav.ask_ai')}  →")
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Icon tile / status pill / driver row / hero helpers
# ---------------------------------------------------------------------------

def icon_tile(icon: str, variant: str = "purple", *, small: bool = False) -> str:
    """Return HTML for a rounded-square icon tile (colored background + emoji)."""
    cls = f"wisag-icon-tile wisag-icon-tile--{variant}"
    if small:
        cls += " wisag-icon-tile--sm"
    return f"<span class='{cls}'>{escape(icon)}</span>"


def status_pill(level: str, label: str) -> str:
    """Critical / warn / healthy pill with a colored dot."""
    lvl = (level or "warn").lower()
    if lvl not in ("critical", "warn", "healthy"):
        lvl = "warn"
    return (f"<span class='wisag-status-pill wisag-status-pill--{lvl}'>"
            f"{escape(label)}</span>")


def driver_row(icon: str, title: str, subtitle: str,
               pct_label: str, variant: str = "neg",
               *, tile_variant: str | None = None,
               show_chevron: bool = True) -> str:
    """Return HTML for one row inside the Why-drop / What-do cards.

    `variant` controls the pct-pill color ("pos" | "neg").
    `tile_variant` controls the icon tile background; defaults to match variant.
    """
    tile_variant = tile_variant or ("red" if variant == "neg" else "green")
    pct_cls = "wisag-driver-pct--pos" if variant == "pos" else "wisag-driver-pct--neg"
    chev = ("<span class='wisag-driver-chev'>›</span>"
            if show_chevron else "<span></span>")
    return f"""
<div class='wisag-driver-row'>
  {icon_tile(icon, tile_variant, small=True)}
  <div>
    <p class='wisag-driver-title'>{escape(title)}</p>
    <p class='wisag-driver-sub'>{escape(subtitle)}</p>
  </div>
  <span class='wisag-driver-pct {pct_cls}'>{escape(pct_label)}</span>
  {chev}
</div>
"""


def kpi_tile(label_key: str, value: str, *, delta: str | None = None,
             delta_negative_is_bad: bool = True, help_key: str | None = None) -> None:
    """Branded KPI tile using st.metric + tooltip from the glossary."""
    help_text = g(help_key) if help_key else None
    delta_color = "inverse" if delta_negative_is_bad else "normal"
    st.metric(label=t(label_key), value=value, delta=delta,
              delta_color=delta_color if delta is not None else "off",
              help=help_text or None)


def severity_badge(level: str) -> str:
    """Return an HTML pill for a severity level. Use via st.markdown(..., unsafe_allow_html=True)."""
    lvl = (level or "low").lower()
    label = SEVERITY_COLORS.get(lvl, {}).get("label", level)
    klass = f"wisag-badge wisag-badge-{lvl}"
    return f"<span class='{klass}'>{escape(label)}</span>"


def impact_pill(eur: float) -> str:
    """€-formatted pill, colored by sign."""
    if pd.isna(eur):
        return "<span class='wisag-pill wisag-pill-neu'>—</span>"
    klass = "wisag-pill-pos" if eur >= 0 else "wisag-pill-neg"
    return f"<span class='wisag-pill {klass}'>{eur:+,.0f} €</span>".replace(",", ".")


def _fmt_euro(v) -> str:
    if pd.isna(v):
        return "—"
    return f"{v:,.0f} €".replace(",", ".")


def _fmt_pct(v) -> str:
    if pd.isna(v):
        return "—"
    return f"{v:+.1%}".replace(".", ",")


def anomaly_card(row: pd.Series, key: str | None = None) -> None:
    """Card UI for a single anomaly row — replaces raw DataFrame display."""
    cc_id = row.get("cost_center_id", "—")
    cc_name = row.get("cost_center_name") or ""
    region = row.get("region", "—")
    service = row.get("service_type", "")
    period = row.get("period")
    period_txt = period.strftime("%Y-%m") if pd.notna(period) else "—"
    severity = (row.get("severity") or "low").lower()
    impact = row.get("impact_eur", 0) or 0
    cm = row.get("cm_db")
    reasons = row.get("anomaly_reasons") or ""

    reasons_de = _translate_reasons(reasons)

    html = f"""
<div class='wisag-card wisag-card-accent'>
  <div style='display:flex;justify-content:space-between;align-items:flex-start;gap:12px;'>
    <div style='flex:1;min-width:0;'>
      <div class='wisag-card-title'>
        {escape(str(cc_id))} · {escape(str(cc_name))}
      </div>
      <div class='wisag-card-meta'>
        {escape(str(region))}{' · ' + escape(str(service)) if service else ''} · {escape(period_txt)}
      </div>
      <div class='wisag-card-body'>
        {escape(reasons_de) if reasons_de else ''}
      </div>
    </div>
    <div style='text-align:right;min-width:180px;'>
      {severity_badge(severity)}<br/>
      <div style='font-size:0.80rem;color:#6B6B6B;margin-top:8px;'>Euro-Wirkung</div>
      <div style='font-size:1.20rem;font-weight:700;color:#1D1D1B;'>
        {_fmt_euro(impact)}
      </div>
      <div style='font-size:0.80rem;color:#6B6B6B;margin-top:4px;'>
        DB: {_fmt_euro(cm) if cm is not None else '—'}
      </div>
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def warning_card(row: pd.Series) -> None:
    """Card UI for an early-warning row."""
    cc_id = row.get("cost_center_id", "—")
    cc_name = row.get("cost_center_name") or ""
    region = row.get("region", "—")
    signal_en = row.get("signal", "")
    signal_de = t(f"signal.{signal_en}")
    if signal_de == f"signal.{signal_en}":
        signal_de = signal_en
    detail = row.get("detail", "")
    severity = (row.get("severity") or "low").lower()
    impact = row.get("impact_eur", 0) or 0
    period = row.get("period")
    period_txt = period.strftime("%Y-%m") if pd.notna(period) else "—"

    html = f"""
<div class='wisag-card wisag-card-accent'>
  <div style='display:flex;justify-content:space-between;align-items:flex-start;gap:12px;'>
    <div style='flex:1;min-width:0;'>
      <div style='margin-bottom:4px;'>
        {severity_badge(severity)}
        <span style='font-weight:600;color:#1D1D1B;margin-left:6px;'>
          {escape(signal_de)}
        </span>
      </div>
      <div class='wisag-card-title'>
        {escape(str(cc_id))} · {escape(str(cc_name))}
      </div>
      <div class='wisag-card-meta'>
        {escape(str(region))} · {escape(period_txt)}
      </div>
      <div class='wisag-card-body'>
        {escape(str(detail))}
      </div>
    </div>
    <div style='text-align:right;min-width:160px;'>
      <div style='font-size:0.80rem;color:#6B6B6B;'>Euro-Wirkung</div>
      <div style='font-size:1.20rem;font-weight:700;color:#1D1D1B;'>
        {_fmt_euro(impact)}
      </div>
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def nav_card(icon: str, title_key: str, desc_key: str, page_path: str) -> None:
    """Landing-page navigation card with an 'Öffnen' button."""
    title = t(title_key)
    desc = t(desc_key)
    html = f"""
<div class='wisag-nav-card'>
  <div class='wisag-nav-card-icon'>{icon}</div>
  <div class='wisag-nav-card-title'>{escape(title)}</div>
  <div class='wisag-nav-card-desc'>{escape(desc)}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=f"{t('nav.open')} →", icon=None)


def friendly_error(message: str, details: str | None = None) -> None:
    """Wrap st.error with a German message + collapsible raw details."""
    st.error(message, icon="⚠️")
    if details:
        with st.expander(t("action.details")):
            st.code(details)


_REASON_TRANSLATIONS = {
    "CM < 0": "Deckungsbeitrag negativ",
    "big MoM jump": "starker Monatssprung",
    "regime flip to negative": "Umschwung ins Negative",
    "plan miss >15%": "Plan-Abweichung > 15 %",
    "z-outlier": "statistischer Ausreißer",
}


def _translate_reasons(reasons: str) -> str:
    """Translate the comma-separated anomaly_reasons string into German."""
    if not reasons:
        return ""
    parts = [p.strip() for p in reasons.split(",")]
    out = []
    for p in parts:
        if p in _REASON_TRANSLATIONS:
            out.append(_REASON_TRANSLATIONS[p])
        elif p.startswith("labor ratio "):
            out.append(p.replace("labor ratio ", "Personalquote "))
        elif p.startswith("z=") and "σ" in p:
            out.append(f"statistischer Ausreißer ({p})")
        else:
            out.append(p)
    return " · ".join(out)
