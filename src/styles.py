"""Global CSS injector — WISAG-branded, light-only Streamlit stylesheet.

Every value in this stylesheet is sourced from ``src.theme.tokens()``. No raw
hex, px, rem, or font-weight literals — if a value isn't in ``theme.py``, add
it there first. See ``docs/style-guide.md`` for the full rationale.
"""
from __future__ import annotations

import streamlit as st

from src.theme import tokens


def _build_css() -> str:
    T = tokens()

    # --- Color tokens ---------------------------------------------------
    accent                 = T["accent"]
    accent_dark            = T["accent_dark"]
    accent_light           = T["accent_light"]
    accent_ai              = T["accent_ai"]
    accent_ai_hover        = T["accent_ai_hover"]
    accent_ai_border       = T["accent_ai_border"]
    accent_ai_border_hover = T["accent_ai_border_hover"]
    bg_app                 = T["bg_app"]
    bg_surface             = T["bg_surface"]
    bg_muted               = T["bg_muted"]
    bg_sidebar             = T["bg_sidebar"]
    fg_primary             = T["fg_primary"]
    fg_secondary           = T["fg_secondary"]
    fg_muted               = T["fg_muted"]
    fg_inverse             = T["fg_inverse"]
    border                 = T["border"]
    border_strong          = T["border_strong"]
    pos                    = T["pos"]
    pos_dark               = T["pos_dark"]
    pos_light              = T["pos_light"]
    neg                    = T["neg"]
    neg_dark               = T["neg_dark"]
    neg_light              = T["neg_light"]
    warn_dark              = T["warn_dark"]
    warn_light             = T["warn_light"]

    # --- Spacing --------------------------------------------------------
    space_1   = T["space_1"]   # 2
    space_2   = T["space_2"]   # 4
    space_3   = T["space_3"]   # 6
    space_4   = T["space_4"]   # 8
    space_5   = T["space_5"]   # 10
    space_6   = T["space_6"]   # 12
    space_7   = T["space_7"]   # 14
    space_8   = T["space_8"]   # 16
    space_9   = T["space_9"]   # 20
    space_10  = T["space_10"]  # 24
    space_12  = T["space_12"]  # 28
    space_14  = T["space_14"]  # 32
    space_16  = T["space_16"]  # 36
    space_18  = T["space_18"]  # 18  (non-grid, card padding)
    space_22  = T["space_22"]  # 22  (non-grid, hero card)
    space_26  = T["space_26"]  # 26  (non-grid, hero card)
    space_30  = T["space_30"]  # 30  (non-grid, hero gradient card)

    # --- Radius ---------------------------------------------------------
    radius_xs   = T["radius_xs"]
    radius_sm   = T["radius_sm"]
    radius_md   = T["radius_md"]
    radius_lg   = T["radius_lg"]
    radius_xl   = T["radius_xl"]
    radius_2xl  = T["radius_2xl"]
    radius_3xl  = T["radius_3xl"]
    radius_pill = T["radius_pill"]

    # --- Typography -----------------------------------------------------
    font_sans        = T["font_sans"]
    font_serif       = T["font_serif"]
    text_2xs         = T["text_2xs"]
    text_xs          = T["text_xs"]
    text_sm          = T["text_sm"]
    text_base        = T["text_base"]
    text_md          = T["text_md"]
    text_lg          = T["text_lg"]
    text_xl          = T["text_xl"]
    text_2xl         = T["text_2xl"]
    text_3xl         = T["text_3xl"]
    weight_medium    = T["weight_medium"]
    weight_semibold  = T["weight_semibold"]
    weight_bold      = T["weight_bold"]
    leading_tight    = T["leading_tight"]
    leading_snug     = T["leading_snug"]
    leading_normal   = T["leading_normal"]
    tracking_tight   = T["tracking_tight"]
    tracking_wide    = T["tracking_wide"]
    tracking_widest  = T["tracking_widest"]

    # --- Shadow / Motion / Layout ---------------------------------------
    shadow         = T["shadow"]
    shadow_lg      = T["shadow_lg"]
    shadow_hero    = T["shadow_hero"]
    duration_fast  = T["duration_fast"]
    duration_base  = T["duration_base"]
    easing         = T["easing_standard"]
    sidebar_width  = T["sidebar_width"]
    content_max    = T["content_max_width"]

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700&family=Newsreader:ital,wght@0,500;1,500&display=swap');

.wisag-logo {{ display: block; line-height: 0; }}
.wisag-logo svg {{ width: 100%; height: auto; display: block; }}


