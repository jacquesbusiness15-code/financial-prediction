"""Portfolio landing page: KPI bar, filters, searchable selectable contract table."""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Callable

import pandas as pd
import streamlit as st

from src import facility_overview as fov
from src.contract_metrics import ContractMetrics, compute_metrics
from src.i18n import t
from src.portfolio_ranking import (
    ContractRanking,
    compute_rankings,
    filter_rankings,
    totals,
)
from src.viz_svg import area_chart


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

_DASH = "—"


def _fmt_eur(v) -> str:
    if v is None or pd.isna(v):
        return _DASH
    return f"{v:,.0f} €".replace(",", ".")


def _fmt_period(p) -> str:
    if p is None or pd.isna(p):
        return _DASH
    return pd.Timestamp(p).strftime("%b %Y")


def _fmt_eur_signed(v) -> str:
    if v is None or pd.isna(v):
        return _DASH
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v):,.0f} €".replace(",", ".")


def _fmt_hours(v) -> str:
    if v is None or pd.isna(v):
        return _DASH
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v):,.0f} h".replace(",", ".")


def _fmt_pct_signed(v) -> str:
    # `safe_pct_change` already gates out noise-level ratios upstream, so the
    # caller either passes a sane number or None.
    if v is None or pd.isna(v):
        return _DASH
    return f"{v * 100:+.1f} %".replace(".", ",")


def _fmt_pp_signed(v) -> str:
    if v is None or pd.isna(v):
        return _DASH
    return f"{v:+.1f} %".replace(".", ",")


# ---------------------------------------------------------------------------
# Overview block (big title + category pills + 12-month chart)
# ---------------------------------------------------------------------------

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
    st.markdown(
        f"<h1 class='wisag-overview-title'>{escape(t('overview.section_title'))}</h1>",
        unsafe_allow_html=True,
    )
    _render_overview_fragment(df)


@st.fragment
def _render_overview_fragment(df: pd.DataFrame) -> None:
    state_key = "portfolio_overview_cat"
    allowed = {k for k, _ in _OVERVIEW_CATEGORY_KEYS}
    current = st.session_state.get(state_key, "revenue")
    if current not in allowed:
        current = "revenue"

    st.markdown("<div class='wisag-cat-bar'>", unsafe_allow_html=True)
    cols = st.columns(3, gap="small")
    for col, (key, label_key) in zip(cols, _OVERVIEW_CATEGORY_KEYS):
        with col:
            if st.button(
                t(label_key),
                key=f"portfolio_cat_{key}",
                type=("primary" if key == current else "secondary"),
                use_container_width=True,
            ):
                st.session_state[state_key] = key
                st.rerun(scope="fragment")
    st.markdown("</div>", unsafe_allow_html=True)

    required = ("period", "revenue_total", "cm_db")
    if df.empty or any(c not in df.columns for c in required):
        st.info(t("overview.no_focus"))
        return

    values, periods = fov.category_series(_aggregate_portfolio_totals(df), current, n=12)
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


# ---------------------------------------------------------------------------
# Filter state + filter bar
# ---------------------------------------------------------------------------

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


def _distinct(df: pd.DataFrame, col: str) -> list[str]:
    if col not in df.columns:
        return []
    return sorted({str(v) for v in df[col].dropna().unique()})


_FILTER_RESET_KEYS = (
    "portfolio_search",
    "portfolio_filter_region",
    "portfolio_filter_client",
    "portfolio_filter_branch",
    "portfolio_filter_reason",
    "portfolio_filter_cost_center",
    "portfolio_filter_month",
    "portfolio_show_profitable",
)


