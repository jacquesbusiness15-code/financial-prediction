"""Single-contract detail view, opened by clicking a row in the portfolio table."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from src import drivers, facility_overview as fov
from src.components import driver_row, hero_card, icon_tile, section_card
from src.contract_metrics import compute_contract_overview_metrics, compute_metrics
from src.early_warning import detect as detect_warnings
from src.i18n import t
from src.kpi_gaps import detect_gaps
from src.portfolio_page import _fmt_eur_signed
from src.portfolio_ranking import compute_rankings
from src.solutions_panel import render as render_solutions_panel
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


def _render_category_pills(state_key: str, btn_key_prefix: str, current: str) -> None:
    st.markdown("<div class='wisag-cat-bar'>", unsafe_allow_html=True)
    cols = st.columns(3, gap="small")
    for col, (key, label_key) in zip(cols, _CATEGORY_KEYS):
        with col:
            if st.button(
                t(label_key),
                key=f"{btn_key_prefix}_{key}",
                type=("primary" if key == current else "secondary"),
                use_container_width=True,
            ):
                st.session_state[state_key] = key
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_overview_block(focus: pd.DataFrame,
                           selected_period: pd.Timestamp,
                           cost_center_id: str) -> None:
    st.markdown(
        f"<h1 class='wisag-overview-title'>{escape(t('overview.section_title'))}</h1>",
        unsafe_allow_html=True,
    )

    state_key = f"contract_detail_cat_{cost_center_id}"
    current = st.session_state.get(state_key, "revenue")
    if current not in {k for k, _ in _CATEGORY_KEYS}:
        current = "revenue"

    _render_category_pills(state_key, f"cat_{cost_center_id}", current)

    hist = focus[focus["period"] <= selected_period]
    values, periods = fov.category_series(hist, current, n=12)
    if len(values) < 2:
        st.info(t("overview.no_focus"))
        return

    trend = fov.linear_trend(values)
    # Red = bad, green = good. Rising costs are bad; rising revenue/CM are good.
    rising = values[-1] > values[0]
    bad_trend = rising if current == "costs" else not rising
    svg = area_chart(
        values, periods,
        declining=bad_trend,
        y_as_pct=False, value_fmt="eur", trendline=trend,
    )
    st.markdown(
        "<div class='wisag-chart-wrap'>"
        f"<p class='wisag-section-sub'>{escape(t('overview.trend_sub'))}</p>"
        f"{svg}"
        "</div>",
        unsafe_allow_html=True,
    )


def _last_str(focus: pd.DataFrame, col: str, fallback: str = "") -> str:
    if col not in focus.columns:
        return fallback
    v = focus[col].iloc[-1]
    return str(v) if pd.notna(v) else fallback


def _has_margin_value(row: pd.Series) -> bool:
    cm_pct = row.get("cm_db_pct")
    if cm_pct is not None and not pd.isna(cm_pct):
        return True
    revenue = row.get("revenue_total")
    return revenue is not None and not pd.isna(revenue) and float(revenue) >= 10.0


def _default_period_index(focus: pd.DataFrame) -> int:
    if focus.empty:
        return 0
    for idx in range(len(focus) - 1, -1, -1):
        if _has_margin_value(focus.iloc[idx]):
            period = pd.Timestamp(focus.iloc[idx]["period"])
            periods = list(focus["period"])
            for i in range(len(periods) - 1, -1, -1):
                if pd.Timestamp(periods[i]) == period:
                    return i
    return len(focus) - 1


def _arrow(value: float | None) -> str:
    if value is None or value == 0:
        return ""
    return " ↑" if value > 0 else " ↓"


def _variant(value: float | None, *, bad_up: bool) -> str | None:
    if value is None or value == 0:
        return None
    if bad_up:
        return "neg" if value > 0 else "pos"
    return "pos" if value > 0 else "neg"


_STATUS_LABEL_KEYS = {
    "critical": "overview.status.critical",
    "warn":     "overview.status.warn",
    "healthy":  "overview.status.healthy",
}


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
        st.session_state[period_state_key] = _default_period_index(focus)
    pick = max(0, min(int(st.session_state[period_state_key]), len(period_labels) - 1))
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

    focus_name = _last_str(focus, "cost_center_name", str(cost_center_id))
    focus_region = _last_str(focus, "region")
    focus_service = _last_str(focus, "service_type")

    focus_month = focus[focus["period"] == selected_period]
    if focus_month.empty:
        focus_month = focus.tail(1)
    current_row = focus_month.iloc[-1]

    prior_rows = focus[focus["period"] < current_row["period"]]
    prior_row = prior_rows.iloc[-1] if not prior_rows.empty else None
    overview = compute_contract_overview_metrics(current_row, prior_row)
    margin_cur = overview.margin_pct
    margin_mom = overview.margin_mom_delta
    cost_mom_eur = overview.cost_mom_eur
    margin_mom_eur = overview.margin_mom_eur

    status_level = fov.status_for(margin_cur, margin_mom)
    # Promote healthy -> warn when costs rose materially even if margin looks fine.
    if (status_level == "healthy" and cost_mom_eur is not None
            and cost_mom_eur > 0):
        status_level = "warn"

    # Cost MoM is always shown as the absolute EUR delta.
    if cost_mom_eur is not None and cost_mom_eur != 0:
        cost_mom_label = _fmt_eur_signed(cost_mom_eur) + _arrow(cost_mom_eur)
        cost_mom_variant = _variant(cost_mom_eur, bad_up=True)
    else:
        cost_mom_label = "—"
        cost_mom_variant = None

    # Margin change vs previous month is shown as an EUR delta so it
    # mirrors the "Kosten vs. Vormonat" (EUR) card next to "Gesamtkosten".
    # The margin-ratio pp delta in `margin_mom` is still used for status/variant.
    if margin_mom_eur is not None and margin_mom_eur != 0:
        margin_mom_label = _fmt_eur_signed(margin_mom_eur) + _arrow(margin_mom_eur)
        margin_mom_variant = _variant(margin_mom_eur, bad_up=False)
    else:
        margin_mom_label = "—"
        margin_mom_variant = None

    hero_card(
        icon_html=icon_tile(fov.emoji_for(focus_service, focus_name), "purple"),
        title=focus_name,
        subtitle=focus_region,
        status_level=status_level,
        status_label=t(_STATUS_LABEL_KEYS[status_level]),
        metrics=[
            {"label": t("overview.cost_total"), "value": _eur(overview.total_cost_eur),
             "help_key": "labor_ratio"},
            {"label": t("overview.cost_mom"), "value": cost_mom_label,
             "variant": cost_mom_variant, "help_key": "labor_ratio"},
            {"label": t("overview.margin"), "value": _eur(overview.margin_eur),
             "help_key": "cm_db"},
            {"label": t("overview.change_mom"), "value": margin_mom_label,
             "variant": margin_mom_variant, "help_key": "cm_pct"},
        ],
    )

    cost_drivers: list[drivers.Driver] = (
        fov.worst_cost_drivers(current_row, prior_row, limit=3)
        if prior_row is not None else []
    )

    action_keys: list[str] = []
    for d in cost_drivers:
        cls = fov.classify_driver(d)
        mapped = fov.DRIVER_ICON[cls][2] if cls in fov.DRIVER_ICON else None
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
        _render_causes_card(cost_drivers, prior_row is not None)
    with col_do:
        _render_actions_card(action_keys)

    _render_kpi_gaps_card(current_row, prior_row)

    _render_solution_finder_card(df, cost_center_id)


def _render_solution_finder_card(df: pd.DataFrame, cost_center_id: str) -> None:
    rankings = compute_rankings(df)
    target = next((r for r in rankings
                   if str(r.cost_center_id) == str(cost_center_id)), None)
    if target is None:
        return
    all_metrics = compute_metrics([target], df)
    if not all_metrics:
        return
    warnings = detect_warnings(df)
    render_solutions_panel(df, cost_center_id, all_metrics[0], warnings)


def _render_causes_card(cost_drivers, have_prior: bool) -> None:
    from src.glossary import g as _g

    if not cost_drivers or not have_prior:
        rows_html = (f"<p class='wisag-driver-sub wisag-empty-row'>"
                     f"{escape(t('overview.no_baseline'))}</p>")
    else:
        rows_html = ""
        for d in cost_drivers:
            cls = fov.classify_driver(d)
            emoji, title_key, _action_key = fov.DRIVER_ICON[cls]
            pct = fov.driver_pct_change(d)
            # `safe_pct_change` returns None when the baseline is too small
            # or sign-flips — in those cases, show the EUR delta.
            pct_label = (f"+{abs(pct):.1%}" if pct is not None
                         else _eur(d.current - d.baseline))
            cause_key = f"{title_key}.cause"
            cause_txt = t(cause_key)
            if cause_txt == cause_key:
                cause_txt = t(f"{title_key}.sub")
            rows_html += driver_row(
                icon=emoji, title=t(title_key), subtitle=cause_txt,
                pct_label=pct_label, variant="neg",
            )
    section_card(
        title=t("overview.cost_causes_title"),
        subtitle=t("overview.cost_causes_sub"),
        rows_html=rows_html,
        title_help=_g("waterfall"),
    )


def _render_actions_card(action_keys: list[str]) -> None:
    from src.glossary import g as _g

    rows_html = ""
    for key in action_keys:
        a = fov.ACTIONS[key]
        why_key = a.get("why_key")
        why_txt = t(why_key) if why_key else None
        if why_txt == why_key:
            why_txt = None
        rows_html += driver_row(
            icon=a["icon"], title=t(a["title_key"]), subtitle=t(a["sub_key"]),
            pct_label=f"+{a['impact']:.1%}", variant="pos", rationale=why_txt,
        )
    section_card(
        title=t("overview.solutions_title"),
        subtitle=t("overview.solutions_sub"),
        rows_html=rows_html,
        hint=t("overview.potential_impact"),
        title_help=_g("impact_eur"),
    )


def _render_kpi_gaps_card(current_row: pd.Series, prior_row: pd.Series | None) -> None:
    """Reflect on which KPIs would sharpen the diagnosis for this period."""
    if prior_row is None:
        gaps = detect_gaps(current_row, [], 0.0, 0.0, limit=4)
    else:
        driver_list = drivers.decompose(current_row, prior_row)
        observed = drivers.observed_delta(current_row, prior_row)
        residual = drivers.residual(driver_list, observed)
        gaps = detect_gaps(current_row, driver_list, observed, residual, limit=4)

    if not gaps:
        rows_html = (f"<p class='wisag-driver-sub wisag-empty-row'>"
                     f"{escape(t('gaps.empty'))}</p>")
    else:
        rows_html = ""
        for gap in gaps:
            rows_html += driver_row(
                icon="?",
                title=t(gap.title_key),
                subtitle=t(gap.reason_key),
                pct_label="",
                variant="neg",
                tile_variant="purple",
                show_chevron=False,
            )
    section_card(
        title=t("gaps.section_title"),
        subtitle=t("gaps.section_sub"),
        rows_html=rows_html,
        hint=t("gaps.section_hint"),
    )
