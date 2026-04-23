"""Shared dataset loader + upload prompt for every Streamlit page.

`load_or_prompt_upload()` is the single entry point. It returns an enriched
DataFrame when data is available, or renders the full-page upload prompt and
returns None (in which case the caller should simply `return`).
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.components import section_card
from src.data_cache import load_or_build_cache
from src.data_loader import SchemaReport, load
from src.i18n import t

DEFAULT_PATH = Path("data/Dataset_anoym.xlsx")


@st.cache_data(show_spinner="Datensatz wird geladen…")
def _load_cached(path: str, sheet: int | str = 0) -> tuple[pd.DataFrame, SchemaReport]:
    return load_or_build_cache(path, sheet=sheet)


def _load_data(path: str) -> pd.DataFrame | None:
    try:
        df, report = _load_cached(path)
    except Exception as e:  # noqa: BLE001
        st.error(t("data.load_failed", err=str(e)))
        return None
    if not report.ok:
        st.error(
            t(
                "data.schema_error",
                m=len(report.matched),
                t=report.expected_total,
                missing=", ".join(report.missing_critical),
            )
        )
        return None
    return df


def _resolve_path() -> str | None:
    candidates = [DEFAULT_PATH, *sorted(DEFAULT_PATH.parent.glob(f"{DEFAULT_PATH.stem}.*"))]
    return next((str(p) for p in candidates if p.exists() and p.is_file()), None)


def render_upload_page() -> None:
    """Full-page upload prompt shown when no dataset is available yet."""
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
        suffix = Path(uploaded.name).suffix.lower() or DEFAULT_PATH.suffix
        target = DEFAULT_PATH.with_suffix(suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(uploaded.getbuffer())
        try:
            _, report = load(str(target))
        except Exception as e:  # noqa: BLE001
            target.unlink(missing_ok=True)
            st.error(t("upload.schema_failed", msg=str(e)))
            return
        if not report.ok:
            target.unlink(missing_ok=True)
            st.error(
                t(
                    "data.schema_error",
                    m=len(report.matched),
                    t=report.expected_total,
                    missing=", ".join(report.missing_critical),
                )
            )
            return
        st.cache_data.clear()
        st.success(t("upload.success"))
        st.rerun()

    reqs = [
        "upload.req_xlsx",
        "upload.req_headers",
        "upload.req_period",
    ]
    rows_html = ""
    for key in reqs:
        rows_html += (
            f"<div class='wisag-req-row'>"
            f"  <div>"
            f"    <p class='wisag-req-title'>{escape(t(f'{key}.title'))}</p>"
            f"    <p class='wisag-req-sub'>{escape(t(f'{key}.sub'))}</p>"
            f"  </div>"
            f"</div>"
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
    """Resolve and return an enriched df, or None if unavailable. No UI side effects beyond st.error."""
    path = _resolve_path()
    df = _load_data(path) if path else None
    if df is not None:
        st.session_state["df"] = df
    return df


def load_or_prompt_upload() -> pd.DataFrame | None:
    """Resolve the dataset, or render the upload page and return None."""
    df = try_load()
    if df is None:
        render_upload_page()
        return None
    return df
