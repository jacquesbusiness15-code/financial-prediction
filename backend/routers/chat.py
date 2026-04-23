"""POST /datasets/{id}/chat — SSE-streamed Claude Q&A over the filtered slice."""
from __future__ import annotations

import json
import os
from typing import AsyncIterator

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.deps import get_dataset
from backend.schemas import ChatRequest
from backend.services.dataset_store import DatasetEntry
from backend.services.filters import apply_filters
from src.llm_copilot import MODEL, SYSTEM_PROMPT

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore

router = APIRouter()


def _sse(event: str | None, data: dict | str) -> bytes:
    body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {body}\n\n".encode("utf-8")


def _safe(v):
    if v is None:
        return None
    try:
        f = float(v)
        return None if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return v


def _build_context(df: pd.DataFrame) -> dict:
    """Compact JSON digest of the filtered slice — mirrors pages/4_Copilot_Chat.py."""
    if df.empty:
        return {"empty": True}
    ctx: dict = {}
    if "period" in df.columns and df["period"].notna().any():
        ctx["period_range"] = {
            "from": df["period"].min().strftime("%Y-%m"),
            "to": df["period"].max().strftime("%Y-%m"),
        }
    ctx["totals"] = {
        "revenue_eur": _safe(df.get("revenue_total", pd.Series([0])).sum()),
        "cm_db_eur": _safe(df.get("cm_db", pd.Series([0])).sum()),
        "cm_planned_eur": _safe(df.get("cm_planned", pd.Series([0])).sum()),
        "cost_centers": int(df["cost_center_id"].nunique()) if "cost_center_id" in df.columns else 0,
    }
    if "region" in df.columns:
        by_region = (df.groupby("region")
                       .agg(revenue_eur=("revenue_total", "sum"),
                            cm_db_eur=("cm_db", "sum"))
                       .reset_index())
        ctx["by_region"] = [
            {"region": r["region"],
             "revenue_eur": _safe(r["revenue_eur"]),
             "cm_db_eur": _safe(r["cm_db_eur"])}
            for _, r in by_region.iterrows()
        ]
    if "cm_vs_plan_delta" in df.columns and "cost_center_id" in df.columns:
        bottom = (df.groupby("cost_center_id")
                    .agg(cost_center_name=("cost_center_name", "first")
                         if "cost_center_name" in df.columns else ("cost_center_id", "first"),
                         region=("region", "first") if "region" in df.columns else ("cost_center_id", "first"),
                         cm_vs_plan_delta=("cm_vs_plan_delta", "sum"))
                    .nsmallest(10, "cm_vs_plan_delta"))
        ctx["worst_plan_gap_cost_centers"] = [
            {"cost_center_id": cc_id, "name": r["cost_center_name"],
             "region": r["region"], "cm_vs_plan_delta_eur": _safe(r["cm_vs_plan_delta"])}
            for cc_id, r in bottom.iterrows()
        ]
    return ctx


async def _stream_chat(messages: list[dict], data_context: dict) -> AsyncIterator[bytes]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if Anthropic is None or not api_key:
        yield _sse("delta", {"text": (
            "⚠️ Claude API not configured on the backend — set ANTHROPIC_API_KEY. "
            "Charts and drivers work without it."
        )})
        yield _sse("done", {"ok": True})
        return

    client = Anthropic(api_key=api_key)
    sys_block = [
        {"type": "text", "text": SYSTEM_PROMPT,
         "cache_control": {"type": "ephemeral"}},
        {"type": "text",
         "text": ("CURRENT DATA CONTEXT (filtered slice):\n```json\n"
                  + json.dumps(data_context, indent=2, default=str)
                  + "\n```"),
         "cache_control": {"type": "ephemeral"}},
    ]

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=900,
            system=sys_block,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield _sse("delta", {"text": text})
    except Exception as e:  # noqa: BLE001
        yield _sse("error", {"message": f"API error: {e}"})
        return
    yield _sse("done", {"ok": True})


@router.post("/datasets/{dataset_id}/chat")
async def post_chat(
    req: ChatRequest,
    entry: DatasetEntry = Depends(get_dataset),
    regions: list[str] | None = Query(default=None),
    services: list[str] | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
):
    df = apply_filters(entry.df, regions, services, start, end)
    ctx = _build_context(df)
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    return StreamingResponse(
        _stream_chat(messages, ctx),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
