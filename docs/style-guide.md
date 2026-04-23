# WISAG Financial Co-Pilot — Style Guide

This is the authoritative reference for every visual decision in the WISAG
Strategic Financial Foresight Co-Pilot. It documents what exists, why it
exists, and the rules for extending it.

**Source of truth**: [`src/theme.py`](../src/theme.py) holds every token in a
single flat dict returned by `tokens()`. The stylesheet at
[`src/styles.py`](../src/styles.py) consumes those tokens via f-strings. No
raw hex, px, rem, or font-weight literal is allowed anywhere in CSS — if the
value you need isn't in `theme.py`, add it there first.

---

## 1. Purpose & scope

The UI serves one persona: a German operations controller scanning dozens of
cost centers for margin risk. Every decision below is optimized for:

- **Scan-ability** on dense data tables, heatmaps, and driver rows.
- **Visual calm** — a single accent color, muted neutrals, and restrained
  motion so that anomalies pop without the UI shouting.
- **Bilingual parity** — German is the default; English is a drop-in via the
  DE/EN switcher. Every literal goes through `i18n.t(...)`.

---

## 2. Brand foundation

| | Hex | Token | Use |
|---|---|---|---|
| WISAG Orange | `#E94E1B` | `accent` | primary CTA, active nav, borders on focus, positive affordance |
| WISAG Orange (dark) | `#C63D0F` | `accent_dark` | hover state for primary buttons |
| WISAG Orange (light) | `#FDE6DC` | `accent_light` | active-nav background, hover tint |
| WISAG Navy | `#1D1D1B` | `fg_primary` | body copy, headings, primary icons |
| Off-white | `#FAFAF7` | `bg_app` | page background |

**Light-only.** The dark theme was removed; there is no plan to reintroduce
it. Do not add `prefers-color-scheme: dark` rules.

**No emojis — anywhere.** Icons are SVG (see §11). This ban covers code,
comments, commit messages, UI strings, markdown docs, and log output. If
existing code contains emojis, replace them during edits.

---

## 3. Color tokens

### 3.1 Surfaces

| Token | Hex | Where |
|---|---|---|
| `bg_app` | `#FAFAF7` | page background |
| `bg_surface` | `#FFFFFF` | cards, tables, sidebar, modals |
| `bg_muted` | `#F5F5F2` | disabled states, placeholder rows, chip backgrounds |
| `bg_sidebar` | `#FFFFFF` | sidebar only |

### 3.2 Foreground

| Token | Hex | Where |
|---|---|---|
| `fg_primary` | `#1D1D1B` | body text, headings |
| `fg_secondary` | `#6B6B6B` | labels, subtitles, hints |
| `fg_muted` | `#9E9E9E` | disabled text, dividers, chevrons |
| `fg_inverse` | `#FFFFFF` | text on accent/gradient backgrounds |

### 3.3 Borders

| Token | Hex | Where |
|---|---|---|
| `border` | `#E8E6E1` | card borders, dividers |
| `border_strong` | `#D8D5CE` | emphasis borders, dashed dropzones |
| `border_subtle` | `#F0EEE9` | reserved — use for nested sub-dividers |

### 3.4 Semantic

| Token | Hex | Meaning |
|---|---|---|
| `pos` / `pos_dark` / `pos_light` | `#2E7D32` / `#1B5E20` / `#C8E6C9` | gains, healthy, growth |
| `neg` / `neg_dark` / `neg_light` | `#C62828` / `#B71C1C` / `#FFCDD2` | losses, critical, declines |
| `warn` / `warn_dark` / `warn_light` | `#F57C00` / `#8A4A00` / `#FFE0B2` | medium severity, attention |
| `heatmap_mid` | `#FFF59D` | heatmap neutral midpoint (between `neg` and `pos`) |

**`warn_dark` is canonical.** Previously this color appeared as `#8A4A00`,
`#B77A2B`, and `#C98A3C` in different places — now there is exactly one dark
warn token.

### 3.5 AI accent (lavender)

Used **only** for AI-generated or exploratory surfaces so they read
distinctly from data. Do not use for core data cards.

| Token | Hex | Where |
|---|---|---|
| `accent_ai` | `#EEE9F7` | Ask-AI CTA background, Explore-more card |
| `accent_ai_hover` | `#E5DEF3` | Hover state of the above |
| `accent_ai_border` | `#E3DCF1` | Border of AI surfaces |
| `accent_ai_border_hover` | `#D6CCE9` | Hover border |

---

## 4. Typography

### 4.1 Families

| Token | Value | Where |
|---|---|---|
| `font_sans` | Inter | everything |
| `font_serif` | Newsreader | hero-gradient italic headline only |
| `font_mono` | ui-monospace | inline code in the upload page hint |