/* ---------- App shell ---------- */
html, body, [class*="st-"], [class*="css-"] {{
    font-family: {font_sans} !important;
    color: {fg_primary};
}}
[data-testid="stAppViewContainer"], .stApp {{ background: {bg_app} !important; }}
[data-testid="stHeader"] {{ background: transparent !important; pointer-events: none !important; }}
[data-testid="stHeader"] * {{ pointer-events: auto; }}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stSidebarHeader"] {{ display: none !important; padding: 0 !important; height: 0 !important; min-height: 0 !important; }}
[data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
[data-testid="stSidebarCollapsedControl"] {{ background: transparent !important; }}
body {{ background: {bg_app}; }}

h1, h2, h3, h4 {{
    color: {fg_primary};
    font-weight: {weight_semibold};
    letter-spacing: {tracking_tight};
}}
h1 {{ font-size: {text_3xl} !important; font-weight: {weight_semibold} !important; }}
h2 {{ font-size: {text_xl} !important; }}
h3 {{ font-size: {text_lg} !important; }}
p, li, span, label, div {{ color: inherit; }}

/* ---------- Buttons ---------- */
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {{
    background-color: {accent} !important;
    border: 1px solid {accent} !important;
    color: {fg_inverse} !important;
    font-weight: {weight_semibold} !important;
    border-radius: {radius_md} !important;
    box-shadow: none !important;
}}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {{
    background-color: {accent_dark} !important;
    border-color: {accent_dark} !important;
}}
.stButton > button:not([kind="primary"]),
.stDownloadButton > button:not([kind="primary"]) {{
    background: {bg_surface} !important;
    border-radius: {radius_md} !important;
    border: 1px solid {border} !important;
    color: {fg_primary} !important;
}}
.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:not([kind="primary"]):hover {{
    border-color: {accent} !important;
    color: {accent} !important;
}}

/* ---------- Metrics ---------- */
[data-testid="stMetric"] {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_xl};
    padding: {space_7} {space_8};
    box-shadow: {shadow};
}}
[data-testid="stMetricLabel"] {{
    color: {fg_secondary} !important;
    font-size: {text_xs} !important;
    font-weight: {weight_medium} !important;
    letter-spacing: {tracking_wide};
    text-transform: none;
}}
[data-testid="stMetricValue"] {{
    color: {fg_primary} !important;
    font-size: {text_2xl} !important;
    font-weight: {weight_semibold} !important;
    letter-spacing: {tracking_tight};
}}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
    background: {bg_sidebar} !important;
    border-right: 1px solid {border};
    width: {sidebar_width} !important;
    min-width: {sidebar_width} !important;
    max-width: {sidebar_width} !important;
    font-family: {font_sans} !important;
}}
[data-testid="stSidebar"] * {{
    font-family: {font_sans} !important;
}}
/* Keep Streamlit's Material icons on the icon font so the ligature renders
   as a glyph instead of the literal text. Two attribute selectors beats both
   the `[class*="st-"]` and `[data-testid="stSidebar"] *` Inter overrides. */
[data-testid="stIconMaterial"][translate="no"],
[data-testid="stIconMaterial"][translate="no"] * {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                 'Material Icons' !important;
}}
[data-testid="stSidebarUserContent"] {{
    padding: {space_9} {space_8} !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding: 0 !important;
}}
[data-testid="stSidebarResizer"] {{ display: none !important; }}
[data-testid="stSidebar"] * {{ color: {fg_primary}; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    font-size: {text_xs} !important;
    letter-spacing: {tracking_widest};
    color: {fg_secondary};
    font-weight: {weight_semibold};
    text-transform: uppercase;
}}

/* Hide Streamlit's default multi-page nav so ONLY our custom nav shows */
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* Language switcher (DE - EN) under the logo */
.wisag-lang-switch {{
    display: inline-flex;
    align-items: center;
    gap: {space_3};
    margin: {space_3} 0 {space_6} 0;
    font-size: {text_xs};
    color: {fg_secondary};
}}
.wisag-lang-switch a {{
    color: {fg_secondary} !important;
    text-decoration: none !important;
    padding: {space_1} {space_4};
    border-radius: {radius_sm};
    font-weight: {weight_medium};
    transition: background-color {duration_fast} {easing};
}}
.wisag-lang-switch a:hover {{ background: {bg_muted}; color: {fg_primary} !important; }}
.wisag-lang-switch a.is-active {{
    background: {bg_muted};
    color: {fg_primary} !important;
    font-weight: {weight_semibold};
}}
.wisag-lang-sep {{ color: {border_strong}; }}

.wisag-sidebar-nav {{
    margin-top: {space_4};
    display: flex;
    flex-direction: column;
    gap: {space_1};
    flex: 1 1 auto;
}}
.wisag-sidebar-nav [data-testid="stPageLink-NavLink"] {{
    padding: {space_4} {space_6} !important;
    border-radius: {radius_md} !important;
    color: {fg_primary} !important;
    font-size: {text_base} !important;
    font-weight: {weight_medium} !important;
    text-decoration: none !important;
    gap: {space_5} !important;
    transition: background-color {duration_fast} {easing};
    border-left: 3px solid transparent !important;
}}
.wisag-sidebar-nav [data-testid="stPageLink-NavLink"]:hover {{
    background: {bg_muted} !important;
}}
.wisag-sidebar-nav [data-testid="stPageLink-NavLink"][aria-current="page"],
.wisag-sidebar-nav .wisag-nav-anchor.is-active {{
    background: {accent_light} !important;
    color: {fg_primary} !important;
    font-weight: {weight_semibold} !important;
    border-left: 3px solid {accent} !important;
}}
.wisag-sidebar-nav .wisag-nav-anchor.is-active .wisag-ico {{
    color: {accent};
}}

/* Raw-anchor nav item (used for Alerts so we can render a real badge pill) */
.wisag-sidebar-nav .wisag-nav-anchor {{
    display: flex;
    align-items: center;
    gap: {space_6};
    padding: {space_5} {space_6};
    border-radius: {radius_md};
    color: {fg_secondary} !important;
    font-size: {text_base};
    font-weight: {weight_medium};
    letter-spacing: 0;
    text-decoration: none !important;
    border-left: 3px solid transparent;
    transition: background-color {duration_fast} {easing}, color {duration_fast} {easing};
}}
.wisag-sidebar-nav .wisag-nav-anchor:hover {{
    background: {bg_muted};
    color: {fg_primary} !important;
}}
.wisag-sidebar-nav .wisag-nav-anchor-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: {space_9};
    height: {space_9};
    flex: none;
}}
.wisag-sidebar-nav .wisag-nav-anchor-label {{ flex: 1; }}
.wisag-ico {{
    width: {space_9};
    height: {space_9};
    stroke: currentColor;
    display: block;
}}
.wisag-sidebar-badge {{
    background: {pos};
    color: {fg_inverse};
    border-radius: {radius_pill};
    padding: 1px {space_4};
    font-size: {text_2xs};
    font-weight: {weight_bold};
    min-width: 18px;
    text-align: center;
    line-height: 1.4;
}}

