"""WISAG Financial Co-Pilot — Streamlit entry point.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.components import (
    friendly_error,
    kpi_tile,
    nav_card,
    setup_page,
    sidebar_logo,
)
from src.data_loader import SchemaReport, load, summary
from src.features import enrich
from src.i18n import t

load_dotenv()

setup_page("app.title")

DEFAULT_PATH = Path("data/Dataset_anoym.xlsx")


@st.cache_data(show_spinner="Datensatz wird geladen…")
def _load_cached(path: str, sheet: int | str = 0) -> tuple[pd.DataFrame, SchemaReport]:
    df, report = load(path, sheet=sheet)
    return enrich(df), report


def _render_schema_health(report: SchemaReport) -> bool:
    """Return True if the dataset is usable, False if critical columns missing."""
    matched = len(report.matched)
    total = report.expected_total

    if not report.ok:
        st.sidebar.error(
            t("data.schema_error", m=matched, t=total,
              missing=", ".join(report.missing_critical))
        )
        return False

    if report.strategy == "position":
        st.sidebar.warning(t("data.schema_position", m=matched, t=total))
    else:
        st.sidebar.success(t("data.schema_ok", m=matched, t=total))

    optional_missing = [c for c in report.missing_expected
                        if c not in report.missing_critical]
    if optional_missing:
        with st.sidebar.expander(t("data.optional_missing", n=len(optional_missing))):
            st.caption(", ".join(optional_missing))
    if report.unmapped_input:
        with st.sidebar.expander(t("data.extra_ignored", n=len(report.unmapped_input))):
            st.caption(", ".join(report.unmapped_input))
    return True


def _collect_source_path() -> str | None:
    """Render the data-source UI inside the admin expander and resolve a path.

    Returns None if the user hasn't supplied an override AND no default dataset
    exists on disk.
    """
    st.markdown(f"**{t('sidebar.data_source')}**")
    url = st.text_input(
        "Google-Sheets-URL (öffentlich)",
        placeholder="https://docs.google.com/spreadsheets/d/e/.../pubhtml",
        help="Öffentlich veröffentlichte (/pubhtml) oder geteilte (/edit) Google-Sheets-URL. "
             "Das Tabellenblatt muss ohne Login lesbar sein.",
    ).strip()
    uploaded = st.file_uploader(
        t("sidebar.upload"), type=["xlsx", "xls", "csv"],
        help=t("sidebar.upload_help"),
    )
    if url:
        return url
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix.lower() or ".xlsx"
        tmp = Path(f".streamlit_upload{suffix}")
        tmp.write_bytes(uploaded.read())
        return str(tmp)
    if DEFAULT_PATH.exists():
        return str(DEFAULT_PATH)
    st.warning(t("data.place_or_upload"))
    return None


def _load_data(path: str) -> pd.DataFrame | None:
    """Load data + render schema health into the current container. Returns None on failure."""
    try:
        df, report = _load_cached(path)
    except Exception as e:  # noqa: BLE001
        st.error(t("data.load_failed", err=str(e)))
        return None

    if not _render_schema_health(report):
        st.stop()

    stats = summary(df)
    st.caption(
        t("data.stats",
          rows=stats['rows'],
          ccs=stats.get('cost_centers', '?'),
          pmin=stats.get('period_min'),
          pmax=stats.get('period_max'))
    )
    return df


def _sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header(t("sidebar.filters"))
    regions = sorted([r for r in df["region"].dropna().unique()]) if "region" in df else []
    services = sorted([s for s in df.get("service_type", pd.Series(dtype=object)).dropna().unique()])

    if len(regions) > 1:
        sel_regions = st.sidebar.multiselect(t("filter.region"), regions, default=regions)
    else:
        sel_regions = regions
        if regions:
            st.sidebar.caption(t("filter.region_only", r=regions[0]))
    sel_services = st.sidebar.multiselect(t("filter.service"), services, default=services)

    if "period" in df.columns and df["period"].notna().any():
        pmin, pmax = df["period"].min(), df["period"].max()
        months = pd.date_range(pmin, pmax, freq="MS")
        if len(months) > 1:
            start, end = st.sidebar.select_slider(
                t("filter.period"),
                options=list(months),
                value=(months[0], months[-1]),
                format_func=lambda d: d.strftime("%Y-%m"),
            )
        else:
            start = end = months[0] if len(months) else None
    else:
        start = end = None

    mask = pd.Series(True, index=df.index)
    if sel_regions:
        mask &= df["region"].isin(sel_regions)
    if sel_services and "service_type" in df.columns:
        mask &= df["service_type"].isin(sel_services)
    if start is not None:
        mask &= (df["period"] >= start) & (df["period"] <= end)

    return df[mask].copy()


def _sidebar_api_status() -> None:
    st.markdown(f"**{t('sidebar.api_status')}**")
    if os.environ.get("ANTHROPIC_API_KEY"):
        st.success(t("sidebar.api_ok"))
    else:
        st.info(t("sidebar.api_missing"))


def _render_hero() -> None:
    st.markdown(
        f"""
