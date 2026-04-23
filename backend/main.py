"""FastAPI entry point for the WISAG Financial Co-Pilot backend.

Run with:
    uvicorn backend.main:app --reload

Wraps the existing pandas / scipy / Claude analytics in src/ behind REST and
Server-Sent-Event endpoints consumed by the Next.js frontend.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import (
    chat,
    datasets,
    deep_dive,
    explain,
    facility_overview,
    plan_vs_actual,
    portfolio,
    warnings,
)

load_dotenv()


def _allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(
    title="WISAG Financial Co-Pilot API",
    version="0.1.0",
    description="REST + SSE backend for the Next.js frontend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


API_PREFIX = "/api"
app.include_router(datasets.router, prefix=API_PREFIX, tags=["datasets"])
app.include_router(portfolio.router, prefix=API_PREFIX, tags=["portfolio"])
app.include_router(deep_dive.router, prefix=API_PREFIX, tags=["deep-dive"])
app.include_router(facility_overview.router, prefix=API_PREFIX, tags=["facility-overview"])
app.include_router(warnings.router, prefix=API_PREFIX, tags=["warnings"])
app.include_router(plan_vs_actual.router, prefix=API_PREFIX, tags=["plan-vs-actual"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["chat"])
app.include_router(explain.router, prefix=API_PREFIX, tags=["explain"])


# Serve the built Next.js static export (web/out) under /. The router
# includes above take precedence thanks to registration order, so /api/*
# still routes to the Python handlers. If the web/out directory does not
# exist yet (fresh checkout where `pnpm build` hasn't run), we simply skip
# mounting and uvicorn keeps running as an API-only server.
_WEB_OUT = Path(__file__).resolve().parent.parent / "web" / "out"
if _WEB_OUT.is_dir():
    app.mount("/", StaticFiles(directory=str(_WEB_OUT), html=True), name="web")
else:
    @app.get("/")
    def _no_web_bundle() -> dict:
        return {
            "status": "api-only",
            "hint": (
                "Static web bundle not built. Run `cd web && pnpm install && "
                "pnpm build`, then restart uvicorn to serve the UI from this "
                "same port."
            ),
        }