/* Ask-AI CTA — lavender AI-accent, bottom-sticky */
.wisag-askai {{
    margin-top: auto;
    padding-top: {space_18};
}}
.wisag-askai-btn {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: {space_5};
    background: {accent_ai};
    color: {fg_primary} !important;
    border: 1px solid {accent_ai_border};
    border-radius: {radius_lg};
    padding: {space_6} {space_7};
    font-weight: {weight_semibold};
    font-size: {text_base};
    text-decoration: none !important;
}}
.wisag-askai-btn:hover {{
    background: {accent_ai_hover};
    border-color: {accent_ai_border_hover};
    color: {fg_primary} !important;
}}
.wisag-askai-label {{
    display: inline-flex;
    align-items: center;
    gap: {space_4};
}}
.wisag-askai-arrow {{
    display: inline-flex;
    align-items: center;
    color: {fg_secondary};
}}

/* Dividers */
hr {{ border-color: {border} !important; }}

/* ---------- Streamlit alerts (info / success / warning / error) ---------- */
[data-testid="stAlert"] {{
    border-radius: {radius_lg};
    border-left-width: 3px;
    background: {bg_surface};
    color: {fg_primary};
}}

/* ---------- Generic card ---------- */
.wisag-card {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_xl};
    padding: {space_8} {space_18};
    margin-bottom: {space_6};
    box-shadow: {shadow};
}}
.wisag-card-title {{
    font-size: {text_md};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0 0 {space_2} 0;
}}
.wisag-card-meta {{
    color: {fg_secondary};
    font-size: {text_sm};
    margin-bottom: {space_5};
}}
.wisag-card-body {{
    color: {fg_primary};
    font-size: {text_base};
    line-height: {leading_normal};
}}
.wisag-card-accent {{
    border-left: 3px solid {accent};
}}

/* ---------- Severity / impact pills ---------- */
/* Severity badge (high / medium / low) — canonical + legacy alias. */
.wisag-badge {{
    display: inline-block;
    padding: {space_1} {space_5};
    border-radius: {radius_pill};
    font-size: {text_2xs};
    font-weight: {weight_semibold};
    letter-spacing: {tracking_wide};
    vertical-align: middle;
}}
.wisag-badge--severity-high, .wisag-badge-high     {{ background: {neg_light};  color: {neg_dark}; }}
.wisag-badge--severity-medium, .wisag-badge-medium {{ background: {warn_light}; color: {warn_dark}; }}
.wisag-badge--severity-low, .wisag-badge-low       {{ background: {pos_light};  color: {pos_dark}; }}

/* Impact pill (pos / neg / neu) — signed EUR or percent. */
.wisag-pill {{
    display: inline-block;
    padding: {space_1} {space_5};
    border-radius: {radius_sm};
    font-size: {text_sm};
    font-weight: {weight_semibold};
    font-variant-numeric: tabular-nums;
}}
.wisag-pill--impact-pos, .wisag-pill-pos {{ background: {pos_light}; color: {pos_dark}; }}
.wisag-pill--impact-neg, .wisag-pill-neg {{ background: {neg_light}; color: {neg_dark}; }}
.wisag-pill--impact-neu, .wisag-pill-neu {{ background: {bg_muted};  color: {fg_secondary}; }}

/* ---------- Hero on landing page (gradient band) ---------- */
.wisag-hero {{
    background: linear-gradient(135deg, {accent} 0%, {accent_dark} 100%);
    border-radius: {radius_2xl};
    padding: {space_26} {space_30};
    color: {fg_inverse};
    margin-bottom: {space_9};
    box-shadow: {shadow_hero};
}}
.wisag-hero h2 {{
    color: {fg_inverse} !important;
    margin: 0 0 {space_3} 0;
    font-weight: {weight_bold};
    font-family: {font_serif};
    font-style: italic;
    letter-spacing: -0.02em;
}}
.wisag-hero p {{
    color: rgba(255,255,255,0.92);
    margin: 0;
    font-size: {text_base};
}}

/* ---------- Landing nav cards (legacy) ---------- */
.wisag-nav-card {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_xl};
    padding: {space_18} {space_9};
    margin-bottom: {space_5};
    transition: border-color {duration_base} {easing}, transform {duration_base} {easing};
    height: 100%;
}}
.wisag-nav-card:hover {{
    border-color: {accent};
    transform: translateY(-1px);
}}
.wisag-nav-card-icon {{ font-size: {text_xl}; margin-bottom: {space_3}; }}
.wisag-nav-card-title {{
    font-size: {text_md};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin-bottom: {space_2};
}}
.wisag-nav-card-desc {{
    color: {fg_secondary};
    font-size: {text_sm};
    line-height: 1.4;
    min-height: 2.6em;
}}

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_lg};
}}
[data-testid="stChatMessage"][data-testid*="assistant"] {{
    border-left: 3px solid {accent};
}}

