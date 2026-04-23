"""Page 5 — Plan vs. Ist: monatliche Abweichungstabelle und Balkendiagramm."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.components import kpi_tile, page_header, setup_page, sidebar_logo
from src.i18n import t
from src.theme import NEG, NEG_DARK, NEG_LIGHT, POS, POS_DARK, POS_LIGHT, WARN_LIGHT, WISAG_NAVY

setup_page("nav.plan_vs_actual", icon="📐")
sidebar_logo()
page_header("pva.title", "pva.subtitle", icon="📐")

df = st.session_state.get("filtered")
if df is None or df.empty:
    st.warning(t("data.no_data_page"))
    st.stop()

if "cm_planned" not in df.columns or "cm_db" not in df.columns:
    st.error(t("pva.missing_cols"))
    st.stop()


def _format_eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", ".")


# Aggregate to monthly
monthly = (df.groupby("period")[["cm_db", "cm_planned", "revenue_total"]]
             .sum()
             .reset_index())
monthly["cm_delta"] = monthly["cm_db"] - monthly["cm_planned"]
monthly["cm_delta_pct"] = monthly["cm_delta"] / monthly["cm_planned"].replace(0, pd.NA)
monthly = monthly.sort_values("period")

# KPI tiles
total_actual = float(monthly["cm_db"].sum())
total_plan = float(monthly["cm_planned"].sum())
total_gap = total_actual - total_plan
worst_row = monthly.loc[monthly["cm_delta"].idxmin()] if not monthly.empty else None

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_tile("kpi.total_actual", _format_eur(total_actual), help_key="cm_db")
with c2:
    kpi_tile("kpi.total_planned", _format_eur(total_plan), help_key="cm_planned")
with c3:
    kpi_tile("kpi.total_gap", _format_eur(total_gap),
             delta=_format_eur(total_gap),
             delta_negative_is_bad=True, help_key="plan_gap")
with c4:
    if worst_row is not None:
        st.metric(
            label=f"{t('kpi.worst_month')} ({worst_row['period'].strftime('%Y-%m')})",
            value=f"{worst_row['cm_delta']:+,.0f} €".replace(",", "."),
            delta_color="inverse",
        )

st.divider()

# ---------- Bar chart ----------
gap_colors = [POS if v >= 0 else NEG for v in monthly["cm_delta"]]
fig = go.Figure(go.Bar(
    x=monthly["period"], y=monthly["cm_delta"],
    marker_color=gap_colors,
    text=[f"{v:+,.0f}" for v in monthly["cm_delta"]],
    textposition="outside",
    name="Abweichung (€)",
))
fig.update_layout(
    title=t("pva.bar_title"),
    height=420, margin=dict(l=40, r=20, t=60, b=40),
    yaxis_title="€",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter, system-ui, sans-serif", color=WISAG_NAVY),
)
fig.update_xaxes(tickformat="%Y-%m")
st.plotly_chart(fig, use_container_width=True)
st.caption(t("pva.chart_caption"))

st.divider()

# ---------- Variance table ----------
st.subheader(t("pva.table_title"))

display = monthly.copy()
display["period"] = display["period"].dt.strftime("%Y-%m")
display = display.rename(columns={
    "period": t("pva.col.month"),
    "cm_db": t("pva.col.actual"),
    "cm_planned": t("pva.col.planned"),
    "cm_delta": t("pva.col.gap_eur"),
    "cm_delta_pct": t("pva.col.gap_pct"),
    "revenue_total": t("pva.col.revenue"),
})


def _style_gap(v):
    if pd.isna(v):
        return ""
    if v < -50_000:
        return f"background-color: {NEG_LIGHT}; color: {NEG_DARK}; font-weight: bold"
    if v < 0:
        return f"background-color: {WARN_LIGHT}"
    if v > 50_000:
        return f"background-color: {POS_LIGHT}; color: {POS_DARK}; font-weight: bold"
    return ""


cols_order = [
    t("pva.col.month"), t("pva.col.revenue"), t("pva.col.planned"),
    t("pva.col.actual"), t("pva.col.gap_eur"), t("pva.col.gap_pct"),
]
styled = (display[cols_order]
          .style
          .format({
              t("pva.col.revenue"): "{:,.0f} €",
              t("pva.col.planned"): "{:,.0f} €",
              t("pva.col.actual"): "{:,.0f} €",
              t("pva.col.gap_eur"): "{:+,.0f} €",
              t("pva.col.gap_pct"): "{:+.1%}",
          }, na_rep="—")
          .map(_style_gap, subset=[t("pva.col.gap_eur")]))
st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

st.caption(t("pva.table_caption"))
