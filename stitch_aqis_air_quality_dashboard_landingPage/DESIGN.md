---
name: Atmospheric Intelligence
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3e4947'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#6e7977'
  outline-variant: '#bdc9c6'
  surface-tint: '#006a63'
  primary: '#005c55'
  on-primary: '#ffffff'
  primary-container: '#0f766e'
  on-primary-container: '#a3faef'
  inverse-primary: '#80d5cb'
  secondary: '#006399'
  on-secondary: '#ffffff'
  secondary-container: '#7bc2ff'
  on-secondary-container: '#004f7b'
  tertiary: '#445266'
  on-tertiary: '#ffffff'
  tertiary-container: '#5c6a7f'
  on-tertiary-container: '#dfeaff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9cf2e8'
  primary-fixed-dim: '#80d5cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#00504a'
  secondary-fixed: '#cde5ff'
  secondary-fixed-dim: '#94ccff'
  on-secondary-fixed: '#001d32'
  on-secondary-fixed-variant: '#004b74'
  tertiary-fixed: '#d5e3fc'
  tertiary-fixed-dim: '#b9c7df'
  on-tertiary-fixed: '#0d1c2e'
  on-tertiary-fixed-variant: '#3a485b'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-metric:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '500'
    lineHeight: 20px
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  tabular-data:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: -0.005em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  label-xs:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.025em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-lg: 1.5rem
  margin: 1rem
  margin-md: 1.5rem
  margin-lg: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 1.75rem
---

## Brand & Style

This design system is engineered for scientific clarity, operational speed, and low visual fatigue during prolonged analytical sessions. Serving environmental scientists, municipal engineers, and industrial compliance monitors, the interface conveys forensic neutrality and immediate readability. 

The aesthetic is purely functional minimalism: structural integrity through balanced white space, exact 1px containment borders, and zero ornamental gradients, soft blurs, or generic SaaS drop-shadows. The interface feels akin to high-precision laboratory hardware or mission-critical aviation instrumentation rendered digitally—authoritative, unobtrusive, and intensely disciplined.

## Colors

The palette is anchored by stark structural neutrals and supplemented with functional atmospheric accents used strictly to indicate state, threshold, or interactivity.

- **Primary (`#0f766e` - Deep Teal):** Active controls, selected metrics, baseline nominal indicators, and confirmed states. Never applied as ambient background wash.
- **Secondary (`#0369a1` - Deep Sky):** Informational callouts, telemetry links, cross-filter tabs, and comparative timeline overlays.
- **Tertiary (`#475569` - Slate 600):** Axis labels, secondary structural text, inactive tab headers, and auxiliary data icons.
- **Neutral (`#0f172a` - Slate 900):** Primary values, key readings, titles, and terminal borders.

### Surface Architecture
- **Canvas Base:** `#f8fafc` (Slate 50)
- **Component & Card Surface:** `#ffffff` (Pure White)
- **Structural Dividers & Outlines:** `#e2e8f0` (Slate 200)
- **Muted Substrate & Table Headers:** `#f1f5f9` (Slate 100)

### Environmental Severity Tokens
Severity indicators exist solely as utilitarian alerts (badges, status pips, cell highlights):
- **Optimal (AQI 0–50):** `#0f766e`
- **Moderate (AQI 51–100):** `#d97706`
- **Unhealthy for Sensitive (AQI 101–150):** `#ea580c`
- **Unhealthy / Hazardous (AQI 151+):** `#be123c`

## Typography

Typography is restricted to two weights: Regular (400) for prose, body labels, and structural metadata; Medium (500) for metric readouts, navigation items, and interactive headers. Semi-bold and bold styles are deliberately prohibited to prevent visual weight imbalances across complex data matrices.

All numeric metric fields must render with `font-feature-settings: 'tnum' 1, 'cv05' 1` enabled, ensuring tabular figures align precisely along decimals in data tables and stream feeds. Lower-case units (`µg/m³`, `ppm`, `ppb`) inherit Regular 400 at a 1-step downscale relative to their associated integer values.

## Layout & Spacing

The layout operates on an immutable 4px base module, using structured nesting to maintain clean sightlines across dense telemetry panels.

- **Desktop (1280px+):** Fluid 12-column system, `gutter-lg` (24px) column spacing, clamped outer canvas margin of `margin-lg` (32px). Max width 1600px centered on ultrawide monitors.
- **Tablet (768px - 1279px):** 6-column fluid system, 16px gutters, 24px canvas margins. Sensor arrays collapse to 2-column card layouts.
- **Mobile (<768px):** 4-column system, 12px gutters, 16px screen margins. Dynamic parameters and telemetry tables transition to scrollable horizontal strip containers.

