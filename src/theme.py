"""WISAG brand tokens — single source of truth for light-theme design decisions."""
from __future__ import annotations

# Legacy brand constants — imported by external callers via the module surface.
WISAG_GREEN = "#6DB233"
WISAG_GREEN_DARK = "#528A28"
WISAG_GREEN_LIGHT = "#E6F2D6"
WISAG_NAVY = "#1D1D1B"
WISAG_GRAY_100 = "#F5F5F5"
WISAG_GRAY_200 = "#EDEDED"
WISAG_GRAY_300 = "#E5E5E5"
WISAG_GRAY_500 = "#9E9E9E"
WISAG_GRAY_600 = "#6B6B6B"

POS = "#2E7D32"
POS_LIGHT = "#C8E6C9"
POS_DARK = "#1B5E20"
NEG = "#C62828"
NEG_LIGHT = "#FFCDD2"
NEG_DARK = "#B71C1C"
NEU = "#9E9E9E"
WARN = "#F57C00"
WARN_DARK = "#8A4A00"
WARN_LIGHT = "#FFE0B2"
HEATMAP_MID = "#FFF59D"

HEATMAP_SCALE = [NEG, HEATMAP_MID, POS]

SEVERITY_COLORS = {
    "high":   {"bg": NEG_LIGHT,  "fg": NEG_DARK,  "label": "Hoch"},
    "medium": {"bg": WARN_LIGHT, "fg": WARN_DARK, "label": "Mittel"},
    "low":    {"bg": POS_LIGHT,  "fg": POS_DARK,  "label": "Niedrig"},
}


LIGHT_TOKENS: dict[str, str] = {
    "bg_app":              "#FAFAF7",
    "bg_surface":          "#FFFFFF",
    "bg_muted":            "#F5F5F2",
    "bg_sidebar":          "#FFFFFF",

    "fg_primary":          "#1D1D1B",
    "fg_secondary":        "#6B6B6B",
    "fg_muted":            "#9E9E9E",
    "fg_inverse":          "#FFFFFF",

    "border":              "#E8E6E1",
    "border_strong":       "#D8D5CE",
    "border_subtle":       "#F0EEE9",

    "accent":              WISAG_GREEN,
    "accent_dark":         WISAG_GREEN_DARK,
    "accent_light":        WISAG_GREEN_LIGHT,

    "pos":                 POS,
    "pos_dark":            POS_DARK,
    "pos_light":           POS_LIGHT,
    "neg":                 NEG,
    "neg_dark":            NEG_DARK,
    "neg_light":           NEG_LIGHT,
    "warn":                WARN,
    "warn_dark":           WARN_DARK,
    "warn_light":          WARN_LIGHT,
    "heatmap_mid":         HEATMAP_MID,

    # Off-brand lavender for AI/exploratory surfaces — deliberately distinct from data colors.
    "accent_ai":           "#EEE9F7",
    "accent_ai_hover":     "#E5DEF3",
    "accent_ai_border":    "#E3DCF1",
    "accent_ai_border_hover": "#D6CCE9",

    # 4px grid plus documented non-grid card paddings (18/22/26/30).
    "space_0":  "0",
    "space_1":  "2px",
    "space_2":  "4px",
    "space_3":  "6px",
    "space_4":  "8px",
    "space_5":  "10px",
    "space_6":  "12px",
    "space_7":  "14px",
    "space_8":  "16px",
    "space_9":  "20px",
    "space_10": "24px",
    "space_12": "28px",
    "space_14": "32px",
    "space_16": "36px",
    "space_20": "40px",
    "space_24": "48px",
    "space_32": "64px",
    "space_18": "18px",
    "space_22": "22px",
    "space_26": "26px",
    "space_30": "30px",

    "radius_xs":   "4px",
    "radius_sm":   "6px",
    "radius_md":   "8px",
    "radius_lg":   "10px",
    "radius_xl":   "12px",
    "radius_2xl":  "14px",
    "radius_3xl":  "16px",
    "radius_pill": "999px",

    "font_sans":  "'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif",
    "font_serif": "'Newsreader', Georgia, serif",
    "font_mono":  "ui-monospace, 'SFMono-Regular', Menlo, monospace",

    "text_2xs":  "0.72rem",
    "text_xs":   "0.78rem",
    "text_sm":   "0.88rem",
    "text_base": "0.94rem",
    "text_md":   "1.02rem",
    "text_lg":   "1.15rem",
    "text_xl":   "1.35rem",
    "text_2xl":  "1.70rem",
    "text_3xl":  "1.90rem",

    "weight_regular":  "400",
    "weight_medium":   "500",
    "weight_semibold": "600",
    "weight_bold":     "700",

    "leading_tight":  "1.1",
    "leading_snug":   "1.25",
    "leading_normal": "1.45",

    "tracking_tight":  "-0.01em",
    "tracking_normal": "0",
    "tracking_wide":   "0.02em",
    "tracking_widest": "0.04em",

    "shadow":       "0 1px 2px rgba(22,22,20,0.04)",
    "shadow_lg":    "0 4px 14px rgba(22,22,20,0.06)",
    "shadow_hero":  "0 4px 16px rgba(109,178,51,0.22)",
    "shadow_focus": "0 0 0 3px rgba(109,178,51,0.28)",

    "duration_fast":   "0.12s",
    "duration_base":   "0.15s",
    "duration_slow":   "0.25s",
    "easing_standard": "ease",

    "focus_ring":       "0 0 0 3px rgba(109,178,51,0.28)",
    "focus_border":     WISAG_GREEN,
    "disabled_bg":      "#F5F5F2",
    "disabled_fg":      "#9E9E9E",
    "disabled_opacity": "0.55",

    "z_base":     "1",
    "z_dropdown": "100",
    "z_sticky":   "200",
    "z_overlay":  "900",
    "z_modal":    "1000",
    "z_toast":    "1100",

    "sidebar_width":     "240px",
    "content_max_width": "1240px",
}


def tokens() -> dict[str, str]:
    return LIGHT_TOKENS


# Documentation-oriented slices of the flat token dict. Kept for introspection.
_COLOR_KEYS = (
    "bg_app", "bg_surface", "bg_muted", "bg_sidebar",
    "fg_primary", "fg_secondary", "fg_muted", "fg_inverse",
    "border", "border_strong", "border_subtle",
    "accent", "accent_dark", "accent_light",
    "pos", "pos_dark", "pos_light",
    "neg", "neg_dark", "neg_light",
    "warn", "warn_dark", "warn_light",
    "heatmap_mid",
    "accent_ai", "accent_ai_hover", "accent_ai_border", "accent_ai_border_hover",
)


def colors() -> dict[str, str]:
    return {k: LIGHT_TOKENS[k] for k in _COLOR_KEYS}


def space() -> dict[str, str]:
    return {k: v for k, v in LIGHT_TOKENS.items() if k.startswith("space_")}


def type_scale() -> dict[str, str]:
    return {k: v for k, v in LIGHT_TOKENS.items() if k.startswith("text_")}


def radius() -> dict[str, str]:
    return {k: v for k, v in LIGHT_TOKENS.items() if k.startswith("radius_")}
