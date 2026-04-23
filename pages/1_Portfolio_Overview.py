"""Page 1 — Overview: one-facility dashboard that mirrors the reference mock.

Layout (identical to the reference picture):
  1. Topbar: breadcrumb · period picker · Export
  2. Hero card: icon + title/region/status pill + Margin + Change vs last month
     + an inline SVG sparkline — all inside ONE bordered white card.
  3. Two side-by-side cards: "Why did the margin drop?" / "What can we do?"
  4. What if? simulator (team size → new margin) + "Explore more scenarios"
  5. Footer: "Data last updated: …"

Nothing else is rendered on this page — the prior DQ banner, worst-period
banner, facility dropdown, and page header were removed so the layout
matches the mock verbatim.
"""
from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from src import anomaly, drivers, facility_overview as fov, sim
from src.components import (
    driver_row,
    icon_tile,
    setup_page,
    sidebar_logo,
    sidebar_nav,
    status_pill,
)
from src.i18n import t
from src.theme import NEG, POS

PAGE_PATH = "pages/1_Portfolio_Overview.py"

setup_page("nav.portfolio", icon="📈")
sidebar_logo()

df = st.session_state.get("filtered")
if df is None or df.empty:
    sidebar_nav(PAGE_PATH, alerts_count=0)
    st.warning(t("data.no_data_page"))
    st.stop()

# --- Alerts-count for the sidebar badge ---
anoms_all = anomaly.top_n(df, n=100)
alerts_count = int((anoms_all.get("severity", pd.Series(dtype=object)) == "high").sum()) \
    if not anoms_all.empty else 0
sidebar_nav(PAGE_PATH, alerts_count=alerts_count)


# ---------- Formatters ----------
def _pct(v, signed: bool = False, points: bool = False) -> str:
    if v is None or pd.isna(v):
        return "—"
    fmt = f"{v:+.1%}" if signed else f"{v:.1%}"
    out = fmt
    if points:
        out = out.replace("%", "%")  # keep % glyph; the mock uses "%" for pp
    return out


def _eur(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.0f} €"


# =============================================================
# TOPBAR: breadcrumb · period picker · Export
# =============================================================
tb_l, tb_m, tb_r = st.columns([3, 2, 1])
with tb_l:
    st.markdown(
        f"<a class='wisag-breadcrumb' href='/' target='_self'>"
        f"{escape(t('overview.back'))}</a>",
        unsafe_allow_html=True,
    )
with tb_m:
    periods = sorted(df["period"].dropna().unique())
    period_labels = [pd.Timestamp(p).strftime("%B %Y") for p in periods]
    default_idx = len(period_labels) - 1
    pick = st.selectbox(
        t("overview.period_label"),
        options=list(range(len(period_labels))),
        format_func=lambda i: period_labels[i],
        index=default_idx,
        label_visibility="collapsed",
        key="overview_period_pick",
    )
    selected_period = pd.Timestamp(periods[pick])
