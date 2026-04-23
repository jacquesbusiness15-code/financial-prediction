"""Claude API wrapper for the Financial Co-Pilot.

Two modes:
  * explain_drivers(context): structured explanation + actions for one anomaly
  * chat(messages, context): free-form Q&A over the filtered KPI slice

Uses prompt caching on the system prompt + the (large) JSON data block so
repeated calls stay cheap and fast during the demo.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

try:
    from anthropic import Anthropic
except ImportError:  # graceful fallback: UI can still render charts
    Anthropic = None  # type: ignore


MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a financial controller co-pilot for WISAG Facility Services.

CONTEXT
Contribution Margin (DB = Deckungsbeitrag) is the key steering metric.
Managers spend ~200h/month manually investigating WHY margins shift.
Your job is to translate the supplied numbers into decision-ready insight.

ANOMALY TAXONOMY — always classify the situation into one of:
  A. **Operational deterioration** — labor cost overrun, productivity drop,
     absence spike, subcontractor escalation, onboarding/training surge.
     This is what managers can *act on*.
  B. **Data artifact** — accounting accrual, billing reversal, one-off
     adjustment, contract start/end effect. This is NOT an operational
     problem — flag it as such and recommend validation with controlling,
     not operational action.
Name the category explicitly in your response. If labor_ratio > 1.0,
state plainly: "Labor costs exceeded revenue this month." That single
fact is the most important thing a manager needs to hear.

STRICT RULES
1. Every € figure you cite MUST appear in the JSON context. Never invent numbers.
2. If a driver is labeled "Unexplained residual", disclose it — don't force a cause.
3. Distinguish FACT (driver deltas, KPIs) from HYPOTHESIS (operational root cause).
   Use "likely" / "suggests" for hypotheses.
4. Be concise: business German-English, not academic. Bullets beat paragraphs.
5. Recommended actions must be concrete and tied to the top 2 drivers — no platitudes.
6. If the month appears to be a data artifact (huge revenue vs trend, massive
   positive CM that breaks the pattern), do NOT recommend operational action —
   recommend validation with controlling.

OUTPUT FORMAT (use these exact markdown headings):
### Classification
**Operational deterioration** or **Data artifact** — one sentence.

### Why the margin moved
(3–4 bullets, each citing a specific driver € from the context)

### Top 3 likely root causes
1. ... (operational, ranked most-likely first)
2. ...
3. ...

### Recommended actions
- ... (specific, owner/timeframe if derivable)
- ...

### Additional KPIs that would sharpen this diagnosis
- ... (name 1–3 data points not currently in the context)"""


@dataclass
class ExplainContext:
    cost_center: str
    region: str
    service: str
    period: str               # ISO date string
    baseline_label: str       # "prior month" | "prior year" | "plan"
    cm_current_eur: float
    cm_baseline_eur: float
    cm_delta_eur: float
    cm_current_pct: float | None
    drivers: list[dict]       # [{name, kind, delta_eur, current, baseline}]
    kpis_vs_peers: list[dict] # benchmarks.kpi_vs_peers rows
    labor_ratio: float | None = None
    hour_variance: float | None = None
    dq_accrual_flag: bool = False
    manager_comment: str | None = None

    def as_payload(self) -> dict:
        return {
            "cost_center": self.cost_center,
            "region": self.region,
            "service": self.service,
            "period": self.period,
            "baseline": self.baseline_label,
            "contribution_margin": {
                "current_eur": round(self.cm_current_eur, 2),
                "baseline_eur": round(self.cm_baseline_eur, 2),
                "delta_eur": round(self.cm_delta_eur, 2),
                "current_pct": (None if self.cm_current_pct is None
                                else round(self.cm_current_pct * 100, 2)),
            },
            "ranked_drivers": [
                {"name": d["name"], "kind": d["kind"],
                 "delta_eur": round(d["delta_eur"], 2),
                 "current_eur": round(d["current"], 2),
                 "baseline_eur": round(d["baseline"], 2)}
                for d in self.drivers
            ],
            "headline_kpis": {
                "labor_ratio": (None if self.labor_ratio is None
                                else round(self.labor_ratio * 100, 1)),
                "hour_variance_h": (None if self.hour_variance is None
                                    else round(self.hour_variance, 0)),
                "data_quality_accrual_flagged": self.dq_accrual_flag,
            },
            "kpis_vs_regional_peers": self.kpis_vs_peers,
            "manager_comment": self.manager_comment or "",
        }


def _client(api_key: str | None = None) -> "Anthropic | None":
    if Anthropic is None:
        return None
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    return Anthropic(api_key=key)


def explain_drivers(ctx: ExplainContext, api_key: str | None = None) -> str:
    """Return a markdown explanation; falls back to a template if API unavailable."""
    client = _client(api_key)
    if client is None:
        return _fallback_explanation(ctx)

    payload = ctx.as_payload()
    user_msg = (
        "Analyse this Contribution Margin shift and respond in the required format.\n\n"
        "```json\n" + json.dumps(payload, indent=2, default=str) + "\n```"
    )
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=900,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_msg}],
        )
        return resp.content[0].text
    except Exception as e:  # noqa: BLE001
        return _fallback_explanation(ctx, error=str(e))


def chat(messages: list[dict], data_context: dict,
         api_key: str | None = None) -> str:
    """Free-form Q&A with the data slice cached in the system turn."""
    client = _client(api_key)
    if client is None:
        return ("⚠️ Claude API not configured — set ANTHROPIC_API_KEY in .env. "
                "Charts and drivers work without it.")
    sys_block = [
        {"type": "text", "text": SYSTEM_PROMPT,
         "cache_control": {"type": "ephemeral"}},
        {"type": "text",
         "text": "CURRENT DATA CONTEXT (filtered slice):\n```json\n"
                 + json.dumps(data_context, indent=2, default=str)
                 + "\n```",
         "cache_control": {"type": "ephemeral"}},
    ]
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=900, system=sys_block, messages=messages,
        )
        return resp.content[0].text
    except Exception as e:  # noqa: BLE001
        return f"⚠️ API error: {e}"


def _fallback_explanation(ctx: ExplainContext, error: str | None = None) -> str:
    """Template-based explanation so the UI degrades gracefully."""
    top = ctx.drivers[:3]
    lines = []
    if error:
        lines.append(f"*(Claude API unavailable — template fallback shown. {error})*\n")
    lines.append("### Why the margin moved")
    for d in top:
        direction = "boosted" if d["delta_eur"] > 0 else "reduced"
        lines.append(f"- **{d['name']}** {direction} CM by "
                     f"{d['delta_eur']:+,.0f}€ "
                     f"({d['baseline']:.0f}€ → {d['current']:.0f}€).")
    lines.append("\n### Top 3 likely root causes")
    lines.append("1. Operational review needed on the top driver above.")
    lines.append("2. Review staffing / absence patterns against plan.")
    lines.append("3. Check subcontractor usage vs. planned ratio.")
    lines.append("\n### Recommended actions")
    lines.append("- Investigate the largest negative driver with the operations lead.")
    lines.append("- Cross-check with regional peers for the same service line.")
    lines.append("\n### Additional KPIs that would sharpen this diagnosis")
    lines.append("- Headcount turnover, sick-day distribution, customer-facing service quality tickets.")
    return "\n".join(lines)
