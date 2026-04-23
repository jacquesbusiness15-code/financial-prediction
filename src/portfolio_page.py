"""Portfolio landing page: KPI bar + filters + searchable, selectable contract table.

Replaces the previous single-contract overview as the landing view. Row selection
stores the chosen `cost_center_id` in `st.session_state["selected_cost_center"]`
so `app.py` can dispatch to the detail view on the next rerun.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

import pandas as pd
import streamlit as st

from src import facility_overview as fov
from src.components import section_card
from src.contract_metrics import ContractMetrics, compute_metrics
from src.i18n import t
from src.portfolio_ranking import (
    ContractRanking,
    compute_rankings,
    filter_rankings,
    totals,
)
from src.viz_svg import area_chart


_OVERVIEW_CATEGORY_KEYS: list[tuple[str, str]] = [
    ("revenue", "overview.cat.revenue"),
    ("costs",   "overview.cat.costs"),
    ("cm",      "overview.cat.cm"),
]


@st.cache_data(show_spinner=False)
def _aggregate_portfolio_totals(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("period", as_index=False)
              .agg(revenue_total=("revenue_total", "sum"),
                   cm_db=("cm_db", "sum"))
              .sort_values("period"))


def _render_portfolio_overview_block(df: pd.DataFrame) -> None:
    """Big "Overview" title + category pill bar + 12-month regression chart.

    Aggregates `revenue_total` and `cm_db` across all cost centers per period.
    """
    st.markdown(
        f"<h1 class='wisag-overview-title'>{escape(t('overview.section_title'))}</h1>",
        unsafe_allow_html=True,
    )
    _render_overview_fragment(df)


@st.fragment
def _render_overview_fragment(df: pd.DataFrame) -> None:
    state_key = "portfolio_overview_cat"
    current = st.session_state.get(state_key, "revenue")
    if current not in {k for k, _ in _OVERVIEW_CATEGORY_KEYS}:
        current = "revenue"

    st.markdown("<div class='wisag-cat-bar'>", unsafe_allow_html=True)
    cols = st.columns(3, gap="small")
    for col, (key, label_key) in zip(cols, _OVERVIEW_CATEGORY_KEYS):
        with col:
            btn_type = "primary" if key == current else "secondary"
            if st.button(
                t(label_key),
                key=f"portfolio_cat_{key}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state[state_key] = key
    st.markdown("</div>", unsafe_allow_html=True)

    if df.empty or "period" not in df.columns \
            or "revenue_total" not in df.columns or "cm_db" not in df.columns:
        st.info(t("overview.no_focus"))
        return

    agg = _aggregate_portfolio_totals(df)

    values, periods = fov.category_series(agg, current, n=12)
    if len(values) < 2:
        st.info(t("overview.no_focus"))
        return

    trend = fov.linear_trend(values)
    declining = trend[-1] < trend[0]
    svg = area_chart(
        values, periods,
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


REASON_KEYS = ["labor", "absence", "training", "subcontractor",
               "material", "vehicle", "revenue", "other"]


@dataclass
class FilterState:
    search: str = ""
    regions: list[str] = field(default_factory=list)
    clients: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    cost_centers: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    month_range: tuple[pd.Timestamp, pd.Timestamp] | None = None
    show_profitable: bool = True


def _fmt_eur(v: float | None) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.0f} €".replace(",", ".")


def _fmt_period(p: pd.Timestamp | None) -> str:
    if p is None or pd.isna(p):
        return "—"
    return pd.Timestamp(p).strftime("%b %Y")


def _distinct(df: pd.DataFrame, col: str) -> list[str]:
    if col not in df.columns:
        return []
    vals = df[col].dropna().unique().tolist()
    return sorted({str(v) for v in vals})


def _render_filters(df: pd.DataFrame) -> FilterState:
    """Render search + filter widgets at the top of the page."""
    state = FilterState()

    state.search = st.text_input(
        label=t("portfolio.filters"),
        key="portfolio_search",
        placeholder=t("portfolio.search_placeholder"),
        label_visibility="collapsed",
    )

    with st.expander(t("portfolio.filters"), expanded=False):
        r1c1, r1c2, r1c3 = st.columns(3)
        r2c1, r2c2, r2c3 = st.columns(3)

        with r1c1:
            state.regions = st.multiselect(
                t("portfolio.filter_region"),
                options=_distinct(df, "region"),
                key="portfolio_filter_region",
            )

        with r1c2:
            periods = sorted(df["period"].dropna().unique()) if "period" in df.columns else []
            if len(periods) >= 2:
                options = [pd.Timestamp(p) for p in periods]
                labels = {p: p.strftime("%b %Y") for p in options}
                if "portfolio_filter_month" not in st.session_state:
                    st.session_state["portfolio_filter_month"] = (options[0], options[-1])
                picked = st.select_slider(
                    t("portfolio.filter_month"),
                    options=options,
                    format_func=lambda p: labels.get(pd.Timestamp(p),
                                                    pd.Timestamp(p).strftime("%b %Y")),
                    key="portfolio_filter_month",
                )
                if isinstance(picked, tuple) and len(picked) == 2:
                    state.month_range = (pd.Timestamp(picked[0]), pd.Timestamp(picked[1]))
            elif len(periods) == 1:
                only = pd.Timestamp(periods[0])
                st.caption(f"{t('portfolio.filter_month')}: {only.strftime('%b %Y')}")
                state.month_range = (only, only)

        with r1c3:
            state.clients = st.multiselect(
                t("portfolio.filter_client"),
                options=_distinct(df, "customer_name"),
                key="portfolio_filter_client",
            )

        with r2c1:
            state.industries = st.multiselect(
                t("portfolio.filter_branch"),
                options=_distinct(df, "industry"),
                key="portfolio_filter_branch",
            )

        with r2c2:
            reason_opts = REASON_KEYS
            state.reasons = st.multiselect(
                t("portfolio.filter_reason"),
                options=reason_opts,
                format_func=lambda k: t(f"reason.{k}"),
                key="portfolio_filter_reason",
            )

        with r2c3:
            state.cost_centers = st.multiselect(
                t("portfolio.filter_cost_center"),
                options=_distinct(df, "cost_center_id"),
                key="portfolio_filter_cost_center",
            )

        toggle_col, reset_col = st.columns([3, 1])
        with toggle_col:
            state.show_profitable = st.checkbox(
                t("portfolio.show_profitable"),
                value=True,
                key="portfolio_show_profitable",
            )
        with reset_col:
            if st.button(t("portfolio.filters_reset"), use_container_width=True):
                for key in (
                    "portfolio_search",
                    "portfolio_filter_region",
                    "portfolio_filter_client",
                    "portfolio_filter_branch",
                    "portfolio_filter_reason",
                    "portfolio_filter_cost_center",
                    "portfolio_filter_month",
                    "portfolio_show_profitable",
                ):
                    st.session_state.pop(key, None)

    return state


def _slice_by_months(df: pd.DataFrame,
                     rng: tuple[pd.Timestamp, pd.Timestamp] | None) -> pd.DataFrame:
    if rng is None or "period" not in df.columns:
        return df
    lo, hi = rng
    if lo > hi:
        lo, hi = hi, lo
    return df[(df["period"] >= lo) & (df["period"] <= hi)].copy()


def _render_kpi_bar(rankings: list[ContractRanking]) -> None:
    stats = totals(rankings)
    total_str = _fmt_eur(stats["total_unprofit_eur"])

    longest = stats["longest"]
    if longest is None or longest.months_unprofitable <= 0:
        longest_value = t("portfolio.kpi_none")
        longest_sub = ""
    else:
        unit_key = ("portfolio.kpi_longest_unit_one"
                    if longest.months_unprofitable == 1
                    else "portfolio.kpi_longest_unit")
        longest_value = t(unit_key, n=longest.months_unprofitable)
        longest_sub = t(
            "portfolio.kpi_longest_unprofit_sub",
            name=longest.cost_center_name,
            since=_fmt_period(longest.first_unprofitable_period),
        )

    left, right = st.columns(2)
    with left:
        st.metric(t("portfolio.kpi_total_unprofit"), total_str)
        st.caption(t("portfolio.kpi_total_unprofit_sub"))
    with right:
        st.metric(t("portfolio.kpi_longest_unprofit"), longest_value)
        if longest_sub:
            st.caption(longest_sub)


# ---------------------------------------------------------------------------
# Tab configuration — each of the five category tabs defines its own columns,
# grid template, sort keys, default sort direction, and i18n header labels.
# ---------------------------------------------------------------------------

TAB_OVERALL = "overall"
TAB_PROFITABILITY = "profitability"
TAB_COST = "cost_structure"
TAB_EFFICIENCY = "efficiency"
TAB_STABILITY = "stability"

_TAB_SLUGS: list[str] = [
    TAB_OVERALL, TAB_PROFITABILITY, TAB_COST, TAB_EFFICIENCY, TAB_STABILITY,
]

_TAB_LABEL_KEYS: dict[str, str] = {
    TAB_OVERALL:       "contracts.tab.overall",
    TAB_PROFITABILITY: "contracts.tab.profitability",
    TAB_COST:          "contracts.tab.cost_structure",
    TAB_EFFICIENCY:    "contracts.tab.efficiency",
    TAB_STABILITY:     "contracts.tab.stability",
}

_GRID_TEMPLATE_BY_TAB: dict[str, str] = {
    TAB_OVERALL:       "grid-template-columns: 1.8fr 1fr 1fr 1fr 1fr 1.2fr 24px",
    TAB_PROFITABILITY: "grid-template-columns: 2fr 1.3fr 1.3fr 1.5fr 1fr 24px",
    TAB_COST:          "grid-template-columns: 2fr 1.4fr 1.4fr 1fr 1.1fr 24px",
    TAB_EFFICIENCY:    "grid-template-columns: 2fr 1.2fr 1.2fr 1.2fr 1.1fr 24px",
    TAB_STABILITY:     "grid-template-columns: 2fr 1fr 1.2fr 1.2fr 1.1fr 24px",
}

_SORT_COLS_BY_TAB: dict[str, list[str]] = {
    TAB_OVERALL:       ["contract", "score_prof", "score_cost", "score_eff",
                        "score_stab", "score_overall"],
    TAB_PROFITABILITY: ["contract", "unrent_mom", "unrent_6m", "top_cost_cat",
                        "trend_mom"],
    TAB_COST:          ["contract", "top_cost_cat_now", "top_cost_increase",
                        "top_cost_increase_pct", "total_cost_pct"],
    TAB_EFFICIENCY:    ["contract", "hours_diff", "ratio_mom", "ratio_6m",
                        "hour_variance"],
    TAB_STABILITY:     ["contract", "duration", "cm_variance", "long_short",
                        "revenue_variance"],
}

# Default direction encodes "worst first" semantics per column.
_DEFAULT_SORT_DIR_BY_TAB: dict[str, dict[str, str]] = {
    TAB_OVERALL: {
        "contract": "asc",
        "score_prof": "asc", "score_cost": "asc", "score_eff": "asc",
        "score_stab": "asc", "score_overall": "asc",
    },
    TAB_PROFITABILITY: {
        "contract": "asc",
        "unrent_mom": "desc", "unrent_6m": "desc",
        "top_cost_cat": "asc", "trend_mom": "asc",
    },
    TAB_COST: {
        "contract": "asc",
        "top_cost_cat_now": "desc",
        "top_cost_increase": "asc",
        "top_cost_increase_pct": "desc",
        "total_cost_pct": "desc",
    },
    TAB_EFFICIENCY: {
        "contract": "asc",
        "hours_diff": "desc", "ratio_mom": "asc", "ratio_6m": "asc",
        "hour_variance": "desc",
    },
    TAB_STABILITY: {
        "contract": "asc",
        "duration": "asc", "cm_variance": "desc", "long_short": "asc",
        "revenue_variance": "desc",
    },
}

_HEADER_KEYS_BY_TAB: dict[str, list[tuple[str, str]]] = {
    TAB_OVERALL: [
        ("contract",      "portfolio.col_contract"),
        ("score_prof",    "contracts.col.score_profitability"),
        ("score_cost",    "contracts.col.score_cost"),
        ("score_eff",     "contracts.col.score_efficiency"),
        ("score_stab",    "contracts.col.score_stability"),
        ("score_overall", "contracts.col.score_overall"),
    ],
    TAB_PROFITABILITY: [
        ("contract",     "portfolio.col_contract"),
        ("unrent_mom",   "contracts.col.unrent_mom"),
        ("unrent_6m",    "contracts.col.unrent_6m"),
        ("top_cost_cat", "contracts.col.top_cost_increase_cat"),
        ("trend_mom",    "contracts.col.trend_mom"),
    ],
    TAB_COST: [
        ("contract",              "portfolio.col_contract"),
        ("top_cost_cat_now",      "contracts.col.top_cost_cat"),
        ("top_cost_increase",     "contracts.col.cost_highest_increase"),
        ("top_cost_increase_pct", "contracts.col.cost_highest_increase_pct"),
        ("total_cost_pct",        "contracts.col.total_cost_increase_pct"),
    ],
    TAB_EFFICIENCY: [
        ("contract",       "portfolio.col_contract"),
        ("hours_diff",     "contracts.col.hours_plan_minus_prod"),
        ("ratio_mom",      "contracts.col.ratio_mom"),
        ("ratio_6m",       "contracts.col.ratio_6m"),
        ("hour_variance",  "contracts.col.hour_variance"),
    ],
    TAB_STABILITY: [
        ("contract",          "portfolio.col_contract"),
        ("duration",          "contracts.col.duration"),
        ("cm_variance",       "contracts.col.cm_variance"),
        ("long_short",        "contracts.col.long_short"),
        ("revenue_variance",  "contracts.col.revenue_variance"),
    ],
}


def _nan_to_none(v):
    try:
        if v is None or pd.isna(v):
            return None
    except (TypeError, ValueError):
        return v
    return v


def _sort_missing(m: ContractMetrics, tab: str, col: str) -> bool:
    """True if this row has no meaningful value for `col` — always sort last."""
    if col == "contract":
        return False
    if tab == TAB_OVERALL:
        return False  # scores always have a numeric default
    if tab == TAB_PROFITABILITY:
        if col == "unrent_mom":   return m.unrent_mom_delta_eur is None
        if col == "unrent_6m":    return m.unrent_6m_delta_eur is None
        if col == "top_cost_cat": return m.top_cost_increase_cat_mom is None
        if col == "trend_mom":    return m.cm_mom_pct is None
    if tab == TAB_COST:
        if col == "top_cost_cat_now":      return m.top_cost_category_now is None
        if col == "top_cost_increase":     return m.top_cost_increase_cat is None
        if col == "top_cost_increase_pct": return m.top_cost_increase_pct is None
        if col == "total_cost_pct":        return m.total_cost_increase_pct is None
    if tab == TAB_EFFICIENCY:
        if col == "hours_diff":    return m.hours_planned_minus_productive is None
        if col == "ratio_mom":     return m.ratio_mom_delta_pp is None
        if col == "ratio_6m":      return m.ratio_6m_delta_pp is None
        if col == "hour_variance": return m.hour_variance is None
    if tab == TAB_STABILITY:
        if col == "duration":         return m.contract_duration_months is None
        if col == "cm_variance":      return m.cm_variance is None
        if col == "long_short":       return False
        if col == "revenue_variance": return m.revenue_variance is None
    return False


def _sort_value(m: ContractMetrics, tab: str, col: str):
    if col == "contract":
        return (m.base.cost_center_name or m.base.cost_center_id or "").lower()
    if tab == TAB_OVERALL:
        if col == "score_prof":    return float(m.profitability_score)
        if col == "score_cost":    return float(m.cost_structure_score)
        if col == "score_eff":     return float(m.efficiency_score)
        if col == "score_stab":    return float(m.stability_score)
        if col == "score_overall": return float(m.overall_score)
    if tab == TAB_PROFITABILITY:
        if col == "unrent_mom":   return float(m.unrent_mom_delta_eur or 0.0)
        if col == "unrent_6m":    return float(m.unrent_6m_delta_eur or 0.0)
        if col == "top_cost_cat": return (m.top_cost_increase_cat_mom or "").lower()
        if col == "trend_mom":    return float(m.cm_mom_pct) if m.cm_mom_pct is not None else 0.0
    if tab == TAB_COST:
        if col == "top_cost_cat_now":      return float(m.top_cost_category_now_eur)
        if col == "top_cost_increase":     return (m.top_cost_increase_cat or "").lower()
        if col == "top_cost_increase_pct": return float(m.top_cost_increase_pct or 0.0)
        if col == "total_cost_pct":        return float(m.total_cost_increase_pct or 0.0)
    if tab == TAB_EFFICIENCY:
        if col == "hours_diff":    return float(m.hours_planned_minus_productive or 0.0)
        if col == "ratio_mom":     return float(m.ratio_mom_delta_pp or 0.0)
        if col == "ratio_6m":      return float(m.ratio_6m_delta_pp or 0.0)
        if col == "hour_variance": return abs(float(m.hour_variance or 0.0))
    if tab == TAB_STABILITY:
        if col == "duration":         return int(m.contract_duration_months or 0)
        if col == "cm_variance":      return float(m.cm_variance or 0.0)
        if col == "long_short":       return 0 if not m.is_long_term else 1  # short first
        if col == "revenue_variance": return float(m.revenue_variance or 0.0)
    return 0


_HOVER_TOOLTIP_CSS = """
<style>
.wisag-portfolio-row-wrap { position: relative; }
.wisag-portfolio-row-tooltip {
  visibility: hidden;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 120ms ease, visibility 0s linear 120ms, transform 120ms ease;
  position: absolute;
  right: 24px;
  bottom: calc(100% + 6px);
  z-index: 50;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 14px 36px rgba(17, 24, 39, 0.14);
  padding: 10px 12px 8px 12px;
  width: 360px;
  pointer-events: none;
}
.wisag-portfolio-row-wrap:hover .wisag-portfolio-row-tooltip {
  visibility: visible;
  opacity: 1;
  transform: translateY(0);
  transition: opacity 120ms ease, visibility 0s, transform 120ms ease;
}
.wisag-portfolio-row-tooltip-title {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 2px 0;
  font-weight: 600;
  letter-spacing: .02em;
}
.wisag-portfolio-row-tooltip-sub {
  font-size: 11px;
  color: #9ca3af;
  margin: 0 0 6px 0;
}
.wisag-portfolio-row-tooltip-empty {
  font-size: 12px;
  color: #9ca3af;
  padding: 12px 4px;
  text-align: center;
}
.wisag-portfolio-sort-link {
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .04em;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.wisag-portfolio-sort-link:hover { color: #111827; }
.wisag-portfolio-sort-link.is-active { color: #111827; }
.wisag-portfolio-sort-arrow {
  font-size: 11px;
  opacity: 0.7;
}
</style>
"""


def _row_cell(value: str, sub: str = "") -> str:
    """One cell inside the 4-column contract row — title + optional muted sub."""
    sub_html = (f"<p class='wisag-driver-sub'>{escape(sub)}</p>" if sub else "")
    return (f"<div><p class='wisag-driver-title'>{escape(value)}</p>{sub_html}</div>")


def _signed_cell(label: str, value: float | None, *,
                 bad_when: str = "positive") -> str:
    """Row cell whose title is colored by the badness of `value`.

    `bad_when`:
      - "positive": positive values are bad (red), negative good (green).
      - "negative": negative values are bad (red), positive good (green).
      - "nonzero":  any non-zero value is bad (red) — used for hour variance.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return _row_cell(label)
    v = float(value)
    if bad_when == "negative":
        cls = ("wisag-driver-title--neg" if v < 0
               else "wisag-driver-title--pos" if v > 0
               else "")
    elif bad_when == "nonzero":
        cls = "wisag-driver-title--neg" if v != 0 else ""
    else:  # "positive"
        cls = ("wisag-driver-title--neg" if v > 0
               else "wisag-driver-title--pos" if v < 0
               else "")
    return (
        f"<div><p class='wisag-driver-title {cls}'>{escape(label)}</p></div>"
    )


def _get_active_tab() -> str:
    tab = st.session_state.get("portfolio_tab", TAB_OVERALL)
    return tab if tab in _TAB_SLUGS else TAB_OVERALL


def _default_sort_for_tab(tab: str) -> tuple[str, str]:
    """Return the (column, direction) used as the landing sort for a tab."""
    defaults = {
        TAB_OVERALL:       ("score_overall",   "asc"),
        TAB_PROFITABILITY: ("unrent_mom",      "desc"),
        TAB_COST:          ("total_cost_pct",  "desc"),
        TAB_EFFICIENCY:    ("hour_variance",   "desc"),
        TAB_STABILITY:     ("duration",        "asc"),
    }
    return defaults.get(tab, ("contract", "asc"))


def _sort_state_keys(tab: str) -> tuple[str, str]:
    return f"portfolio_sort_col_{tab}", f"portfolio_sort_dir_{tab}"


def _consume_tab_query_param() -> None:
    """Promote `?tab=<slug>` into `st.session_state`, then strip it from the URL."""
    qp = st.query_params
    raw = qp.get("tab")
    if not raw:
        return
    slug = str(raw)
    if slug in _TAB_SLUGS:
        st.session_state["portfolio_tab"] = slug
    del qp["tab"]


def _consume_sort_query_param() -> None:
    """Promote `?sort=<col>` into sort state for the active tab, toggling on re-click."""
    qp = st.query_params
    raw = qp.get("sort")
    if not raw:
        return
    col = str(raw)
    tab = _get_active_tab()
    if col not in _SORT_COLS_BY_TAB[tab]:
        del qp["sort"]
        return
    col_key, dir_key = _sort_state_keys(tab)
    current_col = st.session_state.get(col_key)
    if col == current_col:
        current_dir = st.session_state.get(dir_key, "desc")
        st.session_state[dir_key] = "asc" if current_dir == "desc" else "desc"
    else:
        st.session_state[col_key] = col
        st.session_state[dir_key] = _DEFAULT_SORT_DIR_BY_TAB[tab].get(col, "desc")
    del qp["sort"]


def _apply_sort(
    metrics: list[ContractMetrics], tab: str,
) -> tuple[list[ContractMetrics], str, str]:
    col_key, dir_key = _sort_state_keys(tab)
    default_col, default_dir = _default_sort_for_tab(tab)
    col = st.session_state.get(col_key, default_col)
    direction = st.session_state.get(dir_key, default_dir)
    missing = [m for m in metrics if _sort_missing(m, tab, col)]
    present = [m for m in metrics if not _sort_missing(m, tab, col)]
    present.sort(key=lambda m: _sort_value(m, tab, col),
                 reverse=(direction == "desc"))
    return present + missing, col, direction


def _render_tab_bar(active_tab: str) -> None:
    """Render the 5-tab bar as Streamlit buttons.

    Clicking a tab writes to `st.session_state["portfolio_tab"]`. Because the
    enclosing body is wrapped in `@st.fragment`, the mutation only reruns the
    fragment — no full-page refresh.
    """
    cols = st.columns(len(_TAB_SLUGS), gap="small")
    for col, slug in zip(cols, _TAB_SLUGS):
        with col:
            btn_type = "primary" if slug == active_tab else "secondary"
            if st.button(
                t(_TAB_LABEL_KEYS[slug]),
                key=f"portfolio_tab_btn_{slug}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state["portfolio_tab"] = slug


def _render_header_row(tab: str, active_col: str, active_dir: str) -> None:
    """Render sortable column headers as Streamlit buttons.

    Clicking mirrors `_consume_sort_query_param`'s logic — re-clicking the
    active column toggles direction; a different column jumps to its default
    direction. Fragment rerun handles the redraw; no `st.rerun()` needed.
    """
    headers = _HEADER_KEYS_BY_TAB[tab]
    cols = st.columns(len(headers), gap="small")
    col_key, dir_key = _sort_state_keys(tab)
    for ui_col, (col, label_key) in zip(cols, headers):
        with ui_col:
            arrow = ""
            if col == active_col:
                arrow = " ↓" if active_dir == "desc" else " ↑"
            btn_type = "primary" if col == active_col else "secondary"
            if st.button(
                f"{t(label_key)}{arrow}",
                key=f"portfolio_sort_btn_{tab}_{col}",
                type=btn_type,
                use_container_width=True,
            ):
                if col == st.session_state.get(col_key):
                    current_dir = st.session_state.get(dir_key, "desc")
                    st.session_state[dir_key] = (
                        "asc" if current_dir == "desc" else "desc"
                    )
                else:
                    st.session_state[col_key] = col
                    st.session_state[dir_key] = (
                        _DEFAULT_SORT_DIR_BY_TAB[tab].get(col, "desc")
                    )


# ---------------------------------------------------------------------------
# Formatting + small rendering helpers
# ---------------------------------------------------------------------------

def _fmt_eur_signed(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v):,.0f} €".replace(",", ".")


def _fmt_pct_signed(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v * 100:+.1f} %".replace(".", ",")


def _fmt_pp_signed(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.1f} pp".replace(".", ",")


def _fmt_hours(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v):,.0f} h".replace(",", ".")


def _score_band(score: float) -> str:
    if score >= 70:
        return "good"
    if score >= 40:
        return "warn"
    return "bad"


def _score_pill(score: float | None, *, overall: bool = False) -> str:
    if score is None or pd.isna(score):
        return "<span class='wisag-score-pill wisag-score-pill--warn'>—</span>"
    band = _score_band(float(score))
    extra = " wisag-score-pill--overall" if overall else ""
    return (
        f"<span class='wisag-score-pill wisag-score-pill--{band}{extra}'>"
        f"{int(round(float(score)))}</span>"
    )


def _trend_arrow_html(direction: str, delta_eur: float | None) -> str:
    label = t(f"contracts.trend_{direction}")
    if direction == "up":
        arrow = "↑"
        cls = "wisag-trend-arrow--up"
    elif direction == "down":
        arrow = "↓"
        cls = "wisag-trend-arrow--down"
    else:
        arrow = "→"
        cls = "wisag-trend-arrow--flat"
    delta_txt = f" {_fmt_eur_signed(delta_eur)}" if delta_eur not in (None, 0) else ""
    return (
        f"<span class='wisag-trend-arrow {cls}'>"
        f"{arrow} {escape(label)}{escape(delta_txt)}</span>"
    )


def _cost_cat_label(key: str | None) -> str:
    if not key:
        return t("contracts.no_data")
    label = t(f"cost_cat.{key}")
    return label if label != f"cost_cat.{key}" else key


def _contract_identity_cell(r: ContractRanking) -> str:
    """The always-present first cell: contract name + id/customer/region subtitle."""
    bits = [str(r.cost_center_id)]
    if r.customer_name:
        bits.append(r.customer_name)
    if r.region:
        bits.append(r.region)
    return _row_cell(r.cost_center_name or str(r.cost_center_id), " · ".join(bits))


def _render_row_overall(m: ContractMetrics) -> str:
    grid = _GRID_TEMPLATE_BY_TAB[TAB_OVERALL]
    col_contract = _contract_identity_cell(m.base)
    col_prof = f"<div>{_score_pill(m.profitability_score)}</div>"
    col_cost = f"<div>{_score_pill(m.cost_structure_score)}</div>"
    col_eff = f"<div>{_score_pill(m.efficiency_score)}</div>"
    col_stab = f"<div>{_score_pill(m.stability_score)}</div>"
    col_overall = f"<div>{_score_pill(m.overall_score, overall=True)}</div>"
    chev = "<span class='wisag-driver-chev'>›</span>"
    inner = (
        f"<div class='wisag-driver-row' style='{grid};'>"
        f"{col_contract}{col_prof}{col_cost}{col_eff}{col_stab}{col_overall}{chev}"
        f"</div>"
    )
    return _wrap_row_link(inner, m.base)


def _render_row_profitability(m: ContractMetrics) -> str:
    grid = _GRID_TEMPLATE_BY_TAB[TAB_PROFITABILITY]
    col_contract = _contract_identity_cell(m.base)
    # Unrentability increases are bad (red); decreases good (green).
    col_mom = _signed_cell(
        _fmt_eur_signed(m.unrent_mom_delta_eur)
        if m.unrent_mom_delta_eur is not None else t("contracts.no_data"),
        m.unrent_mom_delta_eur,
        bad_when="positive",
    )
    col_6m = _signed_cell(
        _fmt_eur_signed(m.unrent_6m_delta_eur)
        if m.unrent_6m_delta_eur is not None else t("contracts.no_data"),
        m.unrent_6m_delta_eur,
        bad_when="positive",
    )
    col_cat = _row_cell(_cost_cat_label(m.top_cost_increase_cat_mom))
    # Trend vs last month = MoM % change of actual contribution margin.
    # Negative % (margin falling) is bad (red); positive good (green).
    col_trend = _signed_cell(
        _fmt_pct_signed(m.cm_mom_pct)
        if m.cm_mom_pct is not None else t("contracts.no_data"),
        m.cm_mom_pct,
        bad_when="negative",
    )
    chev = "<span class='wisag-driver-chev'>›</span>"
    inner = (
        f"<div class='wisag-driver-row' style='{grid};'>"
        f"{col_contract}{col_mom}{col_6m}{col_cat}{col_trend}{chev}"
        f"</div>"
    )
    return _wrap_row_link(inner, m.base)


def _render_row_cost(m: ContractMetrics) -> str:
    grid = _GRID_TEMPLATE_BY_TAB[TAB_COST]
    col_contract = _contract_identity_cell(m.base)
    col_top_now = _row_cell(
        _cost_cat_label(m.top_cost_category_now),
        _fmt_eur_signed(m.top_cost_category_now_eur).lstrip("+"),
    )
    col_top_inc = _row_cell(
        _cost_cat_label(m.top_cost_increase_cat),
        _fmt_pct_signed(m.top_cost_increase_pct)
        if m.top_cost_increase_pct is not None else t("contracts.no_data"),
    )
    # Cost increases are bad (red); decreases good (green).
    col_inc_pct = _signed_cell(
        _fmt_pct_signed(m.top_cost_increase_pct),
        m.top_cost_increase_pct, bad_when="positive",
    )
    col_total_pct = _signed_cell(
        _fmt_pct_signed(m.total_cost_increase_pct),
        m.total_cost_increase_pct, bad_when="positive",
    )
    chev = "<span class='wisag-driver-chev'>›</span>"
    inner = (
        f"<div class='wisag-driver-row' style='{grid};'>"
        f"{col_contract}{col_top_now}{col_top_inc}{col_inc_pct}{col_total_pct}{chev}"
        f"</div>"
    )
    return _wrap_row_link(inner, m.base)


def _render_row_efficiency(m: ContractMetrics) -> str:
    grid = _GRID_TEMPLATE_BY_TAB[TAB_EFFICIENCY]
    col_contract = _contract_identity_cell(m.base)
    # Planned > productive (positive gap) means lost capacity → bad (red).
    col_diff = _signed_cell(
        _fmt_hours(m.hours_planned_minus_productive),
        m.hours_planned_minus_productive, bad_when="positive",
    )
    # Ratio going down (productive falling vs planned) is bad (red).
    col_mom = _signed_cell(
        _fmt_pp_signed(m.ratio_mom_delta_pp),
        m.ratio_mom_delta_pp, bad_when="negative",
    )
    col_6m = _signed_cell(
        _fmt_pp_signed(m.ratio_6m_delta_pp),
        m.ratio_6m_delta_pp, bad_when="negative",
    )
    # Any non-zero hour variance is undesirable.
    col_var = _signed_cell(
        _fmt_hours(m.hour_variance),
        m.hour_variance, bad_when="nonzero",
    )
    chev = "<span class='wisag-driver-chev'>›</span>"
    inner = (
        f"<div class='wisag-driver-row' style='{grid};'>"
        f"{col_contract}{col_diff}{col_mom}{col_6m}{col_var}{chev}"
        f"</div>"
    )
    return _wrap_row_link(inner, m.base)


def _render_row_stability(m: ContractMetrics) -> str:
    grid = _GRID_TEMPLATE_BY_TAB[TAB_STABILITY]
    col_contract = _contract_identity_cell(m.base)

    # Short-term duration is worse → red; long-term is green.
    dur = m.contract_duration_months
    dur_label = (t("contracts.duration_months", n=int(dur))
                 if dur is not None else t("contracts.no_data"))
    dur_cls = ("wisag-driver-title--pos" if m.is_long_term
               else "wisag-driver-title--neg")
    col_duration = (
        f"<div><p class='wisag-driver-title {dur_cls}'>"
        f"{escape(dur_label)}</p></div>"
    )

    # Variance cells: color by the overall stability_score band.
    band = _score_band(m.stability_score) if m.stability_score is not None else "warn"
    var_cls = ("wisag-driver-title--pos" if band == "good"
               else "wisag-driver-title--neg" if band == "bad" else "")
    cm_var_label = (_fmt_eur_signed(m.cm_variance).lstrip("+")
                    if m.cm_variance is not None else t("contracts.no_data"))
    rev_var_label = (_fmt_eur_signed(m.revenue_variance).lstrip("+")
                     if m.revenue_variance is not None else t("contracts.no_data"))
    col_cm_var = (f"<div><p class='wisag-driver-title {var_cls}'>"
                  f"{escape(cm_var_label)}</p></div>")
    col_rev_var = (f"<div><p class='wisag-driver-title {var_cls}'>"
                   f"{escape(rev_var_label)}</p></div>")

    term_cls = "wisag-term-badge--long" if m.is_long_term else "wisag-term-badge--short"
    term_label = t("contracts.long_term") if m.is_long_term else t("contracts.short_term")
    col_term = (
        f"<div><span class='wisag-term-badge {term_cls}'>"
        f"{escape(term_label)}</span></div>"
    )
    chev = "<span class='wisag-driver-chev'>›</span>"
    inner = (
        f"<div class='wisag-driver-row' style='{grid};'>"
        f"{col_contract}{col_duration}{col_cm_var}{col_term}{col_rev_var}{chev}"
        f"</div>"
    )
    return _wrap_row_link(inner, m.base)


_ROW_RENDERERS = {
    TAB_OVERALL:       _render_row_overall,
    TAB_PROFITABILITY: _render_row_profitability,
    TAB_COST:          _render_row_cost,
    TAB_EFFICIENCY:    _render_row_efficiency,
    TAB_STABILITY:     _render_row_stability,
}


def _wrap_row_link(inner_html: str, r: ContractRanking) -> str:
    """Wrap a row's HTML in the existing click-to-detail link + tooltip envelope."""
    href = f"?cc_id={escape(str(r.cost_center_id))}"
    link = (f"<a class='wisag-driver-row-link' href='{href}' target='_self'>"
            f"{inner_html}</a>")
    tooltip = _build_row_tooltip(r)
    return f"<div class='wisag-portfolio-row-wrap'>{link}{tooltip}</div>"


def _build_row_tooltip(r: ContractRanking) -> str:
    """Small hover panel with a 6-month contribution-margin € trend for this contract."""
    title = escape(r.cost_center_name or str(r.cost_center_id))
    sub = escape(t("portfolio.tooltip_sub"))

    values = [float(v) for v in (r.sparkline_cm_eur or [])]
    periods = list(r.sparkline_periods or [])
    if len(values) >= 2 and len(values) == len(periods):
        # Colour matches the Profitability "Trend vs last month" column:
        # red when MoM CM change is negative, green when positive. Fall back
        # to the 6-month endpoint comparison only when MoM is unknown.
        if r.cm_mom_eur is not None:
            declining = r.cm_mom_eur < 0
        else:
            declining = values[-1] < values[0]
        trend = fov.linear_trend(values)
        chart_svg = area_chart(
            values, periods, declining=declining,
            y_as_pct=False, value_fmt="eur",
            trendline=trend,
        )
        body = f"<div style='width:100%;'>{chart_svg}</div>"
    else:
        body = (f"<div class='wisag-portfolio-row-tooltip-empty'>"
                f"{escape(t('overview.no_baseline'))}</div>")

    return (
        f"<div class='wisag-portfolio-row-tooltip'>"
        f"  <p class='wisag-portfolio-row-tooltip-title'>{title}</p>"
        f"  <p class='wisag-portfolio-row-tooltip-sub'>{sub}</p>"
        f"  {body}"
        f"</div>"
    )


def _render_table(metrics: list[ContractMetrics]) -> None:
    active_tab = _get_active_tab()

    _render_tab_bar(active_tab)

    st.markdown(
        "<div id='wisag-contracts-anchor'></div>",
        unsafe_allow_html=True,
    )

    if not metrics:
        st.info(t("portfolio.empty_all_profitable"))
        return

    ordered, active_col, active_dir = _apply_sort(metrics, active_tab)

    _render_header_row(active_tab, active_col, active_dir)

    render_row = _ROW_RENDERERS[active_tab]
    rows_html = ""
    for m in ordered:
        rows_html += render_row(m)

    section_card(
        title=t("portfolio.header"),
        subtitle="",
        rows_html=rows_html,
        hint=t("portfolio.open_contract_hint"),
    )


def render(df: pd.DataFrame) -> None:
    """Render the Contracts multi-tab landing view."""
    if "portfolio_tab" not in st.session_state:
        st.session_state["portfolio_tab"] = TAB_OVERALL
    # Deep-link support only: first-paint honors `?tab=` / `?sort=` if the
    # user arrived via a shared URL. Once consumed, the params are stripped,
    # and all in-page tab/sort interactions go through session state inside
    # the body fragment — no query-param round-trip, no full-page refresh.
    _consume_tab_query_param()
    _consume_sort_query_param()
    st.markdown(_HOVER_TOOLTIP_CSS, unsafe_allow_html=True)
    _render_portfolio_overview_block(df)
    _render_portfolio_body_fragment(df)


@st.fragment
def _render_portfolio_body_fragment(df: pd.DataFrame) -> None:
    state = _render_filters(df)

    sliced = _slice_by_months(df, state.month_range)
    if sliced.empty:
        st.info(t("portfolio.empty_no_contracts"))
        return

    all_rankings = compute_rankings(sliced)
    filtered = filter_rankings(
        all_rankings,
        regions=state.regions,
        clients=state.clients,
        industries=state.industries,
        cost_centers=state.cost_centers,
        reasons=state.reasons,
        search=state.search,
        only_unprofitable=not state.show_profitable,
    )

    metrics = compute_metrics(filtered, sliced)

    _render_kpi_bar(filtered)
    _render_table(metrics)
