"""Deterministic SVG block-diagram primitives for Buddy's integration figures.

Matplotlib draws Buddy's *quantitative* figures well and its block diagrams
badly, so the integration diagrams (ROS graph, control/safety loop, power
one-line, interconnect, state machine, startup sequence) are emitted as SVG
directly from this module. It is deliberately dependency-free and deterministic:
no timestamps, no UUIDs, no font metrics from the host — the same inputs always
produce byte-identical output, which is what lets the figures be committed
artifacts like everything else `tools/build.py` generates.

Coordinates are plain SVG user units (px) with y growing downward. Nothing here
knows anything about Buddy; the drawing scripts supply all content.

    from blockdiagram import Canvas, BOX_W
    c = Canvas(1180, 760, title="...", subtitle="...")
    jetson = c.box(60, 100, 240, 78, "Jetson Orin Nano", "ROS 2 Jazzy")
    mcu    = c.box(460, 100, 240, 78, "NUCLEO-G474RE", "drive MCU")
    c.edge(jetson.r(), mcu.l(), label="/dev/buddy_drive_mcu")
    c.save(path)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from palette import (  # noqa: E402
    AMBER, BLUE, CRITICAL, GRID, INK, MONO, MUTED, SANS, SURFACE,
)

# Nominal advance widths as a fraction of font size. Real font metrics are not
# available (and would make output host-dependent), so text is measured with a
# constant-ratio estimate. Boxes are explicitly sized by the caller; this is
# only used to centre labels and to size the halo behind edge labels, where a
# few percent of error is invisible.
_W_SANS = 0.53
_W_MONO = 0.60

# Baseline offset for vertically centring a line of text at a given y.
# Computed rather than using dominant-baseline, which not every SVG renderer
# (including some markdown/PDF pipelines) honours.
_BASELINE = 0.35


def text_w(s: str, size: float, mono: bool = False) -> float:
    """Estimated rendered width of `s`, in user units."""
    return len(s) * size * (_W_MONO if mono else _W_SANS)


def wrap(s: str, max_w: float, size: float, mono: bool = False) -> list[str]:
    """Greedy word wrap to a pixel width — box labels size themselves."""
    lines: list[str] = []
    cur = ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if not cur or text_w(trial, size, mono) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ------------------------------------------------------------------ geometry --
@dataclass(frozen=True)
class Port:
    """A connection point on a shape, carrying the side it leaves from."""
    x: float
    y: float
    side: str  # "L" | "R" | "T" | "B"

    def shifted(self, dx: float = 0.0, dy: float = 0.0) -> "Port":
        return Port(self.x + dx, self.y + dy, self.side)


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def l(self, frac: float = 0.5) -> Port:  # noqa: E743 - reads as "left"
        return Port(self.x, self.y + self.h * frac, "L")

    def r(self, frac: float = 0.5) -> Port:
        return Port(self.x + self.w, self.y + self.h * frac, "R")

    def t(self, frac: float = 0.5) -> Port:
        return Port(self.x + self.w * frac, self.y, "T")

    def b(self, frac: float = 0.5) -> Port:
        return Port(self.x + self.w * frac, self.y + self.h, "B")


def _rounded_path(pts: list[tuple[float, float]], r: float = 7.0) -> str:
    """Polyline through `pts` with rounded corners, as an SVG path."""
    if len(pts) < 3:
        return "M " + " L ".join(f"{x:g},{y:g}" for x, y in pts)
    out = [f"M {pts[0][0]:g},{pts[0][1]:g}"]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        d_in = max(abs(x1 - x0), abs(y1 - y0))
        d_out = max(abs(x2 - x1), abs(y2 - y1))
        rr = min(r, d_in / 2, d_out / 2)
        if rr < 1:
            out.append(f"L {x1:g},{y1:g}")
            continue
        ux, uy = (x1 - x0), (y1 - y0)
        n = max(abs(ux), abs(uy)) or 1
        ax, ay = x1 - ux / n * rr, y1 - uy / n * rr
        vx, vy = (x2 - x1), (y2 - y1)
        m = max(abs(vx), abs(vy)) or 1
        bx, by = x1 + vx / m * rr, y1 + vy / m * rr
        out.append(f"L {ax:g},{ay:g} Q {x1:g},{y1:g} {bx:g},{by:g}")
    out.append(f"L {pts[-1][0]:g},{pts[-1][1]:g}")
    return " ".join(out)


def _route(a: Port, b: Port, style: str | None, mid: float | None,
           via: list[tuple[float, float]] | None) -> list[tuple[float, float]]:
    """Orthogonal waypoints from port `a` to port `b`."""
    p0, p1 = (a.x, a.y), (b.x, b.y)
    if via:
        return [p0, *via, p1]
    if style is None:
        pair = (a.side, b.side)
        if pair in (("R", "L"), ("L", "R")):
            style = "hvh"
        elif pair in (("B", "T"), ("T", "B")):
            style = "vhv"
        elif a.side in ("L", "R"):
            style = "hv"
        else:
            style = "vh"
    if style == "straight" or a.x == b.x or a.y == b.y:
        return [p0, p1]  # already collinear — an elbow would be a kink
    if style == "hvh":
        xm = mid if mid is not None else (a.x + b.x) / 2
        return [p0, (xm, a.y), (xm, b.y), p1]
    if style == "vhv":
        ym = mid if mid is not None else (a.y + b.y) / 2
        return [p0, (a.x, ym), (b.x, ym), p1]
    if style == "hv":
        return [p0, (b.x, a.y), p1]
    if style == "vh":
        return [p0, (a.x, b.y), p1]
    raise ValueError(f"unknown route style {style!r}")


# -------------------------------------------------------------------- canvas --
@dataclass
class Canvas:
    width: float
    height: float
    title: str = ""
    subtitle: str = ""
    _bg: list[str] = field(default_factory=list)
    _edges: list[str] = field(default_factory=list)
    _fg: list[str] = field(default_factory=list)
    _arrow_colors: set[str] = field(default_factory=set)
    # audit bookkeeping — see audit()
    _boxes: list[tuple[float, float, float, float, str]] = field(default_factory=list)
    _marks: list[tuple[float, float, float, float, str, int]] = field(default_factory=list)
    _overflows: list[str] = field(default_factory=list)

    # ----------------------------------------------------------- containers --
    def group(self, x: float, y: float, w: float, h: float, label: str = "",
              color: str = MUTED, fill: str | None = None,
              dash: bool = True) -> Box:
        """A labelled region behind the boxes (a subsystem or physical unit)."""
        style = ' stroke-dasharray="6 5"' if dash else ""
        f = f'fill="{fill}"' if fill else 'fill="none"'
        self._bg.append(
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="9" '
            f'{f} stroke="{color}" stroke-width="1.1" opacity="0.9"{style}/>')
        if label:
            self._bg.append(self._text(x + 13, y + 15, label, 10.5, color,
                                       mono=True, weight="600",
                                       letter_spacing=0.7))
        return Box(x, y, w, h)

    def box(self, x: float, y: float, w: float, h: float, title: str,
            subtitle: str = "", rows: tuple[str, ...] | list[str] = (),
            accent: str = BLUE, planned: bool = False, fill: str = SURFACE,
            title_size: float = 12.5, mono_rows: bool = True) -> Box:
        """A component. `planned` draws it dashed — not built/bought yet."""
        stroke = MUTED if planned else GRID
        dash = ' stroke-dasharray="5 4"' if planned else ""
        self._fg.append(
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="5" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"{dash}/>')
        self._fg.append(
            f'<rect x="{x + 1.5:g}" y="{y + 1.5:g}" width="3" '
            f'height="{h - 3:g}" rx="1.5" fill="{accent}"'
            f'{" opacity=\"0.45\"" if planned else ""}/>')

        inner = w - 22  # clear of the accent bar and both borders
        lines: list[tuple[str, float, str, bool, str]] = [
            (ln, title_size, INK, False, "600")
            for ln in wrap(title, inner, title_size)]
        for ln in (wrap(subtitle, inner, 10.5) if subtitle else []):
            lines.append((ln, 10.5, MUTED, False, "400"))
        for r in rows:
            for ln in wrap(r, inner, 9.8, mono_rows):
                lines.append((ln, 9.8, MUTED, mono_rows, "400"))

        owner = len(self._boxes)
        self._boxes.append((x, y, w, h, title))

        heights = [15.5 if s >= title_size else (13.0 if s > 10 else 12.2)
                   for (_, s, _, _, _) in lines]
        total = sum(heights)
        if total > h - 6:
            self._overflows.append(
                f"box {title!r} needs {total:.0f}px of text in a {h:.0f}px box")
        cursor = y + h / 2 - total / 2
        cx = x + w / 2 + 2  # nudge right of the accent bar
        for (txt, size, color, mono, weight), lh in zip(lines, heights):
            yy = cursor + lh / 2
            self._fg.append(self._text(cx, yy, txt, size, color,
                                       mono=mono, weight=weight, anchor="middle"))
            tw = text_w(txt, size, mono)
            self._marks.append((cx - tw / 2, yy - size * 0.7, cx + tw / 2,
                                yy + size * 0.7, txt, owner))
            cursor += lh
        return Box(x, y, w, h)

    # ---------------------------------------------------------------- edges --
    def edge(self, a: Port, b: Port, label: str = "", color: str = BLUE,
             style: str | None = None, mid: float | None = None,
             via: list[tuple[float, float]] | None = None, dash: bool = False,
             width: float = 1.6, both: bool = False, arrow: bool = True,
             label_at: float = 0.5, label_dx: float = 0.0,
             label_dy: float = 0.0, label_mono: bool = True,
             label_size: float = 9.5) -> None:
        pts = _route(a, b, style, mid, via)
        self._arrow_colors.add(color)
        key = color.lstrip("#")
        markers = ""
        if arrow:
            markers += f' marker-end="url(#arw-{key})"'
        if both:
            markers += f' marker-start="url(#arws-{key})"'
        d = ' stroke-dasharray="5 4"' if dash else ""
        self._edges.append(
            f'<path d="{_rounded_path(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="{width:g}" stroke-linecap="round" '
            f'stroke-linejoin="round"{d}{markers}/>')
        if label:
            lx, ly = _point_along(pts, label_at)
            self.tag(lx + label_dx, ly + label_dy, label, color=color,
                     mono=label_mono, size=label_size)

    def tag(self, x: float, y: float, label: str, color: str = MUTED,
            mono: bool = True, size: float = 9.5, weight: str = "500") -> None:
        """A short label with a surface-coloured halo, for placing on a line."""
        w = text_w(label, size, mono) + 9
        self._edges.append(
            f'<rect x="{x - w / 2:g}" y="{y - size * 0.78:g}" width="{w:g}" '
            f'height="{size * 1.56:g}" rx="3" fill="{SURFACE}" opacity="0.94"/>')
        self._edges.append(self._text(x, y, label, size, color, mono=mono,
                                      weight=weight, anchor="middle"))
        self._marks.append((x - w / 2, y - size * 0.78, x + w / 2,
                            y + size * 0.78, f"label {label!r}", -1))

    # ---------------------------------------------------------------- text --
    def label(self, x: float, y: float, text: str, size: float = 11,
              color: str = MUTED, mono: bool = False, weight: str = "400",
              anchor: str = "start", letter_spacing: float = 0.0,
              audit: bool = True) -> None:
        self._fg.append(self._text(x, y, text, size, color, mono=mono,
                                   weight=weight, anchor=anchor,
                                   letter_spacing=letter_spacing))
        if audit:
            tw = text_w(text, size, mono)
            x0 = {"start": x, "middle": x - tw / 2, "end": x - tw}[anchor]
            self._marks.append((x0, y - size * 0.7, x0 + tw, y + size * 0.7,
                                f"text {text[:34]!r}", -1))

    def rule(self, x1: float, y: float, x2: float, color: str = GRID,
             width: float = 1.0, dash: bool = False) -> None:
        d = ' stroke-dasharray="4 4"' if dash else ""
        self._bg.append(
            f'<path d="M {x1:g},{y:g} L {x2:g},{y:g}" stroke="{color}" '
            f'stroke-width="{width:g}"{d}/>')

    def vrule(self, x: float, y1: float, y2: float, color: str = GRID,
              width: float = 1.0, dash: bool = False) -> None:
        d = ' stroke-dasharray="3 5"' if dash else ""
        self._bg.append(
            f'<path d="M {x:g},{y1:g} L {x:g},{y2:g}" stroke="{color}" '
            f'stroke-width="{width:g}"{d}/>')

    def section(self, x: float, y: float, text: str, color: str = MUTED) -> None:
        """An uppercase mono eyebrow, matching the website's section styling."""
        self.label(x, y, text.upper(), size=9.5, color=color, mono=True,
                   weight="600", letter_spacing=1.1)

    def note(self, x: float, y: float, lines: list[str], size: float = 9.8,
             color: str = MUTED, gap: float = 13.5) -> None:
        for i, line in enumerate(lines):
            self.label(x, y + i * gap, line, size=size, color=color)

    def legend(self, x: float, y: float,
               items: list[tuple[str, str]], gap: float = 15.0,
               kind: str = "line", size: float = 9.8) -> None:
        """items = [(color, label), ...] stacked vertically."""
        for i, (color, text) in enumerate(items):
            yy = y + i * gap
            if kind == "line":
                self._fg.append(
                    f'<path d="M {x:g},{yy:g} L {x + 20:g},{yy:g}" '
                    f'stroke="{color}" stroke-width="2.2" '
                    f'stroke-linecap="round"/>')
            else:
                self._fg.append(
                    f'<rect x="{x:g}" y="{yy - 5:g}" width="18" height="10" '
                    f'rx="2.5" fill="{color}"/>')
            self.label(x + 27, yy, text, size=size, color=MUTED)

    def _text(self, x: float, y: float, s: str, size: float, color: str,
              mono: bool = False, weight: str = "400", anchor: str = "start",
              letter_spacing: float = 0.0) -> str:
        ls = f' letter-spacing="{letter_spacing:g}"' if letter_spacing else ""
        return (f'<text x="{x:g}" y="{y + size * _BASELINE:g}" '
                f'font-family="{MONO if mono else SANS}" font-size="{size:g}" '
                f'font-weight="{weight}" fill="{color}" '
                f'text-anchor="{anchor}"{ls}>{esc(s)}</text>')

    # --------------------------------------------------------------- audit --
    def audit(self, margin: float = 2.0) -> list[str]:
        """Geometry problems a reader would see: collisions and overflow.

        The Browser pane is not always available to eyeball a figure, and
        "I looked at it once" does not survive a parameter change that makes a
        label longer. This makes layout a checked property instead: every
        component box, every label, and every edge tag is bounds-checked against
        the canvas and against each other. Called by each drawing script, so a
        collision fails `tools/build.py` rather than shipping quietly.

        Text extents use the constant-ratio estimate from `text_w`, so this
        catches real overlaps and near-misses, not sub-pixel kerning.
        """
        problems: list[str] = list(self._overflows)

        def overlap(a, b, pad: float = 0.0) -> bool:
            return (a[0] < b[2] - pad and b[0] < a[2] - pad
                    and a[1] < b[3] - pad and b[1] < a[3] - pad)

        for x, y, w, h, name in self._boxes:
            if x < margin or y < margin or x + w > self.width - margin \
                    or y + h > self.height - margin:
                problems.append(f"box {name!r} runs outside the canvas")

        for i, (x1, y1, w1, h1, n1) in enumerate(self._boxes):
            for x2, y2, w2, h2, n2 in self._boxes[i + 1:]:
                if overlap((x1, y1, x1 + w1, y1 + h1),
                           (x2, y2, x2 + w2, y2 + h2), pad=0.5):
                    problems.append(f"boxes {n1!r} and {n2!r} overlap")

        for x0, y0, x1, y1, what, owner in self._marks:
            if x0 < margin or y0 < margin or x1 > self.width - margin \
                    or y1 > self.height - margin:
                problems.append(f"{what} runs outside the canvas")
            for j, (bx, by, bw, bh, bname) in enumerate(self._boxes):
                if j == owner:
                    continue
                if overlap((x0, y0, x1, y1), (bx, by, bx + bw, by + bh), pad=1.0):
                    problems.append(f"{what} collides with box {bname!r}")
            if owner >= 0:
                bx, by, bw, bh, bname = self._boxes[owner]
                if x0 < bx + 2 or x1 > bx + bw - 2:
                    problems.append(f"{what} overflows its box {bname!r}")

        for i, m1 in enumerate(self._marks):
            for m2 in self._marks[i + 1:]:
                if m1[5] >= 0 and m1[5] == m2[5]:
                    continue  # lines stacked inside the same box
                if overlap(m1[:4], m2[:4], pad=1.0):
                    problems.append(f"{m1[4]} collides with {m2[4]}")
        return problems

    def check(self) -> None:
        """Audit and abort the build on any layout problem."""
        problems = self.audit()
        if problems:
            for p in problems:
                print(f"LAYOUT: {p}", file=sys.stderr)
            raise SystemExit(f"{len(problems)} layout problems in {self.title!r}")

    # -------------------------------------------------------------- render --
    def render(self) -> str:
        defs = []
        for color in sorted(self._arrow_colors):
            key = color.lstrip("#")
            defs.append(
                f'<marker id="arw-{key}" markerWidth="9" markerHeight="8" '
                f'refX="8.4" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
                f'<path d="M0.6,0.6 L8.4,4 L0.6,7.4 Z" fill="{color}"/></marker>')
            defs.append(
                f'<marker id="arws-{key}" markerWidth="9" markerHeight="8" '
                f'refX="0.6" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
                f'<path d="M8.4,0.6 L0.6,4 L8.4,7.4 Z" fill="{color}"/></marker>')

        head = []
        if self.title:
            head.append(self._text(28, 26, self.title, 15, INK, weight="700"))
        if self.subtitle:
            head.append(self._text(28, 47, self.subtitle, 10.8, MUTED))

        body = "\n  ".join(defs + head + self._bg + self._edges + self._fg)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{self.width:g}" height="{self.height:g}" '
                f'viewBox="0 0 {self.width:g} {self.height:g}" '
                f'role="img" aria-label="{esc(self.title)}">\n'
                f'  <rect width="{self.width:g}" height="{self.height:g}" '
                f'fill="{SURFACE}"/>\n  {body}\n</svg>\n')

    def save(self, path: Path) -> Path:
        self.check()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(), encoding="utf-8", newline="\n")
        return path


def _point_along(pts: list[tuple[float, float]], frac: float) -> tuple[float, float]:
    """Point at `frac` of the total path length — where an edge label goes."""
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lengths = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in segs]
    target = sum(lengths) * frac
    for (a, b), ln in zip(segs, lengths):
        if target <= ln or ln == 0:
            t = (target / ln) if ln else 0.0
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        target -= ln
    return pts[-1]


# Re-exported so drawing scripts import one module.
__all__ = ["Canvas", "Box", "Port", "text_w", "esc",
           "BLUE", "AMBER", "CRITICAL", "MUTED", "INK", "GRID", "SURFACE"]
