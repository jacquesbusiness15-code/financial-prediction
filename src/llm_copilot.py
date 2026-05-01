"""Claude API wrapper for the Financial Co-Pilot."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore


MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a financial controller co-pilot for WISAG Facility Services.

LANGUAGE
Reply in the language of the question. If the user wrote German, answer in
German. The product UI is German-first.

GLOSSARY (German / English equivalents — apply LITERALLY, do not improvise)
  - Umsatz / Revenue            = revenue_total_eur (Gesamterlöse je Vertrag).
  - Kosten / Cost / Gesamtkosten = cost_total_eur = revenue_total_eur - cm_db_eur.
                                  Kosten ist NICHT der Deckungsbeitrag und auch
                                  NICHT der negative Deckungsbeitrag. Eine
                                  profitable Kostenstelle mit hohem Umsatz
                                  hat in der Regel die höchsten Kosten.
  - Deckungsbeitrag / DB / Marge / Margin
                                = cm_db_eur (Umsatz minus variable Kosten);
                                  kann positiv oder negativ sein.
  - Verlust / Loss              = cm_db_eur < 0. "Höchster Verlust" bedeutet
                                  niedrigster (negativster) cm_db_eur.
  - Personalkosten / Labor cost = labor_cost_total (Untermenge der Kosten).

RANKING DISCIPLINE
When the user asks for the contract with the highest/lowest X:
  - "höchste Kosten" / "highest cost"     → sort by cost_total_eur DESC. Use
                                            top_by_cost from the context.
  - "höchster Umsatz" / "highest revenue" → sort by revenue_total_eur DESC.
                                            Use top_by_revenue.
  - "höchste Marge" / "highest margin"    → sort by cm_db_eur DESC. Use
                                            best_contracts.
  - "höchster Verlust" / "biggest loss"   → sort by cm_db_eur ASC (most
                                            negative first). Use top_by_loss.
If the relevant pre-sorted list is missing or empty, say so plainly — do not
guess and do not substitute another list.

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
- ... (name 1–3 data points not currently in the context; if the JSON
  field `detected_kpi_gaps` is non-empty, prefer citing those before
  suggesting new ones — they are already computed from missing columns)"""

_NO_KEY_MSG = ("Claude API not configured — set ANTHROPIC_API_KEY in .env. "
               "Charts and drivers work without it.")


@dataclass
class ExplainContext:
    cost_center: str
    region: str
    service: str
    period: str
    baseline_label: str
    cm_current_eur: float
    cm_baseline_eur: float
    cm_delta_eur: float
    cm_current_pct: float | None
    drivers: list[dict]
    kpis_vs_peers: list[dict]
    labor_ratio: float | None = None
    hour_variance: float | None = None
    dq_accrual_flag: bool = False
    manager_comment: str | None = None
    # Data points the rule engine identified as missing for a sharper
    # diagnosis (each item: {"id", "title", "reason"}). Fed to the AI
    # so it cites these instead of hallucinating new ones.
    kpi_gaps: list[dict] | None = None

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
            "detected_kpi_gaps": list(self.kpi_gaps or []),
            "manager_comment": self.manager_comment or "",
        }


def _client(api_key: str | None = None) -> "Anthropic | None":
    if Anthropic is None:
        return None
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    return Anthropic(api_key=key)


def _cached_system(extra_text: str | None = None) -> list[dict]:
    blocks = [{"type": "text", "text": SYSTEM_PROMPT,
               "cache_control": {"type": "ephemeral"}}]
    if extra_text:
        blocks.append({"type": "text", "text": extra_text,
                       "cache_control": {"type": "ephemeral"}})
    return blocks


def _call(client: "Anthropic", system: list[dict], messages: list[dict]) -> str:
    resp = client.messages.create(
        model=MODEL, max_tokens=900, system=system, messages=messages,
    )
    return resp.content[0].text


def explain_drivers(ctx: ExplainContext, api_key: str | None = None) -> str:
    client = _client(api_key)
    if client is None:
        return _fallback_explanation(ctx)

    user_msg = (
        "Analyse this Contribution Margin shift and respond in the required format.\n\n"
        "```json\n" + json.dumps(ctx.as_payload(), indent=2, default=str) + "\n```"
    )
    try:
        return _call(client, _cached_system(),
                     [{"role": "user", "content": user_msg}])
    except Exception as e:  # noqa: BLE001 - anthropic raises many subclasses; UI must degrade
        return _fallback_explanation(ctx, error=str(e))


