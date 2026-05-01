"""Streamlit-side controller for the floating copilot chat dock."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src import copilot_intent, llm_copilot, speech
from src.contract_metrics import ContractMetrics, compute_metrics
from src.copilot_widget import copilot_widget
from src.i18n import t
from src.portfolio_ranking import compute_rankings

_MAX_CONTEXT_CHARS = 16_000
_WORST_N = 10
_BEST_N = 5
_WORST_N_TRIMMED = 5
_BEST_N_TRIMMED = 3

_SS_MESSAGES = "copilot_messages"
_SS_EXPANDED = "copilot_expanded"
_SS_BUSY = "copilot_busy"
_SS_LAST_NONCE = "copilot_last_nonce"
_SS_PENDING = "copilot_pending_user_msg"

# Pin the custom component iframe to the bottom-right of the VIEWPORT
# (not the scrolling content area). Streamlit places the iframe inside
# its main block container, and several ancestors apply CSS properties
# (``transform``, ``filter``, ``contain``) that create a new containing
# block for ``position: fixed`` — which means a CSS-only fix scrolls
# with the page. The reliable fix is to *reparent* the iframe to
# ``document.body`` via a tiny script, where nothing can trap it.
#
# We still keep the CSS as a defence-in-depth in case the script runs
# before the iframe exists.
_DOCK_PIN_CSS = """
<style>
  iframe[title="src.copilot_widget.wisag_copilot"] {
    position: fixed !important;
    right: 18px !important;
    bottom: 18px !important;
    width: 400px !important;
    max-width: calc(100vw - 36px) !important;
    border: none !important;
    background: transparent !important;
    z-index: 2147483647 !important;
  }
  [data-testid="stCustomComponentV1"]:has(> iframe[title="src.copilot_widget.wisag_copilot"]) {
    position: fixed !important;
    right: 18px !important;
    bottom: 18px !important;
    width: 400px !important;
    height: 400px !important;
    z-index: 2147483647 !important;
    pointer-events: none;
  }
  [data-testid="stCustomComponentV1"]:has(> iframe[title="src.copilot_widget.wisag_copilot"]) iframe {
    pointer-events: all;
  }