Inter is imported with weights `400, 450, 500, 600, 700`. `450` is used
implicitly by form fields — **do not** expose it as a weight token.

### 4.2 Size scale (16px root)

| Token | rem | px | Typical use |
|---|---|---|---|
| `text_2xs` | 0.72 | 11.5 | badges, inline micro-labels |
| `text_xs` | 0.78 | 12.5 | metric labels, subtitles, captions |
| `text_sm` | 0.88 | 14 | section subtitles, table cells, hints |
| `text_base` | 0.94 | 15 | body copy, row titles |
| `text_md` | 1.02 | 16.3 | card titles |
| `text_lg` | 1.15 | 18.4 | h3, section titles on dense pages |
| `text_xl` | 1.35 | 21.6 | h2, hero titles |
| `text_2xl` | 1.70 | 27.2 | large metric values |
| `text_3xl` | 1.90 | 30.4 | h1, hero metric values |

### 4.3 Weights

| Token | Value |
|---|---|
| `weight_regular` | 400 |
| `weight_medium` | 500 |
| `weight_semibold` | **600 — default for all emphasized text** |
| `weight_bold` | 700 |

**`font-weight: 650` is retired.** Inter does not ship a 650 weight —
browsers fall back unpredictably to 600 or 700. Every "heavy" heading
(hero metric value, card title, metric value) uses `weight_semibold` (600).

### 4.4 Line-height

| Token | Value | Use |
|---|---|---|
| `leading_tight` | 1.1 | large numeric values |
| `leading_snug` | 1.25 | card/hero titles |
| `leading_normal` | 1.45 | body copy |

### 4.5 Letter-spacing

| Token | Value | Use |
|---|---|---|
| `tracking_tight` | -0.01em | headings and large metric values |
| `tracking_normal` | 0 | body |
| `tracking_wide` | 0.02em | small-caps-adjacent labels |
| `tracking_widest` | 0.04em | sidebar UPPERCASE headings |

---

## 5. Spacing

A **strict 4px grid** with three documented non-grid exceptions for existing
card paddings. Use the tokens; never type raw px into CSS.

### 5.1 Scale

| Token | Value | Notes |
|---|---|---|
| `space_0` | 0 | reset |
| `space_1` | 2px | micro gap |
| `space_2` | 4px | tight gap |
| `space_3` | 6px | chip gap |
| `space_4` | 8px | standard inline gap |
| `space_5` | 10px | tight row padding |
| `space_6` | 12px | card row padding, inter-row gap |
| `space_7` | 14px | card row padding, gap between icon tiles |
| `space_8` | 16px | card content padding |
| `space_9` | 20px | large card content padding |
| `space_10` | 24px | card outer margin, KPI strip gap |
| `space_12` | 28px | hero metric gap |
| `space_14` | 32px | upload hero vertical padding |
| `space_16` | 36px | upload hero top padding |
| `space_20` | 40px | reserved |
| `space_24` | 48px | reserved |
| `space_32` | 64px | reserved |

### 5.2 Non-grid exceptions

These values are kept as dedicated tokens to render existing card paddings
pixel-identically. Do not introduce new non-grid values without adding a
token and documenting the reason here.

| Token | Value | Used for |
|---|---|---|
| `space_18` | 18px | generic `.wisag-card` and nav-tile horizontal padding |
| `space_22` | 22px | `.wisag-hero-card` vertical, `.wisag-section-card` horizontal, `.wisag-whatif-card` vertical |
| `space_26` | 26px | `.wisag-hero-card` horizontal, landing gradient hero vertical |
| `space_30` | 30px | landing gradient hero horizontal |

---

## 6. Radius

| Token | Value | Use |
|---|---|---|
| `radius_xs` | 4px | inline `<code>` |
| `radius_sm` | 6px | impact pills, peer values |
| `radius_md` | 8px | buttons, nav links, dropzone buttons |
| `radius_lg` | 10px | Ask-AI CTA, dataframes |
| `radius_xl` | 12px | generic cards, warning cards, Explore-more |
| `radius_2xl` | 14px | section cards, nav tiles, What-if card |
| `radius_3xl` | 16px | hero card, chart panel, upload hero |
| `radius_pill` | 999px | status pills, severity badges, chips |

---

## 7. Shadows & elevation

Three canonical shadows. The UI is mostly flat — shadows are a last resort.

| Token | Value | Use |
|---|---|---|
| `shadow` | `0 1px 2px rgba(22,22,20,0.04)` | resting state of every card/surface |
| `shadow_lg` | `0 4px 14px rgba(22,22,20,0.06)` | nav-tile hover lift |
| `shadow_hero` | `0 4px 16px rgba(233,78,27,0.18)` | landing gradient hero only |
| `shadow_focus` | `0 0 0 3px rgba(233,78,27,0.25)` | focus ring (see §9) |

