---
name: Odoo Procurement Decision Support
description: A clear operational workspace for sourced procurement decisions
colors:
  paper: "#eff5f1"
  surface: "#FFFFFF"
  ink: "#173e3d"
  muted: "#536964"
  accent: "#413b76"
  accent-hover: "#373164"
  rail: "#153f40"
  connected: "#167466"
  hairline: "#d1ded6"
  error: "#A43E47"
  series-1: "#5b4fc4"
  series-2: "#1a9a7f"
  grid: "#e3ebe6"
  selected: "#f1eff8"
  nav-hover: "#24504f"
typography:
  display:
    fontSize: "35px"
    letterSpacing: "-0.03em"
    lineHeight: 1.14
  headline:
    fontSize: "24px"
    letterSpacing: "-0.015em"
  title:
    fontSize: "20px"
    letterSpacing: "-0.015em"
  body:
    fontFamily: 'Aptos, "Segoe UI Variable", "Segoe UI", system-ui, sans-serif'
    fontSize: "16px"
  label:
    fontSize: "14px"
  caption:
    fontSize: "12px"
  metric:
    fontSize: "28px"
    fontWeight: 650
rounded:
  bar: "4px"
  navigation: "8px"
  terms: "12px"
  card: "14px"
  step: "50%"
spacing:
  compact: "0.5rem"
  related: "0.75rem"
  standard: "1rem"
  card-wide: "1.25rem"
  section: "1.5rem"
  page-wide: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.surface}"
  navigation:
    textColor: "{colors.surface}"
    rounded: "{rounded.navigation}"
    padding: "0.65rem 0.75rem"
  navigation-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.rail}"
    rounded: "{rounded.navigation}"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "1rem"
    width: "100%"
  supplier-terms:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.terms}"
  step-current:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.surface}"
    rounded: "{rounded.step}"
    width: "1.8rem"
    height: "1.8rem"
---

# Design System: Odoo Procurement Decision Support

## Overview

**Creative North Star: "The procurement workspace"**

A professional, clean operational procurement workspace. Deep green navigation anchors pale green pages, white working surfaces and restrained purple actions. The incumbent identity remains green and purple; it is not a blue rebrand.

Hungarian-first bilingual copy, clear sequencing and progressive disclosure help occasional buyers understand the next action. Comparison values and provenance stay legible; subtle state feedback supports work without decorative motion.

**Key Characteristics:**
- Deep green navigation, pale green canvas, purple actions.
- Readable operational density with expandable detail.
- Explicit workflow and honest, sourced values.
- Keyboard, narrow-screen and reduced-motion support.

This is a scan of the implemented system, not a replacement identity. Sources:
`frontend/theme.py`, `frontend/workspace.py`, `frontend/ui.py`,
`frontend/rxconfig.py`, `frontend/components/workflow.py`, and the Home,
RFQ, results and chart modules in `frontend/planning/`. Installed Radix tokens
supply the numeric type sizes; no external font or image asset is required.

## Colors

### Primary
Deep green **rail** anchors persistent navigation; **ink** carries headings and
primary text. Pale green **paper** is the application canvas.

### Secondary
Restrained purple **accent** identifies actions, focus and workflow progress.
**Selected** is the pale purple selection surface. **Accent-hover** comes from
the workspace's Radix accent override; explicitly colored controls may retain
their own background on hover.

### Tertiary
**Connected** supports connection status. **Series-1** and **series-2** distinguish
chart series with direct labels and shapes. **Error** marks the error-state rule;
semantic amber, jade, green, iris and gray badges use Radix palettes, not custom
hex replacements.

The sidecar tonal ramps are generated swatch previews, not application color
tokens. Only the frontmatter values are normative.

### Neutral
White **surface** holds working content; **muted** supports secondary text;
**hairline** separates cards and rows; **grid** keeps chart scaffolding quiet.
**Nav-hover** is the navigation pointer-hover surface.

## Typography

The body font stack applies throughout the workspace. Use installed system fonts;
there is no separate display face or font download. Tabular numerals align values.
Radix sizes 1–8 used here are 12, 14, 16, 18, 20, 24, 28 and 35px at default scaling.
These are a library scale, not an invented modular ratio.

Home uses display size; creation uses size 7 for its main heading; section headings
use sizes 4–6. Shared headings default to size 4. Labels and helper text use sizes
1–2; metrics use size 7 and weight 650. Default heading and body weights remain
Radix-owned unless explicitly overridden. Main headings use balanced wrapping;
secondary headings tighten tracking. Explanations commonly cap at 58–76ch, with
empty/error bodies at 60ch. Inputs keep a minimum 16px font on phones.

## Layout

