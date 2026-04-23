"""Shared logic for the single-facility overview.

This module centralises the driver classification, action mapping, and
status-level computation that were previously embedded in the Streamlit
`pages/1_Portfolio_Overview.py` page, so the FastAPI layer can reuse them.

No i18n is applied here — we return i18n *keys*, and let the UI layer
translate them. This keeps the backend response stable across locales.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from src import drivers


StatusLevel = Literal["critical", "warn", "healthy"]


# --- Driver class → (icon, i18n key prefix, default action key) ---
DRIVER_ICON: dict[str, tuple[str, str, str | None]] = {
    "labor":         ("👥", "driver.labor",         "shift"),
    "subcontractor": ("🤝", "driver.subcontractor", "subcontractor"),
    "absence":       ("❤",  "driver.absence",       "absence"),
    "training":      ("🎓", "driver.training",      "onboarding"),
    "material":      ("📦", "driver.material",      "pricing"),
    "vehicle":       ("🚚", "driver.vehicle",       "pricing"),
    "revenue":       ("📉", "driver.revenue",       "pricing"),
    "revenue_up":    ("📈", "driver.revenue_up",    None),
    "other":         ("•",  "driver.other",         None),
}


# --- Action catalogue with estimated impact (ratio points, e.g. 0.032 = +3.2 pp) ---
ACTIONS: dict[str, dict] = {
    "shift":         {"icon": "🗓", "title_key": "action.shift.title",
                      "sub_key": "action.shift.sub", "impact": 0.032},
    "absence":       {"icon": "👥", "title_key": "action.absence.title",
                      "sub_key": "action.absence.sub", "impact": 0.015},
    "onboarding":    {"icon": "🚀", "title_key": "action.onboarding.title",
                      "sub_key": "action.onboarding.sub", "impact": 0.008},
    "subcontractor": {"icon": "🤝", "title_key": "action.subcontractor.title",
                      "sub_key": "action.subcontractor.sub", "impact": 0.020},
    "pricing":       {"icon": "🏷", "title_key": "action.pricing.title",
                      "sub_key": "action.pricing.sub", "impact": 0.025},
    "productivity":  {"icon": "⚡", "title_key": "action.productivity.title",
                      "sub_key": "action.productivity.sub", "impact": 0.012},
}


def classify_driver(d: drivers.Driver) -> str:
    """Collapse the detailed Driver name into a compact class key."""
    n = d.name.lower()
    if d.kind == "revenue":
        return "revenue_up" if d.delta_eur >= 0 else "revenue"
    if "vacation" in n or "sick" in n:
        return "absence"
    if "labor" in n:
        return "labor"
    if "sub" in n:
        return "subcontractor"
    if "training" in n or "onboard" in n:
        return "training"
    if "material" in n:
        return "material"
    if "vehicle" in n or "travel" in n:
        return "vehicle"
    return "other"


def driver_pct_change(d: drivers.Driver) -> float | None:
    """Percent change of the driver vs its baseline (for row labels)."""
    if d.baseline == 0:
        return None
    return (d.current - d.baseline) / abs(d.baseline)


def status_for(margin: float | None, mom: float | None) -> StatusLevel:
    if margin is None or pd.isna(margin):
        return "warn"
    if margin < 0:
        return "critical"
    if mom is not None and mom <= -0.03:
        return "critical"
    if margin < 0.03 or (mom is not None and mom < 0):
        return "warn"
    return "healthy"


def emoji_for(service: str | None, name: str | None) -> str:
    s = f"{service or ''} {name or ''}".lower()
    if "airport" in s or "flughafen" in s or "flug" in s:
        return "✈"
    if "klinik" in s or "hospital" in s or "medi" in s:
        return "🏥"
    if "sicher" in s or "security" in s:
        return "🛡"
    if "reinig" in s or "clean" in s:
        return "🧹"
    if "cater" in s or "verpfleg" in s:
        return "🍽"
    if "bau" in s or "technik" in s or "maintenance" in s:
        return "🛠"
    if "schul" in s or "schule" in s or "bildung" in s:
        return "🎓"
    return "🏢"


def sparkline_values(hist: pd.DataFrame, n: int = 6) -> list[float]:
    """Margin % of the last N months for a single-cost-center frame."""
    tail = hist.tail(n).copy()
    if tail.empty or "revenue_total" not in tail.columns:
        return []
    rev = tail["revenue_total"].where(tail["revenue_total"] != 0, pd.NA)
    m = (tail["cm_db"] / rev).fillna(0.0)
    return [float(v) for v in m.tolist()]


def pick_focus_cost_center(df: pd.DataFrame, override: str | None = None) -> str | None:
    """Pick the 'focus' cost center (worst CM) if no override is given."""
    if override is not None and "cost_center_id" in df.columns:
        if override in df["cost_center_id"].unique():
            return override
    if "cm_db" not in df.columns:
        return None
    cand = df[df["cm_db"] < 0].sort_values("cm_db")
    if not cand.empty:
        return cand.iloc[0]["cost_center_id"]
    rank = df.groupby("cost_center_id")["cm_db"].sum().sort_values()
    return rank.index[0] if not rank.empty else None


@dataclass
class DriverItem:
    class_key: str
    icon: str
    title_key: str
    sub_key: str
    pct_change: float | None
    delta_eur: float


@dataclass
class ActionItem:
    key: str
    icon: str
    title_key: str
    sub_key: str
    impact_pct: float


@dataclass
class SparklinePoint:
    period: str
    margin: float


@dataclass
class FacilityOverview:
    cost_center_id: str
    cost_center_name: str | None
    region: str | None
    service_type: str | None
    period: str
    icon: str
    status: StatusLevel
    margin_pct: float | None
    margin_mom_delta: float | None
    sparkline: list[SparklinePoint]
    worst_drivers: list[DriverItem]
    recommended_actions: list[ActionItem]
    baseline_headcount: float
    team_size_suggestion: int


def _row_str(row: pd.Series, col: str) -> str | None:
    if col not in row.index:
        return None
    v = row[col]
    if pd.isna(v):
        return None
    return str(v)


def _row_float(row: pd.Series, col: str) -> float:
    if col not in row.index:
        return 0.0
    v = row[col]
    try:
        return 0.0 if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return 0.0


def worst_drivers_for(current: pd.Series, baseline: pd.Series,
                      limit: int = 3) -> list[DriverItem]:
    """Top `limit` drivers with negative ΔCM, deduped by class key."""
    all_drivers = drivers.decompose(current, baseline)
    out: list[DriverItem] = []
    seen: set[str] = set()
    for d in sorted(all_drivers, key=lambda x: x.delta_eur):
        if d.delta_eur >= 0:
            break
        cls = classify_driver(d)
        if cls in seen or cls not in DRIVER_ICON:
            continue
        seen.add(cls)
        icon, key_prefix, _ = DRIVER_ICON[cls]
        out.append(DriverItem(
            class_key=cls,
            icon=icon,
            title_key=key_prefix,
            sub_key=f"{key_prefix}.sub",
            pct_change=driver_pct_change(d),
            delta_eur=d.delta_eur,
        ))
        if len(out) >= limit:
            break
    return out


def recommended_actions_for(driver_items: list[DriverItem],
                            limit: int = 3) -> list[ActionItem]:
    """Map drivers → up-to-`limit` action recommendations (deduped)."""
    keys: list[str] = []
    for di in driver_items:
        mapped = DRIVER_ICON[di.class_key][2]
        if mapped and mapped not in keys:
            keys.append(mapped)
    for fallback in ("shift", "absence", "onboarding"):
        if len(keys) >= limit:
            break
        if fallback not in keys:
            keys.append(fallback)
    keys = keys[:limit]
    return [
        ActionItem(
            key=k, icon=ACTIONS[k]["icon"],
            title_key=ACTIONS[k]["title_key"],
            sub_key=ACTIONS[k]["sub_key"],
            impact_pct=ACTIONS[k]["impact"],
        )
        for k in keys
    ]


def build(df: pd.DataFrame, cost_center_id: str | None = None,
          period: pd.Timestamp | None = None) -> FacilityOverview | None:
    """Compute the full facility-overview payload for one CC × one month."""
    from src import sim  # local import to avoid circulars

    cc_id = pick_focus_cost_center(df, override=cost_center_id)
    if cc_id is None:
        return None

    focus = df[df["cost_center_id"] == cc_id].sort_values("period").copy()
    if focus.empty:
        return None

    if period is not None:
        focus_month = focus[focus["period"] == period]
        if focus_month.empty:
            focus_month = focus.tail(1)
    else:
        focus_month = focus.tail(1)
    current_row = focus_month.iloc[-1]

    rev = _row_float(current_row, "revenue_total")
    cm = _row_float(current_row, "cm_db")
    margin_cur = (cm / rev) if rev else None

    prior = focus[focus["period"] < current_row["period"]]
    prior_row = prior.iloc[-1] if not prior.empty else None
    if prior_row is not None and _row_float(prior_row, "revenue_total") > 0:
        margin_prev = _row_float(prior_row, "cm_db") / _row_float(prior_row, "revenue_total")
        margin_mom: float | None = (margin_cur or 0) - margin_prev
    else:
        margin_mom = None

    worst = worst_drivers_for(current_row, prior_row) if prior_row is not None else []
    actions = recommended_actions_for(worst)

    spark = [
        SparklinePoint(period=pd.Timestamp(p).strftime("%Y-%m-%d"), margin=v)
        for p, v in zip(focus.tail(6)["period"], sparkline_values(focus, n=6))
    ]

    baseline_hc = sim.estimate_headcount(current_row) or 0.0
    baseline_hc_int = int(round(baseline_hc)) if baseline_hc else 100

    name = _row_str(current_row, "cost_center_name") or str(cc_id)
    region = _row_str(current_row, "region")
    service = _row_str(current_row, "service_type")

    return FacilityOverview(
        cost_center_id=str(cc_id),
        cost_center_name=name,
        region=region,
        service_type=service,
        period=pd.Timestamp(current_row["period"]).strftime("%Y-%m-%d"),
        icon=emoji_for(service, name),
        status=status_for(margin_cur, margin_mom),
        margin_pct=margin_cur,
        margin_mom_delta=margin_mom,
        sparkline=spark,
        worst_drivers=worst,
        recommended_actions=actions,
        baseline_headcount=baseline_hc,
        team_size_suggestion=baseline_hc_int + 10,
    )