Buttons, pills, and nav items do **not** carry shadows.

---

## 8. Motion

| Token | Value | Use |
|---|---|---|
| `duration_fast` | 0.12s | hover state on links, language switcher, driver row |
| `duration_base` | 0.15s | nav-tile lift, file-uploader border change |
| `duration_slow` | 0.25s | reserved for future modals/drawers |
| `easing_standard` | `ease` | the only easing curve |

Never animate on page load. Transitions live on `:hover` and `:focus` only.

---

## 9. Focus & accessibility

- **Focus ring**: `shadow_focus` (a 3px orange glow at 25% alpha). Applied
  to every interactive element that receives keyboard focus.
- **Focus border**: `focus_border` = `accent`. Applied to `select`,
  `input`, `textarea`.
- **Disabled**: `disabled_bg` / `disabled_fg` / `disabled_opacity: 0.55`.
- **Contrast**: all text tokens meet WCAG AA against their intended
  surfaces. `fg_primary` on `bg_app` is 17.5:1. Status badge text
  (`pos_dark` / `neg_dark` / `warn_dark`) against their light backgrounds
  passes AA for normal text.
- **Keyboard**: Streamlit handles focus order; do not override `tabindex`.
- **`aria-current="page"`** is set automatically on the active sidebar nav
  link; our CSS styles that state (not a custom `is-active` class).

---

## 10. Z-index

Use the scale; never pick a raw number.

| Token | Value | Use |
|---|---|---|
| `z_base` | 1 | default content |
| `z_dropdown` | 100 | selects, popovers |
| `z_sticky` | 200 | sidebar sticky items |
| `z_overlay` | 900 | backdrop |
| `z_modal` | 1000 | modal panels |
| `z_toast` | 1100 | transient notifications |

---

## 11. Iconography

- **Style**: Lucide-outline.
- **Size**: 20×20px (36×36 tile for icon tiles, 40×40 for default).
- **Stroke**: 1.75, `stroke-linecap: round`, `stroke-linejoin: round`,
  `fill: none`, `stroke: currentColor`.
- **Location**: every SVG is an inline `_ICON_*` constant in
  [`src/components.py`](../src/components.py).
- **Colors**: never bake a color into the SVG. Use `currentColor` and let
  the surrounding context pick the color via tokens.
- **No external icon library.** No Font Awesome, no Feather, no Material.
- **No emojis.** If you need a new icon, add a new `_ICON_*` constant.

Current icons: Home, Analytics, Forecasts, Scenarios, Reports, Alerts,
Settings, Sparkle (Ask-AI), Arrow (Ask-AI CTA).

---

## 12. Components

Every primitive lives in [`src/components.py`](../src/components.py). Don't
build the same shape inline on a page — extend the primitive or add a new
one.

| Component | When to use |
|---|---|
| `setup_page(title_key, icon=None)` | Call once, first, on every page. Sets page config, parses `?lang=`, injects CSS. |
| `page_header(title_key, subtitle_key)` | Landing-style header with logo. Overview and upload only. |
| `page_section_header(title_key, subtitle_key, icon_html=None)` | Standard header for every subpage body. Renders `.wisag-page-header`. |
| `sidebar_logo()` / `sidebar_nav()` / `sidebar_language_switcher()` | Must be called in the order logo → nav on every page. |
| `icon_tile(icon, variant='purple', small=False)` | Colored rounded square behind an SVG icon. Variants: `purple`, `red`, `green`, `orange`. |
| `status_pill(level, label)` | Critical / warn / healthy with a colored dot. |
| `severity_badge(level)` | High / medium / low (pill without dot). |
| `impact_pill(eur)` | Signed EUR in a rounded pill, colored by sign. |
| `driver_row(icon, title, subtitle, pct_label, variant)` | A single row inside `.wisag-section-card`. |
| `kpi_tile(label_key, value, delta=None, help_key=None)` | KPI metric with glossary tooltip. |
| `anomaly_card(row)` | Two-column card: left body, right severity+impact. |
| `warning_card(row)` | Driver-row-shaped card for the Alerts list. |
| `nav_tile(icon, title_key, page_path, variant)` | Landing page tile. |
| `hero_card(icon_html, title, subtitle, status_level, status_label, metrics, chart_svg)` | Facility-focus overview. |
| `section_card(title, subtitle, rows_html, hint, footer_link)` | "Why drop" / "What do" card shell. |
| `suggestion_chips(chips, state_key)` | Row of pill-styled buttons. |
| `topbar(breadcrumb_label, breadcrumb_href)` | Breadcrumb container. |
| `friendly_error(message, details)` | German error + collapsible details. |

---

## 13. Pill / badge taxonomy

