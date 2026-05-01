"""Registry of operational actions the Solution Finder may recommend.

Each action is declarative data: ids, i18n keys, which issue codes it
addresses, which impact formula to call, who typically owns it, and the
rough timeframe. The rule engine in solution_finder consumes this
registry read-only. Keeping the catalog as a Python literal (not JSON)
preserves type safety and keeps everything greppable.
"""
from __future__ import annotations

from dataclasses import dataclass, field


OWNER_OPS = "ops"
OWNER_SALES = "sales"
OWNER_REGIONAL_MANAGER = "regional_manager"

CATEGORY_COST = "cost"
CATEGORY_REVENUE = "revenue"
CATEGORY_SCOPE = "scope"
CATEGORY_RETENTION = "retention"
CATEGORY_QUALITY = "quality"


@dataclass(frozen=True)
class ActionDefinition:
    id: str
    i18n_title_key: str
    i18n_desc_key: str
    applicable_issues: tuple[str, ...]
    impact_formula_id: str
    owner_role: str
    typical_weeks: int
    effort_score: int  # 1 (quick) .. 5 (major)
    category: str
    mutually_exclusive_with: tuple[str, ...] = field(default_factory=tuple)


ACTIONS: dict[str, ActionDefinition] = {
    "renegotiate_price": ActionDefinition(
        id="renegotiate_price",
        i18n_title_key="action.renegotiate_price.title",
        i18n_desc_key="action.renegotiate_price.description",
        applicable_issues=("plan_gap_widening", "revenue_shortfall"),
        impact_formula_id="renegotiate_price",
        owner_role=OWNER_SALES,
        typical_weeks=8,
        effort_score=3,
        category=CATEGORY_REVENUE,
    ),
    "reprice_hourly": ActionDefinition(
        id="reprice_hourly",
        i18n_title_key="action.reprice_hourly.title",
        i18n_desc_key="action.reprice_hourly.description",
        applicable_issues=("labor_overrun", "revenue_shortfall"),
        impact_formula_id="reprice_hourly",
        owner_role=OWNER_SALES,
        typical_weeks=6,
        effort_score=3,
        category=CATEGORY_REVENUE,
    ),
    "audit_subcontractors": ActionDefinition(
        id="audit_subcontractors",
        i18n_title_key="action.audit_subcontractors.title",
        i18n_desc_key="action.audit_subcontractors.description",
        applicable_issues=("subcontractor_creep",),
        impact_formula_id="reduce_subcontractor_share",
        owner_role=OWNER_OPS,
        typical_weeks=4,
        effort_score=2,
        category=CATEGORY_COST,
    ),
    "reduce_subcontractor_share": ActionDefinition(
        id="reduce_subcontractor_share",
        i18n_title_key="action.reduce_subcontractor_share.title",
        i18n_desc_key="action.reduce_subcontractor_share.description",
        applicable_issues=("subcontractor_creep",),
        impact_formula_id="reduce_subcontractor_share",
        owner_role=OWNER_OPS,
        typical_weeks=10,
        effort_score=4,
        category=CATEGORY_COST,
    ),
    "labor_cost_audit": ActionDefinition(
        id="labor_cost_audit",
        i18n_title_key="action.labor_cost_audit.title",
        i18n_desc_key="action.labor_cost_audit.description",
        applicable_issues=("labor_overrun",),
        impact_formula_id="labor_cost_audit",
        owner_role=OWNER_OPS,
        typical_weeks=4,
        effort_score=2,
        category=CATEGORY_COST,
    ),
    "productivity_improvement": ActionDefinition(
        id="productivity_improvement",
        i18n_title_key="action.productivity_improvement.title",
        i18n_desc_key="action.productivity_improvement.description",
        applicable_issues=("productivity_drop",),
        impact_formula_id="productivity_improvement",
        owner_role=OWNER_OPS,
        typical_weeks=8,
        effort_score=3,
        category=CATEGORY_COST,
    ),
    "absence_intervention": ActionDefinition(
        id="absence_intervention",
        i18n_title_key="action.absence_intervention.title",
        i18n_desc_key="action.absence_intervention.description",
        applicable_issues=("absence_spike",),
        impact_formula_id="absence_intervention",
        owner_role=OWNER_OPS,
        typical_weeks=6,
        effort_score=3,
        category=CATEGORY_COST,
    ),
    "reduce_scope": ActionDefinition(
        id="reduce_scope",
        i18n_title_key="action.reduce_scope.title",
        i18n_desc_key="action.reduce_scope.description",
        applicable_issues=("sustained_loss",),
        impact_formula_id="stop_bleed",
        owner_role=OWNER_REGIONAL_MANAGER,
        typical_weeks=12,
        effort_score=4,
        category=CATEGORY_SCOPE,
        mutually_exclusive_with=("terminate_contract",),
    ),
    "terminate_contract": ActionDefinition(
        id="terminate_contract",
        i18n_title_key="action.terminate_contract.title",
        i18n_desc_key="action.terminate_contract.description",
        applicable_issues=("sustained_loss",),
        impact_formula_id="stop_bleed",
        owner_role=OWNER_REGIONAL_MANAGER,
        typical_weeks=16,
        effort_score=5,
        category=CATEGORY_SCOPE,
        mutually_exclusive_with=("reduce_scope",),
    ),
    "renewal_outreach": ActionDefinition(
        id="renewal_outreach",
        i18n_title_key="action.renewal_outreach.title",
        i18n_desc_key="action.renewal_outreach.description",
        applicable_issues=("renewal_risk",),
        impact_formula_id="renewal_outreach",
        owner_role=OWNER_SALES,
        typical_weeks=4,
        effort_score=2,
        category=CATEGORY_RETENTION,
    ),
    "training_investment": ActionDefinition(
        id="training_investment",
        i18n_title_key="action.training_investment.title",
        i18n_desc_key="action.training_investment.description",
        applicable_issues=("productivity_drop",),
        impact_formula_id="training_investment",
        owner_role=OWNER_OPS,
        typical_weeks=10,
        effort_score=3,
        category=CATEGORY_COST,
    ),
    "quality_remediation": ActionDefinition(
        id="quality_remediation",
        i18n_title_key="action.quality_remediation.title",
        i18n_desc_key="action.quality_remediation.description",
        applicable_issues=("quality_gap",),
        impact_formula_id="quality_remediation",
        owner_role=OWNER_OPS,
        typical_weeks=6,
        effort_score=3,
        category=CATEGORY_QUALITY,
    ),
}


ALL_ISSUE_CODES: frozenset[str] = frozenset(
    code for a in ACTIONS.values() for code in a.applicable_issues
)


def applicable_for(issue_code: str) -> list[ActionDefinition]:
    return [a for a in ACTIONS.values() if issue_code in a.applicable_issues]


def get(action_id: str) -> ActionDefinition:
    return ACTIONS[action_id]
