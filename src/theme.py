"""WISAG brand tokens — single source of truth for colors and sizing."""
from __future__ import annotations

WISAG_ORANGE = "#E94E1B"
WISAG_ORANGE_DARK = "#C63D0F"
WISAG_ORANGE_LIGHT = "#FDE6DC"
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
WARN_LIGHT = "#FFE0B2"

HEATMAP_SCALE = [NEG, "#FFF59D", POS]

SEVERITY_COLORS = {
    "high": {"bg": NEG_LIGHT, "fg": NEG_DARK, "label": "Hoch"},
    "medium": {"bg": WARN_LIGHT, "fg": "#8A4A00", "label": "Mittel"},
    "low": {"bg": POS_LIGHT, "fg": POS_DARK, "label": "Niedrig"},
}
