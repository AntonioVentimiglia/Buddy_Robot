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
# SANS/MONO are CSS font *stacks* written into the SVG. They are rendered by the
# viewer, so listing several is right: each reader gets the best font they have.
SANS = "Helvetica Neue, Helvetica, Arial, system-ui, sans-serif"
MONO = "SF Mono, Menlo, Consolas, Liberation Mono, monospace"

# MPL_SANS is different in kind, and must stay a single bundled font.
#
# matplotlib resolves this list against the fonts INSTALLED ON THE BUILD MACHINE
# and measures glyph widths with whichever it finds. Those widths set the text
# extents, `bbox_inches="tight"` sizes the canvas from the extents, and the
# result is baked into the committed SVG. A list starting with "Helvetica Neue"
# therefore produced 560.109531pt on macOS and 557.195pt on Windows (which has
# no Helvetica Neue and fell through to Arial) — same code, same numbers,
# different output bytes, and a noisy diff on every cross-machine rebuild.
#
# DejaVu Sans ships INSIDE matplotlib, so it is byte-identical on every install
# including CI. Layout geometry is now machine-independent. Note this only fixes
# the measuring: `svg.fonttype="none"` means glyphs are not outlined, so the SVG
# still carries the SANS stack above and readers still see Helvetica if they
# have it. Determinism where it matters, appearance where it doesn't.
MPL_SANS = ["DejaVu Sans"]
