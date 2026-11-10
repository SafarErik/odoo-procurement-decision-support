"""Visual tokens of the workspace: every colour, radius and repeated size the views use.

Names follow the DESIGN.md frontmatter (``accent-hover`` -> ``ACCENT_HOVER``). Views
import the constants; the shell's CSS reads them through ``TOKENS`` as ``$NAME``.
"""

# Colours named in DESIGN.md.
PAPER = "#eff5f1"
SURFACE = "#FFFFFF"
INK = "#173e3d"
MUTED = "#536964"
ACCENT = "#413b76"
ACCENT_HOVER = "#373164"
RAIL = "#153f40"
HAIRLINE = "#d1ded6"
ERROR = "#A43E47"
# Chart series: validated pair (lightness, chroma, CVD and contrast checks pass on white).
SERIES_1 = "#5b4fc4"
SERIES_2 = "#1a9a7f"
GRID = "#e3ebe6"
SELECTED = "#f1eff8"
NAV_HOVER = "#24504f"

# Supporting colours the views use but DESIGN.md does not name.
SUBTLE = "#f6f9f7"  # row hover, nested scenario lists, the scenario draft panel
POLICY_PANEL = "#e7eeea"  # wizard policy explanation box
BAR_TRACK = "#e6ece8"  # empty part of an allocation bar
RADIO_RING = "#9fb3ab"  # unchosen plan radio on Overview
FIELD_ERROR = "#92313b"  # inline wizard field error text
ACCENT_A8 = "#71699c"  # Radix accent step 8 override
TEXT_SELECTION = "#d8d2f0"
BRAND_BORDER = "#668b85"  # brand mark outline on the rail
BRAND_ICON = "#e4eee9"
RECOVERY_BORDER = "#956018"  # "uncertain save" recovery panel
RECOVERY_BACKGROUND = "#FFF8EB"
DRAWER_OVERLAY = "rgba(21,63,64,.35)"  # RAIL at 35 %
LANGUAGE_SWITCH = "rgba(255,255,255,.92)"  # HU/EN switch on the dark rail

# Radii (DESIGN.md rounded).
RADIUS_BAR = "4px"
RADIUS_NAV = "8px"
RADIUS_TERMS = "12px"
RADIUS_CARD = "14px"
RADIUS_STEP = "50%"

# Repeated sizes (DESIGN.md spacing and layout).
CARD_PADDING = ["1rem", "1.25rem"]  # standard, card-wide from the sm breakpoint
PAGE_PADDING = ["1rem", "1.5rem", "2rem"]
PAGE_MAX_WIDTH = "92rem"
RAIL_WIDTH = "14rem"
SIDE_COLUMN = "20rem"  # sticky selected-plan and selected-case column at lg
TOUCH_TARGET = "2.75rem"  # minimum hit height of buttons and native fields
FONT_BODY = 'Aptos, "Segoe UI Variable", "Segoe UI", system-ui, sans-serif'

TOKENS = {name: value for name, value in dict(globals()).items() if name.isupper()}
