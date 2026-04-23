"""Inline-SVG chart helpers — light theme, self-contained (no Plotly)."""
from __future__ import annotations

import math
from html import escape

import pandas as pd
import streamlit as st

from src.theme import tokens


def _fmt_eur_compact(v: float) -> str:
    """Format a EUR amount compactly in German locale (period thousands, comma decimal).

    Scale-aware precision so small values never collapse to "0 EUR":
    - |v| >= 1_000_000 -> "1,2 Mio EUR"
    - |v| >= 1_000     -> "12k EUR"
    - |v| >= 10 or 0   -> "123 EUR"
    - |v| >= 1         -> "2,5 EUR"  (1 decimal)
    - |v| >  0         -> "0,42 EUR" (2 decimals — keeps sub-euro signal visible)
    """
    av = abs(v)
    if av >= 1_000_000:
        s = f"{v/1_000_000:,.1f} Mio EUR"
    elif av >= 1_000:
        s = f"{v/1_000:,.0f}k EUR"
    elif av >= 10 or v == 0:
        s = f"{v:,.0f} EUR"
    elif av >= 1:
        s = f"{v:,.1f} EUR"
    else:
        s = f"{v:,.2f} EUR"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _nice_step(raw_step: float) -> float:
    """Round raw_step up to the nearest 1-2-2.5-5-10 * 10^n."""
    if raw_step <= 0:
        return 1.0
    exp10 = 10 ** math.floor(math.log10(raw_step))
    for m in (1.0, 2.0, 2.5, 5.0, 10.0):
        if m * exp10 >= raw_step:
            return m * exp10
    return 10.0 * exp10


