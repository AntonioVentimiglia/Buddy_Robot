"""The one Buddy figure palette — imported by every figure script.

Light-mode only, matching the generated website's surface (`tools/site/build_site.py`
CSS) so figures sit on the page without a visible seam. These values were the
validated reference palette used by the first figures; this module exists so the
hexes live in exactly one file instead of being copied into each plot script.

Colour is assigned by the *job it does*, never by series index:

    BLUE      designed operating states, data/command flow
    GREEN     power that is present and healthy
    AMBER     caution, degraded, or "verify before trusting"
    CRITICAL  safety path and fault states — never an operating point
    PURPLE    future/planned hardware (arms, CAN-FD, deferred camera)
    PINK      sensing
    MUTED     neutral, ground, annotation
    ORANGE    the seventh categorical slot; unused so far
"""

from __future__ import annotations

# --- surfaces and ink -------------------------------------------------------
SURFACE = "#fcfcfb"   # figure background — matches the site's --surface
INK = "#0b0b0b"       # primary text
MUTED = "#898781"     # secondary text, annotation
GRID = "#e1e0d9"      # gridlines, box rules — matches the site's --rule
AXIS = "#c3c2b7"      # axis spines

# --- categorical hues, fixed order (never cycled) ---------------------------
BLUE = "#2a78d6"
GREEN = "#1baf7a"
AMBER = "#eda100"
PURPLE = "#4a3aa7"
PINK = "#e87ba4"
GREY = "#898781"
ORANGE = "#eb6834"
STACK = [BLUE, GREEN, AMBER, PURPLE, PINK, GREY, ORANGE]

# --- reserved status colour (not part of STACK) -----------------------------
CRITICAL = "#d03b3b"  # fault / safety path only

# --- neutral fills ----------------------------------------------------------
BAND = "#f0efec"      # requirement bands, inactive regions

# --- free-body-diagram category (plot_drive_fbd only) -----------------------
# A *categorical* red for resisting forces, deliberately not CRITICAL: nothing
# in an FBD is a fault. The two never appear in the same figure, so the near
# hues cannot be confused; keep it that way.
RESIST = "#e34948"

# --- semantic aliases used by the integration diagrams ----------------------
C_DATA = BLUE         # ROS topics, command/telemetry flow
C_POWER = GREEN       # power rails and current paths
C_SAFETY = CRITICAL   # E-stop, watchdog, fault transitions
C_FUTURE = PURPLE     # planned / deferred hardware
C_SENSE = PINK        # sensor feeds
C_NEUTRAL = MUTED     # ground, notes, "not built yet"

# --- typography (mirrors the site CSS and the matplotlib rcParams) ----------
SANS = "Helvetica Neue, Helvetica, Arial, system-ui, sans-serif"
MONO = "SF Mono, Menlo, Consolas, Liberation Mono, monospace"
MPL_SANS = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
