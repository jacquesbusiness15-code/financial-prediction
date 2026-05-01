"""Deterministic euro-impact formulas for Solution Finder actions.

Each formula consumes a per-contract row (pandas Series of the latest
monthly record, already enriched by src.features) plus cohort stats from
src.benchmarks and returns an estimated monthly recovery in euros.

All formulas are pure, stateless, and clamped to a sane range to keep the
Solution Finder from surfacing implausible numbers. Assumption
coefficients live as ``ASSUMPTION_*`` module-level constants so they are
greppable and can be tuned in a single place.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Optional

import pandas as pd

from src.benchmarks import CohortStats


# Fraction of the subcontractor cost that is realistically clawed back
# when the share is renegotiated down toward the planned ratio.
ASSUMPTION_SUBC_RECOVERY = 0.50

# Fraction of revenue recovered when the labor cost audit closes the gap
# between actual labor ratio and the planned labor ratio.
ASSUMPTION_LABOR_SAVINGS = 0.15

# Fraction of the planned-minus-productive-hours gap that productivity
# initiatives realistically recover per month.
ASSUMPTION_PRODUCTIVITY_GAIN = 0.10

# Fraction of the peer-vs-self labor ratio delta that repricing can pass
# through to the customer in hourly contracts.
ASSUMPTION_PRICE_PASSTHROUGH = 0.50

# Fraction of labor cost that absence intervention can recover when the
# contract's absence rate sits above the cohort median.
ASSUMPTION_ABSENCE_RECOVERY = 0.40

# Fraction of revenue effectively at risk from a negative quality gap
# (service penalty + re-work proxy).
ASSUMPTION_QUALITY_PENALTY = 0.03

# Fraction of the plan-vs-actual CM gap recovered through renegotiation.
ASSUMPTION_RENEG_RECOVERY = 0.60

# Revenue clamp cap: an action may never claim more than this share of
# monthly revenue as recovered impact.
IMPACT_REVENUE_CAP_SHARE = 0.30


FORMULAS: dict[str, Callable[[pd.Series, CohortStats, Optional[dict]], float]]


def _num(row: pd.Series, key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(value):
        return float(default)
    return value


def _clamp(value: float, revenue_total: float) -> float:
    if value <= 0 or math.isnan(value):
        return 0.0
    cap_base = max(abs(revenue_total), 0.0)
    cap = cap_base * IMPACT_REVENUE_CAP_SHARE if cap_base > 0 else value
    return float(min(value, cap)) if cap > 0 else float(value)


def _reduce_subcontractor_share(row: pd.Series, cohort: CohortStats,
                                 _params: Optional[dict] = None) -> float:
    share = _num(row, "subcontractor_share")
    plan = _num(row, "plan_subcontractor_ratio")
    gap = max(share - plan, 0.0)
    if gap <= 0:
        return 0.0
    subc_total = _num(row, "subcontractor_total")
    if subc_total <= 0:
        subc_total = (
            _num(row, "subcontractor_group")
            + _num(row, "subcontractor_division")
            + _num(row, "subcontractor_external")
        )
    raw = gap * ASSUMPTION_SUBC_RECOVERY * subc_total
    return _clamp(raw, _num(row, "revenue_total"))


def _labor_cost_audit(row: pd.Series, cohort: CohortStats,
                      _params: Optional[dict] = None) -> float:
    labor_ratio = _num(row, "labor_ratio")
    plan_ratio = _num(row, "plan_labor_cost_ratio")
    revenue = _num(row, "revenue_total")
    gap = max(labor_ratio - plan_ratio, 0.0)
    raw = gap * revenue * ASSUMPTION_LABOR_SAVINGS
    return _clamp(raw, revenue)


def _productivity_improvement(row: pd.Series, cohort: CohortStats,
                              _params: Optional[dict] = None) -> float:
    planned = _num(row, "hours_planned")
    productive = _num(row, "hours_productive")
    gap_hours = max(planned - productive, 0.0)
    rate = _num(row, "labor_cost_per_productive_hour")
    raw = gap_hours * rate * ASSUMPTION_PRODUCTIVITY_GAIN
    return _clamp(raw, _num(row, "revenue_total"))


def _reprice_hourly(row: pd.Series, cohort: CohortStats,
                    _params: Optional[dict] = None) -> float:
    revenue_hourly = _num(row, "revenue_hourly")
    peer_labor = cohort.medians.get("labor_ratio")
    labor_ratio = _num(row, "labor_ratio")
    if revenue_hourly <= 0 or peer_labor is None:
        return 0.0
    peer_gap = max(labor_ratio - float(peer_labor), 0.0)
    raw = revenue_hourly * peer_gap * ASSUMPTION_PRICE_PASSTHROUGH
    return _clamp(raw, _num(row, "revenue_total"))


def _absence_intervention(row: pd.Series, cohort: CohortStats,
                          _params: Optional[dict] = None) -> float:
    absence = _num(row, "absence_rate")
    peer = cohort.medians.get("absence_rate")
    if peer is None:
        return 0.0
    gap = max(absence - float(peer), 0.0)
    labor = _num(row, "labor_cost_total")
    raw = gap * labor * ASSUMPTION_ABSENCE_RECOVERY
    return _clamp(raw, _num(row, "revenue_total"))


def _quality_remediation(row: pd.Series, cohort: CohortStats,
                         _params: Optional[dict] = None) -> float:
    quality_gap = _num(row, "quality_gap")
    deficit = max(-quality_gap, 0.0)
    revenue = _num(row, "revenue_total")
    raw = deficit * revenue * ASSUMPTION_QUALITY_PENALTY
    return _clamp(raw, revenue)


def _renegotiate_price(row: pd.Series, cohort: CohortStats,
                       _params: Optional[dict] = None) -> float:
    cm_plan = _num(row, "cm_planned")
    cm = _num(row, "cm_db")
    gap = max(cm_plan - cm, 0.0)
    raw = gap * ASSUMPTION_RENEG_RECOVERY
    return _clamp(raw, _num(row, "revenue_total"))


def _stop_bleed(row: pd.Series, cohort: CohortStats,
                _params: Optional[dict] = None) -> float:
    cm = _num(row, "cm_db")
    raw = max(-cm, 0.0)
    return _clamp(raw, _num(row, "revenue_total"))


def _renewal_outreach(row: pd.Series, cohort: CohortStats,
                      _params: Optional[dict] = None) -> float:
    # Retention value surface (not summed with cost recoveries in the UI).
    revenue = _num(row, "revenue_total")
    return max(revenue, 0.0)


def _training_investment(row: pd.Series, cohort: CohortStats,
                         _params: Optional[dict] = None) -> float:
    prod = _num(row, "productivity_ratio")
    peer = cohort.medians.get("productivity_ratio")
    if peer is None:
        return 0.0
    gap = max(float(peer) - prod, 0.0)
    prod_hours = _num(row, "hours_productive")
    rate = _num(row, "labor_cost_per_productive_hour")
    raw = gap * prod_hours * rate
    return _clamp(raw, _num(row, "revenue_total"))


FORMULAS = {
    "reduce_subcontractor_share": _reduce_subcontractor_share,
    "labor_cost_audit": _labor_cost_audit,
    "productivity_improvement": _productivity_improvement,
    "reprice_hourly": _reprice_hourly,
    "absence_intervention": _absence_intervention,
    "quality_remediation": _quality_remediation,
    "renegotiate_price": _renegotiate_price,
    "stop_bleed": _stop_bleed,
    "renewal_outreach": _renewal_outreach,
    "training_investment": _training_investment,
}


def simulate(
    formula_id: str,
    row: pd.Series,
    cohort: CohortStats,
    params: Optional[dict[str, Any]] = None,
) -> float:
    fn = FORMULAS.get(formula_id)
    if fn is None:
        raise KeyError(f"unknown impact formula: {formula_id!r}")
    return float(fn(row, cohort, params))


def _fmt_eur(value: float) -> str:
    return f"{value:,.0f} EUR".replace(",", ".")


def explain(
    formula_id: str,
    row: pd.Series,
    cohort: CohortStats,
) -> list[tuple[str, str]]:
    """Return a list of (label, value) tuples showing the math step by step.

    Every action card in the UI calls this to render a "how we got this
    number" breakdown underneath the EUR figure. Numbers come from the
    same inputs as ``simulate`` so the two can never disagree.
    """
    if formula_id == "reduce_subcontractor_share":
        share = _num(row, "subcontractor_share")
        plan = _num(row, "plan_subcontractor_ratio")
        gap = max(share - plan, 0.0)
        subc = _num(row, "subcontractor_total")
        raw = gap * ASSUMPTION_SUBC_RECOVERY * subc
        return [
            ("Subunternehmer-Quote (Ist)", f"{share:.1%}"),
            ("Subunternehmer-Quote (Plan)", f"{plan:.1%}"),
            ("Überschreitung", f"{gap:+.1%}"),
            ("Subunternehmer-Kosten gesamt", _fmt_eur(subc)),
            (f"x Rückholquote ({ASSUMPTION_SUBC_RECOVERY:.0%})", _fmt_eur(raw)),
        ]

    if formula_id == "labor_cost_audit":
        lr = _num(row, "labor_ratio")
        plan = _num(row, "plan_labor_cost_ratio")
        gap = max(lr - plan, 0.0)
        rev = _num(row, "revenue_total")
        raw = gap * rev * ASSUMPTION_LABOR_SAVINGS
        return [
            ("Personalquote (Ist)", f"{lr:.1%}"),
            ("Personalquote (Plan)", f"{plan:.1%}"),
            ("Überschreitung", f"{gap:+.1%}"),
            ("Monatsumsatz", _fmt_eur(rev)),
            (f"x Einsparquote ({ASSUMPTION_LABOR_SAVINGS:.0%})", _fmt_eur(raw)),
        ]

    if formula_id == "productivity_improvement":
        hp = _num(row, "hours_planned")
        prod = _num(row, "hours_productive")
        gap_h = max(hp - prod, 0.0)
        rate = _num(row, "labor_cost_per_productive_hour")
        raw = gap_h * rate * ASSUMPTION_PRODUCTIVITY_GAIN
        return [
            ("Soll-Stunden", f"{hp:,.0f}".replace(",", ".")),
            ("Produktive Stunden", f"{prod:,.0f}".replace(",", ".")),
            ("Lücke", f"{gap_h:,.0f} h".replace(",", ".")),
            ("Kosten pro produktiver Stunde", _fmt_eur(rate)),
            (f"x Hebequote ({ASSUMPTION_PRODUCTIVITY_GAIN:.0%})", _fmt_eur(raw)),
        ]

    if formula_id == "reprice_hourly":
        rh = _num(row, "revenue_hourly")
        lr = _num(row, "labor_ratio")
        peer = cohort.medians.get("labor_ratio")
        peer_v = float(peer) if peer is not None else 0.0
        gap = max(lr - peer_v, 0.0)
        raw = rh * gap * ASSUMPTION_PRICE_PASSTHROUGH
        return [
            ("Stundenumsatz", _fmt_eur(rh)),
            ("Personalquote (Ist)", f"{lr:.1%}"),
            ("Personalquote (Cohort-Median)", f"{peer_v:.1%}"),
            ("Differenz", f"{gap:+.1%}"),
            (f"x Durchsetzungsquote ({ASSUMPTION_PRICE_PASSTHROUGH:.0%})",
             _fmt_eur(raw)),
        ]

    if formula_id == "absence_intervention":
        ab = _num(row, "absence_rate")
        peer = cohort.medians.get("absence_rate")
        peer_v = float(peer) if peer is not None else 0.0
        gap = max(ab - peer_v, 0.0)
        labor = _num(row, "labor_cost_total")
        raw = gap * labor * ASSUMPTION_ABSENCE_RECOVERY
        return [
            ("Ausfallquote (Ist)", f"{ab:.1%}"),
            ("Ausfallquote (Cohort-Median)", f"{peer_v:.1%}"),
            ("Überschreitung", f"{gap:+.1%}"),
            ("Personalkosten gesamt", _fmt_eur(labor)),
            (f"x Rückholquote ({ASSUMPTION_ABSENCE_RECOVERY:.0%})",
             _fmt_eur(raw)),
        ]

    if formula_id == "quality_remediation":
        qg = _num(row, "quality_gap")
        deficit = max(-qg, 0.0)
        rev = _num(row, "revenue_total")
        raw = deficit * rev * ASSUMPTION_QUALITY_PENALTY
        return [
            ("Qualitätslücke", f"{qg:+.1%}"),
            ("Monatsumsatz", _fmt_eur(rev)),
            (f"x Pen./Nacharb. ({ASSUMPTION_QUALITY_PENALTY:.0%})",
             _fmt_eur(raw)),
        ]

    if formula_id == "renegotiate_price":
        cmp_ = _num(row, "cm_planned")
        cm = _num(row, "cm_db")
        gap = max(cmp_ - cm, 0.0)
        raw = gap * ASSUMPTION_RENEG_RECOVERY
        return [
            ("Plan-Deckungsbeitrag", _fmt_eur(cmp_)),
            ("Ist-Deckungsbeitrag", _fmt_eur(cm)),
            ("Lücke", _fmt_eur(gap)),
            (f"x Durchsetzungsquote ({ASSUMPTION_RENEG_RECOVERY:.0%})",
             _fmt_eur(raw)),
        ]

    if formula_id == "stop_bleed":
        cm = _num(row, "cm_db")
        raw = max(-cm, 0.0)
        return [
            ("Ist-Deckungsbeitrag", _fmt_eur(cm)),
            ("Stoppen des Verlusts", _fmt_eur(raw)),
        ]

    if formula_id == "renewal_outreach":
        rev = _num(row, "revenue_total")
        return [
            ("Monatsumsatz (Erhalt)", _fmt_eur(rev)),
        ]

    if formula_id == "training_investment":
        prod = _num(row, "productivity_ratio")
        peer = cohort.medians.get("productivity_ratio")
        peer_v = float(peer) if peer is not None else 0.0
        gap = max(peer_v - prod, 0.0)
        ph = _num(row, "hours_productive")
        rate = _num(row, "labor_cost_per_productive_hour")
        raw = gap * ph * rate
        return [
            ("Produktivität (Ist)", f"{prod:.1%}"),
            ("Produktivität (Cohort)", f"{peer_v:.1%}"),
            ("Lücke", f"{gap:+.1%}"),
            ("Produktive Stunden", f"{ph:,.0f}".replace(",", ".")),
            ("Kosten pro produktiver Stunde", _fmt_eur(rate)),
            ("Potenzial (vor Kappung)", _fmt_eur(raw)),
        ]

    return []
