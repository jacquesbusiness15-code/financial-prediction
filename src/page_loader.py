"""Shared dataset loader and upload prompt for every Streamlit page."""
from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.components import section_card
from src.data_cache import load_or_build_cache
from src.data_loader import SchemaReport
from src.i18n import t

DEFAULT_PATH = Path("data/Dataset_anoym.xlsx")


@st.cache_data(show_spinner="Datensatz wird geladen...")
def _load_cached(path: str, sheet: int | str = 0) -> tuple[pd.DataFrame, SchemaReport]:
    return load_or_build_cache(path, sheet=sheet)


def _schema_error_msg(report: SchemaReport) -> str:
    return t("data.schema_error",
             m=len(report.matched),
             t=report.expected_total,
             missing=", ".join(report.missing_critical))


def _load_data(path: str) -> pd.DataFrame | None:
    try:
        df, report = _load_cached(path)
    except (OSError, ValueError) as e:
        st.error(t("data.load_failed", err=str(e)))
        return None
    if not report.ok:
        st.error(_schema_error_msg(report))
        return None
    return df


def _resolve_path() -> str | None:
    candidates = [DEFAULT_PATH, *sorted(DEFAULT_PATH.parent.glob(f"{DEFAULT_PATH.stem}.*"))]
    return next((str(p) for p in candidates if p.exists() and p.is_file()), None)


def _handle_upload(uploaded) -> None:
    suffix = Path(uploaded.name).suffix.lower() or DEFAULT_PATH.suffix
    target = DEFAULT_PATH.with_suffix(suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(uploaded.getbuffer())
    # Parse + enrich once; stash the DataFrame in session_state so the rerun
    # that switches from upload page to dashboard skips re-reading the file.
    try:
        df, report = load_or_build_cache(str(target))
    except Exception as e:  # noqa: BLE001 - surface any parser error to the user
        target.unlink(missing_ok=True)
        st.error(t("upload.schema_failed", msg=str(e)))
        return
    if not report.ok:
        target.unlink(missing_ok=True)
        st.error(_schema_error_msg(report))
        return
    st.cache_data.clear()
    st.session_state["df"] = df
    st.session_state["dataset_confirmed"] = True
    st.success(t("upload.success"))
    st.rerun()


def render_upload_page() -> None:
    st.markdown(
        f"""
<div class='wisag-upload-hero'>
  <h2 class='wisag-upload-hero-title'>{escape(t('upload.title'))}</h2>
  <p class='wisag-upload-hero-sub'>{escape(t('upload.subtitle'))}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        label=t("upload.cta"),
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=False,
        key="dataset_upload",
        help=t("upload.cta_help"),
    )
    if uploaded is not None:
        _handle_upload(uploaded)

    rows_html = "".join(
        f"<div class='wisag-req-row'>"
        f"  <div>"
        f"    <p class='wisag-req-title'>{escape(t(f'{key}.title'))}</p>"
        f"    <p class='wisag-req-sub'>{escape(t(f'{key}.sub'))}</p>"
        f"  </div>"
        f"</div>"
        for key in ("upload.req_xlsx", "upload.req_headers", "upload.req_period")
    )
    section_card(
        title=t("upload.requirements_title"),
        subtitle=t("upload.requirements_sub"),
        rows_html=rows_html,
    )

    st.markdown(
        f"<p class='wisag-upload-footer-hint'>{t('upload.sample_hint')}</p>",
        unsafe_allow_html=True,
    )


def try_load() -> pd.DataFrame | None:
    # Hot path: upload handler primed the df into session_state, so the rerun
    # that shows the dashboard doesn't have to re-read the parquet cache.
    cached = st.session_state.get("df")
    if cached is not None and _resolve_path() is not None:
        st.session_state.setdefault("dataset_confirmed", True)
        return cached

    path = _resolve_path()
    if path is None:
        return None
    if not st.session_state.get("dataset_confirmed"):
        st.session_state["dataset_confirmed"] = True
    df = _load_data(path)
    if df is not None:
        st.session_state["df"] = df
    return df


def load_or_prompt_upload() -> pd.DataFrame | None:
    df = try_load()
    if df is None:
        render_upload_page()
    return df