with tb_r:
    st.download_button(
        label=f"⬇  {t('overview.export')}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"wisag_export_{selected_period.strftime('%Y-%m')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =============================================================
# Pick the focus cost center (invisible to the user — defaults to the
# worst-CM facility; overridable via st.session_state from other pages).
# =============================================================
focus_id = fov.pick_focus_cost_center(df, override=st.session_state.get("demo_cost_center"))
if focus_id is None:
    st.info(t("overview.no_focus"))
    st.stop()
st.session_state["demo_cost_center"] = focus_id

focus = df[df["cost_center_id"] == focus_id].sort_values("period").copy()
if focus.empty:
    st.info(t("overview.no_focus"))
    st.stop()

focus_name = (str(focus["cost_center_name"].iloc[-1])
              if "cost_center_name" in focus.columns
              and pd.notna(focus["cost_center_name"].iloc[-1])
              else str(focus_id))
focus_region = (str(focus["region"].iloc[-1])
                if "region" in focus.columns
                and pd.notna(focus["region"].iloc[-1]) else "")
focus_service = (str(focus["service_type"].iloc[-1])
                 if "service_type" in focus.columns
                 and pd.notna(focus["service_type"].iloc[-1]) else "")


# --- Most-recent-month snapshot + MoM context ---
focus_month = focus[focus["period"] == selected_period]
if focus_month.empty:
    focus_month = focus.tail(1)
current_row = focus_month.iloc[-1]

rev_cur = float(current_row.get("revenue_total") or 0)
cm_cur = float(current_row.get("cm_db") or 0)
margin_cur = (cm_cur / rev_cur) if rev_cur else 0.0

prior_rows = focus[focus["period"] < current_row["period"]]
prior_row = prior_rows.iloc[-1] if not prior_rows.empty else None
if prior_row is not None and (prior_row.get("revenue_total") or 0) > 0:
    margin_prev = float(prior_row["cm_db"] or 0) / float(prior_row["revenue_total"])
    margin_mom = margin_cur - margin_prev
else:
    margin_prev = None
    margin_mom = None


# --- Status classification (Critical / Watch / Healthy) ---
_STATUS_LABEL_KEYS = {
    "critical": "overview.status.critical",
    "warn":     "overview.status.warn",
    "healthy":  "overview.status.healthy",
}
status_level = fov.status_for(margin_cur, margin_mom)
status_label = t(_STATUS_LABEL_KEYS[status_level])


# =============================================================
# HERO CARD (one bordered white card; SVG sparkline inline on the right)
# =============================================================

def _svg_sparkline(values: list[float], *, declining: bool) -> str:
    """Inline SVG area chart — rendered INSIDE the hero's HTML block."""
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = max(hi - lo, 1e-9)
    n = len(values)
    width, height, pad_t, pad_b = 220, 80, 10, 20
    y_range = height - pad_t - pad_b
    xs = [i * (width / (n - 1)) if n > 1 else width / 2 for i in range(n)]
    ys = [pad_t + (1 - (v - lo) / span) * y_range for v in values]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = (f"M{xs[0]:.1f},{height - pad_b:.1f} L"
            + poly
            + f" L{xs[-1]:.1f},{height - pad_b:.1f} Z")
    stroke = NEG if declining else POS
    fill = "rgba(198,40,40,0.18)" if declining else "rgba(46,125,50,0.18)"
    axis_y_max = f"{max(values) * 100:.0f}%"
    axis_y_mid = f"{(max(values) + min(values)) / 2 * 100:.0f}%"
    axis_y_min = f"{min(values) * 100:.0f}%"
    return f"""
<svg viewBox='0 0 {width + 46} {height}' width='{width + 46}' height='{height}'
     style='display:block;'>
  <g font-family='Inter, system-ui, sans-serif' font-size='10' fill='#6B6B6B'>
    <text x='{width + 4}' y='{pad_t + 4}'>{axis_y_max}</text>
    <text x='{width + 4}' y='{pad_t + y_range / 2 + 4}'>{axis_y_mid}</text>
    <text x='{width + 4}' y='{pad_t + y_range + 4}'>{axis_y_min}</text>
  </g>
  <path d='{area}' fill='{fill}' stroke='none' />
  <polyline points='{poly}' fill='none' stroke='{stroke}' stroke-width='2' />
</svg>
"""


mom_neg = (margin_mom is not None) and (margin_mom < 0)
mom_cls = ("wisag-hero-metric-value--neg" if mom_neg
           else ("wisag-hero-metric-value--pos"
                 if margin_mom and margin_mom > 0 else ""))
mom_text = _pct(margin_mom, signed=True) if margin_mom is not None else "—"
mom_arrow = " ↓" if mom_neg else (" ↑" if margin_mom and margin_mom > 0 else "")

sparkline_svg = _svg_sparkline(fov.sparkline_values(focus, n=5), declining=mom_neg)
hero_icon = icon_tile(fov.emoji_for(focus_service, focus_name), "purple")
hero_status = status_pill(status_level, status_label)

st.markdown(
    f"""
<div class='wisag-hero-card'>
  <div class='wisag-hero-grid'>
    <div style='display:flex;align-items:center;gap:16px;'>
      {hero_icon}
      <div>
        <h2 class='wisag-hero-title'>{escape(focus_name)}</h2>
        <p class='wisag-hero-sub'>{escape(focus_region)}</p>
        {hero_status}
      </div>
    </div>
    <div>
      <div class='wisag-hero-metric-label'>{escape(t('overview.margin'))}</div>
      <div class='wisag-hero-metric-value'>{_pct(margin_cur)}</div>
    </div>
    <div>
      <div class='wisag-hero-metric-label'>{escape(t('overview.change_mom'))}</div>
      <div class='wisag-hero-metric-value {mom_cls}'>{mom_text}{mom_arrow}</div>
    </div>
    <div class='wisag-hero-spark'>{sparkline_svg}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# =============================================================
# DRIVER DECOMPOSITION (reuse src/drivers.py) + action mapping
# =============================================================
top_drivers: list[drivers.Driver] = []
if prior_row is not None:
    top_drivers = drivers.decompose(current_row, prior_row)

DRIVER_ICON = fov.DRIVER_ICON
ACTIONS = fov.ACTIONS


worst_drivers: list[tuple[str, drivers.Driver]] = []
seen_classes: set[str] = set()
for d in sorted(top_drivers, key=lambda x: x.delta_eur):
    if d.delta_eur >= 0:
        break
    cls = fov.classify_driver(d)
    if cls in seen_classes or cls not in DRIVER_ICON:
        continue
    seen_classes.add(cls)
    worst_drivers.append((cls, d))
    if len(worst_drivers) == 3:
        break


action_keys: list[str] = []
for cls, _d in worst_drivers:
    mapped = DRIVER_ICON[cls][2]
    if mapped and mapped not in action_keys:
        action_keys.append(mapped)
for fallback in ("shift", "absence", "onboarding"):
    if len(action_keys) >= 3:
        break
    if fallback not in action_keys:
        action_keys.append(fallback)
action_keys = action_keys[:3]


# =============================================================
# TWO SIDE-BY-SIDE CARDS
# =============================================================
col_why, col_do = st.columns(2)

with col_why:
    why_rows_html = ""
    if not worst_drivers or prior_row is None:
        why_rows_html = (
            f"<p class='wisag-driver-sub' style='padding:12px 0;'>"
            f"{escape(t('overview.no_baseline'))}</p>"
        )
    else:
        for cls, d in worst_drivers:
            emoji, title_key, _action = DRIVER_ICON[cls]
            pct = fov.driver_pct_change(d)
            if pct is not None:
                pct_label = (f"+{abs(pct):.1%}" if pct > 0
                             else f"-{abs(pct):.1%}")
            else:
                pct_label = _eur(abs(d.delta_eur))
            why_rows_html += driver_row(
                icon=emoji,
                title=t(title_key),
                subtitle=t(f"{title_key}.sub"),
                pct_label=pct_label,
                variant="neg",
            )
    st.markdown(
        f"""
<div class='wisag-section-card'>
  <div class='wisag-section-head'>
    <div>
      <h3 class='wisag-section-title'>{escape(t('overview.why_drop'))} ⓘ</h3>
      <p class='wisag-section-sub'>{escape(t('overview.why_drop_sub'))}</p>
    </div>
  </div>
  {why_rows_html}
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='wisag-view-all'>", unsafe_allow_html=True)
    if hasattr(st, "page_link"):
        st.page_link("pages/2_Deep_Dive.py", label=t("overview.view_all_drivers"))
    st.markdown("</div>", unsafe_allow_html=True)

with col_do:
    do_rows_html = ""
    for key in action_keys:
        a = ACTIONS[key]
        do_rows_html += driver_row(
            icon=a["icon"],
            title=t(a["title_key"]),
            subtitle=t(a["sub_key"]),
            pct_label=f"+{a['impact']:.1%}",
            variant="pos",
        )
    st.markdown(
        f"""
<div class='wisag-section-card'>
  <div class='wisag-section-head'>
    <div>
      <h3 class='wisag-section-title'>{escape(t('overview.what_do'))}</h3>
      <p class='wisag-section-sub'>{escape(t('overview.what_do_sub'))}</p>
    </div>
    <div class='wisag-section-hint'>{escape(t('overview.potential_impact'))}</div>
  </div>
  {do_rows_html}
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='wisag-view-all'>", unsafe_allow_html=True)
    if hasattr(st, "page_link"):
        st.page_link("pages/3_Early_Warnings.py",
                     label=t("overview.view_all_actions"))
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# WHAT-IF CARD
# =============================================================
st.markdown(
    "<div style='height:16px;'></div>"
    "<div class='wisag-section-card' style='padding-bottom:4px;margin-bottom:8px;'>"
    f"  <h3 class='wisag-section-title' style='margin:0;'>"
    f"    {escape(t('overview.whatif'))}"
    "  </h3>"
    f"  <p class='wisag-section-sub' style='margin:2px 0 0 0;'>"
    f"    {escape(t('overview.whatif_sub'))}</p>"
    "</div>",
    unsafe_allow_html=True,
)

baseline_hc = sim.estimate_headcount(current_row)
baseline_hc_int = int(round(baseline_hc)) if baseline_hc else 100

wif_l, wif_m, wif_r = st.columns([3, 2, 2])

with wif_l:
    sub_l, sub_m, sub_r = st.columns([2, 1, 2])
    with sub_l:
        bl_in = st.number_input(
            t("overview.team_size"),
            value=baseline_hc_int, min_value=1, step=1, key="wif_bl",
        )
    with sub_m:
        st.markdown(
            "<div style='text-align:center;padding-top:34px;"
            "font-size:1.3rem;color:#6B6B6B;'>→</div>",
            unsafe_allow_html=True,
        )
    with sub_r:
        new_in = st.number_input(
            t("overview.employees"),
            value=baseline_hc_int, min_value=0, step=1, key="wif_new",
        )

    sim_result = sim.simulate_team_size(
        current_row, new_headcount=new_in, baseline_headcount=bl_in,
    )
    st.markdown(
        "<div style='margin-top:6px;'>"
        "<span class='wisag-pill wisag-pill-pos'>"
        f"{escape(t('overview.productivity_gain', p=_pct(sim_result.productivity_gain_pct, signed=True)))}"
        "</span></div>",
        unsafe_allow_html=True,
    )

with wif_m:
    delta_cls = ("wisag-whatif-delta--pos" if sim_result.delta_margin >= 0
                 else "wisag-whatif-delta--neg")
    st.markdown(
        f"""
<div>
  <div class='wisag-whatif-label'>{escape(t('overview.new_margin'))}</div>
  <div class='wisag-whatif-value'>{_pct(sim_result.new_margin)}</div>
  <div class='{delta_cls}'>
    {escape(t('overview.vs_current', p=_pct(sim_result.delta_margin, signed=True, points=True)))}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

with wif_r:
    st.markdown(
        f"""
<div class='wisag-explore-card'>
  <span class='wisag-icon-tile wisag-icon-tile--sm'
        style='background:#E6D6F5;color:#4A148C;'>💡</span>
  <div class='wisag-explore-card-body'>
    <p class='wisag-explore-title'>{escape(t('overview.explore_more'))}</p>
    <p class='wisag-explore-sub'>{escape(t('overview.explore_more_sub'))}</p>
  </div>
  <span class='wisag-driver-chev'>›</span>
</div>
""",
        unsafe_allow_html=True,
    )
    if hasattr(st, "page_link"):
        st.page_link("pages/4_Copilot_Chat.py",
                     label=f"✨  {t('overview.explore_more')}  →")


# =============================================================
# FOOTER
# =============================================================
st.markdown(
    f"""
<div class='wisag-footer-ts'>
  🕒 {escape(t('overview.data_updated', ts=datetime.now().strftime('%b %d, %Y, %H:%M')))}
</div>
""",
    unsafe_allow_html=True,
)
