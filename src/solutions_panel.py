"""UI for the Solution Finder card on the contract detail page.

Each recommendation is rendered as a three-question card:

    1. **Was wir tun** - one sentence describing the action.
    2. **Warum das hilft** - the cause-and-fix logic, grounded in the
       specific data column that drove the problem.
    3. **Was es bringt** - the EUR figure, the step-by-step math that
       produced it, and a plain-language outcome sentence.

All strings come through ``src.i18n`` (DE/EN). No emojis.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from src import action_tracker
from src.benchmarks import CohortStats, cohort_stats
from src.contract_metrics import ContractMetrics
from src.cost_drivers import CostDriver
from src.i18n import t
from src.solution_catalog import ACTIONS
from src.solution_finder import (
    DEFAULT_TOP_N,
    MAX_TOP_N,
    ActionRecommendation,
    recommend,
)
from src.solution_impact import explain as impact_explain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DASH = "—"


def _fmt_eur(value: float) -> str:
    return f"{value:,.0f} EUR".replace(",", ".")


def _fmt_eur_or_dash(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return _DASH
    try:
        return _fmt_eur(float(value))
    except (TypeError, ValueError):
        return _DASH


def _fmt_realized(row: pd.Series) -> str:
    val = row.get("realized_cm_delta")
    if val is not None and not (isinstance(val, float) and pd.isna(val)):
        try:
            return _fmt_eur(float(val))
        except (TypeError, ValueError):
            pass
    if str(row.get("status")) == "done":
        return t("solutions.realized_pending")
    return t("solutions.realized_not_ready")


def _fmt_created(value) -> str:
    if value is None:
        return _DASH
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return _DASH
    return ts.strftime("%d.%m.%Y")


def _safe_float(v) -> float:
    if v is None:
        return 0.0
    try:
        if pd.isna(v):
            return 0.0
    except (TypeError, ValueError):
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _safe_period(v) -> Optional[pd.Timestamp]:
    if v is None:
        return None
    ts = pd.to_datetime(v, errors="coerce")
    return None if pd.isna(ts) else ts


def _confidence_label(value: float) -> str:
    if value >= 0.66:
        return t("solutions.confidence.high")
    if value >= 0.33:
        return t("solutions.confidence.med")
    return t("solutions.confidence.low")


def _owner_label(owner_role: str) -> str:
    key = f"solutions.owner.{owner_role}"
    label = t(key)
    return label if label != key else owner_role


def _action_title(action_id: str) -> str:
    action = ACTIONS.get(action_id)
    if action is None:
        return action_id
    return t(action.i18n_title_key)


def _status_label(status: str) -> str:
    key = f"solutions.status.{status}"
    label = t(key)
    return label if label != key else status


def _t_or(key: str, fallback: str) -> str:
    val = t(key)
    return val if val != key else fallback


def _driver_label(driver: CostDriver) -> str:
    return _t_or(f"column.{driver.column}", driver.column)


def _driver_fix_label(driver: CostDriver) -> str:
    return _t_or(f"sub_action.{driver.sub_action_id}.title",
                 driver.sub_action_id)


def _latest_row(df: pd.DataFrame, cost_center_id: str) -> Optional[pd.Series]:
    focus = df[df["cost_center_id"] == cost_center_id]
    if focus.empty:
        return None
    focus = focus.sort_values("period")
    return focus.iloc[-1]


def _history(df: pd.DataFrame, cost_center_id: str) -> pd.DataFrame:
    hist = df[df["cost_center_id"] == cost_center_id].copy()
    if hist.empty:
        return hist
    return hist.sort_values("period")


# ---------------------------------------------------------------------------
# The three-question card
# ---------------------------------------------------------------------------

def _why_body(rec: ActionRecommendation) -> str:
    """Produce the 'Why this helps' paragraph, grounded in the top driver."""
    base = _t_or(f"why_prose.{rec.action_id}", "")
    if not rec.drivers:
        trail = t("solutions.no_drivers_text")
        return f"{base}\n\n{trail}" if base else trail

    top = rec.drivers[0]
    label = _driver_label(top)
    share_pct = f"{top.share_of_issue * 100:.0f}%"

    if top.column.startswith("revenue_"):
        delta_txt = (f"{top.delta_pct:+.0%}"
                     if top.delta_pct is not None else _fmt_eur(top.delta_eur))
        direction = "unter"
    else:
        delta_txt = (f"+{top.delta_pct:.0%}"
                     if top.delta_pct is not None else _fmt_eur(top.delta_eur))
        direction = "über"

    evidence = (
        f"**Beobachtung:** {label} liegt {delta_txt} {direction} dem "
        f"eigenen 3-Monats-Schnitt ({_fmt_eur(top.baseline_eur)}). "
        f"Diese einzelne Spalte erklärt {share_pct} der Lücke."
    )

    extras: list[str] = []
    for d in rec.drivers[1:3]:
        extras.append(
            f"- {_driver_label(d)}: "
            f"{(f'{d.delta_pct:+.0%}' if d.delta_pct is not None else _fmt_eur(d.delta_eur))} "
            f"- Fix: {_driver_fix_label(d)}"
        )

    parts = [base, evidence]
    if extras:
        parts.append("\n".join(extras))
    return "\n\n".join(p for p in parts if p)


def _outcome_sentence(rec: ActionRecommendation) -> str:
    impact_str = _fmt_eur(rec.estimated_impact_eur_month)
    if rec.category == "retention":
        return t("solutions.q3_outcome_retention", impact=impact_str)
    if rec.category == "scope":
        return t("solutions.q3_outcome_scope", impact=impact_str)
    if rec.category == "revenue":
        return t("solutions.q3_outcome_revenue", impact=impact_str)
    return t("solutions.q3_outcome_cost", impact=impact_str)


def _render_math_breakdown(
    rec: ActionRecommendation,
    latest: pd.Series,
    cohort: CohortStats,
) -> None:
    action = ACTIONS.get(rec.action_id)
    if action is None:
        return
    rows = impact_explain(action.impact_formula_id, latest, cohort)
    if not rows:
        return
    st.markdown(f"**{t('solutions.q3_math_title')}**")
    math_df = pd.DataFrame(rows, columns=["Schritt", "Wert"])
    st.dataframe(math_df, use_container_width=True, hide_index=True)
    raw = _extract_raw_from_math(rows)
    capped = rec.estimated_impact_eur_month
    if raw is not None and abs(raw - capped) > 0.5:
        st.caption(t("solutions.q3_cap_note", capped=_fmt_eur(capped)))


def _extract_raw_from_math(rows: list[tuple[str, str]]) -> Optional[float]:
    """Pull the pre-cap EUR value out of the last step, if present."""
    if not rows:
        return None
    _, last_value = rows[-1]
    digits = last_value.replace(".", "").replace(" EUR", "").replace("+", "")
    try:
        return float(digits)
    except ValueError:
        return None


def _render_action_card(
    cost_center_id: str,
    rec: ActionRecommendation,
    latest_row: pd.Series,
    cohort: CohortStats,
    index: int,
) -> None:
    with st.container(border=True):
        st.markdown(f"### {index}. {_action_title(rec.action_id)}")
        action = ACTIONS.get(rec.action_id)
        if action is not None:
            st.caption(t(action.i18n_desc_key))

        st.markdown(
            f"- {t('solutions.meta_owner', owner=_owner_label(rec.owner_role))}\n"
            f"- {t('solutions.meta_timeframe', weeks=rec.timeframe_weeks)}\n"
            f"- {t('solutions.meta_confidence', conf=_confidence_label(rec.confidence))}"
        )

        # Question 1 - What we'll do
        st.markdown(f"#### {t('solutions.q1_title')}")
        q1_text = _t_or(f"what_prose.{rec.action_id}", "")
        if q1_text:
            st.markdown(q1_text)
        elif action is not None:
            st.markdown(t(action.i18n_desc_key))

        # Question 2 - Why it helps
        st.markdown(f"#### {t('solutions.q2_title')}")
        st.markdown(_why_body(rec))

        # Question 3 - What it's worth
        st.markdown(f"#### {t('solutions.q3_title')}")
        st.markdown(_outcome_sentence(rec))
        _render_math_breakdown(rec, latest_row, cohort)

        st.markdown(f"**{t('solutions.ready_to_track')}**")
        click_key = f"sf_{cost_center_id}_{rec.action_id}_log"
        confirm_key = f"{click_key}__confirmed"
        if st.button(
            t("solutions.log_action"),
            key=click_key,
            type="primary",
        ):
            action_tracker.log_action(
                contract_id=str(cost_center_id),
                action_id=rec.action_id,
                owner=rec.owner_role,
                estimated_impact=rec.estimated_impact_eur_month,
                baseline_cm_db=_safe_float(latest_row.get("cm_db")),
                baseline_period=_safe_period(latest_row.get("period")),
            )
            st.session_state[confirm_key] = True
            try:
                st.toast(t("solutions.track_confirmed",
                           title=_action_title(rec.action_id)))
            except Exception:  # noqa: BLE001 - toast is best-effort
                pass
            st.rerun()

        if st.session_state.get(confirm_key):
            st.success(t("solutions.track_confirmed",
                         title=_action_title(rec.action_id)), icon=None)


# ---------------------------------------------------------------------------
# Tracked actions
# ---------------------------------------------------------------------------

def _tracked_to_table(tracked: pd.DataFrame) -> pd.DataFrame:
    if tracked.empty:
        return tracked
    out = pd.DataFrame(index=tracked.index)
    out[t("solutions.col.action")] = tracked["action_id"].map(_action_title)
    out[t("solutions.col.status")] = tracked["status"].map(_status_label)
    out[t("solutions.col.impact")] = tracked["estimated_impact"].map(_fmt_eur_or_dash)
    out[t("solutions.realized_column")] = [
        _fmt_realized(row) for _, row in tracked.iterrows()
    ]
    out[t("solutions.col.owner")] = tracked["owner"].fillna("").map(
        lambda o: _owner_label(o) if o in {"ops", "sales", "regional_manager"}
        else (o or ""))
    out[t("solutions.col.created")] = tracked["created_at"].map(_fmt_created)
    return out


def _render_status_buttons(cost_center_id: str, entry_id: int) -> None:
    cols = st.columns(3)
    labels = [
        ("in_progress", t("solutions.btn.mark_in_progress")),
        ("done", t("solutions.btn.mark_done")),
        ("abandoned", t("solutions.btn.mark_abandoned")),
    ]
    for col, (status, label) in zip(cols, labels):
        with col:
            key = f"sf_status_{cost_center_id}_{entry_id}_{status}"
            if st.button(label, key=key, use_container_width=True):
                action_tracker.update_status(entry_id, status)  # type: ignore[arg-type]
                st.rerun()


def _render_tracked(cost_center_id: str, df: pd.DataFrame) -> None:
    tracked = action_tracker.list_for_contract(str(cost_center_id))
    st.markdown(f"#### {t('solutions.tracked_title')}")
    if tracked.empty:
        st.caption(t("solutions.tracked_empty"))
        return

    for _, row in tracked.iterrows():
        if (str(row["status"]) == "done"
                and pd.isna(row["realized_cm_delta"])):
            try:
                action_tracker.measure_outcome(int(row["id"]), df)
            except Exception:  # noqa: BLE001 - keep UI resilient
                pass
    tracked = action_tracker.list_for_contract(str(cost_center_id))

    table = _tracked_to_table(tracked)
    st.dataframe(table, use_container_width=True, hide_index=True)

    open_rows = tracked[tracked["status"].isin({"proposed", "in_progress"})]
    for _, row in open_rows.iterrows():
        st.markdown(f"*{_action_title(row['action_id'])}*")
        _render_status_buttons(cost_center_id, int(row["id"]))


def _render_llm_narrative(
    cost_center_id: str,
    recs: list[ActionRecommendation],
    metrics: ContractMetrics,
    latest_row: pd.Series,
    cohort: CohortStats,
) -> None:
    if not recs:
        return
    with st.expander(t("solutions.llm_narrative_title"), expanded=False):
        try:
            from src.llm_copilot import suggest_actions
        except Exception:  # noqa: BLE001
            st.caption(t("solutions.llm_unavailable"))
            return
        cache_key = (f"sf_llm_{cost_center_id}_"
                     + "|".join(r.action_id for r in recs))
        cached = st.session_state.get(cache_key)
        if cached is None:
            try:
                cached = suggest_actions(metrics, latest_row, cohort, recs)
            except Exception:  # noqa: BLE001
                cached = t("solutions.llm_unavailable")
            st.session_state[cache_key] = cached
        st.markdown(cached)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render(
    df: pd.DataFrame,
    cost_center_id: str,
    metrics: ContractMetrics,
    warnings: Optional[pd.DataFrame] = None,
    top_n: int = DEFAULT_TOP_N,
) -> None:
    """Render the Solutions card."""
    latest = _latest_row(df, cost_center_id)
    if latest is None:
        return
    history = _history(df, cost_center_id)
    cohort = cohort_stats(
        df,
        region=(str(latest.get("region"))
                if latest.get("region") is not None else None),
        industry=(str(latest.get("industry"))
                  if latest.get("industry") is not None else None),
        service_type=(str(latest.get("service_type"))
                      if latest.get("service_type") is not None else None),
    )

    warnings_df = warnings if warnings is not None else pd.DataFrame()
    recs = recommend(metrics, latest, history, warnings_df,
                     cohort, top_n=min(max(top_n, 1), MAX_TOP_N))

    if not recs:
        st.info(t("solutions.empty"))
    else:
        for i, rec in enumerate(recs, start=1):
            _render_action_card(cost_center_id, rec, latest, cohort, i)

    _render_tracked(cost_center_id, df)
    _render_llm_narrative(cost_center_id, recs, metrics, latest, cohort)
