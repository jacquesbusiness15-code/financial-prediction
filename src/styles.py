"""Global CSS injector — WISAG-branded Streamlit theme."""
from __future__ import annotations

import streamlit as st

from src.theme import (
    WISAG_ORANGE,
    WISAG_ORANGE_DARK,
    WISAG_ORANGE_LIGHT,
    WISAG_NAVY,
    WISAG_GRAY_100,
    WISAG_GRAY_200,
    WISAG_GRAY_300,
    WISAG_GRAY_500,
    WISAG_GRAY_600,
    POS,
    POS_LIGHT,
    POS_DARK,
    NEG,
    NEG_LIGHT,
    NEG_DARK,
    WARN_LIGHT,
)

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="st-"], [class*="css-"] {{
    font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Arial, sans-serif !important;
    color: {WISAG_NAVY};
}}

h1, h2, h3, h4 {{
    color: {WISAG_NAVY};
    font-weight: 600;
    letter-spacing: -0.01em;
}}

h1 {{ font-size: 2.0rem !important; }}
h2 {{ font-size: 1.5rem !important; }}
h3 {{ font-size: 1.2rem !important; }}

/* Primary buttons — WISAG orange */
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {{
    background-color: {WISAG_ORANGE} !important;
    border: 1px solid {WISAG_ORANGE} !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {{
    background-color: {WISAG_ORANGE_DARK} !important;
    border-color: {WISAG_ORANGE_DARK} !important;
}}

/* Secondary buttons */
.stButton > button:not([kind="primary"]) {{
    border-radius: 6px !important;
    border-color: {WISAG_GRAY_300} !important;
    color: {WISAG_NAVY} !important;
}}
.stButton > button:not([kind="primary"]):hover {{
    border-color: {WISAG_ORANGE} !important;
    color: {WISAG_ORANGE} !important;
}}

/* KPI / metric tiles */
[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid {WISAG_GRAY_300};
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}
[data-testid="stMetricLabel"] {{
    color: {WISAG_GRAY_600} !important;
    font-size: 0.80rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
[data-testid="stMetricValue"] {{
    color: {WISAG_NAVY} !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: #FFFFFF;
    border-right: 1px solid {WISAG_GRAY_300};
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    font-size: 0.95rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: {WISAG_GRAY_600};
    font-weight: 600;
}}

/* Active sidebar nav link — orange left-border */
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    border-left: 3px solid {WISAG_ORANGE} !important;
    background: {WISAG_ORANGE_LIGHT} !important;
    color: {WISAG_ORANGE_DARK} !important;
    font-weight: 600 !important;
}}

/* Dividers */
hr {{ border-color: {WISAG_GRAY_200} !important; }}

/* Alert banners */
[data-testid="stAlert"] {{
    border-radius: 8px;
    border-left-width: 4px;
}}

/* Cards */
.wisag-card {{
    background: #FFFFFF;
    border: 1px solid {WISAG_GRAY_300};
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}
.wisag-card-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: {WISAG_NAVY};
    margin: 0 0 4px 0;
}}
.wisag-card-meta {{
    color: {WISAG_GRAY_600};
    font-size: 0.85rem;
    margin-bottom: 10px;
}}
.wisag-card-body {{
    color: {WISAG_NAVY};
    font-size: 0.95rem;
    line-height: 1.4;
}}
.wisag-card-accent {{
    border-left: 4px solid {WISAG_ORANGE};
}}

/* Severity badges */
.wisag-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    vertical-align: middle;
}}
.wisag-badge-high   {{ background: {NEG_LIGHT}; color: {NEG_DARK}; }}
.wisag-badge-medium {{ background: {WARN_LIGHT}; color: #8A4A00; }}
.wisag-badge-low    {{ background: {POS_LIGHT}; color: {POS_DARK}; }}

/* Impact pills (positive / negative euros) */
.wisag-pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}}
.wisag-pill-pos {{ background: {POS_LIGHT}; color: {POS_DARK}; }}
.wisag-pill-neg {{ background: {NEG_LIGHT}; color: {NEG_DARK}; }}
.wisag-pill-neu {{ background: {WISAG_GRAY_100}; color: {WISAG_GRAY_600}; }}

/* Hero section on landing */
.wisag-hero {{
    background: linear-gradient(135deg, {WISAG_ORANGE} 0%, {WISAG_ORANGE_DARK} 100%);
    border-radius: 12px;
    padding: 28px 32px;
    color: #FFFFFF;
    margin-bottom: 20px;
}}
.wisag-hero h2 {{
    color: #FFFFFF !important;
    margin: 0 0 6px 0;
    font-weight: 700;
}}
.wisag-hero p {{
    color: rgba(255,255,255,0.92);
    margin: 0;
    font-size: 1.0rem;
}}

