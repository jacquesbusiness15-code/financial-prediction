"""Page 4 — Co-Pilot Chat: freie Q&A auf dem gefilterten Datensatz."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.components import page_header, setup_page, sidebar_logo
from src.i18n import t
from src.llm_copilot import chat

setup_page("nav.chat", icon="💬")
sidebar_logo()
page_header("chat.title", "chat.subtitle", icon="💬")

df = st.session_state.get("filtered")
if df is None or df.empty:
    st.warning(t("data.no_data_page"))
    st.stop()


def _build_context(df: pd.DataFrame) -> dict:
    """Kompakte KPI-Übersicht als Kontext für das LLM (cache-freundlich)."""
    latest_period = df["period"].max()
    latest = df[df["period"] == latest_period]
    by_region = (df.groupby("region")[["revenue_total", "cm_db"]]
                   .sum().reset_index())
    by_region["cm_db_pct"] = by_region["cm_db"] / by_region["revenue_total"]

    top_gap = (df.sort_values("cm_vs_plan_delta")
                 .head(10)[["period", "region", "cost_center_id",
                            "cost_center_name", "cm_db", "cm_planned",
                            "cm_vs_plan_delta"]]
                 if "cm_vs_plan_delta" in df.columns else pd.DataFrame())

    return {
        "period_range": [str(df["period"].min()), str(latest_period)],
        "totals": {
            "revenue_total": float(df.get("revenue_total", pd.Series([0])).sum()),
            "cm_db_total": float(df.get("cm_db", pd.Series([0])).sum()),
            "cm_planned_total": float(df.get("cm_planned", pd.Series([0])).sum()),
        },
        "regions_summary": by_region.to_dict("records"),
        "latest_month_rows": int(len(latest)),
        "top_plan_gap_cost_centers": top_gap.astype(str).to_dict("records"),
    }


ctx = _build_context(df)

with st.expander(f"💡 {t('chat.try_asking')}", expanded=True):
    st.markdown(t("chat.examples"))

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for m in st.session_state.chat_messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input(t("chat.input_placeholder")):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner(t("chat.thinking")):
            reply = chat(
                st.session_state.chat_messages,
                data_context=ctx,
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
            )
        st.markdown(reply)
    st.session_state.chat_messages.append({"role": "assistant", "content": reply})

if st.session_state.chat_messages and st.button(t("chat.clear")):
    st.session_state.chat_messages = []
    st.rerun()