/* ---------- Body padding ---------- */
.block-container {{
    padding-top: 1.2rem !important;
    max-width: {content_max};
}}

/* ---------- Form focus ---------- */
.stSelectbox [data-baseweb="select"]:focus-within,
.stMultiSelect [data-baseweb="select"]:focus-within {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 1px {accent} !important;
}}
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
.stTextInput input,
.stNumberInput input {{
    background: {bg_surface} !important;
    border-color: {border} !important;
    color: {fg_primary} !important;
}}

/* Pointer cursor on the full dropdown control and every option row. */
.stSelectbox [data-baseweb="select"],
.stSelectbox [data-baseweb="select"] *,
.stSelectbox [data-baseweb="select"] input,
.stSelectbox [data-baseweb="select"] div,
.stSelectbox [data-baseweb="select"] svg,
.stMultiSelect [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] *,
.stMultiSelect [data-baseweb="select"] input,
.stMultiSelect [data-baseweb="select"] div,
.stMultiSelect [data-baseweb="select"] svg,
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[data-baseweb="menu"] [role="option"],
[data-baseweb="menu"] [role="option"] *,
[data-baseweb="select"] [role="combobox"],
[data-baseweb="select"] [role="combobox"] * {{
    cursor: pointer !important;
}}
.stSelectbox input[readonly],
.stMultiSelect input[readonly],
[data-baseweb="select"] input {{
    cursor: pointer !important;
    caret-color: transparent;
}}

/* Clickable driver/action rows inside Why-drop / What-do cards */
.wisag-driver-row-link {{
    display: block;
    color: inherit;
    text-decoration: none !important;
    cursor: pointer;
    border-radius: {radius_md};
    transition: background-color {duration_fast} {easing};
}}
.wisag-driver-row-link:hover {{
    background: {bg_muted};
}}
.wisag-driver-row-link:hover .wisag-driver-chev {{
    color: {accent};
    transform: translateX(2px);
}}
.wisag-driver-row-link .wisag-driver-chev {{
    transition: color {duration_fast} {easing}, transform {duration_fast} {easing};
}}

/* =============================================================
   Facility-focus dashboard (Portfolio Overview)
   ============================================================= */

/* --- Shared page header (used by every page) --- */
.wisag-page-header {{
    display: flex;
    align-items: center;
    gap: {space_6};
    margin-bottom: {space_6};
}}
.wisag-page-header h2 {{ margin: 0; }}
.wisag-page-header .wisag-page-header-sub {{ margin: 0; }}

/* --- Topbar --- */
.wisag-topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: {space_6};
}}
.wisag-breadcrumb {{
    color: {fg_secondary};
    font-size: {text_sm};
    font-weight: {weight_medium};
    text-decoration: none;
}}
.wisag-breadcrumb:hover {{ color: {accent}; }}

/* --- Hero card (facility view) --- */
.wisag-hero-card {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_3xl};
    padding: {space_22} {space_26};
    box-shadow: {shadow};
    margin-bottom: {space_8};
}}
.wisag-hero-identity {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: {space_9};
    flex-wrap: wrap;
}}
.wisag-hero-name-block {{
    display: flex;
    align-items: center;
    gap: {space_7};
    flex: 1 1 auto;
    min-width: 240px;
}}
.wisag-hero-initial {{
    width: 52px;
    height: 52px;
    border-radius: {radius_2xl};
    background: {bg_muted};
    color: {fg_primary};
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: {text_xl};
    font-weight: {weight_semibold};
    flex: none;
    border: 1px solid {border};
}}
.wisag-hero-title {{
    font-size: {text_xl};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0;
    letter-spacing: {tracking_tight};
    line-height: {leading_snug};
}}
.wisag-hero-sub {{
    color: {fg_secondary};
    font-size: {text_sm};
    margin: {space_1} 0 {space_4} 0;
}}
.wisag-hero-metrics {{
    display: flex;
    gap: {space_12};
    align-items: flex-end;
    flex-wrap: wrap;
}}
.wisag-hero-metrics > div + div {{
    padding-left: {space_12};
    border-left: 1px solid {border};
}}
.wisag-hero-metric-label {{
    color: {fg_secondary};
    font-size: {text_xs};
    letter-spacing: {tracking_wide};
    margin-bottom: {space_1};
}}
.wisag-hero-metric-value {{
    color: {fg_primary};
    font-size: {text_3xl};
    font-weight: {weight_semibold};
    line-height: {leading_tight};
    font-variant-numeric: tabular-nums;
    letter-spacing: {tracking_tight};
}}
.wisag-hero-metric-value--neg {{ color: {neg_dark}; }}
.wisag-hero-metric-value--pos {{ color: {pos_dark}; }}
.wisag-hero-chart {{
    flex: 0 1 320px;
    min-width: 220px;
    max-width: 360px;
}}
.wisag-hero-chart svg {{ max-height: 130px; }}

/* --- Overview section (H1 + category bar + chart wrap) --- */
.wisag-overview-title {{
    font-size: {text_3xl};
    font-weight: {weight_bold};
    color: {fg_primary};
    letter-spacing: {tracking_tight};
    margin: {space_4} 0 {space_6} 0;
    line-height: {leading_tight};
}}
.wisag-cat-bar {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_xl};
    padding: {space_3};
    margin-bottom: {space_6};
    box-shadow: {shadow};
}}
.wisag-chart-wrap {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_2xl};
    padding: {space_9} {space_10};
    box-shadow: {shadow};
    margin-bottom: {space_8};
}}
.wisag-chart-wrap .wisag-section-sub {{ margin: 0 0 {space_5} 0; }}