def _render_filters(df: pd.DataFrame) -> FilterState:
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
            state.month_range = _render_month_slider(df)

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
            state.reasons = st.multiselect(
                t("portfolio.filter_reason"),
                options=REASON_KEYS,
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
                for key in _FILTER_RESET_KEYS:
                    st.session_state.pop(key, None)
                st.rerun(scope="fragment")

    return state


def _render_month_slider(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp] | None:
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
            return (pd.Timestamp(picked[0]), pd.Timestamp(picked[1]))
        return None
    if len(periods) == 1:
        only = pd.Timestamp(periods[0])
        st.caption(f"{t('portfolio.filter_month')}: {only.strftime('%b %Y')}")
        return (only, only)
    return None


def _slice_by_months(df: pd.DataFrame,
                     rng: tuple[pd.Timestamp, pd.Timestamp] | None) -> pd.DataFrame:
    if rng is None or "period" not in df.columns:
        return df
    lo, hi = rng
    if lo > hi:
        lo, hi = hi, lo
    return df[(df["period"] >= lo) & (df["period"] <= hi)].copy()


# ---------------------------------------------------------------------------
# KPI bar
# ---------------------------------------------------------------------------

def _render_kpi_bar(rankings: list[ContractRanking]) -> None:
    stats = totals(rankings)
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
        st.metric(t("portfolio.kpi_total_unprofit"), _fmt_eur(stats["total_unprofit_eur"]))
        st.caption(t("portfolio.kpi_total_unprofit_sub"))
    with right:
        st.metric(t("portfolio.kpi_longest_unprofit"), longest_value)
        if longest_sub:
            st.caption(longest_sub)


# ---------------------------------------------------------------------------
# Tab + column configuration. One dict per tab, keyed by column slug.
# Each column spec: (header_key, sort_dir_default, sort_value_fn, sort_missing_fn)
# ---------------------------------------------------------------------------

TAB_OVERALL = "overall"
TAB_PROFITABILITY = "profitability"
TAB_REVENUE = "revenue_trend"
TAB_COST = "cost_structure"
TAB_EFFICIENCY = "efficiency"
TAB_STABILITY = "stability"

_TAB_SLUGS: list[str] = [
    TAB_PROFITABILITY, TAB_REVENUE, TAB_COST, TAB_EFFICIENCY, TAB_STABILITY,
]

_TAB_LABEL_KEYS: dict[str, str] = {
    TAB_OVERALL:       "contracts.tab.overall",
    TAB_PROFITABILITY: "contracts.tab.profitability",
    TAB_REVENUE:       "contracts.tab.revenue_trend",
    TAB_COST:          "contracts.tab.cost_structure",
    TAB_EFFICIENCY:    "contracts.tab.efficiency",
    TAB_STABILITY:     "contracts.tab.stability",
}

_GRID_TEMPLATE_BY_TAB: dict[str, str] = {
    TAB_OVERALL:       "grid-template-columns: 1.8fr 1fr 1fr 1fr 1fr 1.2fr 24px",
    TAB_PROFITABILITY: "grid-template-columns: 2fr 1.3fr 1.3fr 1.5fr 1fr 24px",
    TAB_REVENUE:       "grid-template-columns: 2fr 1.3fr 1.3fr 1.5fr 1fr 24px",
    TAB_COST:          "grid-template-columns: 2fr 1.4fr 1.4fr 1fr 1.1fr 24px",
    TAB_EFFICIENCY:    "grid-template-columns: 2fr 1.2fr 1.2fr 1.2fr 1.1fr 24px",
    TAB_STABILITY:     "grid-template-columns: 2fr 1fr 1.2fr 1.2fr 1.1fr 24px",
}


def _contract_sort(m: ContractMetrics) -> str:
    return (m.base.cost_center_name or m.base.cost_center_id or "").lower()


def _missing_attr(attr: str) -> Callable[[ContractMetrics], bool]:
    return lambda m: getattr(m, attr) is None


def _float_attr(attr: str, default: float = 0.0) -> Callable[[ContractMetrics], float]:
    return lambda m: float(getattr(m, attr) or default)


def _str_attr(attr: str) -> Callable[[ContractMetrics], str]:
    return lambda m: (getattr(m, attr) or "").lower()


_NEVER_MISSING = lambda m: False

# One tuple per column: (header_i18n_key, default_sort_dir, sort_value_fn, is_missing_fn)
_TAB_COLUMNS: dict[str, dict[str, tuple[str, str, Callable, Callable]]] = {
    TAB_OVERALL: {
        "contract":      ("portfolio.col_contract",             "asc",  _contract_sort, _NEVER_MISSING),
        "score_prof":    ("contracts.col.score_profitability",  "asc",  _float_attr("profitability_score"), _NEVER_MISSING),
        "score_cost":    ("contracts.col.score_cost",           "asc",  _float_attr("cost_structure_score"), _NEVER_MISSING),
        "score_eff":     ("contracts.col.score_efficiency",     "asc",  _float_attr("efficiency_score"), _NEVER_MISSING),
        "score_stab":    ("contracts.col.score_stability",      "asc",  _float_attr("stability_score"), _NEVER_MISSING),
        "score_overall": ("contracts.col.score_overall",        "asc",  _float_attr("overall_score"), _NEVER_MISSING),
    },
    TAB_PROFITABILITY: {
        "contract":     ("portfolio.col_contract",                 "asc",  _contract_sort, _NEVER_MISSING),
        "unrent_mom":   ("contracts.col.unrent_mom",               "desc", _float_attr("unrent_mom_delta_eur"), _missing_attr("unrent_mom_delta_eur")),
        "unrent_6m":    ("contracts.col.unrent_6m",                "desc", _float_attr("unrent_6m_delta_eur"),  _missing_attr("unrent_6m_delta_eur")),
        "top_cost_cat": ("contracts.col.top_cost_increase_cat",    "asc",  _str_attr("top_cost_increase_cat"), _missing_attr("top_cost_increase_cat")),
        "trend_mom":    ("contracts.col.trend_mom",                "asc",
                         lambda m: float(m.base.cm_mom_eur or 0.0),
                         lambda m: m.base.cm_mom_eur is None),
    },
    TAB_REVENUE: {
        "contract":           ("portfolio.col_contract",                "asc",  _contract_sort, _NEVER_MISSING),
        "revenue_mom":        ("contracts.col.revenue_mom",             "asc",  _float_attr("revenue_mom_delta_eur"), _missing_attr("revenue_mom_delta_eur")),
        "revenue_6m":         ("contracts.col.revenue_6m",              "asc",  _float_attr("revenue_6m_delta_eur"),  _missing_attr("revenue_6m_delta_eur")),
        "top_decline_stream": ("contracts.col.top_decline_stream",      "asc",  _float_attr("top_revenue_decline_eur"), _missing_attr("top_revenue_decline_cat")),
        "revenue_trend":      ("contracts.col.revenue_trend",           "asc",
                               lambda m: {"down": 0, "flat": 1, "up": 2, "no_data": 3}.get(m.revenue_trend_dir, 3),
                               lambda m: m.revenue_trend_dir == "no_data"),
    },
    TAB_COST: {
        "contract":              ("portfolio.col_contract",                    "asc",  _contract_sort, _NEVER_MISSING),
        "top_cost_cat_now":      ("contracts.col.top_cost_cat",                "desc", _float_attr("top_cost_category_now_eur"), _missing_attr("top_cost_category_now")),
        "top_cost_increase":     ("contracts.col.cost_highest_increase",      "asc",  _str_attr("top_cost_increase_cat"), _missing_attr("top_cost_increase_cat")),
        "top_cost_increase_pct": ("contracts.col.cost_highest_increase_pct",  "desc", _float_attr("top_cost_increase_pct"), _missing_attr("top_cost_increase_pct")),
        "total_cost_pct":        ("contracts.col.total_cost_increase_pct",    "desc", _float_attr("total_cost_increase_pct"), _missing_attr("total_cost_increase_pct")),
    },
    TAB_EFFICIENCY: {
        "contract":      ("portfolio.col_contract",              "asc",  _contract_sort, _NEVER_MISSING),
        "hours_diff":    ("contracts.col.hours_plan_minus_prod", "desc", _float_attr("hours_planned_minus_productive"), _missing_attr("hours_planned_minus_productive")),
        "ratio_mom":     ("contracts.col.ratio_mom",             "asc",  _float_attr("ratio_mom_delta_pp"), _missing_attr("ratio_mom_delta_pp")),
        "ratio_6m":      ("contracts.col.ratio_6m",              "asc",  _float_attr("ratio_6m_delta_pp"), _missing_attr("ratio_6m_delta_pp")),
        "hour_variance": ("contracts.col.hour_variance",         "desc", lambda m: abs(float(m.hour_variance or 0.0)), _missing_attr("hour_variance")),
    },
    TAB_STABILITY: {
        "contract":         ("portfolio.col_contract",          "asc",  _contract_sort, _NEVER_MISSING),
        "duration":         ("contracts.col.duration",          "asc",  lambda m: int(m.contract_duration_months or 0), _missing_attr("contract_duration_months")),
        "cm_variance":      ("contracts.col.cm_variance",       "desc", _float_attr("cm_variance"), _missing_attr("cm_variance")),
        "long_short":       ("contracts.col.long_short",        "asc",  lambda m: 0 if not m.is_long_term else 1, _NEVER_MISSING),
        "revenue_variance": ("contracts.col.revenue_variance",  "desc", _float_attr("revenue_variance"), _missing_attr("revenue_variance")),
    },
}


def _default_sort_for_tab(tab: str) -> tuple[str, str]:
    defaults = {
        TAB_OVERALL:       ("score_overall",   "asc"),
        TAB_PROFITABILITY: ("unrent_mom",      "desc"),
        TAB_REVENUE:       ("revenue_mom",     "asc"),
        TAB_COST:          ("total_cost_pct",  "desc"),
        TAB_EFFICIENCY:    ("hour_variance",   "desc"),
        TAB_STABILITY:     ("duration",        "asc"),
    }
    return defaults.get(tab, ("contract", "asc"))


# ---------------------------------------------------------------------------
# Tab + sort URL param handling
# ---------------------------------------------------------------------------

def _get_active_tab() -> str:
    tab = st.session_state.get("portfolio_tab", TAB_PROFITABILITY)
    return tab if tab in _TAB_SLUGS else TAB_PROFITABILITY


def _sort_state_keys(tab: str) -> tuple[str, str]:
    return f"portfolio_sort_col_{tab}", f"portfolio_sort_dir_{tab}"


def _toggle_sort(tab: str, col: str) -> None:
    col_key, dir_key = _sort_state_keys(tab)
    if col == st.session_state.get(col_key):
        current_dir = st.session_state.get(dir_key, "desc")
        st.session_state[dir_key] = "asc" if current_dir == "desc" else "desc"
        return
    st.session_state[col_key] = col
    st.session_state[dir_key] = _TAB_COLUMNS[tab][col][1]


def _consume_tab_query_param() -> None:
    qp = st.query_params
    raw = qp.get("tab")
    if not raw:
        return
    slug = str(raw)
    if slug in _TAB_SLUGS:
        st.session_state["portfolio_tab"] = slug
    del qp["tab"]


def _consume_sort_query_param() -> None:
    qp = st.query_params
    raw = qp.get("sort")
    if not raw:
        return
    col = str(raw)
    tab = _get_active_tab()
    if col in _TAB_COLUMNS[tab]:
        _toggle_sort(tab, col)
    del qp["sort"]


def _apply_sort(
    metrics: list[ContractMetrics], tab: str,
) -> tuple[list[ContractMetrics], str, str]:
    col_key, dir_key = _sort_state_keys(tab)
    default_col, default_dir = _default_sort_for_tab(tab)
    col = st.session_state.get(col_key, default_col)
    direction = st.session_state.get(dir_key, default_dir)
    _header, _default_dir, sort_fn, missing_fn = _TAB_COLUMNS[tab][col]
    missing = [m for m in metrics if missing_fn(m)]
    present = [m for m in metrics if not missing_fn(m)]
    present.sort(key=sort_fn, reverse=(direction == "desc"))
    return present + missing, col, direction


# ---------------------------------------------------------------------------
# Hover tooltip CSS + shared HTML helpers
# ---------------------------------------------------------------------------

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

_CHEV_HTML = "<span class='wisag-driver-chev'>›</span>"


def _row_cell(value: str, sub: str = "") -> str:
    sub_html = f"<p class='wisag-driver-sub'>{escape(sub)}</p>" if sub else ""
    return f"<div><p class='wisag-driver-title'>{escape(value)}</p>{sub_html}</div>"


def _colored_cell(label: str, cls: str) -> str:
    return f"<div><p class='wisag-driver-title {cls}'>{escape(label)}</p></div>"


def _signed_cell(label: str, value: float | None, *,
                 bad_when: str = "positive") -> str:
    """bad_when: 'positive' (>0 is red), 'negative' (<0 is red), 'nonzero' (!=0 is red)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return _row_cell(label)
    v = float(value)
    if bad_when == "negative":
        cls = ("wisag-driver-title--neg" if v < 0
               else "wisag-driver-title--pos" if v > 0 else "")
    elif bad_when == "nonzero":
        cls = "wisag-driver-title--neg" if v != 0 else ""
    else:
        cls = ("wisag-driver-title--neg" if v > 0
               else "wisag-driver-title--pos" if v < 0 else "")
    return _colored_cell(label, cls)


def _fmt_or_nodata(v, formatter: Callable[[object], str]) -> str:
    return formatter(v) if v is not None else t("contracts.no_data")


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
    return (f"<span class='wisag-score-pill wisag-score-pill--{band}{extra}'>"
            f"{int(round(float(score)))}</span>")


def _cost_cat_label(key: str | None) -> str:
    if not key:
        return t("contracts.no_data")
    label = t(f"cost_cat.{key}")
    return label if label != f"cost_cat.{key}" else key


def _revenue_stream_label(key: str | None) -> str:
    if not key:
        return t("contracts.no_data")
    label = t(f"revenue_stream.{key}")
    return label if label != f"revenue_stream.{key}" else key


_REVENUE_TREND_CLASS: dict[str, str] = {
    "down": "wisag-driver-title--neg",
    "up":   "wisag-driver-title--pos",
    "flat": "",
    "no_data": "",
}


def _contract_identity_cell(r: ContractRanking) -> str:
    bits = [str(r.cost_center_id)]
    if r.customer_name:
        bits.append(r.customer_name)
    if r.region:
        bits.append(r.region)
    return _row_cell(r.cost_center_name or str(r.cost_center_id), " · ".join(bits))


# ---------------------------------------------------------------------------
# Per-tab row renderers
# ---------------------------------------------------------------------------

def _row_overall(m: ContractMetrics) -> list[str]:
    return [
        _contract_identity_cell(m.base),
        f"<div>{_score_pill(m.profitability_score)}</div>",
        f"<div>{_score_pill(m.cost_structure_score)}</div>",
        f"<div>{_score_pill(m.efficiency_score)}</div>",
        f"<div>{_score_pill(m.stability_score)}</div>",
        f"<div>{_score_pill(m.overall_score, overall=True)}</div>",
    ]


def _row_profitability(m: ContractMetrics) -> list[str]:
    # CM MoM is rendered in EUR rather than %: CM can flip sign and a
    # percentage change across a sign flip (or near-zero baseline) is not a
    # meaningful business number. EUR compares cleanly across contracts.
    return [
        _contract_identity_cell(m.base),
        _signed_cell(_fmt_or_nodata(m.unrent_mom_delta_eur, _fmt_eur_signed),
                     m.unrent_mom_delta_eur, bad_when="positive"),
        _signed_cell(_fmt_or_nodata(m.unrent_6m_delta_eur, _fmt_eur_signed),
                     m.unrent_6m_delta_eur, bad_when="positive"),
        _row_cell(_cost_cat_label(m.top_cost_increase_cat)),
        _signed_cell(_fmt_or_nodata(m.base.cm_mom_eur, _fmt_eur_signed),
                     m.base.cm_mom_eur, bad_when="negative"),
    ]


def _row_revenue_trend(m: ContractMetrics) -> list[str]:
    if m.top_revenue_decline_cat is None:
        stream_cell = _row_cell(t("contracts.no_data"))
    else:
        stream_cell = _row_cell(
            _revenue_stream_label(m.top_revenue_decline_cat),
            _fmt_eur_signed(m.top_revenue_decline_eur),
        )

    trend_cls = _REVENUE_TREND_CLASS.get(m.revenue_trend_dir, "")
    trend_label = t(f"contracts.col.revenue_trend.{m.revenue_trend_dir}")
    if trend_label == f"contracts.col.revenue_trend.{m.revenue_trend_dir}":
        # i18n fallback if an unexpected state slips through.
        trend_label = t("contracts.no_data")
    trend_cell = _colored_cell(trend_label, trend_cls)

    return [
        _contract_identity_cell(m.base),
        _signed_cell(_fmt_or_nodata(m.revenue_mom_delta_eur, _fmt_eur_signed),
                     m.revenue_mom_delta_eur, bad_when="negative"),
        _signed_cell(_fmt_or_nodata(m.revenue_6m_delta_eur, _fmt_eur_signed),
                     m.revenue_6m_delta_eur, bad_when="negative"),
        stream_cell,
        trend_cell,
    ]


def _row_cost(m: ContractMetrics) -> list[str]:
    return [
        _contract_identity_cell(m.base),
        _row_cell(_cost_cat_label(m.top_cost_category_now),
                  _fmt_eur_signed(m.top_cost_category_now_eur).lstrip("+")),
        _row_cell(_cost_cat_label(m.top_cost_increase_cat),
                  _fmt_or_nodata(m.top_cost_increase_pct, _fmt_pct_signed)),
        _signed_cell(_fmt_pct_signed(m.top_cost_increase_pct),
                     m.top_cost_increase_pct, bad_when="positive"),
        _signed_cell(_fmt_pct_signed(m.total_cost_increase_pct),
                     m.total_cost_increase_pct, bad_when="positive"),
    ]


def _row_efficiency(m: ContractMetrics) -> list[str]:
    return [
        _contract_identity_cell(m.base),
        _signed_cell(_fmt_hours(m.hours_planned_minus_productive),
                     m.hours_planned_minus_productive, bad_when="positive"),
        _signed_cell(_fmt_pp_signed(m.ratio_mom_delta_pp),
                     m.ratio_mom_delta_pp, bad_when="negative"),
        _signed_cell(_fmt_pp_signed(m.ratio_6m_delta_pp),
                     m.ratio_6m_delta_pp, bad_when="negative"),
        _signed_cell(_fmt_hours(m.hour_variance),
                     m.hour_variance, bad_when="nonzero"),
    ]


def _row_stability(m: ContractMetrics) -> list[str]:
    dur = m.contract_duration_months
    dur_label = (t("contracts.duration_months", n=int(dur))
                 if dur is not None else t("contracts.no_data"))
    dur_cls = ("wisag-driver-title--pos" if m.is_long_term
               else "wisag-driver-title--neg")

    band = _score_band(m.stability_score) if m.stability_score is not None else "warn"
    var_cls = ("wisag-driver-title--pos" if band == "good"
               else "wisag-driver-title--neg" if band == "bad" else "")

    cm_var_label = (_fmt_eur_signed(m.cm_variance).lstrip("+")
                    if m.cm_variance is not None else t("contracts.no_data"))
    rev_var_label = (_fmt_eur_signed(m.revenue_variance).lstrip("+")
                     if m.revenue_variance is not None else t("contracts.no_data"))

    term_cls = "wisag-term-badge--long" if m.is_long_term else "wisag-term-badge--short"
    term_label = t("contracts.long_term") if m.is_long_term else t("contracts.short_term")

    return [
        _contract_identity_cell(m.base),
        _colored_cell(dur_label, dur_cls),
        _colored_cell(cm_var_label, var_cls),
        f"<div><span class='wisag-term-badge {term_cls}'>{escape(term_label)}</span></div>",
        _colored_cell(rev_var_label, var_cls),
    ]


_ROW_CELLS_BY_TAB: dict[str, Callable[[ContractMetrics], list[str]]] = {
    TAB_PROFITABILITY: _row_profitability,
    TAB_REVENUE:       _row_revenue_trend,
    TAB_COST:          _row_cost,
    TAB_EFFICIENCY:    _row_efficiency,
    TAB_STABILITY:     _row_stability,
}


def _wrap_row_link(inner_html: str, r: ContractRanking) -> str:
    href = f"?cc_id={escape(str(r.cost_center_id))}"
    link = (f"<a class='wisag-driver-row-link' href='{href}' target='_self'>"
            f"{inner_html}</a>")
    return f"<div class='wisag-portfolio-row-wrap'>{link}{_build_row_tooltip(r)}</div>"


def _build_row_tooltip(r: ContractRanking) -> str:
    """6-month CM sparkline hover panel for this contract."""
    title = escape(r.cost_center_name or str(r.cost_center_id))
    sub = escape(t("portfolio.tooltip_sub"))

    values = [float(v) for v in (r.sparkline_cm_eur or [])]
    periods = list(r.sparkline_periods or [])
    if len(values) >= 2 and len(values) == len(periods):
        # Match the Profitability "Trend vs last month" coloring: MoM-driven.
        declining = (r.cm_mom_eur < 0 if r.cm_mom_eur is not None
                     else values[-1] < values[0])
        trend = fov.linear_trend(values)
        chart_svg = area_chart(
            values, periods, declining=declining,
            y_as_pct=False, value_fmt="eur", trendline=trend,
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


def _render_row(m: ContractMetrics, tab: str) -> str:
    grid = _GRID_TEMPLATE_BY_TAB[tab]
    cells = "".join(_ROW_CELLS_BY_TAB[tab](m))
    inner = (f"<div class='wisag-driver-row' style='{grid};'>"
             f"{cells}{_CHEV_HTML}</div>")
    return _wrap_row_link(inner, m.base)


# ---------------------------------------------------------------------------
# Tab bar + header row + table
# ---------------------------------------------------------------------------

def _render_tab_bar(active_tab: str) -> None:
    cols = st.columns(len(_TAB_SLUGS), gap="small")
    for col, slug in zip(cols, _TAB_SLUGS):
        with col:
            if st.button(
                t(_TAB_LABEL_KEYS[slug]),
                key=f"portfolio_tab_btn_{slug}",
                type=("primary" if slug == active_tab else "secondary"),
                use_container_width=True,
            ):
                st.session_state["portfolio_tab"] = slug
                st.rerun(scope="fragment")


def _render_header_row(tab: str, active_col: str, active_dir: str) -> None:
    columns = _TAB_COLUMNS[tab]
    cols = st.columns(len(columns), gap="small")
    for ui_col, (col, (label_key, _d, _s, _m)) in zip(cols, columns.items()):
        with ui_col:
            arrow = (" ↓" if active_dir == "desc" else " ↑") if col == active_col else ""
            if st.button(
                f"{t(label_key)}{arrow}",
                key=f"portfolio_sort_btn_{tab}_{col}",
                type=("primary" if col == active_col else "secondary"),
                use_container_width=True,
            ):
                _toggle_sort(tab, col)
                st.rerun(scope="fragment")


def _render_table(metrics: list[ContractMetrics]) -> None:
    active_tab = _get_active_tab()

    with st.container():
        st.markdown(
            "<div class='wisag-portfolio-card-marker'></div>"
            f"<h3 class='wisag-section-title'>{escape(t('portfolio.header'))}</h3>",
            unsafe_allow_html=True,
        )

        _render_tab_bar(active_tab)

        st.markdown("<div id='wisag-contracts-anchor'></div>", unsafe_allow_html=True)

        if not metrics:
            st.info(t("portfolio.empty_all_profitable"))
            return

        ordered, active_col, active_dir = _apply_sort(metrics, active_tab)
        _render_header_row(active_tab, active_col, active_dir)

        rows_html = "".join(_render_row(m, active_tab) for m in ordered)
        st.markdown(rows_html, unsafe_allow_html=True)
        st.markdown(
            f"<div class='wisag-section-hint'>{escape(t('portfolio.open_contract_hint'))}</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def render(df: pd.DataFrame) -> None:
    """Render the Contracts multi-tab landing view."""
    if "portfolio_tab" not in st.session_state:
        st.session_state["portfolio_tab"] = TAB_PROFITABILITY
    # Deep-link only: honor ?tab / ?sort on first paint, then strip so in-page
    # interactions stay inside the fragment without a full-page refresh.
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
