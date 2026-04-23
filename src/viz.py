"""Plotly chart helpers — waterfall, heatmap, time series, KPI bullets."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.theme import (
    WISAG_ORANGE,
    WISAG_NAVY,
    HEATMAP_SCALE,
    POS,
    NEG,
    NEU,
)

# Backwards-compatible aliases (names kept — values updated to WISAG brand).
WISAG_GREEN = WISAG_ORANGE   # deprecated name; use WISAG_ORANGE.
WISAG_DARK = WISAG_NAVY      # deprecated name; use WISAG_NAVY.


def waterfall(df_wf: pd.DataFrame, observed_delta: float,
              title: str = "Treiberzerlegung der ΔDB (€)") -> go.Figure:
    """df_wf columns: label, delta, kind."""
    measures = ["relative"] * len(df_wf)
    colors = [
        POS if (k == "revenue" and d > 0) or (k == "cost" and d > 0) else
        NEG if (k in ("revenue", "cost") and d < 0) else NEU
        for k, d in zip(df_wf["kind"], df_wf["delta"])
    ]
    fig = go.Figure(go.Waterfall(
        name="ΔDB",
        orientation="v",
        measure=measures + ["total"],
        x=list(df_wf["label"]) + ["Beobachtete ΔDB"],
        y=list(df_wf["delta"]) + [observed_delta],
        connector={"line": {"color": "#BDBDBD"}},
        decreasing={"marker": {"color": NEG}},
        increasing={"marker": {"color": POS}},
        totals={"marker": {"color": WISAG_NAVY}},
        text=[f"{v:+,.0f} €" for v in df_wf["delta"]] + [f"{observed_delta:+,.0f} €"],
        textposition="outside",
    ))
    fig.update_layout(
        title=title, showlegend=False, height=450,
        yaxis_title="€-Beitrag zur ΔDB",
        margin=dict(l=40, r=20, t=60, b=120),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", color=WISAG_NAVY),
    )
    fig.update_xaxes(tickangle=-30)
    return fig


def heatmap_cm_pct(df: pd.DataFrame,
                   value_col: str = "cm_db_pct",
                   row_dim: str = "auto",
                   top_n: int = 20) -> go.Figure:
    """CM% heatmap — adaptive row dimension.

    `row_dim`:
      * "region" → region × month
      * "cost_center" → top_n cost centers by revenue × month
      * "auto" (default) → region if multiple regions, else cost_center
    """
    if df.empty:
        return go.Figure()

    if row_dim == "auto":
        row_dim = "region" if df.get("region", pd.Series()).nunique() > 1 else "cost_center"

    if row_dim == "region" and "region" in df.columns:
        pivot = (df.groupby(["region", "period"])[value_col]
                   .mean()
                   .reset_index()
                   .pivot(index="region", columns="period", values=value_col))
        title = "Deckungsbeitrag % — Region × Monat"
    else:
        # top-N cost centers by revenue
        if "cost_center_id" not in df.columns:
            return go.Figure()
        rev_rank = (df.groupby("cost_center_id")["revenue_total"]
                      .sum().nlargest(top_n).index)
        sub = df[df["cost_center_id"].isin(rev_rank)].copy()
        sub["cc_label"] = sub["cost_center_id"].astype(str)
        if "cost_center_name" in sub.columns:
            sub["cc_label"] = (sub["cost_center_id"].astype(str) + " · "
                               + sub["cost_center_name"].fillna("").astype(str).str.slice(0, 25))
        pivot = (sub.groupby(["cc_label", "period"])[value_col]
                    .mean()
                    .reset_index()
                    .pivot(index="cc_label", columns="period", values=value_col))
        title = f"Deckungsbeitrag % — Top {top_n} Kostenstellen × Monat"

    pivot = pivot.sort_index()
    fig = px.imshow(
        pivot,
        color_continuous_scale=HEATMAP_SCALE,
        aspect="auto",
        labels=dict(color="DB %"),
        zmin=-0.1, zmax=0.25,
    )
    fig.update_layout(title=title,
                      height=max(420, 24 * len(pivot) + 120),
                      margin=dict(l=40, r=20, t=60, b=40),
                      plot_bgcolor="#FFFFFF",
                      paper_bgcolor="#FFFFFF",
                      font=dict(family="Inter, system-ui, sans-serif", color=WISAG_NAVY))
    fig.update_xaxes(tickformat="%Y-%m")
    return fig


# Keep backward-compatible alias (old name still works):
heatmap_region_month = heatmap_cm_pct


def cm_timeseries(history: pd.DataFrame, title: str = "DB im Zeitverlauf") -> go.Figure:
    fig = go.Figure()
    if history.empty:
        return fig
    if "cm_db" in history.columns:
        fig.add_trace(go.Scatter(
            x=history["period"], y=history["cm_db"],
            mode="lines+markers", name="Ist-DB (€)",
            line=dict(color=WISAG_ORANGE, width=3),
            marker=dict(size=7),
        ))
    if "cm_planned" in history.columns and history["cm_planned"].notna().any():
        fig.add_trace(go.Scatter(
            x=history["period"], y=history["cm_planned"],
            mode="lines", name="Plan-DB (€)",
            line=dict(color=WISAG_NAVY, width=2, dash="dash"),
        ))
    fig.update_layout(title=title, height=360, hovermode="x unified",
                      margin=dict(l=40, r=20, t=60, b=40),
                      yaxis_title="€", legend=dict(orientation="h", y=-0.15),
                      plot_bgcolor="#FFFFFF",
                      paper_bgcolor="#FFFFFF",
                      font=dict(family="Inter, system-ui, sans-serif", color=WISAG_NAVY))
    return fig


def kpi_vs_peer_bullet(compare_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: value vs peer median, per KPI."""
    if compare_df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=compare_df["kpi"], x=compare_df["value"],
        orientation="h", name="Diese Kostenstelle",
        marker_color=WISAG_ORANGE,
        text=[f"{v:.2f}" for v in compare_df["value"]],
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        y=compare_df["kpi"], x=compare_df["peer_median"],
        mode="markers", name="Regionaler Peer-Median",
        marker=dict(color=WISAG_NAVY, symbol="line-ns-open", size=18,
                    line=dict(width=3)),
    ))
    fig.update_layout(
        title="Kennzahlen vs. regionale Peers",
        height=40 * len(compare_df) + 120,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", color=WISAG_NAVY),
    )
    return fig