Three distinct pill families. All share `radius_pill` but differ in what
they communicate. **Always use canonical class names in new code.** Legacy
aliases are kept for backward compatibility but will be removed in a
future pass.

| Family | Meaning | Canonical class | Legacy alias |
|---|---|---|---|
| Severity badge | High / Medium / Low (ordered risk) | `.wisag-badge--severity-high` etc. | `.wisag-badge-high` etc. |
| Impact pill | Positive / Negative / Neutral number | `.wisag-pill--impact-pos` etc. | `.wisag-pill-pos` etc. |
| Status pill | Critical / Warn / Healthy (health dot) | `.wisag-status--critical` etc. | `.wisag-status-pill--critical` etc. |

Emitters in `components.py` currently emit the legacy names; CSS aliases
both. When changing the emitters, remove the alias in the same change.

---

## 14. Layout

- **Sidebar width**: `sidebar_width` = 240px (fixed; no resize).
- **Content max-width**: `content_max_width` = 1240px.
- **Desktop-first**: no breakpoints. Streamlit's native column wrap handles
  the narrow-viewport case.
- **Page structure** every page follows:
  1. `setup_page(...)`
  2. `sidebar_logo()` + `sidebar_nav(active=..., alerts_count=...)`
  3. `page_section_header(title_key, subtitle_key)`
  4. Body sections separated by `<div class='wisag-stack-gap'></div>`

---

## 15. Do / Don't

### Don't

- Inline styles (`style='padding:12px 0;'`) — use a utility class.
- Raw hex, px, rem, or font-weight in `styles.py` or pages — use a token.
- `font-weight: 650`. Use `weight_semibold` (600).
- Emojis anywhere. Add a new `_ICON_*` SVG instead.
- New icon libraries. Stay with inline Lucide-style SVG.
- New root colors or greys. If you need a new shade, extend `theme.py`.
- `!important` on anything besides Streamlit-override selectors where
  specificity forces our hand.
- Custom focus-visible styles per component — inherit the global ring.

### Do

- Add new tokens to `theme.py`, then reference them via f-strings in
  `styles.py`.
- Document non-grid spacing values as dedicated tokens (see §5.2).
- Emit canonical pill class names in new code.
- Keep Streamlit's auto `aria-current="page"` as the active-state source.
- Run `streamlit run app.py` and eyeball every page before merging.

---

## 16. Cheat sheet

### Colors (most-used)

```
accent          #E94E1B   bg_app            #FAFAF7   pos_dark    #1B5E20
accent_dark     #C63D0F   bg_surface        #FFFFFF   neg_dark    #B71C1C
accent_light    #FDE6DC   bg_muted          #F5F5F2   warn_dark   #8A4A00
fg_primary      #1D1D1B   border            #E8E6E1   accent_ai   #EEE9F7
fg_secondary    #6B6B6B   border_strong    #D8D5CE
```

### Spacing (most-used)

```
2   space_1     12   space_6      22   space_22
4   space_2     14   space_7      24   space_10
6   space_3     16   space_8      26   space_26
8   space_4     18   space_18     28   space_12
10  space_5     20   space_9      32   space_14
```

### Radius

```
4   radius_xs    10  radius_lg    14  radius_2xl   999  radius_pill
6   radius_sm    12  radius_xl    16  radius_3xl
8   radius_md
```

### Type

```
text_2xs  0.72    text_base  0.94    text_xl   1.35
text_xs   0.78    text_md    1.02    text_2xl  1.70
text_sm   0.88    text_lg    1.15    text_3xl  1.90
```

### Weights

```
400 weight_regular    500 weight_medium    600 weight_semibold    700 weight_bold
```

### Shadows

```
shadow        0 1px 2px rgba(22,22,20,0.04)       resting cards
shadow_lg     0 4px 14px rgba(22,22,20,0.06)      nav-tile hover
shadow_hero   0 4px 16px rgba(233,78,27,0.18)     gradient hero
shadow_focus  0 0 0 3px rgba(233,78,27,0.25)      focus ring
```

---

## 17. Changelog

- **v1.0 (2026-04-23)** — Initial formalization. Expanded
  [`src/theme.py`](../src/theme.py) from 14 color tokens to 101 tokens
  covering spacing, radius, type, weight, motion, shadow, focus, z-index,
  and layout. Refactored [`src/styles.py`](../src/styles.py) to consume
  every value via tokens. Retired `font-weight: 650`. Canonicalized three
  `warn_dark` variants into one. Promoted lavender Ask-AI colors to
  `accent_ai*` tokens. Added canonical pill / status / badge class names
  alongside legacy aliases. Introduced `page_section_header` helper and
  utility classes (`wisag-empty-row`, `wisag-stack-gap`,
  `wisag-severity-chip`, `wisag-page-header`) to eliminate inline styles
  on pages.