/* --- Chart panel (full-width sparkline area) --- */
.wisag-chart {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_3xl};
    padding: {space_18} {space_9} {space_6} {space_9};
    box-shadow: {shadow};
    margin-bottom: {space_8};
}}
.wisag-chart-head {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: {space_3};
    gap: {space_6};
    flex-wrap: wrap;
}}
.wisag-chart-title {{
    font-size: {text_base};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0;
}}
.wisag-chart-sub {{
    font-size: {text_xs};
    color: {fg_secondary};
    margin: 0;
}}

/* --- Icon tiles (used by driver rows + nav tiles) --- */
.wisag-icon-tile {{
    width: 40px;
    height: 40px;
    border-radius: {radius_lg};
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex: none;
}}
.wisag-icon-tile--purple {{ background: {bg_muted};     color: {fg_primary}; }}
.wisag-icon-tile--red    {{ background: {neg_light};    color: {neg_dark}; }}
.wisag-icon-tile--green  {{ background: {pos_light};    color: {pos_dark}; }}
.wisag-icon-tile--orange {{ background: {accent_light}; color: {accent_dark}; }}
.wisag-icon-tile--sm {{ width: 36px; height: 36px; font-size: 1.05rem; border-radius: 9px; }}

/* --- Status pill (critical / warn / healthy) — canonical + legacy alias --- */
.wisag-status, .wisag-status-pill {{
    display: inline-flex;
    align-items: center;
    gap: {space_3};
    padding: {space_1} {space_5};
    border-radius: {radius_pill};
    font-size: {text_2xs};
    font-weight: {weight_semibold};
    letter-spacing: {tracking_wide};
}}
.wisag-status::before, .wisag-status-pill::before {{
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}}
.wisag-status--critical, .wisag-status-pill--critical {{ background: {neg_light};  color: {neg_dark}; }}
.wisag-status--warn,     .wisag-status-pill--warn     {{ background: {warn_light}; color: {warn_dark}; }}
.wisag-status--healthy,  .wisag-status-pill--healthy  {{ background: {pos_light};  color: {pos_dark}; }}

/* --- Section cards ("Why drop" / "What do") --- */
.wisag-section-card {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_2xl};
    padding: {space_9} {space_22};
    box-shadow: {shadow};
    height: 100%;
}}
.wisag-section-title {{
    font-size: {text_md};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0 0 {space_2} 0;
    letter-spacing: -0.005em;
}}
.wisag-section-sub {{
    color: {fg_secondary};
    font-size: {text_sm};
    margin-bottom: {space_7};
}}
.wisag-section-head {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: {space_7};
}}
.wisag-section-hint {{
    color: {fg_secondary};
    font-size: {text_2xs};
    letter-spacing: 0.03em;
    margin-top: {space_18};
}}
.wisag-section-footer {{
    margin-top: {space_5};
    padding: {space_5} {space_7};
    background: {bg_muted};
    border-radius: {radius_lg};
    font-weight: {weight_semibold};
    font-size: {text_sm};
    color: {fg_primary};
    display: flex;
    align-items: center;
    justify-content: space-between;
    text-decoration: none !important;
    transition: background-color {duration_fast} {easing};
}}
.wisag-section-footer:hover {{ background: {accent_light}; color: {fg_primary}; }}
.wisag-section-footer::after {{
    content: "›";
    color: {fg_muted};
    font-size: {text_lg};
    font-weight: 400;
}}

/* --- Driver / action rows --- */
.wisag-driver-row {{
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    gap: {space_7};
    align-items: center;
    padding: {space_6} {space_7};
    border-top: 1px solid {border};
}}
.wisag-driver-row:first-of-type {{ border-top: none; padding-top: {space_2}; }}
.wisag-driver-title {{
    font-size: {text_base};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0;
}}
.wisag-driver-sub {{
    color: {fg_secondary};
    font-size: {text_xs};
    margin: {space_1} 0 0 0;
}}
.wisag-driver-why {{
    color: {fg_muted};
    font-size: {text_xs};
    font-style: italic;
    margin: {space_1} 0 0 0;
}}
.wisag-driver-pct {{
    font-weight: {weight_semibold};
    font-size: {text_base};
    font-variant-numeric: tabular-nums;
    padding: {space_1} {space_4};
    border-radius: {radius_sm};
}}
.wisag-driver-pct--neg {{ background: {neg_light}; color: {neg_dark}; }}
.wisag-driver-pct--pos {{ background: {pos_light}; color: {pos_dark}; }}

/* Text-only signed variants — same typography as .wisag-driver-title,
   just tinted. Used for numeric row cells that should not get a pill. */
.wisag-driver-title--neg {{ color: {neg_dark}; }}
.wisag-driver-title--pos {{ color: {pos_dark}; }}
.wisag-driver-chev {{
    color: {fg_muted};
    font-size: {text_lg};
    font-weight: 400;
}}

