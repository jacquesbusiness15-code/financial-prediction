"""WISAG Financial Co-Pilot — Streamlit entry point.

The landing view at ``/`` is the portfolio ranking table (contracts sorted by
latest-month unprofitability). Clicking a row sets
``st.session_state["selected_cost_center"]`` and this dispatcher switches to
the single-contract detail view.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src import contract_detail_page, early_warning, portfolio_page
from src.components import setup_page, sidebar_logo, sidebar_nav
from src.page_loader import render_upload_page, try_load

load_dotenv()

setup_page("app.title")


def _alerts_count(df: pd.DataFrame | None) -> int:
    if df is None or df.empty:
        return 0
    try:
        alerts = early_warning.detect(df)
        return int(len(alerts))
    except Exception:  # noqa: BLE001
        return 0


def _consume_cc_query_param() -> None:
    """Promote `?cc_id=<id>` from the URL into session state, then strip it."""
    qp = st.query_params
    raw = qp.get("cc_id")
    if raw:
        st.session_state["selected_cost_center"] = str(raw)
        del qp["cc_id"]


def main() -> None:
    sidebar_logo()
    _consume_cc_query_param()
    df = try_load()
    sidebar_nav(active="overview", alerts_count=_alerts_count(df))
    if df is None:
        render_upload_page()
        return

    selected = st.session_state.get("selected_cost_center")
    if selected and "cost_center_id" in df.columns and selected in df["cost_center_id"].astype(str).unique():
        contract_detail_page.render(df, selected)
    else:
        if selected:
            st.session_state.pop("selected_cost_center", None)
        portfolio_page.render(df)


if __name__ == "__main__":
    main()
