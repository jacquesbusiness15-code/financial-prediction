"""Page 2 — Detailanalyse: Zeitreihe, Treiberwasserfall, KI-Erklärung."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src import benchmarks, drivers, viz
from src.components import page_header, setup_page, sidebar_logo
from src.i18n import t
from src.llm_copilot import ExplainContext, explain_drivers

setup_page("nav.deepdive", icon="🔎")
sidebar_logo()
page_header("deepdive.title", "deepdive.subtitle", icon="🔎")

df_all = st.session_state.get("df")
df = st.session_state.get("filtered")
if df is None or df.empty or df_all is None:
    st.warning(t("data.no_data_page"))
    st.stop()


def _format_eur(v: float) -> str:
    return f"{v:+,.0f} €".replace(",", ".")


# ---------- Cost center picker ----------
ccs = (df[["cost_center_id", "cost_center_name", "customer_name", "region"]]
       .drop_duplicates()
       .dropna(subset=["cost_center_id"])
       .sort_values("cost_center_id"))
ccs["label"] = ccs.apply(
    lambda r: f"{r['cost_center_id']} · "
              f"{r.get('cost_center_name', '') or ''} "
              f"({r.get('region', '—')})",
    axis=1,
)

demo_cc = st.session_state.get("demo_cost_center")
default_idx = 0
if demo_cc is not None:
    matches = ccs.index[ccs["cost_center_id"] == demo_cc].tolist()
    if matches:
        default_idx = ccs.index.get_loc(matches[0])

col_a, col_b = st.columns([3, 2])
with col_a:
    chosen_label = st.selectbox(t("deepdive.cost_center"),
                                ccs["label"].tolist(),
                                index=default_idx)
    chosen_cc = ccs.loc[ccs["label"] == chosen_label, "cost_center_id"].iloc[0]

# ---------- Baseline (quick-compare chips) ----------
with col_b:
    st.markdown(f"**{t('deepdive.baseline')}**")
    mode_labels = {
        t("deepdive.baseline_prior_month"): "prior month",
        t("deepdive.baseline_prior_year"): "prior year",
        t("deepdive.baseline_plan"): "plan",
    }
    mode_de = st.radio(
        label="baseline",
        options=list(mode_labels.keys()),
        horizontal=True,
        label_visibility="collapsed",
    )
    mode = mode_labels[mode_de]

history = (df_all[df_all["cost_center_id"] == chosen_cc]
           .sort_values("period").reset_index(drop=True))
if history.empty:
    st.error(t("deepdive.no_data"))
    st.stop()

periods = history["period"].dropna().tolist()
demo_period = st.session_state.get("demo_period")
default_period = periods[-1]
if demo_period is not None and demo_cc == chosen_cc:
    if demo_period in periods:
        default_period = demo_period

sel_period = st.select_slider(
    t("deepdive.period"),
    options=periods,
    value=default_period,
    format_func=lambda d: d.strftime("%Y-%m"),
)
current_row = history.loc[history["period"] == sel_period].iloc[0]

# ---------- Resolve baseline row ----------
if mode == "prior month":
    baseline_target = sel_period - pd.DateOffset(months=1)
    baseline_rows = history.loc[history["period"] == baseline_target]
    baseline = baseline_rows.iloc[0] if not baseline_rows.empty else None
    baseline_label = baseline_target.strftime("%Y-%m") if baseline is not None else "n/a"
elif mode == "prior year":
    baseline_target = sel_period - pd.DateOffset(years=1)
    baseline_rows = history.loc[history["period"] == baseline_target]
    baseline = baseline_rows.iloc[0] if not baseline_rows.empty else None
    baseline_label = baseline_target.strftime("%Y-%m") if baseline is not None else "n/a"
else:  # plan
    baseline = drivers.build_plan_baseline(current_row)
    baseline_label = "Plan"

if baseline is None:
    st.warning(t("deepdive.no_baseline", mode=mode_de))
    st.stop()

# ---------- Timeline ----------
st.plotly_chart(
    viz.cm_timeseries(history, title=t("deepdive.timeline_title", cc=chosen_cc)),
    use_container_width=True,
)

# ---------- Driver decomposition ----------
drv = drivers.decompose(current_row, baseline)
observed = drivers.observed_delta(current_row, baseline)
wf_df = drivers.to_waterfall_df(drv, observed)

# Residual warning
if abs(observed) > 1:
    # Sum of listed drivers vs observed delta → residual
    explained = float(wf_df["delta"].sum())
    residual = observed - explained
    if abs(residual) / max(abs(observed), 1) > 0.05:
        st.warning(
            t("deepdive.residual_warn", pct=abs(residual) / abs(observed)),
            icon="ℹ️",
        )

col_wf, col_kpi = st.columns([3, 2])
with col_wf:
    st.plotly_chart(
        viz.waterfall(wf_df, observed,
                      title=t("deepdive.waterfall_title",
                              baseline=baseline_label,
                              delta=_format_eur(observed))),
        use_container_width=True,
    )

with col_kpi:
    st.subheader(t("deepdive.kpi_peers"))
    kvs = benchmarks.kpi_vs_peers(df_all, current_row)
    if not kvs.empty:
        st.plotly_chart(viz.kpi_vs_peer_bullet(kvs), use_container_width=True)
    else:
        st.info(t("deepdive.kpi_peers_empty"))

# ---------- AI explanation ----------
st.divider()
st.subheader(f"🤖 {t('deepdive.ai_title')}")
st.caption(t("deepdive.ai_preview"))

ctx = ExplainContext(
    cost_center=str(current_row.get("cost_center_name") or current_row.get("cost_center_id")),
    region=str(current_row.get("region", "—")),
    service=str(current_row.get("service_type", "—")),
    period=sel_period.strftime("%Y-%m"),
    baseline_label=baseline_label,
    cm_current_eur=float(current_row.get("cm_db", 0) or 0),
    cm_baseline_eur=float(baseline.get("cm_db", 0) or 0),
    cm_delta_eur=float(observed),
    cm_current_pct=(float(current_row.get("cm_db_pct"))
                    if pd.notna(current_row.get("cm_db_pct")) else None),
    drivers=[d.as_dict() for d in drv[:10]],
    kpis_vs_peers=kvs.to_dict("records") if not kvs.empty else [],
    labor_ratio=(float(current_row.get("labor_ratio"))
                 if pd.notna(current_row.get("labor_ratio")) else None),
    hour_variance=(float(current_row.get("hour_variance"))
                   if pd.notna(current_row.get("hour_variance")) else None),
    dq_accrual_flag=bool(current_row.get("dq_accrual_flag", False)),
    manager_comment=(str(current_row.get("manager_comment"))
                     if pd.notna(current_row.get("manager_comment")) else None),
)

if st.button(t("action.generate_explanation"), type="primary"):
    with st.spinner(t("deepdive.ai_asking")):
        explanation = explain_drivers(ctx, api_key=os.environ.get("ANTHROPIC_API_KEY"))
    st.session_state[f"explanation_{chosen_cc}_{sel_period}"] = explanation

explanation = st.session_state.get(f"explanation_{chosen_cc}_{sel_period}")
if explanation:
    st.markdown(explanation)
    st.download_button(
        f"📋 {t('deepdive.download')}",
        data=explanation,
        file_name=f"db_erklaerung_{chosen_cc}_{sel_period.strftime('%Y%m')}.md",
    )
else:
    st.caption(t("deepdive.ai_hint"))
