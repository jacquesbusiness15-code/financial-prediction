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
        f"<div class='wisag-logo' style='width:{width_px}px;margin-bottom:8px;'>{svg}</div>",
        unsafe_allow_html=True,
    )


def _apply_query_params() -> None:
    """Read `?lang=` from the URL, sync to session_state, then strip.

    The sidebar language switcher uses real <a href='?lang=en'> links so it
    works without fighting Streamlit's widget flow. This function makes them
    actually stick.
    """
    qp = st.query_params
    if "lang" in qp:
        val = qp["lang"]
        if val in ("de", "en"):
            st.session_state["lang"] = val
        del qp["lang"]


def setup_page(page_title_key: str, icon: str | None = None) -> None:
    """Call once at the very top of each page (before any st.* output).

    Wraps st.set_page_config + query-param sync + CSS injection so every page
    has a consistent frame and picks up the active theme/language.
    """
    st.set_page_config(
        page_title=t(page_title_key),
        page_icon=icon or None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_query_params()
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


def page_section_header(title_key: str, subtitle_key: str | None = None,
                        *, icon_html: str | None = None) -> None:
    """Small title block used at the top of every subpage body.

    Renders a ``.wisag-page-header`` flex row with an h2 and optional
    subtitle. Replaces the inline ``<div style='display:flex;...'>`` block
    that used to be duplicated across every subpage.
    """
    title = t(title_key)
    sub = t(subtitle_key) if subtitle_key else ""
    sub_html = (
        f"<p class='wisag-section-sub wisag-page-header-sub'>{escape(sub)}</p>"
        if sub else ""
    )
    icon_block = f"<div>{icon_html}</div>" if icon_html else ""
    st.markdown(
        f"<div class='wisag-page-header'>"
        f"{icon_block}"
        f"<div>"
        f"<h2>{escape(title)}</h2>"
        f"{sub_html}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def sidebar_language_switcher() -> None:
    """Render a compact DE · EN language switcher in the sidebar."""
    lang = st.session_state.get("lang", "de")
    de_cls = "is-active" if lang == "de" else ""
    en_cls = "is-active" if lang == "en" else ""
    with st.sidebar:
        st.markdown(
            f"""
<div class='wisag-lang-switch'>
  <a href='?lang=de' target='_self' class='{de_cls}'>DE</a>
  <span class='wisag-lang-sep'>·</span>
  <a href='?lang=en' target='_self' class='{en_cls}'>EN</a>
</div>
""",
            unsafe_allow_html=True,
        )


def sidebar_logo() -> None:
    """Render the WISAG logo at the top of the sidebar."""
    with st.sidebar:
        _render_logo(width_px=140)


# ---------------------------------------------------------------------------
# Sidebar nav
# ---------------------------------------------------------------------------

_NAV_PAGES: list[tuple[str, str, str]] = [
    # (page_path, i18n_label_key, icon)
    ("app.py", "nav.overview_short", ""),
]


def sidebar_nav(active: str = "overview", alerts_count: int = 3) -> None:  # noqa: ARG001
    """Render the sidebar nav.

    Only the Overview entry is shown; other sections were removed.

    ``active`` and ``alerts_count`` are retained for call-site compatibility
    but are no longer used.
    """
    with st.sidebar:
        st.markdown("<nav class='wisag-sidebar-nav'>", unsafe_allow_html=True)
        for page_path, key, icon in _NAV_PAGES:
            st.page_link(page_path, label=t(key), icon=icon or None)
        st.markdown("</nav>", unsafe_allow_html=True)


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
               show_chevron: bool = True,
               href: str | None = None,
               rationale: str | None = None) -> str:
    """Return HTML for one row inside the Why-drop / What-do cards.

    `variant` controls the pct-pill color ("pos" | "neg").
    `tile_variant` controls the icon tile background; defaults to match variant.
    `href` makes the whole row a clickable link to that route.
    `rationale` renders a second subtitle line (italicised) explaining *why*
    this row matters — used for "Why this cuts cost" hints on action rows.
    """
    tile_variant = tile_variant or ("red" if variant == "neg" else "green")
    pct_cls = "wisag-driver-pct--pos" if variant == "pos" else "wisag-driver-pct--neg"
    chev = ("<span class='wisag-driver-chev'>›</span>"
            if show_chevron else "<span></span>")
    rationale_html = (
        f"<p class='wisag-driver-why'>{escape(rationale)}</p>"
        if rationale else ""
    )
    inner = f"""
<div class='wisag-driver-row'>
  {icon_tile(icon, tile_variant, small=True)}
  <div>
    <p class='wisag-driver-title'>{escape(title)}</p>
    <p class='wisag-driver-sub'>{escape(subtitle)}</p>
    {rationale_html}
  </div>
  <span class='wisag-driver-pct {pct_cls}'>{escape(pct_label)}</span>
  {chev}
</div>
"""
    if href:
        return (f"<a class='wisag-driver-row-link' href='{escape(href)}' "
                f"target='_self'>{inner}</a>")
    return inner


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
  <div class='wisag-anomaly-row'>
    <div class='wisag-anomaly-body'>
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
    <div class='wisag-anomaly-right'>
      {severity_badge(severity)}<br/>
      <div class='wisag-impact-label'>Euro-Wirkung</div>
      <div class='wisag-impact-value'>{_fmt_euro(impact)}</div>
      <div class='wisag-impact-sub'>DB: {_fmt_euro(cm) if cm is not None else '—'}</div>
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Signal → icon / tile color (keeps warning cards visual-first, not text-first)
# ---------------------------------------------------------------------------

_SIGNAL_ICON: dict[str, str] = {
    "Declining CM trend":     "",
    "Absence spike":          "",
    "Productivity drop":      "",
    "Subcontractor creep":    "",
    "Contract renewal risk":  "",
    "Plan gap widening":      "",
}

_SEVERITY_TILE: dict[str, str] = {
    "high":   "red",
    "medium": "orange",
    "low":    "green",
}


def warning_card(row: pd.Series) -> None:
    """Card UI for an early-warning row — driver-row shape to match the mock."""
    cc_id = row.get("cost_center_id", "—")
    cc_name = row.get("cost_center_name") or ""
    region = row.get("region", "—")
    signal_en = row.get("signal", "")
    signal_label = t(f"signal.{signal_en}")
    if signal_label == f"signal.{signal_en}":
        signal_label = signal_en
    severity = (row.get("severity") or "low").lower()
    impact = row.get("impact_eur", 0) or 0
    period = row.get("period")
    period_txt = period.strftime("%b %Y") if pd.notna(period) else "—"

    icon = _SIGNAL_ICON.get(signal_en, "")
    tile_variant = _SEVERITY_TILE.get(severity, "red")
    subtitle_bits = [str(cc_id)]
    if cc_name:
        subtitle_bits.append(str(cc_name))
    subtitle_bits.append(str(region))
    subtitle_bits.append(period_txt)
    subtitle = " · ".join(subtitle_bits)

    # Use the same driver_row shape the mock uses for "Why" / "What" rows,
    # with an €-delta pill on the right instead of a %-pill.
    impact_cls = "wisag-driver-pct--neg" if impact < 0 else "wisag-driver-pct--pos"
    impact_label = _fmt_euro(impact)

    html = f"""
<div class='wisag-warning-card'>
  <div class='wisag-driver-row' style='border-top:none;padding:2px 0;'>
    {icon_tile(icon, tile_variant, small=True)}
    <div>
      <p class='wisag-driver-title'>{escape(signal_label)}</p>
      <p class='wisag-driver-sub'>{escape(subtitle)}</p>
    </div>
    <span class='wisag-driver-pct {impact_cls}'>{escape(impact_label)}</span>
    <span class='wisag-driver-chev'>›</span>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def nav_card(icon: str, title_key: str, desc_key: str, page_path: str) -> None:
    """Legacy landing-page nav card (kept for compatibility — new pages use `nav_tile`)."""
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


# ---------------------------------------------------------------------------
# Shared primitives that every revamped page uses
# ---------------------------------------------------------------------------

def topbar(breadcrumb_label: str | None = None,
           *, breadcrumb_href: str = "/") -> None:
    """Open a `.wisag-topbar-grid` row. Caller fills the right side with widgets.

    Usage:
        l, r = topbar_cols()
        with l: ...breadcrumb...
        with r: ...controls...
    """
    st.markdown("<div class='wisag-topbar-grid'>", unsafe_allow_html=True)
    if breadcrumb_label:
        st.markdown(
            f"<a class='wisag-breadcrumb' href='{escape(breadcrumb_href)}' target='_self'>"
            f"‹ {escape(breadcrumb_label)}</a>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def hero_card(*, icon_html: str | None = None,
              title: str = "", subtitle: str = "",
              status_level: str | None = None, status_label: str | None = None,
              metrics: list[dict] | None = None,
              chart_svg: str | None = None) -> None:
    """Render the mock's hero card: identity block + inline metrics + optional chart.

    `metrics` is a list of {label, value, variant? ("pos"|"neg"|None)}.
    `icon_html` is pre-rendered HTML for the leading icon tile / initial.
    """
    metrics = metrics or []
    metrics_html = ""
    for m in metrics:
        val_cls = ""
        if m.get("variant") == "neg":
            val_cls = "wisag-hero-metric-value--neg"
        elif m.get("variant") == "pos":
            val_cls = "wisag-hero-metric-value--pos"
        metrics_html += (
            f"<div>"
            f"  <div class='wisag-hero-metric-label'>{escape(str(m.get('label','')))}</div>"
            f"  <div class='wisag-hero-metric-value {val_cls}'>{m.get('value','')}</div>"
            f"</div>"
        )

    status_html = ""
    if status_level and status_label:
        status_html = status_pill(status_level, status_label)

    chart_html = (
        f"<div class='wisag-hero-chart'>{chart_svg}</div>" if chart_svg else ""
    )

    st.markdown(
        f"""
<div class='wisag-hero-card'>
  <div class='wisag-hero-identity'>
    <div class='wisag-hero-name-block'>
      {icon_html or ''}
      <div>
        <h2 class='wisag-hero-title'>{escape(title)}</h2>
        <p class='wisag-hero-sub'>{escape(subtitle) or '&nbsp;'}</p>
        {status_html}
      </div>
    </div>
    <div class='wisag-hero-metrics'>{metrics_html}</div>
    {chart_html}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def section_card(*, title: str, subtitle: str = "",
                 rows_html: str = "", hint: str | None = None,
                 footer_link: dict | None = None) -> None:
    """Render the "Why drop" / "What do" style card.

    `footer_link` optionally renders a muted "View all ›" footer row;
    shape: {"label": str, "href": str}.
    """
    hint_html = (
        f"<div class='wisag-section-hint'>{escape(hint)}</div>" if hint else ""
    )
    footer_html = ""
    if footer_link:
        footer_html = (
            f"<a class='wisag-section-footer' "
            f"href='{escape(str(footer_link.get('href', '#')))}' target='_self'>"
            f"{escape(str(footer_link.get('label', '')))}"
            f"</a>"
        )
    st.markdown(
        f"""
<div class='wisag-section-card'>
  <div class='wisag-section-head'>
    <div>
      <h3 class='wisag-section-title'>{escape(title)}</h3>
      <p class='wisag-section-sub'>{escape(subtitle) or '&nbsp;'}</p>
    </div>
    {hint_html}
  </div>
  {rows_html or ''}
  {footer_html}
</div>
""",
        unsafe_allow_html=True,
    )


def suggestion_chips(chips: list[str], *, state_key: str = "suggestion_clicked") -> str | None:
    """Render a compact row of clickable suggestion chips.

    Returns the clicked chip's label on the rerun it was clicked, else None.
    Uses `st.button` so the click triggers a normal rerun.
    """
    cols = st.columns(max(1, len(chips)))
    clicked: str | None = None
    for i, chip in enumerate(chips):
        with cols[i]:
            if st.button(chip, key=f"chip_{state_key}_{i}",
                         use_container_width=True):
                clicked = chip
    return clicked


def nav_tile(icon: str, title_key: str, page_path: str,
             *, variant: str = "purple") -> None:
    """Landing-page nav tile — pastel icon tile + title, no description paragraph.

    Renders a visual tile that is a child of a `.wisag-nav-tile` wrapper, with
    a real `st.page_link` inside for navigation. CSS dresses the page_link to
    sit under the tile.
    """
    title = t(title_key)
    st.markdown(
        f"<div class='wisag-nav-tile wisag-nav-tile--{variant}'>"
        f"  {icon_tile(icon, variant)}"
        f"  <div class='wisag-nav-tile-title'>{escape(title)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=f"{title} →")


def friendly_error(message: str, details: str | None = None) -> None:
    """Wrap st.error with a German message + collapsible raw details."""
    st.error(message)
    if details:
        with st.expander(t("action.details")):
            st.code(details)


_REASON_TRANSLATIONS = {
    "CM < 0": "Marge negativ",
    "big MoM jump": "starke Veränderung zum Vormonat",
    "regime flip to negative": "Wechsel ins Minus",
    "plan miss >15%": "mehr als 15 % unter Plan",
    "z-outlier": "ungewöhnlicher Wert",
}


def _translate_reasons(reasons: str) -> str:
    """Translate the comma-separated anomaly_reasons string into plain German."""
    if not reasons:
        return ""
    parts = [p.strip() for p in reasons.split(",")]
    out = []
    for p in parts:
        if p in _REASON_TRANSLATIONS:
            out.append(_REASON_TRANSLATIONS[p])
        elif p.startswith("labor ratio "):
            out.append(p.replace("labor ratio ", "Personalkosten "))
        elif p.startswith("z=") and "σ" in p:
            out.append("ungewöhnlicher Wert")
        else:
            out.append(p)
    return " · ".join(out)