Desktop-first, fluid and usable on phones. A fixed 14rem rail gives way at Reflex
`lg` to a sticky mobile bar and left drawer. The page frame caps at 92rem with
responsive 1rem, 1.5rem and 2rem padding. Content uses `min-width:0` and wrapping
rather than forcing page-wide overflow. The drawer is at most 20rem or 85vw and
accounts for safe-area inset at the mobile bar.

The preparation wizard is a horizontal, scrollable sequence on larger screens;
at 600px and below it becomes a two-column grid. Demand fields stack initially
and split at `md`; supplier fields expand progressively. Review uses a table at
`md` and above and compact summaries below. Plan cards split at `sm`; at `lg`
the selected allocation occupies a sticky 20rem side column. Home sections split
at `lg`. Retain framework breakpoint names rather than introducing competing
pixel values. Wide comparison tables scroll inside labelled focusable regions.
Case tabs scroll horizontally; changing the view brings the selected tab into view.

## Elevation & Depth

Shared cards, supplier terms and navigation are flat: white and tinted surfaces,
hairline borders and a purple top rule on the decision summary provide hierarchy.
No application shadow scale is defined. Radix overlays and controls retain their
library behavior; do not convert that into an invented custom shadow vocabulary.
The mobile drawer has a translucent deep-green overlay.

## Shapes

Use the frontmatter's card radius for shared cards and its terms radius for
supplier accordions, quotation choices and plan summaries. Navigation, review
rows and tooltips use the navigation radius. Workflow numbers are circular;
allocation bars have the smaller bar radius. Keep these distinct instead of
normalizing every element to one radius. Card padding increases to 1.25rem on
wider layouts.

## Components

### Buttons
Purple solid primary actions; Radix outline and ghost controls for supporting
actions. The theme is light, iris accent, sage gray, small radius. Preserve Radix
button geometry rather than assigning the card radius to controls. Workspace
buttons have a minimum 2.75rem hit height, wrapped text and manipulation touch
behavior. Pointer hover changes color with a 140ms ease transition; enabled press
scales to .98. Disabled controls use a not-allowed cursor; navigation also fades.

### Inputs / Fields
Use labelled Radix controls with attached explanatory text. Focus-within draws a
2px purple outline, offset 2px. Global keyboard focus uses a 3px purple outline,
offset 3px; rail and drawer focus use white. The skip link becomes visible on focus.
Programmatically focused headings do not acquire a decorative outline.

### Chips
Status badges pair text with Radix semantic colors. Source badges distinguish
Odoo, buyer changes and suggestions using database, pencil and information icons.
The current workflow number uses purple fill and white text; inactive numbers
use a white surface, muted text and a hairline border. Color is never the sole
carrier of source, status or chart identity.

### Cards / Containers
Shared white bordered cards hold sections and states. Supplier terms expand under
a full-width button, show source labels and group quantity ranges in fieldsets.
Plan summaries show cost, premium, exposure and allocation before selection.
Selected plans use a pale purple fill and accent border. Selection is explicitly
separate from approval; the selected allocation announces changes politely.

### Navigation
Home, Cases and New procurement live in the deep-green rail or matching drawer.
The active item uses pale green fill, dark text and weight 650. Drawer and discard
dialogs restore focus. HU/EN switching remains visible in the shell. Audit is a
secondary view; expandable explanations keep technical detail out of the main path.

### Feedback and charts
Busy actions disable conflicting navigation and show a spinner or status skeletons.
Error cards use an alert role and offer retry when available; empty states explain
what can happen next. Home displays bounded recent records, never fabricated totals.
Charts read stored values and offer table/text equivalents. Tradeoff points are
labelled directly, use circle/diamond shapes, and retain space from axes; selected
points receive an outline. Recharts series animation is disabled.

Reduced motion shortens animations/transitions to .01ms, one iteration, disables
smooth scrolling and hides closed drawers/overlays while preserving presence
cleanup. Do not add decorative entrance animation.

## Do's and Don'ts

### Do:
- Do retain the incumbent green and purple identity.
- Do use the shared card and source-badge helpers before creating new patterns.
- Do keep Hungarian and English labels understandable and allow them to wrap.
- Do label chart series and keep table or text equivalents nearby.
- Do distinguish selection, calculation, approval and PDF creation.
- Do show bounded recent records honestly, including empty, busy and error states.

### Don't:
- Don't invent library-wide totals from the bounded Home queries.
- Don't present supplier exposure as a failure probability.
- Don't hide the selected mobile tab outside the visible tab strip.
- Don't add decorative motion, a new font dependency or invented elevation.
- Don't replace the Python/Reflex/Radix/Recharts implementation with a standalone React application.