def chat(messages: list[dict], data_context: dict,
         api_key: str | None = None) -> str:
    client = _client(api_key)
    if client is None:
        return _NO_KEY_MSG
    ctx_block = ("CURRENT DATA CONTEXT (filtered slice):\n```json\n"
                 + json.dumps(data_context, indent=2, default=str)
                 + "\n```")
    try:
        return _call(client, _cached_system(ctx_block), messages)
    except Exception as e:  # noqa: BLE001 - UI must degrade on any API failure
        return f"API error: {e}"


_SOLUTION_FINDER_SYSTEM = """You are decorating a deterministic list of
recommended actions produced by a rule engine. Your job is NOT to invent
new actions or new euro figures. For each supplied action, produce:
(a) one-sentence, customer-ready talking point,
(b) a flagged risk or counter-argument,
(c) prerequisites.
If the evidence for an action looks weak (severity just above the floor,
cohort scope "global", confidence "low"), say so plainly. Be concise,
business German-English, bullets beat paragraphs. Never cite a euro
figure that is not present in the supplied JSON."""


def suggest_actions(
    metrics,  # ContractMetrics
    latest_row,  # pd.Series
    cohort,  # CohortStats
    recommendations,  # list[ActionRecommendation]
    api_key: str | None = None,
) -> str:
    """Decorate rule-based recommendations with narrative talking points."""
    from src.solution_catalog import ACTIONS  # local import to avoid cycles

    if not recommendations:
        return ""

    catalog_summary = {
        a.id: {
            "title_key": a.i18n_title_key,
            "applicable_issues": list(a.applicable_issues),
            "owner_role": a.owner_role,
            "typical_weeks": a.typical_weeks,
            "effort_score": a.effort_score,
            "category": a.category,
        } for a in ACTIONS.values()
    }

    context = {
        "cost_center": str(metrics.base.cost_center_id),
        "customer_name": metrics.base.customer_name,
        "region": metrics.base.region,
        "overall_score": metrics.overall_score,
        "cohort": {"scope": cohort.scope, "size": cohort.size},
        "recommendations": [
            {
                "action_id": r.action_id,
                "matched_issues": list(r.matched_issues),
                "estimated_impact_eur_month": round(r.estimated_impact_eur_month, 0),
                "confidence": round(r.confidence, 2),
                "owner_role": r.owner_role,
                "timeframe_weeks": r.timeframe_weeks,
                "category": r.category,
            } for r in recommendations
        ],
    }

    client = _client(api_key)
    if client is None:
        return _fallback_suggest_actions(recommendations)

    catalog_block = ("ACTION CATALOG (static, cacheable):\n```json\n"
                     + json.dumps(catalog_summary, indent=2) + "\n```")
    system: list[dict] = [
        {"type": "text", "text": _SOLUTION_FINDER_SYSTEM,
         "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": catalog_block,
         "cache_control": {"type": "ephemeral"}},
    ]
    user_msg = ("Decorate these rule-based recommendations for the listed "
                "cost center. Do NOT invent new actions or numbers.\n\n"
                "```json\n" + json.dumps(context, indent=2, default=str) + "\n```")
    try:
        return _call(client, system, [{"role": "user", "content": user_msg}])
    except Exception as e:  # noqa: BLE001 - UI must degrade
        return _fallback_suggest_actions(recommendations, error=str(e))


def _fallback_suggest_actions(recommendations, error: str | None = None) -> str:
    from src.solution_catalog import ACTIONS  # local import to avoid cycles

    lines: list[str] = []
    if error:
        lines.append(f"*(Claude API unavailable - template fallback shown. {error})*\n")
    for rec in recommendations:
        action = ACTIONS.get(rec.action_id)
        if action is None:
            continue
        lines.append(f"- **{action.i18n_title_key}** ({action.owner_role}, "
                     f"{action.typical_weeks}w)")
    return "\n".join(lines) if lines else ""


def _fallback_explanation(ctx: ExplainContext, error: str | None = None) -> str:
    lines = []
    if error:
        lines.append(f"*(Claude API unavailable — template fallback shown. {error})*\n")
    lines.append("### Why the margin moved")
    for d in ctx.drivers[:3]:
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
    if ctx.kpi_gaps:
        for gap in ctx.kpi_gaps:
            title = gap.get("title") or gap.get("id", "")
            reason = gap.get("reason", "")
            lines.append(f"- **{title}** — {reason}".rstrip(" —"))
    else:
        lines.append("- Headcount turnover, sick-day distribution, customer-facing service quality tickets.")
    return "\n".join(lines)