/* Nav cards on landing */
.wisag-nav-card {{
    background: #FFFFFF;
    border: 1px solid {WISAG_GRAY_300};
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    transition: border-color 0.15s ease, transform 0.15s ease;
    height: 100%;
}}
.wisag-nav-card:hover {{
    border-color: {WISAG_ORANGE};
    transform: translateY(-1px);
}}
.wisag-nav-card-icon {{
    font-size: 1.6rem;
    margin-bottom: 6px;
}}
.wisag-nav-card-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: {WISAG_NAVY};
    margin-bottom: 4px;
}}
.wisag-nav-card-desc {{
    color: {WISAG_GRAY_600};
    font-size: 0.90rem;
    line-height: 1.4;
    min-height: 2.6em;
}}

/* Chat bubble accent */
[data-testid="stChatMessage"][data-testid*="assistant"] {{
    border-left: 3px solid {WISAG_ORANGE};
    background: #FFFFFF;
}}

/* Hide the default "app" link at the top of the sidebar nav label "app" */
[data-testid="stSidebarNav"] ul li:first-child a span {{
    font-weight: 600;
}}

/* Tighten top padding so the logo sits close to the top */
.block-container {{
    padding-top: 1.5rem !important;
}}

/* Make select/multiselect focus ring orange */
.stSelectbox [data-baseweb="select"]:focus-within,
.stMultiSelect [data-baseweb="select"]:focus-within {{
    border-color: {WISAG_ORANGE} !important;
    box-shadow: 0 0 0 1px {WISAG_ORANGE} !important;
}}

/* =============================================================
   Facility-focus dashboard (Portfolio Overview)
   ============================================================= */

/* Hide Streamlit's default multi-page nav so ONLY our custom nav shows */
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* --- Custom sidebar nav (real st.page_link widgets styled via CSS) --- */
.wisag-sidebar-nav {{
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 2px;
}}
.wisag-sidebar-nav [data-testid="stPageLink-NavLink"] {{
    padding: 10px 12px !important;
    border-radius: 8px !important;
    color: {WISAG_NAVY} !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    transition: background-color 0.1s ease;
}}
.wisag-sidebar-nav [data-testid="stPageLink-NavLink"]:hover {{
    background: {WISAG_GRAY_100} !important;
}}
.wisag-sidebar-nav [data-testid="stPageLink-NavLink"][aria-current="page"] {{
    background: {WISAG_ORANGE_LIGHT} !important;
    color: {WISAG_ORANGE_DARK} !important;
    font-weight: 600 !important;
    border-left: 3px solid {WISAG_ORANGE} !important;
}}

.wisag-askai {{ margin-top: 20px; }}
.wisag-askai [data-testid="stPageLink-NavLink"] {{
    background: {WISAG_ORANGE} !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    box-shadow: 0 2px 6px rgba(233,78,27,0.25) !important;
    justify-content: space-between !important;
}}
.wisag-askai [data-testid="stPageLink-NavLink"]:hover {{
    background: {WISAG_ORANGE_DARK} !important;
    color: #FFFFFF !important;
}}

/* --- Topbar (breadcrumb + period picker + export) --- */
.wisag-topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}
.wisag-breadcrumb {{
    color: {WISAG_GRAY_600};
    font-size: 0.90rem;
    font-weight: 500;
    text-decoration: none;
}}
.wisag-breadcrumb:hover {{ color: {WISAG_ORANGE}; }}

/* --- Hero card --- */
.wisag-hero-card {{
    background: #FFFFFF;
    border: 1px solid {WISAG_GRAY_300};
    border-radius: 14px;
    padding: 22px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 16px;
}}
.wisag-hero-grid {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 32px;
    flex-wrap: wrap;
}}
.wisag-hero-grid > div:first-child {{ flex: 1 1 auto; }}
.wisag-hero-spark {{
    flex: 0 0 auto;
    display: flex;
    align-items: center;
}}
.wisag-hero-spark svg {{ max-width: 100%; height: auto; }}
.wisag-hero-title {{
    font-size: 1.35rem;
    font-weight: 700;
    color: {WISAG_NAVY};
    margin: 0;
    line-height: 1.2;
}}
.wisag-hero-sub {{
    color: {WISAG_GRAY_600};
    font-size: 0.90rem;
    margin: 2px 0 8px 0;
}}
.wisag-hero-metric-label {{
    color: {WISAG_GRAY_600};
    font-size: 0.80rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}}
