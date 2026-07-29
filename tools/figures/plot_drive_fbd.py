#!/usr/bin/env python3
"""Render the free-body diagrams behind docs/analysis/drive_torque_and_pivot_scrub.md.

Left panel:  side-view FBD on a ramp (straight-line tractive force, section 2).
Right panel: top-view pivot kinematics (scrub moment balance, section 6).

    python3 tools/figures/plot_drive_fbd.py [--png [path]]

Output: assets/figures/drive_fbd.svg
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Arc
from matplotlib.transforms import Affine2D

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from buddy_calcs import P  # noqa: E402

# geometry from design_params.yaml (single source of truth)
WHEEL_X = P["wheels"]["x_offset_m"]
WHEEL_Y = P["wheels"]["y_offset_m"]
CHASSIS_L = P["chassis"]["length_m"]
CHASSIS_W = P["chassis"]["width_m"]
WHEEL_DIA = 2 * P["wheels"]["radius_m"]
WHEEL_TH = P["wheels"]["width_m"]

# palette — one definition for every Buddy figure (tools/figures/palette.py)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import AXIS, BAND, INK, MPL_SANS, MUTED, SURFACE  # noqa: E402
from palette import BLUE  # drive/tractive forces                  # noqa: E402
from palette import RESIST as RED  # resisting forces (friction, rolling res.)
from palette import PURPLE as VIOLET  # weight/normal pair          # noqa: E402


def arrow(ax, xy0, xy1, color, lw=2.0, style="-|>", ls="solid", zorder=6):
    ax.add_patch(FancyArrowPatch(xy0, xy1, arrowstyle=style, mutation_scale=14,
                                 color=color, lw=lw, linestyle=ls, zorder=zorder))


def ramp_panel(ax):
    theta_draw = 18  # exaggerated for legibility; labeled symbolically
    th = math.radians(theta_draw)
    # ramp wedge
    ax.fill([0, 4.4, 4.4], [0, 0, 4.4 * math.tan(th)], color=BAND, zorder=1)
    ax.plot([0, 4.4], [0, 4.4 * math.tan(th)], color=AXIS, lw=1.5, zorder=2)
    ax.plot([0, 4.4], [0, 0], color=AXIS, lw=1.2, zorder=2)
    ax.add_patch(Arc((0, 0), 2.4, 2.4, theta1=0, theta2=theta_draw, color=MUTED, lw=1.2))
    ax.text(1.36, 0.16, r"$\theta$", fontsize=12, color=INK)

    # robot body on the incline
    cx, cy = 2.5, 2.5 * math.tan(th)
    body = Rectangle((cx - 0.62, cy + 0.10), 1.24, 0.55, facecolor="#ffffff",
                     edgecolor=INK, lw=1.4, zorder=4)
    body.set_transform(Affine2D().rotate_deg_around(cx, cy, theta_draw) + ax.transData)
    ax.add_patch(body)
    # CG of body (in rotated frame)
    gx = cx - 0.375 * math.sin(th) + 0.0
    gy = cy + 0.375 * math.cos(th)
    ax.plot([gx], [gy], marker="o", markersize=5, color=INK, zorder=6)

    ux, uy = math.cos(th), math.sin(th)          # up-slope unit vector
    nx, ny = -math.sin(th), math.cos(th)         # surface normal unit vector

    # weight (from CG, straight down)
    arrow(ax, (gx, gy), (gx, gy - 1.5), VIOLET)
    ax.text(gx + 0.07, gy - 1.5, r"$mg$", fontsize=12, color=VIOLET)
    # normal (from contact, along surface normal)
    arrow(ax, (cx, cy), (cx + 1.1 * nx, cy + 1.1 * ny), VIOLET)
    ax.text(cx + 1.1 * nx - 0.55, cy + 1.1 * ny + 0.10, r"$N = mg\cos\theta$",
            fontsize=11, color=VIOLET)
    # tractive force (up-slope, at contact)
    arrow(ax, (cx, cy), (cx + 1.5 * ux, cy + 1.5 * uy), BLUE)
    ax.text(cx + 1.55 * ux, cy + 1.5 * uy - 0.22, r"$F$ (tractive)", fontsize=11,
            color=BLUE, fontweight="bold")
    # rolling resistance (down-slope, at contact)
    arrow(ax, (cx, cy), (cx - 1.0 * ux, cy - 1.0 * uy), RED)
    ax.text(cx - 1.05 * ux, cy - 1.05 * uy + 0.30, r"$C_{rr}mg\cos\theta$",
            fontsize=11, color=RED, ha="right")
    # acceleration annotation (kinematic, dashed hollow arrow above body)
    ax0 = (gx + 0.45 * ux, gy + 0.45 * uy + 0.28)
    ax1 = (gx + 1.35 * ux, gy + 1.35 * uy + 0.28)
    arrow(ax, ax0, ax1, MUTED, lw=1.6, ls=(0, (4, 3)))
    ax.text(ax1[0] - 0.1, ax1[1] + 0.12, r"$a$", fontsize=12, color=MUTED)

    ax.text(0.1, 3.55, r"$F = ma + mg\sin\theta + C_{rr}mg\cos\theta$",
            fontsize=11.5, color=INK)
    ax.set_title("Straight-line: ramp free-body diagram", fontsize=11,
                 color=INK, loc="left")
    ax.set_xlim(-0.4, 4.6)
    ax.set_ylim(-0.55, 4.0)


def pivot_panel(ax):
    s = 10.0  # meters -> plot units
    # chassis and wheels (top view; +x forward/up in this drawing)
    ax.add_patch(Rectangle((-CHASSIS_W / 2 * s, -CHASSIS_L / 2 * s),
                           CHASSIS_W * s, CHASSIS_L * s, facecolor="#ffffff",
                           edgecolor=INK, lw=1.4, zorder=3))
    for sx in (+1, -1):      # lateral side (y)
        for sy in (+1, -1):  # fore-aft (x)
            wx, wy = sx * WHEEL_Y * s, sy * WHEEL_X * s
            ax.add_patch(Rectangle((wx - WHEEL_TH / 2 * s, wy - WHEEL_DIA / 2 * s),
                                   WHEEL_TH * s, WHEEL_DIA * s, facecolor=BAND,
                                   edgecolor=INK, lw=1.2, zorder=4))
            # friction: tangential, opposing CCW pivot -> clockwise tangent
            r = math.hypot(wx, wy)
            tx, ty = wy / r, -wx / r  # clockwise tangent unit vector
            arrow(ax, (wx, wy), (wx + 1.05 * tx, wy + 1.05 * ty), RED, lw=1.8)
            # drive force: longitudinal (along chassis x, drawn vertical);
            # CCW pivot -> right side forward, left side reverse
            ddir = +1 if sx > 0 else -1
            arrow(ax, (wx, wy), (wx, wy + 1.3 * ddir), BLUE, lw=2.0)

    # pivot center + rotation arrow
    ax.plot([0], [0], marker="o", markersize=5, color=INK, zorder=6)
    ax.add_patch(Arc((0, 0), 1.5, 1.5, theta1=210, theta2=120, color=MUTED, lw=1.6,
                     zorder=5))
    arrow(ax, (0.72, 0.32), (0.62, 0.48), MUTED, lw=1.6)
    ax.text(0.30, 0.78, r"$\omega$", fontsize=12, color=MUTED)

    # radius d to front-right wheel patch
    wx, wy = WHEEL_Y * s, WHEEL_X * s
    ax.plot([0, wx], [0, wy], color=MUTED, lw=1.2, linestyle=(0, (4, 3)), zorder=5)
    ax.text(wx / 2 + 0.16, wy / 2 - 0.32, r"$d$", fontsize=12, color=MUTED, zorder=6)

    # lateral offset dimension y_w
    yline = -CHASSIS_L / 2 * s - 1.15
    arrow(ax, (0, yline), (WHEEL_Y * s, yline), MUTED, lw=1.1, style="<|-|>")
    ax.plot([0, 0], [yline - 0.18, yline + 0.18], color=MUTED, lw=1.0)
    ax.plot([WHEEL_Y * s, WHEEL_Y * s], [yline - 0.18, yline + 0.18], color=MUTED, lw=1.0)
    ax.text(WHEEL_Y * s / 2 - 0.30, yline - 0.62, r"$y_w$", fontsize=11, color=MUTED)

    # legend-ish labels
    ax.text(-3.4, 3.35, "drive force (longitudinal)", fontsize=10, color=BLUE,
            fontweight="bold")
    ax.text(-3.4, 2.90, r"scrub friction $\mu N$ (tangential)", fontsize=10,
            color=RED, fontweight="bold")
    ax.text(-3.4, -3.9, r"$\mu\, mg\, d \;=\; 4\,F_{wheel}\,y_w$", fontsize=11.5,
            color=INK)
    ax.set_title("Pivot-in-place: top view, moment balance", fontsize=11,
                 color=INK, loc="left")
    ax.set_xlim(-3.6, 3.6)
    ax.set_ylim(-4.3, 3.8)


def main() -> int:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": MPL_SANS,
        "svg.fonttype": "none",
        "svg.hashsalt": "buddy",
        "mathtext.fontset": "dejavusans",
    })
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 5.0), dpi=100)
    fig.patch.set_facecolor(SURFACE)
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        ax.set_aspect("equal")
        ax.axis("off")
    ramp_panel(ax1)
    pivot_panel(ax2)
    fig.suptitle("Buddy drive-base force models (docs/analysis/drive_torque_and_pivot_scrub.md)",
                 fontsize=12, color=INK, x=0.02, ha="left")

    out = REPO / "assets" / "figures" / "drive_fbd.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="svg", bbox_inches="tight", facecolor=SURFACE,
                metadata={"Date": None})
    print(f"wrote {out.relative_to(REPO)}")
    if len(sys.argv) > 1 and sys.argv[1] == "--png":
        png = Path(sys.argv[2]) if len(sys.argv) > 2 else out.with_suffix(".png")
        fig.savefig(png, format="png", dpi=160, bbox_inches="tight", facecolor=SURFACE)
        print(f"wrote {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
