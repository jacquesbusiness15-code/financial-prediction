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
ICON_PATH = Path("assets/wisag_icon.png")


@lru_cache(maxsize=1)
def _logo_svg() -> str:
    if not LOGO_PATH.exists():
        return ""
    try:
        return LOGO_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def _render_logo(width_px: int = 140) -> None:
    svg = _logo_svg()
    if not svg:
        return
    # Strip XML/DOCTYPE prologue — inline <svg> renders fine without it.
    idx = svg.find("<svg")
    if idx > 0:
        svg = svg[idx:]
    st.markdown(
        f"<div class='wisag-logo' style='width:{width_px}px;margin-bottom:8px;'>{svg}</div>",
        unsafe_allow_html=True,
    )


def _apply_query_params() -> None:
    # Sidebar language switcher uses real <a href='?lang=en'> links to bypass
    # Streamlit's widget flow; this moves the value into session_state.
    qp = st.query_params
    if "lang" in qp and qp["lang"] in ("de", "en"):
        st.session_state["lang"] = qp["lang"]
        del qp["lang"]


def setup_page(page_title_key: str, icon: str | None = None) -> None:
    if icon:
        page_icon = icon
    elif ICON_PATH.exists():
        page_icon = str(ICON_PATH)
    elif LOGO_PATH.exists():
        page_icon = str(LOGO_PATH)
    else:
        page_icon = None
    st.set_page_config(
        page_title=t(page_title_key),
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_query_params()
    inject_global_css()


def page_header(title_key: str, subtitle_key: str | None = None,
                icon: str | None = None) -> None:
    _render_logo(width_px=140)
    title = (f"{icon}  " if icon else "") + t(title_key)
    st.markdown(f"<h1 style='margin-bottom:0.2rem'>{escape(title)}</h1>",
                unsafe_allow_html=True)
    if subtitle_key:
        st.caption(t(subtitle_key))


def page_section_header(title_key: str, subtitle_key: str | None = None,
                        *, icon_html: str | None = None) -> None:
    sub = t(subtitle_key) if subtitle_key else ""
    sub_html = (
        f"<p class='wisag-section-sub wisag-page-header-sub'>{escape(sub)}</p>"
        if sub else ""
    )
    icon_block = f"<div>{icon_html}</div>" if icon_html else ""
    st.markdown(
        f"<div class='wisag-page-header'>{icon_block}"
        f"<div><h2>{escape(t(title_key))}</h2>{sub_html}</div></div>",
        unsafe_allow_html=True,
    )


def sidebar_language_switcher() -> None:
    lang = st.session_state.get("lang", "de")
    de_cls = "is-active" if lang == "de" else ""
    en_cls = "is-active" if lang == "en" else ""
    with st.sidebar:
        st.markdown(
            f"<div class='wisag-lang-switch'>"
            f"<a href='?lang=de' target='_self' class='{de_cls}'>DE</a>"
            f"<span class='wisag-lang-sep'>·</span>"
            f"<a href='?lang=en' target='_self' class='{en_cls}'>EN</a>"
            f"</div>",
            unsafe_allow_html=True,
        )


def sidebar_logo() -> None:
    with st.sidebar:
        _render_logo(width_px=140)


_NAV_PAGES: list[tuple[str, str, str]] = [
    ("app.py", "nav.overview_short", ""),
]


def sidebar_nav(active: str = "overview", alerts_count: int = 3) -> None:  # noqa: ARG001
    # `active`/`alerts_count` kept for call-site compatibility; nav is single-entry now.
    # Rendered as plain anchors instead of st.page_link because the app is a single-script
    # entry (no pages/ registry), which makes st.page_link raise KeyError: 'url_pathname'.
    with st.sidebar:
        items_html = []
        for _page_path, key, icon in _NAV_PAGES:
            icon_html = f"<span class='wisag-sidebar-nav-icon'>{escape(icon)}</span>" if icon else ""
            items_html.append(
                f"<a class='wisag-sidebar-nav-item is-active' href='?' target='_self'>"
                f"{icon_html}<span>{escape(t(key))}</span></a>"
            )
        st.markdown(
            "<nav class='wisag-sidebar-nav'>" + "".join(items_html) + "</nav>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='margin-top: 12px;'>", unsafe_allow_html=True)
        if st.button("📂 Datensatz wechseln", use_container_width=True, key="sidebar_change_dataset"):
            st.session_state.pop("dataset_confirmed", None)
            st.session_state.pop("df", None)
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def icon_tile(icon: str, variant: str = "purple", *, small: bool = False) -> str:
    cls = f"wisag-icon-tile wisag-icon-tile--{variant}"
    if small:
        cls += " wisag-icon-tile--sm"
    return f"<span class='{cls}'>{escape(icon)}</span>"


def status_pill(level: str, label: str) -> str:
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
    tile_variant = tile_variant or ("red" if variant == "neg" else "green")
    pct_cls = "wisag-driver-pct--pos" if variant == "pos" else "wisag-driver-pct--neg"
    chev = "<span class='wisag-driver-chev'>›</span>" if show_chevron else "<span></span>"
    rationale_html = (
        f"<p class='wisag-driver-why'>{escape(rationale)}</p>" if rationale else ""
    )
    inner = (
        f"<div class='wisag-driver-row'>"
        f"{icon_tile(icon, tile_variant, small=True)}"
        f"<div>"
        f"<p class='wisag-driver-title'>{escape(title)}</p>"
        f"<p class='wisag-driver-sub'>{escape(subtitle)}</p>"
        f"{rationale_html}"
        f"</div>"
        f"<span class='wisag-driver-pct {pct_cls}'>{escape(pct_label)}</span>"
        f"{chev}"
        f"</div>"
    )
    if href:
        return (f"<a class='wisag-driver-row-link' href='{escape(href)}' "
                f"target='_self'>{inner}</a>")
    return inner


def kpi_tile(label_key: str, value: str, *, delta: str | None = None,
             delta_negative_is_bad: bool = True, help_key: str | None = None) -> None:
    help_text = g(help_key) if help_key else None
    if delta is None:
        delta_color = "off"
    else:
        delta_color = "inverse" if delta_negative_is_bad else "normal"
    st.metric(label=t(label_key), value=value, delta=delta,
              delta_color=delta_color, help=help_text or None)


def severity_badge(level: str) -> str:
    lvl = (level or "low").lower()
    label = SEVERITY_COLORS.get(lvl, {}).get("label", level)
    return f"<span class='wisag-badge wisag-badge-{lvl}'>{escape(label)}</span>"


def impact_pill(eur: float) -> str:
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


_REASON_TRANSLATIONS = {
    "CM < 0": "Marge negativ",
    "big MoM jump": "starke Veränderung zum Vormonat",
    "regime flip to negative": "Wechsel ins Minus",
    "plan miss >15%": "mehr als 15 % unter Plan",
    "z-outlier": "ungewöhnlicher Wert",
}


def _translate_reasons(reasons: str) -> str:
    if not reasons:
        return ""
    out: list[str] = []
    for p in (p.strip() for p in reasons.split(",")):
        if p in _REASON_TRANSLATIONS:
            out.append(_REASON_TRANSLATIONS[p])
        elif p.startswith("labor ratio "):
            out.append(p.replace("labor ratio ", "Personalkosten "))
        elif p.startswith("z=") and "σ" in p:
            out.append("ungewöhnlicher Wert")
        else:
            out.append(p)
    return " · ".join(out)


def anomaly_card(row: pd.Series, key: str | None = None) -> None:
    cc_id = row.get("cost_center_id", "—")
    cc_name = row.get("cost_center_name") or ""
    region = row.get("region", "—")
    service = row.get("service_type", "")
    period = row.get("period")
    period_txt = period.strftime("%Y-%m") if pd.notna(period) else "—"
    severity = (row.get("severity") or "low").lower()
    impact = row.get("impact_eur", 0) or 0
    cm = row.get("cm_db")
    reasons_de = _translate_reasons(row.get("anomaly_reasons") or "")

    meta = f"{escape(str(region))}"
    if service:
        meta += f" · {escape(str(service))}"
    meta += f" · {escape(period_txt)}"

    st.markdown(
        f"<div class='wisag-card wisag-card-accent'>"
        f"<div class='wisag-anomaly-row'>"
        f"<div class='wisag-anomaly-body'>"
        f"<div class='wisag-card-title'>{escape(str(cc_id))} · {escape(str(cc_name))}</div>"
        f"<div class='wisag-card-meta'>{meta}</div>"
        f"<div class='wisag-card-body'>{escape(reasons_de) if reasons_de else ''}</div>"
        f"</div>"
        f"<div class='wisag-anomaly-right'>"
        f"{severity_badge(severity)}<br/>"
        f"<div class='wisag-impact-label'>Euro-Wirkung</div>"
        f"<div class='wisag-impact-value'>{_fmt_euro(impact)}</div>"
        f"<div class='wisag-impact-sub'>DB: {_fmt_euro(cm) if cm is not None else '—'}</div>"
        f"</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


_SEVERITY_TILE: dict[str, str] = {"high": "red", "medium": "orange", "low": "green"}


def warning_card(row: pd.Series) -> None:
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

    tile_variant = _SEVERITY_TILE.get(severity, "red")
    subtitle_bits = [str(cc_id)]
    if cc_name:
        subtitle_bits.append(str(cc_name))
    subtitle_bits.extend([str(region), period_txt])
    subtitle = " · ".join(subtitle_bits)

    impact_cls = "wisag-driver-pct--neg" if impact < 0 else "wisag-driver-pct--pos"
    impact_label = _fmt_euro(impact)

    st.markdown(
        f"<div class='wisag-warning-card'>"
        f"<div class='wisag-driver-row' style='border-top:none;padding:2px 0;'>"
        f"{icon_tile('', tile_variant, small=True)}"
        f"<div>"
        f"<p class='wisag-driver-title'>{escape(signal_label)}</p>"
        f"<p class='wisag-driver-sub'>{escape(subtitle)}</p>"
        f"</div>"
        f"<span class='wisag-driver-pct {impact_cls}'>{escape(impact_label)}</span>"
        f"<span class='wisag-driver-chev'>›</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def nav_card(icon: str, title_key: str, desc_key: str, page_path: str) -> None:
    title = t(title_key)
    desc = t(desc_key)
    st.markdown(
        f"<div class='wisag-nav-card'>"
        f"<div class='wisag-nav-card-icon'>{icon}</div>"
        f"<div class='wisag-nav-card-title'>{escape(title)}</div>"
        f"<div class='wisag-nav-card-desc'>{escape(desc)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=f"{t('nav.open')} →", icon=None)


def topbar(breadcrumb_label: str | None = None,
           *, breadcrumb_href: str = "/") -> None:
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
    metrics_html = ""
    for m in metrics or []:
        variant = m.get("variant")
        val_cls = (
            "wisag-hero-metric-value--neg" if variant == "neg"
            else "wisag-hero-metric-value--pos" if variant == "pos"
            else ""
        )
        help_text = m.get("help") or (g(m["help_key"]) if m.get("help_key") else "")
        help_attr = f" title='{escape(str(help_text))}'" if help_text else ""
        metrics_html += (
            f"<div{help_attr}>"
            f"<div class='wisag-hero-metric-label'>{escape(str(m.get('label','')))}</div>"
            f"<div class='wisag-hero-metric-value {val_cls}'>{m.get('value','')}</div>"
            f"</div>"
        )

    status_html = (
        status_pill(status_level, status_label)
        if status_level and status_label else ""
    )
    chart_html = f"<div class='wisag-hero-chart'>{chart_svg}</div>" if chart_svg else ""

    st.markdown(
        f"<div class='wisag-hero-card'>"
        f"<div class='wisag-hero-identity'>"
        f"<div class='wisag-hero-name-block'>"
        f"{icon_html or ''}"
        f"<div>"
        f"<h2 class='wisag-hero-title'>{escape(title)}</h2>"
        f"<p class='wisag-hero-sub'>{escape(subtitle) or '&nbsp;'}</p>"
        f"{status_html}"
        f"</div></div>"
        f"<div class='wisag-hero-metrics'>{metrics_html}</div>"
        f"{chart_html}"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def section_card(*, title: str, subtitle: str = "",
                 rows_html: str = "", hint: str | None = None,
                 footer_link: dict | None = None,
                 title_help: str | None = None) -> None:
    hint_html = f"<div class='wisag-section-hint'>{escape(hint)}</div>" if hint else ""
    help_mark = (
        f" <span class='wisag-section-help' title='{escape(str(title_help))}' "
        f"aria-label='info' role='img'>?</span>"
        if title_help else ""
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
        f"<div class='wisag-section-card'>"
        f"<div class='wisag-section-head'>"
        f"<div>"
        f"<h3 class='wisag-section-title'>{escape(title)}{help_mark}</h3>"
        f"<p class='wisag-section-sub'>{escape(subtitle) or '&nbsp;'}</p>"
        f"</div>"
        f"{hint_html}"
        f"</div>"
        f"{rows_html or ''}"
        f"{footer_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def suggestion_chips(chips: list[str], *, state_key: str = "suggestion_clicked") -> str | None:
    cols = st.columns(max(1, len(chips)))
    clicked: str | None = None
    for i, chip in enumerate(chips):
        with cols[i]:
            if st.button(chip, key=f"chip_{state_key}_{i}", use_container_width=True):
                clicked = chip
    return clicked


def nav_tile(icon: str, title_key: str, page_path: str,
             *, variant: str = "purple") -> None:
    title = t(title_key)
    st.markdown(
        f"<div class='wisag-nav-tile wisag-nav-tile--{variant}'>"
        f"{icon_tile(icon, variant)}"
        f"<div class='wisag-nav-tile-title'>{escape(title)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=f"{title} →")


def friendly_error(message: str, details: str | None = None) -> None:
    st.error(message)
    if details:
        with st.expander(t("action.details")):
            st.code(details)