/* --- What-if card --- */
.wisag-whatif-card {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_2xl};
    padding: {space_22} {space_10};
    box-shadow: {shadow};
    margin-top: {space_2};
}}
/* Style the st.container() that holds the What-if section as one card. */
.wisag-whatif-anchor {{ display: none; }}
div[data-testid="stVerticalBlock"]:has(
    > div > div[data-testid="stMarkdown"] .wisag-whatif-anchor
) {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_2xl};
    padding: {space_9} {space_22};
    box-shadow: {shadow};
    margin-top: {space_2};
}}
.wisag-whatif-title {{ margin: 0; }}
.wisag-whatif-sub {{ margin: {space_1} 0 {space_7} 0; }}
.wisag-whatif-label {{
    color: {fg_secondary};
    font-size: {text_xs};
    letter-spacing: {tracking_wide};
}}
.wisag-whatif-value {{
    color: {fg_primary};
    font-size: 1.85rem;
    font-weight: {weight_semibold};
    line-height: {leading_tight};
    font-variant-numeric: tabular-nums;
    letter-spacing: {tracking_tight};
}}
.wisag-whatif-delta--pos {{ color: {pos_dark}; font-weight: {weight_semibold}; }}
.wisag-whatif-delta--neg {{ color: {neg_dark}; font-weight: {weight_semibold}; }}

/* --- Explore-more card (AI-accent lavender, clickable) --- */
.wisag-explore-wrap {{
    display: flex;
    align-items: center;
    justify-content: stretch;
    height: 100%;
    min-height: 100%;
}}
.wisag-explore-wrap > .wisag-explore-card {{ flex: 1; }}
.wisag-explore-card {{
    background: {accent_ai};
    border: 1px solid {accent_ai_border};
    border-radius: {radius_xl};
    padding: {space_8} {space_18};
    display: flex;
    align-items: center;
    gap: {space_6};
    color: {fg_primary};
    text-decoration: none !important;
    transition: background-color {duration_fast} {easing}, border-color {duration_fast} {easing};
}}
.wisag-explore-card:hover {{
    background: {accent_ai_hover};
    border-color: {accent_ai_border_hover};
}}
.wisag-explore-card-icon {{
    width: 40px; height: 40px;
    border-radius: {radius_lg};
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: {bg_surface};
    font-size: 1.25rem;
    flex: none;
}}
.wisag-explore-card-body {{ flex: 1; }}
.wisag-explore-title {{ font-weight: {weight_semibold}; font-size: {text_base}; margin: 0 0 {space_1} 0; }}
.wisag-explore-sub {{ font-size: {text_xs}; margin: 0; color: {fg_secondary}; }}

/* --- Footer timestamp --- */
.wisag-footer-ts {{
    color: {fg_secondary};
    font-size: {text_xs};
    display: flex;
    align-items: center;
    gap: {space_3};
    margin-top: {space_10};
}}

/* Plotly transparent background */
.js-plotly-plot .plotly .main-svg {{
    background: transparent !important;
}}

/* DataFrames */
.stDataFrame, [data-testid="stDataFrame"] {{
    background: {bg_surface};
    border-radius: {radius_md};
}}

/* =============================================================
   Shared primitives introduced by the revamp
   ============================================================= */

/* Topbar grid — visual layer only (columns provided by Streamlit) */
.wisag-topbar-grid {{ margin-bottom: {space_6}; }}

/* Nav tiles on the landing page (replaces heavy nav_card) */
.wisag-nav-tile {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_2xl};
    padding: {space_18} {space_18} {space_5} {space_18};
    display: flex;
    align-items: center;
    gap: {space_7};
    box-shadow: {shadow};
    transition: border-color {duration_base} {easing}, transform {duration_base} {easing};
    margin-bottom: {space_2};
}}
.wisag-nav-tile:hover {{
    border-color: {accent};
    transform: translateY(-1px);
    box-shadow: {shadow_lg};
}}
.wisag-nav-tile-title {{
    font-size: {text_md};
    font-weight: {weight_semibold};
    color: {fg_primary};
    line-height: {leading_snug};
}}
/* The real page_link sits below the visual tile — dress it to a subtle link. */
.wisag-nav-tile + div [data-testid="stPageLink-NavLink"] {{
    padding: {space_3} 0 {space_5} 0 !important;
    color: {accent} !important;
    font-size: {text_sm} !important;
    font-weight: {weight_semibold} !important;
    text-decoration: none !important;
    border: none !important;
    background: transparent !important;
}}

/* Suggestion chips — st.buttons styled as compact pills */
[data-testid="stButton"] button[key^="chip_"],
.stButton button[data-testid*="chip_"] {{
    background: {bg_muted} !important;
    border: 1px solid {border} !important;
    color: {fg_primary} !important;
    border-radius: {radius_pill} !important;
    padding: {space_3} {space_7} !important;
    font-size: {text_sm} !important;
    font-weight: {weight_medium} !important;
    white-space: normal !important;
    text-align: left !important;
}}

/* Warning card (early-warnings page) — bordered row, no divider between */
.wisag-warning-card {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_xl};
    padding: {space_5} {space_8};
    margin-bottom: {space_4};
    box-shadow: {shadow};
    transition: border-color {duration_fast} {easing};
}}
.wisag-warning-card:hover {{
    border-color: {border_strong};
}}

/* KPI strip (consolidated replacement for row-of-4 metrics) */
.wisag-kpi-strip {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_2xl};
    padding: {space_7} {space_18};
    box-shadow: {shadow};
    display: flex;
    align-items: center;
    gap: {space_10};
    flex-wrap: wrap;
    margin-bottom: {space_7};
}}
.wisag-kpi-strip-item {{
    display: flex;
    align-items: center;
    gap: {space_5};
    min-width: 0;
}}
.wisag-kpi-strip-label {{
    color: {fg_secondary};
    font-size: {text_xs};
    font-weight: {weight_medium};
}}
.wisag-kpi-strip-value {{
    color: {fg_primary};
    font-size: {text_lg};
    font-weight: {weight_semibold};
    font-variant-numeric: tabular-nums;
    letter-spacing: {tracking_tight};
}}
.wisag-kpi-strip-sep {{
    width: 1px;
    height: 28px;
    background: {border};
}}