.wisag-hero-metric-value {{
    color: {WISAG_NAVY};
    font-size: 1.90rem;
    font-weight: 700;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}
.wisag-hero-metric-value--neg {{ color: {NEG_DARK}; }}
.wisag-hero-metric-value--pos {{ color: {POS_DARK}; }}

/* --- Icon tiles --- */
.wisag-icon-tile {{
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    flex: none;
}}
.wisag-icon-tile--purple {{ background: #EDE1F7; color: #6A1B9A; }}
.wisag-icon-tile--red    {{ background: {NEG_LIGHT}; color: {NEG_DARK}; }}
.wisag-icon-tile--green  {{ background: {POS_LIGHT}; color: {POS_DARK}; }}
.wisag-icon-tile--orange {{ background: {WISAG_ORANGE_LIGHT}; color: {WISAG_ORANGE_DARK}; }}
.wisag-icon-tile--sm {{ width: 40px; height: 40px; font-size: 1.2rem; border-radius: 10px; }}

/* --- Status pills (critical / warn / healthy) --- */
.wisag-status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}}
.wisag-status-pill::before {{
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}}
.wisag-status-pill--critical {{ background: {NEG_LIGHT}; color: {NEG_DARK}; }}
.wisag-status-pill--warn     {{ background: {WARN_LIGHT}; color: #8A4A00; }}
.wisag-status-pill--healthy  {{ background: {POS_LIGHT}; color: {POS_DARK}; }}

/* --- Section cards (Why did it drop / What can we do) --- */
.wisag-section-card {{
    background: #FFFFFF;
    border: 1px solid {WISAG_GRAY_300};
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    height: 100%;
}}
.wisag-section-title {{
    font-size: 1.10rem;
    font-weight: 700;
    color: {WISAG_NAVY};
    margin: 0 0 4px 0;
}}
.wisag-section-sub {{
    color: {WISAG_GRAY_600};
    font-size: 0.88rem;
    margin-bottom: 14px;
}}
.wisag-section-head {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 14px;
}}
.wisag-section-hint {{
    color: {WISAG_GRAY_600};
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 20px;
}}

/* --- Driver / action rows inside the section cards --- */
.wisag-driver-row {{
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    gap: 14px;
    align-items: center;
    padding: 12px 0;
    border-top: 1px solid {WISAG_GRAY_200};
}}
.wisag-driver-row:first-of-type {{ border-top: none; padding-top: 4px; }}
.wisag-driver-title {{
    font-size: 0.98rem;
    font-weight: 600;
    color: {WISAG_NAVY};
    margin: 0;
}}
.wisag-driver-sub {{
    color: {WISAG_GRAY_600};
    font-size: 0.83rem;
    margin: 2px 0 0 0;
}}
.wisag-driver-pct {{
    font-weight: 700;
    font-size: 1.00rem;
    font-variant-numeric: tabular-nums;
    padding: 4px 10px;
    border-radius: 6px;
}}
.wisag-driver-pct--neg {{ background: {NEG_LIGHT}; color: {NEG_DARK}; }}
.wisag-driver-pct--pos {{ background: {POS_LIGHT}; color: {POS_DARK}; }}
.wisag-driver-chev {{
    color: {WISAG_GRAY_500};
    font-size: 1.1rem;
    font-weight: 400;
}}

/* --- What-if card --- */
.wisag-whatif-card {{
    background: #FFFFFF;
    border: 1px solid {WISAG_GRAY_300};
    border-radius: 14px;
    padding: 22px 24px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    margin-top: 4px;
}}
.wisag-whatif-label {{
    color: {WISAG_GRAY_600};
    font-size: 0.80rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.wisag-whatif-value {{
    color: {WISAG_NAVY};
    font-size: 1.90rem;
    font-weight: 700;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}
.wisag-whatif-delta--pos {{ color: {POS_DARK}; font-weight: 600; }}
.wisag-whatif-delta--neg {{ color: {NEG_DARK}; font-weight: 600; }}

/* --- Explore-more lavender card --- */
.wisag-explore-card {{
    background: #F1E7FB;
    border-radius: 12px;
    padding: 16px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #4A148C;
}}
.wisag-explore-card-body {{ flex: 1; }}
.wisag-explore-title {{ font-weight: 700; font-size: 0.95rem; margin: 0 0 2px 0; }}
.wisag-explore-sub {{ font-size: 0.82rem; margin: 0; color: #6A1B9A; }}

/* --- Footer timestamp --- */
.wisag-footer-ts {{
    color: {WISAG_GRAY_600};
    font-size: 0.83rem;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 24px;
}}

/* Make page_link used as the 'View all' footer render as a subtle orange link */
.wisag-view-all > div > a,
.wisag-view-all > a {{
    color: {WISAG_ORANGE} !important;
    font-weight: 600;
    font-size: 0.90rem;
    text-decoration: none;
}}
.wisag-view-all > div > a:hover,
.wisag-view-all > a:hover {{
    color: {WISAG_ORANGE_DARK} !important;
    text-decoration: underline;
}}
</style>
"""


def inject_global_css() -> None:
    """Inject the global stylesheet. Call once per page right after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)