<div class='wisag-hero'>
  <h2>{t('app.welcome')}</h2>
  <p>{t('app.subtitle')}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_nav_grid() -> None:
    st.markdown(f"### {t('nav.home')}")
    row1 = st.columns(2)
    with row1[0]:
        nav_card("📈", "nav.portfolio", "nav.portfolio.desc",
                 "pages/1_Portfolio_Overview.py")
    with row1[1]:
        nav_card("🔎", "nav.deepdive", "nav.deepdive.desc",
                 "pages/2_Deep_Dive.py")
    row2 = st.columns(2)
    with row2[0]:
        nav_card("⚠️", "nav.warnings", "nav.warnings.desc",
                 "pages/3_Early_Warnings.py")
    with row2[1]:
        nav_card("💬", "nav.chat", "nav.chat.desc",
                 "pages/4_Copilot_Chat.py")
    row3 = st.columns(2)
    with row3[0]:
        nav_card("📐", "nav.plan_vs_actual", "nav.plan_vs_actual.desc",
                 "pages/5_Plan_vs_Actual.py")


def _format_eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", ".")


def main() -> None:
    sidebar_logo()

    # Admin controls (data source UI + API status) live inside a collapsed
    # expander so managers see only the filters by default. The actual data
    # load runs unconditionally once the path is resolved — so the default
    # dataset in data/ is picked up without the user having to expand anything.
    with st.sidebar.expander(f"⚙️ {t('sidebar.settings')}", expanded=False):
        st.caption(t("sidebar.settings_help"))
        path = _collect_source_path()
        st.markdown("---")
        _sidebar_api_status()
        df = _load_data(path) if path else None

    _render_hero()

    if df is None:
        friendly_error(t("data.no_data_warn"))
        _render_nav_grid()
        return

    filtered = _sidebar_filters(df)
    st.session_state["df"] = df
    st.session_state["filtered"] = filtered

    # KPI snapshot for the current filter
    rev = float(filtered.get("revenue_total", pd.Series([0])).sum())
    cm = float(filtered.get("cm_db", pd.Series([0])).sum())
    plan = float(filtered.get("cm_planned", pd.Series([0])).sum())
    plan_gap = cm - plan
    n_cc = filtered["cost_center_id"].nunique() if "cost_center_id" in filtered else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_tile("kpi.revenue", _format_eur(rev), help_key="revenue")
    with c2:
        kpi_tile("kpi.cm", _format_eur(cm), help_key="cm_db")
    with c3:
        kpi_tile("kpi.plan_gap", _format_eur(plan_gap),
                 delta=_format_eur(plan_gap),
                 delta_negative_is_bad=True,
                 help_key="plan_gap")
    with c4:
        kpi_tile("kpi.cost_centers", f"{n_cc}", help_key="cost_centers")

    st.divider()
    _render_nav_grid()


if __name__ == "__main__":
    main()