/* Inline chart legend (colored dots + short label) */
.wisag-legend {{
    display: inline-flex;
    align-items: center;
    gap: {space_7};
    font-size: {text_xs};
    color: {fg_secondary};
}}
.wisag-legend-dot {{
    display: inline-flex;
    align-items: center;
    gap: {space_3};
}}
.wisag-legend-dot::before {{
    content: "";
    width: 9px; height: 9px; border-radius: 50%;
    background: currentColor;
}}
.wisag-legend-dot--pos {{ color: {pos_dark}; }}
.wisag-legend-dot--neg {{ color: {neg_dark}; }}
.wisag-legend-dot--neu {{ color: {fg_muted}; }}

/* Compact peer-comparison row (Details page) */
.wisag-peer-row {{
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: {space_7};
    align-items: center;
    padding: {space_5} 0;
    border-top: 1px solid {border};
}}
.wisag-peer-row:first-of-type {{ border-top: none; }}
.wisag-peer-label {{
    color: {fg_primary};
    font-weight: {weight_medium};
    font-size: {text_base};
}}
.wisag-peer-value {{
    color: {fg_primary};
    font-weight: {weight_semibold};
    font-variant-numeric: tabular-nums;
    padding: {space_1} {space_4};
    border-radius: {radius_sm};
    background: {bg_muted};
}}
.wisag-peer-median {{
    color: {fg_secondary};
    font-size: {text_xs};
    font-variant-numeric: tabular-nums;
}}

/* Shrunken landing hero (less wall-of-text) */
.wisag-hero--compact {{ padding: {space_18} {space_10}; }}
.wisag-hero--compact h2 {{ font-size: {text_xl} !important; }}
.wisag-hero--compact p {{ font-size: {text_sm}; }}

/* =============================================================
   Utility classes (replace inline styles on pages)
   ============================================================= */

/* Empty-state / placeholder row inside a section card */
.wisag-empty-row {{
    padding: {space_6} 0;
    margin: 0;
}}
.wisag-empty-row--sm {{ padding: {space_3} 0; }}

/* Vertical spacer between stacked sections */
.wisag-stack-gap {{ height: {space_4}; }}
.wisag-stack-gap--md {{ height: {space_6}; }}
.wisag-stack-gap--lg {{ height: {space_8}; }}

/* Alert detail panel layout */
.wisag-alert-detail-head {{
    display: flex;
    align-items: center;
    gap: {space_4};
}}
.wisag-alert-detail-h4 {{
    margin-top: {space_6};
}}
.wisag-alert-detail-cta {{
    margin-top: {space_6};
}}

/* Detail-panel severity chip (used by Alerts expanded view) */
.wisag-severity-chip {{
    display: inline-flex;
    align-items: center;
    padding: {space_3} {space_6};
    border-radius: {radius_md};
    font-size: {text_sm};
    font-weight: {weight_semibold};
    color: {fg_primary};
    text-decoration: none !important;
}}
.wisag-severity-chip:hover {{ color: {accent}; }}

/* Inline arrow separator (used in the What-if section between inputs) */
.wisag-wif-arrow {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding-top: 34px;
    font-size: {text_lg};
    color: {fg_secondary};
}}

/* Small top-margin for status line below a dataframe */
.wisag-status-line {{ margin-top: {space_3}; }}

/* Anomaly card layout (two-column row + right column typography) */
.wisag-anomaly-row {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: {space_6};
}}
.wisag-anomaly-body {{ flex: 1; min-width: 0; }}
.wisag-anomaly-right {{ text-align: right; min-width: 180px; }}
.wisag-impact-label {{
    font-size: {text_xs};
    color: {fg_secondary};
    margin-top: {space_4};
}}
.wisag-impact-value {{
    font-size: {text_lg};
    font-weight: {weight_bold};
    color: {fg_primary};
}}
.wisag-impact-sub {{
    font-size: {text_xs};
    color: {fg_secondary};
    margin-top: {space_2};
}}

/* =============================================================
   Upload page (shown when no dataset is loaded yet)
   ============================================================= */
.wisag-upload-hero {{
    background: {bg_surface};
    border: 1px solid {border};
    border-radius: {radius_3xl};
    padding: {space_16} {space_14} {space_12} {space_14};
    box-shadow: {shadow};
    margin-bottom: {space_8};
    text-align: center;
}}
.wisag-upload-hero .wisag-icon-tile {{
    width: 64px;
    height: 64px;
    border-radius: {radius_3xl};
    font-size: 1.9rem;
    margin: 0 auto {space_7} auto;
}}
.wisag-upload-hero-title {{
    font-size: {text_2xl};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0 0 {space_3} 0;
    letter-spacing: {tracking_tight};
}}
.wisag-upload-hero-sub {{
    color: {fg_secondary};
    font-size: 1.0rem;
    line-height: {leading_normal};
    max-width: 560px;
    margin: 0 auto;
}}

