"""POST /datasets/{id}/explain — SSE-streamed driver explanation."""
from __future__ import annotations

import json
import os
from typing import AsyncIterator

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.deps import get_dataset
from backend.schemas import ExplainRequest
from backend.services.dataset_store import DatasetEntry
from src.benchmarks import kpi_vs_peers
from src.drivers import build_plan_baseline, decompose, observed_delta, pick_baseline
from src.llm_copilot import MODEL, SYSTEM_PROMPT, ExplainContext, _fallback_explanation

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore

router = APIRouter()


def _sse(event: str | None, data: dict | str) -> bytes:
    body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {body}\n\n".encode("utf-8")


def _baseline_label(mode: str) -> str:
    return {"mom": "prior month", "yoy": "prior year", "plan": "plan"}.get(mode, mode)


def _build_context(df: pd.DataFrame, req: ExplainRequest) -> ExplainContext:
    cc_rows = df[df["cost_center_id"].astype(str) == str(req.cost_center_id)].sort_values("period")
    if cc_rows.empty:
        raise HTTPException(status_code=404,
                            detail=f"No rows for cost_center_id={req.cost_center_id}")
    try:
        current_period = pd.Timestamp(req.period)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Bad period: {e}") from e

    current_rows = cc_rows[cc_rows["period"] == current_period]
    if current_rows.empty:
        raise HTTPException(status_code=404,
                            detail=f"No row at period={req.period} for cc={req.cost_center_id}")
    current = current_rows.iloc[0]

    if req.baseline_mode == "plan":
        baseline = build_plan_baseline(current)
    else:
        baseline = pick_baseline(cc_rows, current_period, mode=req.baseline_mode)
        if baseline is None:
            raise HTTPException(status_code=404,
                                detail=f"No baseline for mode={req.baseline_mode}")

    drivers = decompose(current, baseline)
    obs = observed_delta(current, baseline)
    peers = kpi_vs_peers(df, current)
    peers_list = peers.to_dict("records") if not peers.empty else []

    return ExplainContext(
        cost_center=str(req.cost_center_id),
        region=str(current.get("region") or ""),
        service=str(current.get("service_type") or ""),
        period=current_period.strftime("%Y-%m-%d"),
        baseline_label=_baseline_label(req.baseline_mode),
        cm_current_eur=float(current.get("cm_db") or 0.0),
        cm_baseline_eur=float(baseline.get("cm_db") or 0.0),
        cm_delta_eur=float(obs or 0.0),
        cm_current_pct=(None if pd.isna(current.get("cm_db_pct"))
                        else float(current.get("cm_db_pct"))),
        drivers=[d.as_dict() for d in drivers],
        kpis_vs_peers=peers_list,
        labor_ratio=(None if pd.isna(current.get("labor_ratio"))
                     else float(current.get("labor_ratio"))),
        hour_variance=(None if pd.isna(current.get("hour_variance"))
                       else float(current.get("hour_variance"))),
        dq_accrual_flag=bool(current.get("dq_accrual_flag", False)),
        manager_comment=current.get("manager_comment") if isinstance(current.get("manager_comment"), str) else None,
    )


async def _stream_explain(ctx: ExplainContext) -> AsyncIterator[bytes]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if Anthropic is None or not api_key:
        # fallback to template, still stream as a single delta
        yield _sse("delta", {"text": _fallback_explanation(ctx)})
        yield _sse("done", {"ok": True})
        return

    payload = ctx.as_payload()
    user_msg = (
        "Analyse this Contribution Margin shift and respond in the required format.\n\n"
        "```json\n" + json.dumps(payload, indent=2, default=str) + "\n```"
    )
    client = Anthropic(api_key=api_key)
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=900,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield _sse("delta", {"text": text})
    except Exception as e:  # noqa: BLE001
        yield _sse("delta", {"text": _fallback_explanation(ctx, error=str(e))})
    yield _sse("done", {"ok": True})


@router.post("/datasets/{dataset_id}/explain")
async def post_explain(
    req: ExplainRequest,
    entry: DatasetEntry = Depends(get_dataset),
):
    ctx = _build_context(entry.df, req)
    return StreamingResponse(
        _stream_explain(ctx),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
