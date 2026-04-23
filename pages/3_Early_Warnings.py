"""Page 3 — Frühwarnungen: vorausschauende Risikoliste mit KI-Maßnahmenplan."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src import benchmarks, drivers, early_warning
from src.components import (
    kpi_tile,
    page_header,
    setup_page,
    sidebar_logo,
    warning_card,
)
from src.i18n import t
from src.llm_copilot import ExplainContext, explain_drivers

setup_page("nav.warnings", icon="⚠️")
sidebar_logo()
page_header("warnings.title", "warnings.subtitle", icon="⚠️")

df = st.session_state.get("filtered")
df_all = st.session_state.get("df")
if df is None or df.empty:
    st.warning(t("data.no_data_page"))
    st.stop()


def _format_eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", ".")


# ---------- Rules explainer ----------
with st.expander(f"ℹ️ {t('warnings.rules_title')}", expanded=False):
    st.markdown(t("warnings.rules_body"))


warnings = early_warning.detect(df)
if warnings.empty:
    st.success(t("warnings.none"))
    st.stop()

# ---------- Summary tiles ----------
sev = warnings["severity"].value_counts()
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_tile("kpi.high_severity", f"{int(sev.get('high', 0))}", help_key="severity")
with c2:
    kpi_tile("kpi.medium_severity", f"{int(sev.get('medium', 0))}", help_key="severity")
with c3:
    kpi_tile("kpi.low_severity", f"{int(sev.get('low', 0))}", help_key="severity")
with c4:
    top10_sum = warnings.nlargest(10, 'impact_eur')['impact_eur'].sum()
    kpi_tile("kpi.eur_at_stake", _format_eur(top10_sum), help_key="impact_eur")


st.divider()


# ---------- Warning cards ----------
for _, row in warnings.iterrows():
    warning_card(row)


st.divider()


# ---------- Deep-dive on a single warning ----------
st.subheader(f"🎯 {t('warnings.action_title')}")
labels = []
for r in warnings.itertuples():
    signal_en = getattr(r, "signal", "")
    signal_de = t(f"signal.{signal_en}")
    if signal_de == f"signal.{signal_en}":
        signal_de = signal_en
    sev_label = t(f"severity.{(r.severity or 'low').lower()}")
    cc_name = getattr(r, "cost_center_name", "") or ""
    labels.append(f"[{sev_label}] {signal_de} · {r.cost_center_id} ({cc_name})")

pick = st.selectbox(t("warnings.pick"), labels)
idx = labels.index(pick)
warn = warnings.iloc[idx]

cc = warn["cost_center_id"]
history = df_all[df_all["cost_center_id"] == cc].sort_values("period")
if history.empty:
    st.info(t("warnings.no_history"))
    st.stop()

current_row = history.iloc[-1]
prior_target = current_row["period"] - pd.DateOffset(months=1)
baseline_rows = history[history["period"] == prior_target]
baseline = (baseline_rows.iloc[0] if not baseline_rows.empty
            else history.iloc[-2] if len(history) >= 2 else None)

if baseline is None:
    st.info(t("warnings.not_enough_history"))
    st.stop()

drv = drivers.decompose(current_row, baseline)
observed = drivers.observed_delta(current_row, baseline)
kvs = benchmarks.kpi_vs_peers(df_all, current_row)

ctx = ExplainContext(
    cost_center=str(current_row.get("cost_center_name") or cc),
    region=str(current_row.get("region", "—")),
    service=str(current_row.get("service_type", "—")),
    period=current_row["period"].strftime("%Y-%m"),
    baseline_label=f"prior month + early-warning signal: {warn['signal']}",
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
    manager_comment=f"EARLY WARNING — {warn['signal']}: {warn['detail']}",
)

if st.button(t("warnings.ai_button"), type="primary"):
    with st.spinner(t("deepdive.ai_asking")):
        explanation = explain_drivers(ctx, api_key=os.environ.get("ANTHROPIC_API_KEY"))
    st.session_state[f"ew_explanation_{cc}"] = explanation

explanation = st.session_state.get(f"ew_explanation_{cc}")
if explanation:
    st.markdown(explanation)