Section panels, telemetry grids, and analytics modules maintain vertical separation through consistent multiples of `space-lg` (20px). Internal padding inside operational cards uses `space-md` (12px) for high-density sensor grids and `space-lg` (20px) for macro trend charts.

## Elevation & Depth

This design system avoids drop-shadows entirely. Visual containment and hierarchical separation are achieved through flat surface boundaries and precise contrast calibration:

1. **Surface Separation:** A base canvas of `#f8fafc` contrasted against foreground containers in pure `#ffffff`.
2. **Perimeter Definition:** Every panel, table, input, and standalone card features a uniform border: `1px solid #e2e8f0`.
3. **Stacked Depth (Modals & Flyouts):** Overlays, date pickers, and sensor configuration drawers use a solid `1px solid #cbd5e1` outline and an immediate background fill of `#ffffff`, accompanied by a semi-transparent slate wash backdrop (`#0f172a` at 20% opacity). No blurred backdrop filters or diffused atmospheric glows are allowed.
4. **Nested Regions:** Sub-containers (such as chart tooltips and summary counters) utilize `#f8fafc` with `1px solid #e2e8f0` to articulate internal compartments without elevation artifacts.

## Shapes

Corner radii are restrained to maintain an engineered, dashboard-focused aesthetic:

- **Cards & Data Panels:** Standardized at `rounded-lg` (8px / 0.5rem) to soften large modular surfaces without appearing playful.
- **Micro UI & Interactive Units:** Inputs, dropdown buttons, table row selections, and badges utilize `rounded` (6px) or `rounded-lg` (8px).
- **Status Indicator Dots:** Completely circular (`border-radius: 9999px`) sized at fixed 6px or 8px increments.
- **No pill buttons:** Pill silhouettes are strictly forbidden for actionable buttons and segmented toggles to preserve horizontal layout efficiency in dense toolbars.

## Components

### Buttons & Interactive Controls
- **Primary Button:** Background `#0f766e`, text `#ffffff`, font-weight 500. Height 36px, horizontal padding 14px, radius 8px. Hover state: `#115e59`. Active state: `#134e4a`. No drop-shadows.
- **Secondary / Outline Button:** Background `#ffffff`, border `1px solid #e2e8f0`, text `#0f172a`, font-weight 500. Hover: background `#f8fafc`, border `#cbd5e1`.
- **Ghost Button:** Background transparent, text `#475569`, font-weight 500. Hover: background `#f1f5f9`, text `#0f172a`.
- **Segmented Filter Switch:** A continuous container bordered with `#e2e8f0` housing segmented buttons. The selected state renders `#ffffff` with a `1px solid #cbd5e1` border and `#0f172a` text.

### Badges & Status Chips
- Height 22px, padding 2px 8px, border radius 6px. Font size 11px, weight 500, tabular figures.
- Composed of a solid 6px circular dot positioned adjacent to status text.
- Backgrounds are tint-free or low-saturation: `#f1f5f9` with border `1px solid #e2e8f0` for standard tags; alert badges use subtle contextual borders (e.g., border `#fecdd3`, background `#fff1f2`, text `#9f1239` for critical exceedances).

### Input Fields & Selects
- Height 36px, background `#ffffff`, border `1px solid #e2e8f0`, border-radius 8px.
- Typography: font size 13px, weight 400, text `#0f172a`. Placeholder: `#94a3b8`.
- Focus state: border `1px solid #0f766e`, explicit `outline: 1px solid #0f766e` with 0px offset (crisp technical outline, no blurry focus rings).

### Checkboxes & Radios
- Size: 16px by 16px square (checkbox) or circle (radio).
- Unchecked: background `#ffffff`, border `1px solid #cbd5e1`.
- Checked: background `#0f766e`, border `#0f766e`, inner icon/dot pure `#ffffff`.

### Telemetry Cards & Metric Blocks
- Background `#ffffff`, border `1px solid #e2e8f0`, border-radius 8px, padding 16px.
- Structure: Metric title (12px, weight 500, `#475569`), followed by current value (36px, weight 500, `#0f172a`, tabular digits) paired with unit token (12px, weight 400, `#64748b`), followed by micro trend delta indicator.
- Never use colored card backgrounds; contextual risk is indicated solely via a 2px top border or a status pip.

### Data Tables
- Row height: 40px compact, 48px standard. 
- Header: background `#f8fafc`, bottom border `1px solid #e2e8f0`, typography 11px uppercase, weight 500, tracking 0.025em, text `#475569`.
- Rows: background `#ffffff`, bottom border `1px solid #f1f5f9`. Hover: background `#f8fafc`.
- Numerical columns right-aligned with monospace/tabular-numeric orientation.