@st.cache_data(show_spinner=False)
def area_chart(values: list[float], periods: list[pd.Timestamp],
               *, declining: bool = False,
               y_as_pct: bool = True, value_fmt: str = "pct",
               forecast_from: int | None = None,
               confidence_band: tuple[list[float], list[float]] | None = None,
               trendline: list[float] | None = None) -> str:
    """Clean inline-SVG area chart — smooth curve, subtle gridlines, month ticks.

    `value_fmt` supports "pct" (e.g. 8.2%) and "eur" (e.g. 12.4k €).
    `trendline`, if provided with the same length as `values`, is drawn as a
    dashed straight overlay (typically a linear-regression fit).
    """
    if not values or len(values) < 2:
        return ""

    tok = tokens()
    accent_pos = tok["pos"]
    accent_neg = tok["neg"]
    axis_color = tok["fg_secondary"]
    grid_color = tok["border"]
    surface = tok["bg_surface"]

    width, height = 720, 200
    pad_t, pad_r, pad_b, pad_l = 18, 18, 36, 52
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    extra_for_span: list[float] = []
    if confidence_band is not None:
        lo_band, hi_band = confidence_band
        extra_for_span = list(lo_band) + list(hi_band)
    if trendline is not None and len(trendline) == len(values):
        extra_for_span = extra_for_span + list(trendline)
    lo = min(list(values) + extra_for_span)
    hi = max(list(values) + extra_for_span)
    span = max(hi - lo, 0.005 if y_as_pct else 1.0)
    y_lo = lo - span * 0.18
    y_hi = hi + span * 0.18
    y_span = y_hi - y_lo

    n = len(values)
    xs = [pad_l + i * (plot_w / (n - 1)) for i in range(n)]
    ys = [pad_t + (1 - (v - y_lo) / y_span) * plot_h for v in values]

    band_svg = ""
    if confidence_band is not None:
        lo_band, hi_band = confidence_band
        if len(lo_band) == n and len(hi_band) == n:
            ys_lo = [pad_t + (1 - (v - y_lo) / y_span) * plot_h for v in lo_band]
            ys_hi = [pad_t + (1 - (v - y_lo) / y_span) * plot_h for v in hi_band]
            top = " ".join(f"{xs[i]:.1f},{ys_hi[i]:.1f}" for i in range(n))
            bot = " ".join(f"{xs[i]:.1f},{ys_lo[i]:.1f}" for i in range(n - 1, -1, -1))
            band_svg = (
                f"<polygon points='{top} {bot}' "
                f"fill='{tok['accent']}' fill-opacity='0.10' stroke='none'/>"
            )

    fx_svg = ""
    if forecast_from is not None and 0 < forecast_from < n:
        fx_x = xs[forecast_from]
        fx_svg = (
            f"<line x1='{fx_x:.1f}' y1='{pad_t:.1f}'"
            f" x2='{fx_x:.1f}' y2='{pad_t + plot_h:.1f}'"
            f" stroke='{axis_color}' stroke-width='1'"
            f" stroke-dasharray='4 3' opacity='0.5'/>"
        )

    # Smooth cubic-bezier path.
    path = f"M {xs[0]:.1f},{ys[0]:.1f}"
    for i in range(1, n):
        mx = (xs[i - 1] + xs[i]) / 2
        path += (f" C {mx:.1f},{ys[i-1]:.1f}"
                 f" {mx:.1f},{ys[i]:.1f}"
                 f" {xs[i]:.1f},{ys[i]:.1f}")
    area = (path
            + f" L {xs[-1]:.1f},{pad_t + plot_h:.1f}"
            + f" L {xs[0]:.1f},{pad_t + plot_h:.1f} Z")

    stroke = accent_neg if declining else accent_pos
    fill_top = stroke + "33"
    fill_bot = stroke + "00"

    def _fmt(v: float) -> str:
        if value_fmt == "pct":
            return f"{v * 100:.1f}%"
        # eur — compact display that scales: single euros, k, Mio
        return _fmt_eur_compact(v)

    grid_lines = ""
    for frac in (0.0, 0.5, 1.0):
        y = pad_t + frac * plot_h
        val = y_hi - frac * y_span
        grid_lines += (
            f"<line x1='{pad_l:.1f}' y1='{y:.1f}'"
            f" x2='{pad_l + plot_w:.1f}' y2='{y:.1f}'"
            f" stroke='{grid_color}' stroke-width='1'"
            f" stroke-dasharray='{'' if frac == 0.0 else '2 3'}'/>"
            f"<text x='{pad_l - 8:.1f}' y='{y + 4:.1f}' text-anchor='end'"
            f" font-size='11' fill='{axis_color}'>{escape(_fmt(val))}</text>"
        )

    x_labels = ""
    if periods and len(periods) == n:
        idxs = sorted({0, n // 2, n - 1})
        for i in idxs:
            lab = pd.Timestamp(periods[i]).strftime("%b %y")
            x_labels += (
                f"<text x='{xs[i]:.1f}' y='{height - 12:.1f}'"
                f" text-anchor='middle' font-size='11' fill='{axis_color}'>"
                f"{escape(lab)}</text>"
            )

    trend_svg = ""
    if trendline is not None and len(trendline) == n:
        ys_trend = [pad_t + (1 - (v - y_lo) / y_span) * plot_h for v in trendline]
        pts = " ".join(f"{xs[i]:.1f},{ys_trend[i]:.1f}" for i in range(n))
        trend_svg = (
            f"<polyline points='{pts}' fill='none' stroke='{axis_color}'"
            f" stroke-width='1.6' stroke-dasharray='5 4'"
            f" stroke-linecap='round' opacity='0.85'/>"
        )

    last_x, last_y = xs[-1], ys[-1]
    last_lab = _fmt(values[-1])
    bubble_w = max(58, len(last_lab) * 8 + 14)
    bubble_x = min(last_x + 10, pad_l + plot_w - bubble_w - 2)
    bubble_y = max(pad_t + 6, last_y - 22)
    highlight = (
        f"<circle cx='{last_x:.1f}' cy='{last_y:.1f}' r='9'"
        f" fill='{stroke}' fill-opacity='0.16'/>"
        f"<circle cx='{last_x:.1f}' cy='{last_y:.1f}' r='4.5'"
        f" fill='{surface}' stroke='{stroke}' stroke-width='2'/>"
        f"<g transform='translate({bubble_x:.1f},{bubble_y:.1f})'>"
        f"  <rect rx='6' ry='6' width='{bubble_w}' height='20'"
        f"        fill='{stroke}' opacity='0.95'/>"
        f"  <text x='{bubble_w / 2:.1f}' y='14' text-anchor='middle'"
        f"        font-size='11' font-weight='600' fill='#FFFFFF'"
        f"        font-family='Inter, system-ui, sans-serif'"
        f"        font-variant-numeric='tabular-nums'>{escape(last_lab)}</text>"
        f"</g>"
    )

    grad_id = f"wg{abs(hash(tuple(values))) % 100000}"
    return f"""
<svg viewBox='0 0 {width} {height}' width='100%'
     preserveAspectRatio='xMidYMid meet'
     style='display:block;max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif;'>
  <defs>
    <linearGradient id='{grad_id}' x1='0' x2='0' y1='0' y2='1'>
      <stop offset='0%' stop-color='{fill_top}'/>
      <stop offset='100%' stop-color='{fill_bot}'/>
    </linearGradient>
  </defs>
  {grid_lines}
  {band_svg}
  {fx_svg}
  <path d='{area}' fill='url(#{grad_id})' stroke='none'/>
  <path d='{path}' fill='none' stroke='{stroke}' stroke-width='2.2'
        stroke-linecap='round' stroke-linejoin='round'/>
  {trend_svg}
  {highlight}
  {x_labels}
</svg>
"""


def _color_for(v: float, lo: float, hi: float) -> str:
    """Map v ∈ [lo, hi] to a red→yellow→green gradient (light theme)."""
    if hi <= lo:
        return tokens()["heatmap_mid"]
    t = max(0.0, min(1.0, (v - lo) / (hi - lo)))
    # Two-stop interpolation red→yellow (0→0.5) then yellow→green (0.5→1.0)
    if t <= 0.5:
        frac = t / 0.5
        r = int(0xC6 + (0xFF - 0xC6) * frac)
        g = int(0x28 + (0xF5 - 0x28) * frac)
        b = int(0x28 + (0x9D - 0x28) * frac)
    else:
        frac = (t - 0.5) / 0.5
        r = int(0xFF + (0x2E - 0xFF) * frac)
        g = int(0xF5 + (0x7D - 0xF5) * frac)
        b = int(0x9D + (0x32 - 0x9D) * frac)
    return f"#{r:02X}{g:02X}{b:02X}"


def heatmap_grid(values_2d: list[list[float | None]],
                 row_labels: list[str],
                 col_labels: list[str],
                 *, value_fmt: str = "pct") -> str:
    """Render a CM%-style heatmap as inline SVG (no external chart lib)."""
    if not values_2d or not values_2d[0]:
        return ""
    tok = tokens()
    axis_color = tok["fg_secondary"]

    nrows = len(values_2d)
    ncols = len(values_2d[0])
    cell_w = 56
    cell_h = 34
    label_w = 120
    label_h = 32
    width = label_w + ncols * cell_w + 12
    height = label_h + nrows * cell_h + 12

    flat = [v for row in values_2d for v in row if v is not None]
    if not flat:
        return ""
    lo = min(flat)
    hi = max(flat)

    def _fmt(v: float | None) -> str:
        if v is None:
            return "—"
        if value_fmt == "pct":
            return f"{v*100:.1f}%"
        return f"{v:,.0f}"

    header = ""
    for j, label in enumerate(col_labels):
        cx = label_w + j * cell_w + cell_w / 2
        header += (
            f"<text x='{cx:.1f}' y='{label_h - 10:.1f}' text-anchor='middle'"
            f" font-size='11' fill='{axis_color}'>{escape(label)}</text>"
        )

    rows_svg = ""
    for i, (row, rlabel) in enumerate(zip(values_2d, row_labels)):
        ry = label_h + i * cell_h
        rows_svg += (
            f"<text x='{label_w - 10:.1f}' y='{ry + cell_h/2 + 4:.1f}'"
            f" text-anchor='end' font-size='12' fill='{tok['fg_primary']}'>"
            f"{escape(rlabel)}</text>"
        )
        for j, v in enumerate(row):
            cx = label_w + j * cell_w
            fill = _color_for(v, lo, hi) if v is not None else tok["bg_muted"]
            rows_svg += (
                f"<rect x='{cx + 2:.1f}' y='{ry + 2:.1f}'"
                f" width='{cell_w - 4:.1f}' height='{cell_h - 4:.1f}'"
                f" rx='4' ry='4' fill='{fill}'/>"
                f"<text x='{cx + cell_w/2:.1f}' y='{ry + cell_h/2 + 4:.1f}'"
                f" text-anchor='middle' font-size='10.5'"
                f" font-family='Inter, system-ui, sans-serif'"
                f" font-variant-numeric='tabular-nums'"
                f" fill='{tok['fg_primary']}'>{escape(_fmt(v))}</text>"
            )

    return f"""
<svg viewBox='0 0 {width} {height}' width='100%'
     preserveAspectRatio='xMidYMid meet'
     style='display:block;max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif;'>
  {header}
  {rows_svg}
</svg>
"""


def grouped_bars(rows: list[tuple[str, float, float]],
                 *, labels: tuple[str, str] = ("Plan", "Ist"),
                 value_fmt: str = "eur") -> str:
    """Render plan-vs-actual grouped bars. `rows` is list of (label, plan, actual)."""
    if not rows:
        return ""
    tok = tokens()
    axis_color = tok["fg_secondary"]
    grid_color = tok["border"]
    plan_color = tok["fg_muted"]
    actual_color = tok["accent"]

    width, height = 720, 260
    pad_t, pad_r, pad_b, pad_l = 24, 18, 64, 60
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    all_vals = [v for _, p, a in rows for v in (p, a)]
    max_v = max(all_vals) if all_vals else 0.0
    min_v = min(all_vals) if all_vals else 0.0

    # Nice 1-2-5 axis: always include zero, snap bounds to round multiples.
    y_hi_raw = max(max_v, 0.0)
    y_lo_raw = min(min_v, 0.0)
    if y_hi_raw == y_lo_raw:
        y_hi_raw = y_lo_raw + 1.0
    target_ticks = 4
    step = _nice_step((y_hi_raw - y_lo_raw) / target_ticks)
    y_hi = math.ceil(y_hi_raw / step) * step
    y_lo = math.floor(y_lo_raw / step) * step
    if y_hi == y_lo:
        y_hi = y_lo + step
    y_span = y_hi - y_lo

    def y_of(v: float) -> float:
        return pad_t + (1 - (v - y_lo) / y_span) * plot_h

    def _fmt(v: float) -> str:
        if value_fmt == "eur":
            return _fmt_eur_compact(v)
        return f"{v:.1%}"

    # Gridlines at exact step multiples (round numbers on Y-axis).
    grid = ""
    ticks: list[float] = []
    t = y_lo
    while t <= y_hi + step * 0.5:
        ticks.append(t)
        t += step
    for val in ticks:
        y = y_of(val)
        is_zero = abs(val) < step * 1e-6
        dash = "" if is_zero else "2 3"
        grid += (
            f"<line x1='{pad_l:.1f}' y1='{y:.1f}'"
            f" x2='{pad_l + plot_w:.1f}' y2='{y:.1f}'"
            f" stroke='{grid_color}' stroke-width='1'"
            f" stroke-dasharray='{dash}'/>"
            f"<text x='{pad_l - 8:.1f}' y='{y + 4:.1f}' text-anchor='end'"
            f" font-size='11' fill='{axis_color}'>{escape(_fmt(val))}</text>"
        )

    n = len(rows)
    group_w = plot_w / n
    bar_w = min(18, group_w * 0.35)
    # Thin month labels so they never overlap after rotation.
    if n <= 12:
        step_x = 1
    elif n <= 24:
        step_x = 2
    elif n <= 36:
        step_x = 3
    else:
        step_x = math.ceil(n / 12)
    bars = ""
    labels_svg = ""
    zero_y = y_of(0)
    label_y = height - pad_b + 18
    for i, (label, plan, actual) in enumerate(rows):
        gx = pad_l + i * group_w + group_w / 2
        plan_x = gx - bar_w - 2
        act_x = gx + 2
        for val, x, color in ((plan, plan_x, plan_color), (actual, act_x, actual_color)):
            by = y_of(val)
            top = min(by, zero_y)
            h = abs(by - zero_y)
            bars += (
                f"<rect x='{x:.1f}' y='{top:.1f}' width='{bar_w:.1f}'"
                f" height='{max(h, 1):.1f}' rx='2' ry='2' fill='{color}'/>"
            )
        show_label = (i == 0) or (i == n - 1) or (i % step_x == 0)
        if show_label:
            labels_svg += (
                f"<text x='{gx:.1f}' y='{label_y:.1f}'"
                f" text-anchor='end' font-size='11' fill='{axis_color}'"
                f" transform='rotate(-45 {gx:.1f} {label_y:.1f})'>"
                f"{escape(label)}</text>"
            )

    legend = (
        f"<g transform='translate({pad_l + plot_w - 130:.1f},{pad_t - 12:.1f})'>"
        f"  <rect x='0' y='0' width='10' height='10' fill='{plan_color}' rx='2'/>"
        f"  <text x='14' y='9' font-size='11' fill='{axis_color}'>{escape(labels[0])}</text>"
        f"  <rect x='60' y='0' width='10' height='10' fill='{actual_color}' rx='2'/>"
        f"  <text x='74' y='9' font-size='11' fill='{axis_color}'>{escape(labels[1])}</text>"
        f"</g>"
    )

    return f"""
<svg viewBox='0 0 {width} {height}' width='100%'
     preserveAspectRatio='xMidYMid meet'
     style='display:block;max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif;'>
  {grid}
  {bars}
  {labels_svg}
  {legend}
</svg>
"""
