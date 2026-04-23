"""Single-contract detail view, opened by clicking a row in the portfolio table.

Lifted verbatim from the old `app.py._render_overview`, with two changes:

- Accepts an explicit `cost_center_id` instead of picking the worst CM.
- Renders a "Back to overview" link that clears the session-state selection
  and returns to the portfolio view.
"""
from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from src import drivers, facility_overview as fov, sim
from src.components import driver_row, hero_card, icon_tile, section_card
from src.i18n import t
from src.viz_svg import area_chart


def _pct(v, signed: bool = False) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.1%}" if signed else f"{v:.1%}"


def _eur(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.0f} €".replace(",", ".")


def _render_back_link() -> None:
    if st.button(t("overview.back"), key="contract_detail_back"):
        st.session_state.pop("selected_cost_center", None)
        st.session_state.pop("portfolio_table", None)
        st.rerun()


_CATEGORY_KEYS: list[tuple[str, str]] = [
    ("revenue", "overview.cat.revenue"),
    ("costs",   "overview.cat.costs"),
    ("cm",      "overview.cat.cm"),
]


def _render_overview_block(focus: pd.DataFrame,
                           selected_period: pd.Timestamp,
                           cost_center_id: str) -> None:
    """Big "Overview" title + category pill bar + 12-month regression chart."""
    st.markdown(
        f"<h1 class='wisag-overview-title'>{escape(t('overview.section_title'))}</h1>",
        unsafe_allow_html=True,
    )

    state_key = f"contract_detail_cat_{cost_center_id}"
    current = st.session_state.get(state_key, "revenue")
    if current not in {k for k, _ in _CATEGORY_KEYS}:
        current = "revenue"

    st.markdown("<div class='wisag-cat-bar'>", unsafe_allow_html=True)
    cols = st.columns(3, gap="small")
    for col, (key, label_key) in zip(cols, _CATEGORY_KEYS):
        with col:
            btn_type = "primary" if key == current else "secondary"
            if st.button(
                t(label_key),
                key=f"cat_{cost_center_id}_{key}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state[state_key] = key
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    hist = focus[focus["period"] <= selected_period]
    values, periods = fov.category_series(hist, current, n=12)
    if len(values) < 2:
        st.info(t("overview.no_focus"))
        return

    trend = fov.linear_trend(values)
    declining = trend[-1] < trend[0]
    svg = area_chart(
        values,
        periods,
        declining=declining,
        y_as_pct=False,
        value_fmt="eur",
        trendline=trend,
    )

    st.markdown(
        "<div class='wisag-chart-wrap'>"
        f"<p class='wisag-section-sub'>{escape(t('overview.trend_sub'))}</p>"
        f"{svg}"
        "</div>",
        unsafe_allow_html=True,
    )


def render(df: pd.DataFrame, cost_center_id: str) -> None:
    """Render the single-contract overview for ``cost_center_id``."""
    _render_back_link()

    focus = df[df["cost_center_id"] == cost_center_id].sort_values("period").copy()
    if focus.empty:
        st.info(t("overview.no_focus"))
        return

    periods = sorted(focus["period"].dropna().unique())
    if not periods:
        st.info(t("overview.no_focus"))
        return
    period_labels = [pd.Timestamp(p).strftime("%B %Y") for p in periods]

    period_state_key = f"contract_detail_period_{cost_center_id}"
    if period_state_key not in st.session_state:
        st.session_state[period_state_key] = len(period_labels) - 1
    pick = int(st.session_state[period_state_key])
    pick = max(0, min(pick, len(period_labels) - 1))
    selected_period = pd.Timestamp(periods[pick])

    tb_l, tb_r = st.columns([5, 1])
    with tb_l:
        with st.popover(period_labels[pick], use_container_width=False):
            for i, label in enumerate(period_labels):
                if st.button(
                    label,
                    key=f"contract_detail_period_opt_{cost_center_id}_{i}",
                    use_container_width=True,
                ):
                    st.session_state[period_state_key] = i
                    st.rerun()
    with tb_r:
        st.download_button(
            label=t("overview.export"),
            data=focus.to_csv(index=False).encode("utf-8"),
            file_name=f"wisag_{cost_center_id}_{selected_period.strftime('%Y-%m')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    _render_overview_block(focus, selected_period, cost_center_id)

    focus_name = (str(focus["cost_center_name"].iloc[-1])
                  if "cost_center_name" in focus.columns
                  and pd.notna(focus["cost_center_name"].iloc[-1])
                  else str(cost_center_id))
    focus_region = (str(focus["region"].iloc[-1])
                    if "region" in focus.columns
                    and pd.notna(focus["region"].iloc[-1]) else "")
    focus_service = (str(focus["service_type"].iloc[-1])
                     if "service_type" in focus.columns
                     and pd.notna(focus["service_type"].iloc[-1]) else "")

    focus_month = focus[focus["period"] == selected_period]
    if focus_month.empty:
        focus_month = focus.tail(1)
    current_row = focus_month.iloc[-1]

    rev_cur = float(current_row.get("revenue_total") or 0)
    cm_cur = float(current_row.get("cm_db") or 0)
    margin_cur = (cm_cur / rev_cur) if rev_cur else 0.0
    cost_cur = rev_cur - cm_cur

    prior_rows = focus[focus["period"] < current_row["period"]]
    prior_row = prior_rows.iloc[-1] if not prior_rows.empty else None
    if prior_row is not None and (prior_row.get("revenue_total") or 0) > 0:
        rev_prev = float(prior_row["revenue_total"])
        cm_prev = float(prior_row["cm_db"] or 0)
        margin_prev = cm_prev / rev_prev
        margin_mom = margin_cur - margin_prev
        cost_prev = rev_prev - cm_prev
        cost_mom_pct = ((cost_cur - cost_prev) / cost_prev) if cost_prev > 0 else None
    else:
        margin_mom = None
        cost_mom_pct = None

    status_level = fov.status_for(margin_cur, margin_mom)
    # A 5 %+ cost jump is notable even when margin still looks fine — promote
    # healthy → warn so the status pill matches the cost story.
    if (status_level == "healthy" and cost_mom_pct is not None
            and cost_mom_pct >= 0.05):
        status_level = "warn"
    status_label_keys = {
        "critical": "overview.status.critical",
        "warn":     "overview.status.warn",
        "healthy":  "overview.status.healthy",
    }
    mom_neg = (margin_mom is not None) and (margin_mom < 0)
    cost_up = (cost_mom_pct is not None) and (cost_mom_pct > 0)
    cost_mom_label = (
        f"{cost_mom_pct:+.1%}" + (" ↑" if cost_up else (" ↓" if cost_mom_pct and cost_mom_pct < 0 else ""))
        if cost_mom_pct is not None else "—"
    )

    history_tail = focus[focus["period"] <= current_row["period"]].tail(6)
    spark_values = fov.sparkline_values(history_tail, n=6)
    spark_periods = list(history_tail["period"].tolist())

    spark_svg = (
        area_chart(spark_values, spark_periods, declining=mom_neg)
        if spark_values and len(spark_values) >= 2
        else None
    )

    hero_card(
        icon_html=icon_tile(fov.emoji_for(focus_service, focus_name), "purple"),
        title=focus_name,
        subtitle=focus_region,
        status_level=status_level,
        status_label=t(status_label_keys[status_level]),
        metrics=[
            {"label": t("overview.cost_total"), "value": _eur(cost_cur)},
            {"label": t("overview.cost_mom"),
             "value": cost_mom_label,
             "variant": "neg" if cost_up else ("pos" if cost_mom_pct and cost_mom_pct < 0 else None)},
            {"label": t("overview.margin"), "value": _pct(margin_cur)},
            {"label": t("overview.change_mom"),
             "value": (_pct(margin_mom, signed=True) if margin_mom is not None else "—")
                      + (" ↓" if mom_neg else (" ↑" if margin_mom and margin_mom > 0 else "")),
             "variant": "neg" if mom_neg else ("pos" if margin_mom and margin_mom > 0 else None)},
        ],
        chart_svg=spark_svg,
    )

    DRIVER_ICON = fov.DRIVER_ICON
    ACTIONS = fov.ACTIONS

    cost_drivers: list[drivers.Driver] = (
        fov.worst_cost_drivers(current_row, prior_row, limit=3)
        if prior_row is not None else []
    )

    action_keys: list[str] = []
    for d in cost_drivers:
        cls = fov.classify_driver(d)
        mapped = DRIVER_ICON[cls][2] if cls in DRIVER_ICON else None
        if mapped and mapped not in action_keys:
            action_keys.append(mapped)
    for fallback in ("shift", "absence", "onboarding"):
        if len(action_keys) >= 3:
            break
        if fallback not in action_keys:
            action_keys.append(fallback)
    action_keys = action_keys[:3]

    col_why, col_do = st.columns(2)

    with col_why:
        rows_html = ""
        if not cost_drivers or prior_row is None:
            rows_html = (
                f"<p class='wisag-driver-sub wisag-empty-row'>"
                f"{escape(t('overview.no_baseline'))}</p>"
            )
        else:
            for d in cost_drivers:
                cls = fov.classify_driver(d)
                emoji, title_key, _action = DRIVER_ICON[cls]
                pct = fov.driver_pct_change(d)
                pct_label = (
                    f"+{abs(pct):.1%}" if pct is not None
                    else _eur(d.current - d.baseline)
                )
                cause_key = f"{title_key}.cause"
                cause_txt = t(cause_key)
                # Fall back to the short sub line if no `.cause` string is defined.
                if cause_txt == cause_key:
                    cause_txt = t(f"{title_key}.sub")
                rows_html += driver_row(
                    icon=emoji,
                    title=t(title_key),
                    subtitle=cause_txt,
                    pct_label=pct_label,
                    variant="neg",
                )
        section_card(
            title=t("overview.cost_causes_title"),
            subtitle=t("overview.cost_causes_sub"),
            rows_html=rows_html,
        )

    with col_do:
        rows_html = ""
        for key in action_keys:
            a = ACTIONS[key]
            why_key = a.get("why_key")
            why_txt = t(why_key) if why_key else None
            if why_txt == why_key:  # missing translation → render without rationale
                why_txt = None
            rows_html += driver_row(
                icon=a["icon"],
                title=t(a["title_key"]),
                subtitle=t(a["sub_key"]),
                pct_label=f"+{a['impact']:.1%}",
                variant="pos",
                rationale=why_txt,
            )
        section_card(
            title=t("overview.solutions_title"),
            subtitle=t("overview.solutions_sub"),
            rows_html=rows_html,
            hint=t("overview.potential_impact"),
        )

    st.markdown("<div class='wisag-stack-gap wisag-stack-gap--md'></div>",
                unsafe_allow_html=True)

    with st.container():
        st.markdown(
            "<span class='wisag-whatif-anchor'></span>"
            f"<h3 class='wisag-section-title wisag-whatif-title'>"
            f"{escape(t('overview.whatif'))}</h3>"
            f"<p class='wisag-section-sub wisag-whatif-sub'>"
            f"{escape(t('overview.whatif_sub'))}</p>",
            unsafe_allow_html=True,
        )

        baseline_hc = sim.estimate_headcount(current_row)
        baseline_hc_int = int(round(baseline_hc)) if baseline_hc else 100

        wif_l, wif_m, wif_r = st.columns([3, 2, 2], vertical_alignment="center")

        with wif_l:
            sub_l, sub_m, sub_r = st.columns([2, 1, 2])
            with sub_l:
                bl_in = st.number_input(
                    t("overview.team_size"),
                    value=baseline_hc_int, min_value=1, step=1,
                    key=f"wif_bl_{cost_center_id}",
                )
            with sub_m:
                st.markdown(
                    "<div class='wisag-wif-arrow'>→</div>",
                    unsafe_allow_html=True,
                )
            with sub_r:
                new_in = st.number_input(
                    t("overview.employees"),
                    value=baseline_hc_int, min_value=0, step=1,
                    key=f"wif_new_{cost_center_id}",
                )

            sim_result = sim.simulate_team_size(
                current_row, new_headcount=new_in, baseline_headcount=bl_in,
            )
            st.markdown(
                "<div class='wisag-status-line'>"
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
    {escape(t('overview.vs_current', p=_pct(sim_result.delta_margin, signed=True)))}
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

        with wif_r:
            st.markdown(
                f"""
<div class='wisag-explore-wrap'>
  <div class='wisag-explore-card'>
    <div class='wisag-explore-card-body'>
      <p class='wisag-explore-title'>{escape(t('overview.explore_more'))}</p>
      <p class='wisag-explore-sub'>{escape(t('overview.explore_more_sub'))}</p>
    </div>
    <span class='wisag-driver-chev'>›</span>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
<div class='wisag-footer-ts'>
  {escape(t('overview.data_updated', ts=datetime.now().strftime('%b %d, %Y · %H:%M')))}
</div>
""",
        unsafe_allow_html=True,
    )