/* Dress the native file_uploader as a big dashed dropzone */
[data-testid="stFileUploader"] {{
    background: {bg_surface};
    border: 1px dashed {border_strong};
    border-radius: {radius_2xl};
    padding: {space_4} {space_4};
    box-shadow: {shadow};
    transition: border-color {duration_base} {easing}, background {duration_base} {easing};
    margin-bottom: {space_8};
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {accent};
    background: {accent_light};
}}
[data-testid="stFileUploader"] section {{
    background: transparent !important;
    border: none !important;
    padding: {space_9} {space_18} !important;
}}
[data-testid="stFileUploader"] section > button,
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploader"] button {{
    background: {accent} !important;
    border: 1px solid {accent} !important;
    color: {fg_inverse} !important;
    font-weight: {weight_semibold} !important;
    border-radius: {radius_md} !important;
}}
[data-testid="stFileUploader"] section > button:hover,
[data-testid="stFileUploaderDropzone"] button:hover,
[data-testid="stFileUploader"] button:hover {{
    background: {accent_dark} !important;
    border-color: {accent_dark} !important;
}}
[data-testid="stFileUploader"] small {{
    color: {fg_muted} !important;
}}

/* Requirements list — reuse section_card with a cleaner row shape */
.wisag-req-row {{
    display: grid;
    grid-template-columns: auto 1fr;
    gap: {space_7};
    align-items: center;
    padding: {space_6} 0;
    border-top: 1px solid {border};
}}
.wisag-req-row:first-of-type {{ border-top: none; padding-top: {space_2}; }}
.wisag-req-title {{
    font-size: {text_base};
    font-weight: {weight_semibold};
    color: {fg_primary};
    margin: 0;
}}
.wisag-req-sub {{
    color: {fg_secondary};
    font-size: {text_sm};
    margin: {space_1} 0 0 0;
    line-height: 1.4;
}}

.wisag-upload-footer-hint {{
    margin-top: {space_7};
    color: {fg_secondary};
    font-size: {text_sm};
    text-align: center;
}}
.wisag-upload-footer-hint code {{
    background: {bg_muted};
    padding: 1px {space_3};
    border-radius: {radius_xs};
    font-size: {text_xs};
    color: {fg_primary};
}}

/* ---------- Contracts category tab bar ---------- */
#wisag-contracts-anchor {{
    scroll-margin-top: 24px;
}}
.wisag-contracts-tabs {{
    display: flex;
    flex-wrap: wrap;
    gap: {space_1};
    padding: {space_2};
    margin: 0 0 {space_6} 0;
    background: {bg_muted};
    border-radius: {radius_md};
    width: fit-content;
    max-width: 100%;
}}
.wisag-contracts-tab {{
    padding: {space_3} {space_7};
    border-radius: {radius_sm};
    font-size: {text_sm};
    font-weight: {weight_medium};
    color: {fg_secondary} !important;
    text-decoration: none !important;
    cursor: pointer;
    transition: background-color {duration_fast} {easing},
                color {duration_fast} {easing};
    white-space: nowrap;
}}
.wisag-contracts-tab:hover {{
    color: {fg_primary} !important;
    background: rgba(255, 255, 255, 0.55);
}}
.wisag-contracts-tab.is-active {{
    background: {bg_surface};
    color: {fg_primary} !important;
    font-weight: {weight_semibold};
    box-shadow: {shadow};
}}

/* ---------- Score pill (0-100, green / amber / red) ---------- */
.wisag-score-pill {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 46px;
    padding: {space_1} {space_4};
    border-radius: {radius_pill};
    font-size: {text_sm};
    font-weight: {weight_semibold};
    letter-spacing: {tracking_tight};
    border: 1px solid transparent;
}}
.wisag-score-pill--good {{
    background: {pos_light};
    color: {pos_dark};
    border-color: {pos};
}}
.wisag-score-pill--warn {{
    background: {warn_light};
    color: {warn_dark};
    border-color: {warn_dark};
}}
.wisag-score-pill--bad {{
    background: {neg_light};
    color: {neg_dark};
    border-color: {neg};
}}
.wisag-score-pill--overall {{
    min-width: 54px;
    font-size: {text_base};
}}

/* Stack the overall score above the stability score in the Overall tab. */
.wisag-score-stack {{
    display: flex;
    flex-direction: column;
    gap: {space_1};
    align-items: flex-start;
}}
.wisag-score-stack-label {{
    font-size: {text_2xs};
    color: {fg_muted};
    letter-spacing: {tracking_wide};
    text-transform: uppercase;
}}

/* Long-term / short-term badge on the stability tab. */
.wisag-term-badge {{
    display: inline-flex;
    align-items: center;
    padding: {space_1} {space_4};
    border-radius: {radius_pill};
    font-size: {text_xs};
    font-weight: {weight_medium};
    border: 1px solid {border};
    color: {fg_secondary};
    background: {bg_muted};
}}
.wisag-term-badge--long {{
    color: {pos_dark};
    background: {pos_light};
    border-color: {pos};
}}
.wisag-term-badge--short {{
    color: {warn_dark};
    background: {warn_light};
    border-color: {warn_dark};
}}

/* Trend arrow variants for the Profitability tab (unrentability direction). */
.wisag-trend-arrow {{
    display: inline-flex;
    align-items: center;
    gap: {space_2};
    font-size: {text_sm};
    font-weight: {weight_medium};
}}
.wisag-trend-arrow--up {{ color: {neg_dark}; }}
.wisag-trend-arrow--down {{ color: {pos_dark}; }}
.wisag-trend-arrow--flat {{ color: {fg_muted}; }}
</style>
"""


def inject_global_css() -> None:
    """Inject the global stylesheet (light-only)."""
    st.markdown(_build_css(), unsafe_allow_html=True)
