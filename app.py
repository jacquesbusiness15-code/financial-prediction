"""WISAG Financial Co-Pilot Streamlit entry point.

Run with: streamlit run app.py
"""
from __future__ import annotations

import atexit
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src import contract_detail_page, copilot_chat, early_warning, portfolio_page
from src.components import setup_page, sidebar_logo, sidebar_nav
from src.page_loader import DEFAULT_PATH, render_upload_page, try_load


def _purge_uploaded_dataset() -> None:
    """Remove any persisted dataset and its parquet cache.

    Runs once on interpreter startup (covers orphaned data from a previous
    crashed/killed session) and again via atexit on graceful shutdown.
    """
    for p in DEFAULT_PATH.parent.glob(f"{DEFAULT_PATH.stem}.*"):
        try:
            p.unlink()
        except OSError:
            pass
    cache_dir = Path("data") / ".cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)


_purge_uploaded_dataset()
atexit.register(_purge_uploaded_dataset)

load_dotenv()
setup_page("app.title")


def _alerts_count(df: pd.DataFrame | None) -> int:
    if df is None or df.empty:
        return 0
    try:
        return int(len(early_warning.detect(df)))
    except Exception:  # noqa: BLE001
        return 0


def _consume_cc_query_param() -> None:
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
    if (selected and "cost_center_id" in df.columns
            and selected in df["cost_center_id"].astype(str).unique()):
        contract_detail_page.render(df, selected)
    else:
        if selected:
            st.session_state.pop("selected_cost_center", None)
        portfolio_page.render(df)

    copilot_chat.render(df)


if __name__ == "__main__":
    main()
