"""Rule engine that turns diagnostics into prescriptive actions.

Consumes read-only outputs of ``src.contract_metrics.compute_metrics``,
``src.early_warning.detect`` and an enriched latest-row from
``src.features.enrich``. Emits a ranked list of ``ActionRecommendation``
objects per contract. Deterministic; no LLM calls here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import math
import pandas as pd

from src.benchmarks import CohortStats
from src.contract_metrics import ContractMetrics
from src.cost_drivers import CostDriver, identify_drivers_for_issue
from src.solution_catalog import ACTIONS, ActionDefinition
from src.solution_impact import IMPACT_REVENUE_CAP_SHARE, simulate


# Filtering floors keep low-signal noise off the recommendations list.
# The severity floor is the primary filter. The euro-impact floor is
# disabled by default so the feature works on anonymised / scaled data;
# raise it from the caller (e.g. Streamlit UI) when the numbers are
# known to be nominal euros.
MIN_ISSUE_SEVERITY = 0.20
MIN_IMPACT_EUR_MONTH = 0.0
DEFAULT_TOP_N = 3
MAX_TOP_N = 5

# Rule thresholds.
LABOR_OVERRUN_PP = 0.05        # labor_ratio above plan_labor_cost_ratio by >= 5pp
SUBC_CREEP_PP = 0.05           # subcontractor_share above plan ratio by >= 5pp
PRODUCTIVITY_DROP_PP = 0.10    # productivity below cohort median by >= 10pp
ABSENCE_SPIKE_PP = 0.02        # absence above cohort median by >= 2pp
QUALITY_GAP_PP = 0.02          # actual-target quality below target by >= 2pp
PLAN_GAP_EUR = 2_000.0         # cm_planned - cm_db >= 2000 EUR
RENEWAL_WINDOW_DAYS = 120      # renewal outreach if contract ends within 120 days
SUSTAINED_LOSS_MIN_MONTHS = 2  # 2+ consecutive negative months counts as sustained


@dataclass(frozen=True)
class Issue:
    code: str
    severity: float  # 0..1
    evidence: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ActionRecommendation:
    action_id: str
    matched_issues: tuple[str, ...]
    estimated_impact_eur_month: float
    confidence: float
    owner_role: str
    timeframe_weeks: int
    quick_win_score: float
    category: str
    drivers: tuple[CostDriver, ...] = ()


# ---------------------------------------------------------------------------
# Diagnostics: extract issues from existing signals (do not recompute metrics)
# ---------------------------------------------------------------------------

def _clamp01(x: float) -> float:
    if x is None or math.isnan(x):
        return 0.0
    return max(0.0, min(1.0, float(x)))


def _num(row: pd.Series, key: str, default: float = 0.0) -> float:
    v = row.get(key, default)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(v):
        return float(default)
    return v


def _sev_from_ratio(actual: float, threshold: float, scale: float) -> float:
    excess = actual - threshold
    if excess <= 0:
        return 0.0
    return _clamp01(excess / scale)


def diagnose(
    metrics: ContractMetrics,
    latest_row: pd.Series,
    history: pd.DataFrame,
    warnings: pd.DataFrame,
    cohort: CohortStats,
) -> list[Issue]:
    """Emit issue codes derived from metrics, enriched row and warnings."""
    issues: list[Issue] = []

    labor_ratio = _num(latest_row, "labor_ratio")
    plan_labor = _num(latest_row, "plan_labor_cost_ratio")
    if plan_labor > 0 and labor_ratio > 0:
        sev = _sev_from_ratio(labor_ratio, plan_labor + LABOR_OVERRUN_PP, 0.25)
        if sev > 0:
            issues.append(Issue("labor_overrun", sev,
                                {"labor_ratio": labor_ratio,
                                 "plan_labor_cost_ratio": plan_labor,
                                 "delta_pp": labor_ratio - plan_labor}))

    subc_share = _num(latest_row, "subcontractor_share")
    plan_subc = _num(latest_row, "plan_subcontractor_ratio")
    if plan_subc > 0 and subc_share > 0:
        sev = _sev_from_ratio(subc_share, plan_subc + SUBC_CREEP_PP, 0.25)
        if sev > 0:
            issues.append(Issue("subcontractor_creep", sev,
                                {"subcontractor_share": subc_share,
                                 "plan_subcontractor_ratio": plan_subc,
                                 "delta_pp": subc_share - plan_subc}))

    prod = _num(latest_row, "productivity_ratio")
    peer_prod = cohort.medians.get("productivity_ratio")
    if peer_prod is not None and prod > 0:
        sev = _sev_from_ratio(float(peer_prod) - prod, PRODUCTIVITY_DROP_PP, 0.25)
        if sev > 0:
            issues.append(Issue("productivity_drop", sev,
                                {"productivity_ratio": prod,
                                 "peer_median": float(peer_prod),
                                 "delta_pp": prod - float(peer_prod)}))

    absence = _num(latest_row, "absence_rate")
    peer_abs = cohort.medians.get("absence_rate")
    if peer_abs is not None and absence > 0:
        sev = _sev_from_ratio(absence - float(peer_abs), ABSENCE_SPIKE_PP, 0.10)
        if sev > 0:
            issues.append(Issue("absence_spike", sev,
                                {"absence_rate": absence,
                                 "peer_median": float(peer_abs),
                                 "delta_pp": absence - float(peer_abs)}))

    quality_gap = _num(latest_row, "quality_gap")
    if quality_gap < 0:
        sev = _sev_from_ratio(-quality_gap, QUALITY_GAP_PP, 0.10)
        if sev > 0:
            issues.append(Issue("quality_gap", sev,
                                {"quality_gap": quality_gap}))

    cm_planned = _num(latest_row, "cm_planned")
    cm_db = _num(latest_row, "cm_db")
    plan_gap_eur = cm_planned - cm_db
    if plan_gap_eur >= PLAN_GAP_EUR:
        revenue = max(_num(latest_row, "revenue_total"), 1.0)
        sev = _clamp01(plan_gap_eur / max(abs(cm_planned), revenue * 0.2))
        if sev > 0:
            issues.append(Issue("plan_gap_widening", sev,
                                {"cm_planned": cm_planned,
                                 "cm_db": cm_db,
                                 "gap_eur": plan_gap_eur}))

    # Revenue shortfall: lower revenue than cohort median relative to planned CM.
    revenue_shortfall = cm_planned > 0 and cm_db < 0
    if revenue_shortfall:
        sev = _clamp01(-cm_db / max(cm_planned, 1.0))
        if sev > 0:
            issues.append(Issue("revenue_shortfall", sev,
                                {"cm_planned": cm_planned, "cm_db": cm_db}))

    # Sustained loss - two or more consecutive negative months of cm_db.
    cm_series = _tail_cm_series(history)
    consec = _consecutive_negative_tail(cm_series)
    if consec >= SUSTAINED_LOSS_MIN_MONTHS:
        sev = _clamp01(consec / 6.0)
        issues.append(Issue("sustained_loss", sev,
                            {"consecutive_negative_months": consec,
                             "latest_cm_db": cm_db}))

    # Renewal risk - honour the early_warning output if present, else compute.
    renewal_days = _days_to_contract_end(latest_row)
    if renewal_days is not None and 0 <= renewal_days <= RENEWAL_WINDOW_DAYS:
        sev = _clamp01(1.0 - renewal_days / RENEWAL_WINDOW_DAYS)
        issues.append(Issue("renewal_risk", sev,
                            {"days_to_end": renewal_days}))

    # Augment severity with early_warning signals (same contract) if available.
    if warnings is not None and not warnings.empty:
        try:
            cc = str(metrics.base.cost_center_id)
            mine = warnings[warnings["cost_center_id"].astype(str) == cc]
        except (KeyError, AttributeError):
            mine = pd.DataFrame()
        if not mine.empty:
            issues = _boost_with_warnings(issues, mine)

    # Deduplicate by code, keeping the highest severity version.
    by_code: dict[str, Issue] = {}
    for issue in issues:
        prior = by_code.get(issue.code)
        if prior is None or issue.severity > prior.severity:
            by_code[issue.code] = issue
    return sorted(by_code.values(), key=lambda i: i.severity, reverse=True)


def _tail_cm_series(history: pd.DataFrame) -> pd.Series:
    if history is None or history.empty or "cm_db" not in history.columns:
        return pd.Series(dtype="float64")
    if "period" in history.columns:
        history = history.sort_values("period")
    return pd.to_numeric(history["cm_db"], errors="coerce").dropna()


def _consecutive_negative_tail(series: pd.Series) -> int:
    count = 0
    for value in reversed(series.tolist()):
        if value is None or math.isnan(value):
            break
        if value < 0:
            count += 1
        else:
            break
    return count


def _days_to_contract_end(row: pd.Series) -> Optional[int]:
    end = row.get("contract_end")
    period = row.get("period")
    if pd.isna(end) or pd.isna(period):
        return None
    try:
        delta = (pd.Timestamp(end) - pd.Timestamp(period)).days
    except (TypeError, ValueError):
        return None
    return int(delta)


_WARNING_TO_ISSUE = {
    "Declining CM trend": "plan_gap_widening",
    "Absence spike": "absence_spike",
    "Productivity drop": "productivity_drop",
    "Subcontractor creep": "subcontractor_creep",
    "Contract renewal risk": "renewal_risk",
    "Plan gap widening": "plan_gap_widening",
}

_SEVERITY_BOOST = {"high": 0.30, "medium": 0.15, "low": 0.05}


def _boost_with_warnings(issues: list[Issue], warnings: pd.DataFrame) -> list[Issue]:
    boosted: list[Issue] = list(issues)
    by_code: dict[str, int] = {issue.code: i for i, issue in enumerate(boosted)}
    for _, warning in warnings.iterrows():
        code = _WARNING_TO_ISSUE.get(str(warning.get("signal")))
        if code is None:
            continue
        boost = _SEVERITY_BOOST.get(str(warning.get("severity", "low")), 0.0)
        if code in by_code:
            idx = by_code[code]
            cur = boosted[idx]
            boosted[idx] = Issue(cur.code, _clamp01(cur.severity + boost),
                                 {**cur.evidence, "warning": str(warning.get("detail"))})
        else:
            boosted.append(Issue(code, _clamp01(0.35 + boost),
                                 {"warning": str(warning.get("detail"))}))
            by_code[code] = len(boosted) - 1
    return boosted


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

def _confidence(issue_severity: float, cohort: CohortStats) -> float:
    return _clamp01(issue_severity * cohort.adequacy())


def _quick_win(impact_eur: float, effort: int) -> float:
    # Higher is better. Effort in [1..5] -> divisor in [1..5].
    return impact_eur / max(effort, 1)


def recommend(
    metrics: ContractMetrics,
    latest_row: pd.Series,
    history: pd.DataFrame,
    warnings: pd.DataFrame,
    cohort: CohortStats,
    top_n: int = DEFAULT_TOP_N,
    min_impact_eur: float = MIN_IMPACT_EUR_MONTH,
) -> list[ActionRecommendation]:
    """Return top ``top_n`` actions ranked by euro impact per unit of effort."""
    top_n = int(min(max(top_n, 1), MAX_TOP_N))
    issues = [i for i in diagnose(metrics, latest_row, history, warnings, cohort)
              if i.severity >= MIN_ISSUE_SEVERITY]
    if not issues:
        return []

    # Per-issue driver decomposition (done once per issue, reused below).
    drivers_by_issue: dict[str, tuple[CostDriver, ...]] = {
        issue.code: tuple(identify_drivers_for_issue(issue.code, latest_row, history))
        for issue in issues
    }
    revenue_cap = max(_num(latest_row, "revenue_total"), 0.0) * IMPACT_REVENUE_CAP_SHARE
    if revenue_cap <= 0:
        # Dormant / zero-revenue contracts: fall back to abs(cm_db) so the
        # driver-based impact remains grounded in observed losses.
        revenue_cap = abs(_num(latest_row, "cm_db"))

    best_by_action: dict[str, ActionRecommendation] = {}
    for issue in issues:
        issue_drivers = drivers_by_issue.get(issue.code, ())
        for action in _matching_actions(issue.code):
            formula_impact = simulate(action.impact_formula_id, latest_row, cohort)
            driver_impact = _driver_based_impact(action.impact_formula_id,
                                                 issue_drivers)
            if revenue_cap > 0 and action.category != "retention":
                driver_impact = min(driver_impact, revenue_cap)
            impact = max(formula_impact, driver_impact)
            if action.category != "retention" and impact < min_impact_eur:
                continue
            rec = ActionRecommendation(
                action_id=action.id,
                matched_issues=(issue.code,),
                estimated_impact_eur_month=impact,
                confidence=_confidence(issue.severity, cohort),
                owner_role=action.owner_role,
                timeframe_weeks=action.typical_weeks,
                quick_win_score=_quick_win(impact, action.effort_score),
                category=action.category,
                drivers=issue_drivers,
            )
            prior = best_by_action.get(action.id)
            if prior is None or rec.quick_win_score > prior.quick_win_score:
                merged_issues = tuple(sorted(set(
                    (prior.matched_issues if prior else ()) + rec.matched_issues)))
                merged_drivers = _merge_drivers(
                    prior.drivers if prior else (), rec.drivers)
                best_by_action[action.id] = ActionRecommendation(
                    action_id=rec.action_id,
                    matched_issues=merged_issues,
                    estimated_impact_eur_month=max(
                        rec.estimated_impact_eur_month,
                        prior.estimated_impact_eur_month if prior else 0.0,
                    ),
                    confidence=max(
                        rec.confidence,
                        prior.confidence if prior else 0.0,
                    ),
                    owner_role=rec.owner_role,
                    timeframe_weeks=rec.timeframe_weeks,
                    quick_win_score=rec.quick_win_score,
                    category=rec.category,
                    drivers=merged_drivers,
                )

    recs = list(best_by_action.values())
    recs = _resolve_mutual_exclusions(recs)
    recs.sort(key=lambda r: (-r.quick_win_score, -r.estimated_impact_eur_month,
                             r.timeframe_weeks))
    return recs[:top_n]


def _matching_actions(issue_code: str) -> list[ActionDefinition]:
    return [a for a in ACTIONS.values() if issue_code in a.applicable_issues]


# Fraction of the observed column overrun that is realistically recoverable
# by the matching action. Conservative by design; paired with the formula
# estimate via max() so the recommendation is never below either signal.
_DRIVER_RECOVERY_RATE: dict[str, float] = {
    "reduce_subcontractor_share": 0.50,
    "labor_cost_audit":           0.15,
    "productivity_improvement":   0.10,
    "absence_intervention":       0.40,
    "quality_remediation":        0.05,
    "renegotiate_price":          0.60,
    "stop_bleed":                 0.80,
    "reprice_hourly":             0.20,
    "training_investment":        0.10,
    "renewal_outreach":           0.0,
}


def _driver_based_impact(
    formula_id: str,
    drivers: tuple[CostDriver, ...],
) -> float:
    """Compute impact as a fraction of the observed MoM cost overrun.

    This grounds the euro estimate in actual cost movements rather than
    only the ratio-vs-plan gap, so scaled / anonymised datasets still
    produce meaningful numbers.
    """
    rate = _DRIVER_RECOVERY_RATE.get(formula_id, 0.0)
    if rate <= 0 or not drivers:
        return 0.0
    total_bad_delta = sum(max(d.delta_eur, 0.0) for d in drivers
                          if not d.column.startswith("revenue_"))
    total_bad_delta += sum(max(-d.delta_eur, 0.0) for d in drivers
                           if d.column.startswith("revenue_"))
    return float(total_bad_delta * rate)


def _merge_drivers(
    prior: tuple[CostDriver, ...],
    new: tuple[CostDriver, ...],
) -> tuple[CostDriver, ...]:
    seen: dict[str, CostDriver] = {d.column: d for d in prior}
    for d in new:
        if d.column not in seen or abs(d.delta_eur) > abs(seen[d.column].delta_eur):
            seen[d.column] = d
    return tuple(sorted(seen.values(), key=lambda d: abs(d.delta_eur), reverse=True))


def _resolve_mutual_exclusions(
    recs: list[ActionRecommendation],
) -> list[ActionRecommendation]:
    by_id = {r.action_id: r for r in recs}
    drop: set[str] = set()
    for rec in recs:
        action = ACTIONS.get(rec.action_id)
        if action is None:
            continue
        for other_id in action.mutually_exclusive_with:
            if other_id in by_id and other_id != rec.action_id:
                loser = (rec.action_id if by_id[other_id].quick_win_score
                         >= rec.quick_win_score else other_id)
                drop.add(loser)
    return [r for r in recs if r.action_id not in drop]
