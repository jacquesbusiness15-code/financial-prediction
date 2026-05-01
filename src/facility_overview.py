"""Shared logic for the single-facility overview.

Returns i18n keys, not translated strings, so the response is locale-stable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from src import drivers


StatusLevel = Literal["critical", "warn", "healthy"]


DRIVER_ICON: dict[str, tuple[str, str, str | None]] = {
    "labor":         ("", "driver.labor",         "shift"),
    "subcontractor": ("", "driver.subcontractor", "subcontractor"),
    "absence":       ("", "driver.absence",       "absence"),
    "training":      ("", "driver.training",      "onboarding"),
    "material":      ("", "driver.material",      "pricing"),
    "vehicle":       ("", "driver.vehicle",       "pricing"),
    "revenue":       ("", "driver.revenue",       "pricing"),
    "revenue_up":    ("", "driver.revenue_up",    None),
    "other":         ("", "driver.other",         None),
}


def _action(key: str, impact: float) -> dict:
    return {
        "icon": "",
        "title_key": f"action.{key}.title",
        "sub_key": f"action.{key}.sub",
        "why_key": f"action.{key}.why",
        "impact": impact,
    }


# Impact is ratio points (0.032 = +3.2 pp).
ACTIONS: dict[str, dict] = {
    "shift":         _action("shift",         0.032),
    "absence":       _action("absence",       0.015),
    "onboarding":    _action("onboarding",    0.008),
    "subcontractor": _action("subcontractor", 0.020),
    "pricing":       _action("pricing",       0.025),
    "productivity":  _action("productivity",  0.012),
}


_DRIVER_NAME_RULES: list[tuple[tuple[str, ...], str]] = [
    (("vacation", "sick"),    "absence"),
    (("labor",),              "labor"),
    (("sub",),                "subcontractor"),
    (("training", "onboard"), "training"),
    (("material",),           "material"),
    (("vehicle", "travel"),   "vehicle"),
]


def classify_driver(d: drivers.Driver) -> str:
    if d.kind == "revenue":
        return "revenue_up" if d.delta_eur >= 0 else "revenue"
    n = d.name.lower()
    for needles, cls in _DRIVER_NAME_RULES:
        if any(k in n for k in needles):
            return cls
    return "other"


def driver_pct_change(d: drivers.Driver) -> float | None:
    # Cost drivers only; sign-flipping would already be a data oddity.
    # Local import avoids a cycle (contract_metrics → portfolio_ranking → here).
    from src.contract_metrics import safe_pct_change

    return safe_pct_change(d.current, d.baseline)


def status_for(margin: float | None, mom: float | None) -> StatusLevel:
    if margin is None or pd.isna(margin):
        return "warn"
    if margin < 0 or (mom is not None and mom <= -0.03):
        return "critical"
    if margin < 0.03 or (mom is not None and mom < 0):
        return "warn"
    return "healthy"


def emoji_for(service: str | None, name: str | None) -> str:
    return ""


def sparkline_values(hist: pd.DataFrame, n: int = 6) -> list[float]:
    tail = hist.tail(n)
    if tail.empty or "revenue_total" not in tail.columns:
        return []
    rev = tail["revenue_total"].where(tail["revenue_total"] != 0, pd.NA)
    m = (tail["cm_db"] / rev).fillna(0.0)
    return [float(v) for v in m.tolist()]


def category_series(focus: pd.DataFrame, category: str, n: int = 12
                    ) -> tuple[list[float], list[pd.Timestamp]]:
    if focus.empty or "revenue_total" not in focus.columns or "cm_db" not in focus.columns:
        return [], []
    tail = focus.tail(n)
    rev = tail["revenue_total"].fillna(0.0)
    cm = tail["cm_db"].fillna(0.0)
    if category == "revenue":
        vals = rev
    elif category == "costs":
        vals = rev - cm
    else:
        vals = cm
    return [float(v) for v in vals.tolist()], list(tail["period"].tolist())


def linear_trend(values: list[float]) -> list[float]:
    import numpy as np

    n = len(values)
    if n < 2:
        return list(values)
    x = np.arange(n, dtype=float)
    m, b = np.polyfit(x, np.array(values, dtype=float), 1)
    return [float(m * i + b) for i in range(n)]


def pick_focus_cost_center(df: pd.DataFrame, override: str | None = None) -> str | None:
    if (override is not None and "cost_center_id" in df.columns
            and override in df["cost_center_id"].unique()):
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
    return None if pd.isna(v) else str(v)


def _row_float(row: pd.Series, col: str) -> float:
    if col not in row.index:
        return 0.0
    v = row[col]
    try:
        return 0.0 if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return 0.0


def _dedup_classified(all_drivers, *, keep) -> list:
    out = []
    seen: set[str] = set()
    for d in all_drivers:
        if not keep(d):
            continue
        cls = classify_driver(d)
        if cls in seen or cls not in DRIVER_ICON:
            continue
        seen.add(cls)
        out.append((cls, d))
    return out


def worst_drivers_for(current: pd.Series, baseline: pd.Series,
                      limit: int = 3) -> list[DriverItem]:
    all_drivers = sorted(drivers.decompose(current, baseline),
                         key=lambda x: x.delta_eur)
    items: list[DriverItem] = []
    for cls, d in _dedup_classified(all_drivers, keep=lambda x: x.delta_eur < 0):
        icon, key_prefix, _ = DRIVER_ICON[cls]
        items.append(DriverItem(
            class_key=cls, icon=icon, title_key=key_prefix,
            sub_key=f"{key_prefix}.sub",
            pct_change=driver_pct_change(d), delta_eur=d.delta_eur,
        ))
        if len(items) >= limit:
            break
    return items


def worst_cost_drivers(current: pd.Series, baseline: pd.Series,
                       limit: int = 3) -> list[drivers.Driver]:
    # Cost-only view: rank by biggest MoM EUR increase. `delta_eur` on a cost
    # driver is `-(cost_cur - cost_base)`, so ascending = biggest-increase-first.
    cost_only = sorted(
        (d for d in drivers.decompose(current, baseline)
         if d.kind == "cost" and d.current > d.baseline),
        key=lambda d: d.delta_eur,
    )
    out: list[drivers.Driver] = []
    for _cls, d in _dedup_classified(cost_only, keep=lambda _d: True):
        out.append(d)
        if len(out) >= limit:
            break
    return out


def recommended_actions_for(driver_items: list[DriverItem],
                            limit: int = 3) -> list[ActionItem]:
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
    return [
        ActionItem(
            key=k, icon=ACTIONS[k]["icon"],
            title_key=ACTIONS[k]["title_key"],
            sub_key=ACTIONS[k]["sub_key"],
            impact_pct=ACTIONS[k]["impact"],
        )
        for k in keys[:limit]
    ]


def build(df: pd.DataFrame, cost_center_id: str | None = None,
          period: pd.Timestamp | None = None) -> FacilityOverview | None:
    from src import sim  # local import avoids a circular

    cc_id = pick_focus_cost_center(df, override=cost_center_id)
    if cc_id is None:
        return None

    focus = df[df["cost_center_id"] == cc_id].sort_values("period").copy()
    if focus.empty:
        return None

    focus_month = focus[focus["period"] == period] if period is not None else focus.tail(0)
    if focus_month.empty:
        focus_month = focus.tail(1)
    current_row = focus_month.iloc[-1]

    rev = _row_float(current_row, "revenue_total")
    cm = _row_float(current_row, "cm_db")
    margin_cur = (cm / rev) if rev else None

    prior = focus[focus["period"] < current_row["period"]]
    prior_row = prior.iloc[-1] if not prior.empty else None
    prior_rev = _row_float(prior_row, "revenue_total") if prior_row is not None else 0.0
    if prior_row is not None and prior_rev > 0:
        margin_prev = _row_float(prior_row, "cm_db") / prior_rev
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