</style>
"""

# Reparent the src.copilot_widget.wisag_copilot iframe to document.body so its
# `position: fixed` is anchored to the viewport regardless of what
# transforms/filters/contains Streamlit applies to ancestors. Runs
# inside its own components.v1.html iframe (same-origin → can touch
# the parent document). Idempotent: a flag on `window.parent` plus a
# MutationObserver handle Streamlit reruns that recreate the iframe.
# Streamlit custom-component iframes are cross-origin and ship with no
# `allow` attribute, so `navigator.mediaDevices.getUserMedia` is blocked
# by the Permissions Policy. We can't set the attribute server-side, so
# we add it from a sibling iframe (same-origin to the streamlit shell)
# and force a one-time reload to apply the new policy. The widget then
# survives subsequent renders without the script touching it again.
_MIC_PERMISSION_JS = """
<script>
(function () {
  var parentWin = window.parent;
  if (parentWin.__wisagMicSetupDone) return;
  var parentDoc = parentWin.document;
  function ensure() {
    var iframe = parentDoc.querySelector(
      'iframe[title="src.copilot_widget.wisag_copilot"]');
    if (!iframe) return false;
    parentWin.__wisagMicSetupDone = true;
    var current = iframe.getAttribute('allow') || '';
    if (current.indexOf('microphone') !== -1) return true;
    iframe.setAttribute('allow',
      (current ? current + '; ' : '') + 'microphone');
    var src = iframe.getAttribute('src');
    if (src) iframe.setAttribute('src', src);
    return true;
  }
  if (ensure()) return;
  var obs = new MutationObserver(function () {
    if (ensure()) obs.disconnect();
  });
  obs.observe(parentDoc.body, { childList: true, subtree: true });
})();
</script>
"""

_DOCK_PIN_JS = """
<script>
(function () {
  var parentWin = window.parent;
  var parentDoc = parentWin.document;
  var STYLE = (
    'position:fixed!important;'
    + 'right:18px!important;'
    + 'bottom:18px!important;'
    + 'width:400px!important;'
    + 'max-width:calc(100vw - 36px)!important;'
    + 'border:none!important;'
    + 'background:transparent!important;'
    + 'z-index:2147483647!important;'
    + 'color-scheme:normal!important;'
  );
  function pin() {
    var iframe = parentDoc.querySelector('iframe[title="src.copilot_widget.wisag_copilot"]');
    if (!iframe) return false;
    if (iframe.parentElement !== parentDoc.body) {
      parentDoc.body.appendChild(iframe);
    }
    if (iframe.getAttribute('data-wisag-pinned') !== '1') {
      iframe.setAttribute('style', STYLE);
      iframe.setAttribute('data-wisag-pinned', '1');
    }
    return true;
  }
  // Try immediately, then keep an observer alive across reruns.
  pin();
  if (!parentWin.__wisagCopilotObserver) {
    var obs = new MutationObserver(function () { pin(); });
    obs.observe(parentDoc.body, { childList: true, subtree: true });
    parentWin.__wisagCopilotObserver = obs;
  }
})();
</script>
"""


def _safe_round(value, digits: int = 0):
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _metric_row(m: ContractMetrics) -> dict:
    r = m.base
    revenue_eur = _safe_round(r.current_revenue_eur, 0)
    cm_eur = _safe_round(r.current_cm_eur, 0)
    cost_eur = (
        revenue_eur - cm_eur
        if revenue_eur is not None and cm_eur is not None
        else None
    )
    margin_pct = (
        _safe_round(r.current_margin_pct * 100.0, 1)
        if r.current_margin_pct is not None
        else None
    )
    return {
        "id": str(r.cost_center_id),
        "name": r.cost_center_name or str(r.cost_center_id),
        "region": r.region or None,
        "customer": r.customer_name or None,
        "industry": r.industry or None,
        "revenue_total_eur": revenue_eur,
        "cm_db_eur": cm_eur,
        "cost_total_eur": cost_eur,
        "cm_pct": margin_pct,
        "cm_mom_pct": _safe_round(
            (r.cm_mom_pct * 100.0) if r.cm_mom_pct is not None else None, 1,
        ),
        "cm_mom_eur": _safe_round(r.cm_mom_eur, 0),
        "months_unprofitable": int(r.months_unprofitable or 0),
        "top_cost_category_now": m.top_cost_category_now,
        "top_cost_category_now_eur": _safe_round(m.top_cost_category_now_eur, 0),
        "top_cost_increase_cat": m.top_cost_increase_cat,
        "overall_score": _safe_round(m.overall_score, 0),
    }


def _aggregate_totals(df: pd.DataFrame) -> dict:
    if df is None or df.empty or "period" not in df.columns:
        return {}
    agg = (df.groupby("period", as_index=False)
             .agg(revenue_total=("revenue_total", "sum"),
                  cm_db=("cm_db", "sum"),
                  contracts=("cost_center_id", "nunique"))
             .sort_values("period"))
    if agg.empty:
        return {}

    def _row(r) -> dict:
        revenue = _safe_round(r["revenue_total"], 0)
        cm = _safe_round(r["cm_db"], 0)
        cost = _safe_round(revenue - cm, 0) if revenue is not None and cm is not None else None
        return {
            "period": str(pd.Timestamp(r["period"]).date()),
            "revenue_total_eur": revenue,
            "cm_db_eur": cm,
            "cost_total_eur": cost,
            "contract_count": int(r["contracts"] or 0),
        }

    out = {"latest": _row(agg.iloc[-1])}
    if len(agg) >= 2:
        out["previous"] = _row(agg.iloc[-2])
    return out


def _group_counts(df: pd.DataFrame, col: str) -> dict[str, int]:
    if df is None or df.empty or col not in df.columns:
        return {}
    latest = df["period"].max() if "period" in df.columns else None
    slice_df = df[df["period"] == latest] if latest is not None else df
    counts = (slice_df.groupby(col)["cost_center_id"].nunique()
                      .sort_values(ascending=False))
    return {str(k): int(v) for k, v in counts.items() if pd.notna(k)}


_RANK_LIST_N = 5


def _row_value(row: dict, key: str) -> float:
    """Sortable key with NaN/None pushed to the bottom of DESC sorts."""
    val = row.get(key)
    if val is None:
        return float("-inf")
    try:
        if pd.isna(val):
            return float("-inf")
        return float(val)
    except (TypeError, ValueError):
        return float("-inf")


@st.cache_data(show_spinner=False)
def _build_context_cached(df_token: tuple, df: pd.DataFrame) -> dict:
    del df_token  # cache key only
    rankings = compute_rankings(df)
    metrics = compute_metrics(rankings, df)

    def _score(m):
        return m.overall_score if m.overall_score is not None else 50.0

    worst = sorted(metrics, key=_score)[:_WORST_N]
    best = sorted(metrics, key=_score, reverse=True)[:_BEST_N]

    rows = [_metric_row(m) for m in metrics]
    top_by_cost = sorted(rows, key=lambda r: _row_value(r, "cost_total_eur"),
                         reverse=True)[:_RANK_LIST_N]
    top_by_revenue = sorted(rows, key=lambda r: _row_value(r, "revenue_total_eur"),
                            reverse=True)[:_RANK_LIST_N]
    # cm_db_eur ASC is the most-negative-first ordering.
    top_by_loss = sorted(rows, key=lambda r: _row_value(r, "cm_db_eur"))[:_RANK_LIST_N]

    return {
        "portfolio_totals": _aggregate_totals(df),
        "contracts_by_region": _group_counts(df, "region"),
        "contracts_by_industry": _group_counts(df, "industry"),
        "worst_contracts": [_metric_row(m) for m in worst],
        "best_contracts": [_metric_row(m) for m in best],
        "top_by_cost": top_by_cost,
        "top_by_revenue": top_by_revenue,
        "top_by_loss": top_by_loss,
        "total_contracts": int(df["cost_center_id"].nunique())
            if "cost_center_id" in df.columns else 0,
    }


def _df_cache_token(df: pd.DataFrame) -> tuple:
    if df is None or df.empty:
        return (0, None)
    latest = None
    if "period" in df.columns and not df["period"].empty:
        try:
            latest = str(pd.Timestamp(df["period"].max()).date())
        except (TypeError, ValueError):
            latest = None
    nunique = (int(df["cost_center_id"].nunique())
               if "cost_center_id" in df.columns else 0)
    return (len(df), latest, nunique)


def _build_context(df: pd.DataFrame) -> dict:
    ctx = _build_context_cached(_df_cache_token(df), df)
    blob = json.dumps(ctx, default=str)
    if len(blob) <= _MAX_CONTEXT_CHARS:
        return ctx
    # Truncate so the prompt cache stays hot and per-turn cost bounded.
    trimmed = dict(ctx)
    trimmed["worst_contracts"] = trimmed.get("worst_contracts", [])[:_WORST_N_TRIMMED]
    trimmed["best_contracts"] = trimmed.get("best_contracts", [])[:_BEST_N_TRIMMED]
    trimmed["_truncated"] = True
    return trimmed


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault(_SS_MESSAGES, [])
    ss.setdefault(_SS_EXPANDED, False)
    ss.setdefault(_SS_BUSY, False)
    ss.setdefault(_SS_LAST_NONCE, -1)
    ss.setdefault(_SS_PENDING, None)


def _run_llm_turn(df: pd.DataFrame) -> None:
    ss = st.session_state
    pending = ss.get(_SS_PENDING)
    if not pending:
        return
    try:
        reply = llm_copilot.chat(list(ss[_SS_MESSAGES]), _build_context(df))
    except Exception as exc:  # noqa: BLE001 - UI must degrade on any failure
        reply = t("copilot.error_no_key") + f"\n\n({exc})"
    ss[_SS_MESSAGES].append({"role": "assistant", "content": reply})
    ss[_SS_PENDING] = None
    ss[_SS_BUSY] = False
    ss[_SS_EXPANDED] = True


def _try_deterministic_answer(text: str, df: pd.DataFrame, lang: str) -> str | None:
    """Return a verified ranking answer if `text` is a top-N question, else None.

    Routing this in Python (instead of asking the LLM) is the actual fix for
    the bug where "höchste Kosten" was answered with the most-negative-margin
    contract. The data is the source of truth; the LLM never sees this turn.
    """
    intent = copilot_intent.detect_ranking_intent(text, lang=lang)
    if intent is None:
        return None
    answer = copilot_intent.answer_ranking(intent, df)
    return copilot_intent.format_ranking_answer(answer, lang=lang)


def _enqueue_user_message(text: str, df: pd.DataFrame) -> None:
    """Append the user turn and either answer it deterministically or queue
    the LLM call. Caller is responsible for triggering st.rerun()."""
    ss = st.session_state
    ss[_SS_MESSAGES].append({"role": "user", "content": text})
    ss[_SS_EXPANDED] = True
    lang = ss.get("lang", "de")
    reply = _try_deterministic_answer(text, df, lang)
    if reply is not None:
        ss[_SS_MESSAGES].append({"role": "assistant", "content": reply})
        ss[_SS_BUSY] = False
        ss[_SS_PENDING] = None
        return
    ss[_SS_BUSY] = True
    ss[_SS_PENDING] = text


def _handle_event(event: dict, df: pd.DataFrame) -> None:
    ss = st.session_state
    nonce = event.get("nonce")
    if not isinstance(nonce, int) or nonce <= ss.get(_SS_LAST_NONCE, -1):
        return
    ss[_SS_LAST_NONCE] = nonce

    ev_type = event.get("type")
    if ev_type == "state":
        ss[_SS_EXPANDED] = bool(event.get("expanded", False))
        return
    if ev_type == "audio":
        audio_b64 = str(event.get("data", ""))
        mime = str(event.get("mime", "audio/webm"))
        try:
            text = speech.transcribe(
                audio_b64, mime=mime, lang=ss.get("lang", "de"),
            )
        except Exception as exc:  # noqa: BLE001 - UI must degrade
            ss[_SS_MESSAGES].append({
                "role": "assistant",
                "content": f"{t('copilot.error_no_key')}\n\n({exc})",
            })
            ss[_SS_EXPANDED] = True
            st.rerun()
            return
        if not text:
            return
        _enqueue_user_message(text, df)
        st.rerun()
        return
    if ev_type != "send":
        return
    text = str(event.get("text", "")).strip()
    if not text:
        return
    _enqueue_user_message(text, df)
    st.rerun()


def render(df: pd.DataFrame) -> None:
    """Render the floating copilot dock. Call once at the end of a page."""
    _init_state()
    ss = st.session_state

    # Pin the iframe fixed bottom-right before it paints.
    st.markdown(_DOCK_PIN_CSS, unsafe_allow_html=True)
    # Grant the widget iframe `allow=microphone` so getUserMedia works
    # for the dictation button. Forces a one-time reload on first paint.
    components.html(_MIC_PERMISSION_JS, height=0, width=0)
    # And — crucially — reparent it to <body> so ancestor transforms
    # cannot trap its `position: fixed`.
    # components.html(_DOCK_PIN_JS, height=0, width=0)

    # Run any queued LLM turn before the widget paints so the reply is visible.
    if ss.get(_SS_PENDING):
        _run_llm_turn(df)

    event = copilot_widget(
        messages=list(ss[_SS_MESSAGES]),
        expanded=bool(ss[_SS_EXPANDED]),
        busy=bool(ss[_SS_BUSY]),
        lang=ss.get("lang", "de"),
        placeholder=t("copilot.placeholder"),
        mic_hint=t("copilot.mic_hint"),
        empty_greeting=t("copilot.empty_greeting"),
        thinking_label=t("chat.thinking"),
        send_label=t("copilot.send"),
        mic_label=t("copilot.mic"),
        read_aloud_label=t("copilot.read_aloud"),
        stop_reading_label=t("copilot.stop_reading"),
    )

    if isinstance(event, dict):
        _handle_event(event, df)
