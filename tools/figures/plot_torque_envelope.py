#!/usr/bin/env python3
"""Render the Buddy v0.1 per-wheel torque envelope figure.

Imports the sizing math from robot_ws/tools/torque_sweep.py so the figure can
never drift from the analysis. Regenerate after any parameter change:

    python3 tools/figures/plot_torque_envelope.py

Output: assets/figures/torque_envelope.svg
Parameters mirror docs/research/hardware/motors_and_gearboxes/motor_sizing_and_selection.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "robot_ws" / "tools"))
from torque_sweep import torque_nm  # noqa: E402

# v0.1 design parameters (single place; keep in sync with the sizing doc)
MASS_KG = 20.0
WHEEL_R = 0.06
DRIVEN = 4
CRR = 0.05
EFF = 0.75
SF = 2.0
ACCEL = 0.5
WHEEL_X, WHEEL_Y = 0.09, 0.13  # from buddy_params.xacro

# Palette (validated reference palette, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES_1 = "#2a78d6"  # blue: climb + accel (design case)
SERIES_2 = "#1baf7a"  # aqua: steady climb (sub-3:1 on light -> direct-labeled)
BAND = "#f0efec"      # neutral requirement band


def pivot_torque(mu: float) -> float:
    """Per-wheel torque to pivot in place against tire scrub (peak/stall)."""
    contact_r = math.hypot(WHEEL_X, WHEEL_Y)
    resist_moment = mu * MASS_KG * 9.80665 * contact_r
    return (resist_moment / (4 * WHEEL_Y)) * WHEEL_R / EFF


def main() -> int:
    ramps = [r / 2 for r in range(0, 41)]  # 0..20 deg
    t_accel = [torque_nm(MASS_KG, WHEEL_R, DRIVEN, ACCEL, r, CRR, EFF, SF) for r in ramps]
    t_steady = [torque_nm(MASS_KG, WHEEL_R, DRIVEN, 0.0, r, CRR, EFF, SF) for r in ramps]
    piv_lo, piv_hi = pivot_torque(0.6), pivot_torque(0.8)

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "svg.fonttype": "none",
    })
    fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=100)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # Pivot-in-place requirement band (dominant constraint)
    ax.axhspan(piv_lo, piv_hi, color=BAND, zorder=1)
    ax.text(0.4, (piv_lo + piv_hi) / 2, "pivot-in-place on carpet ($\\mu$ = 0.6–0.8)\npeak / stall requirement",
            fontsize=9, color=INK, va="center", zorder=4)

    # Motor stall reference lines (identity by label, not color)
    for stall, name, label_x, ha in [
        (3.73, "goBILDA 5203 26.9:1 stall — selected", 20.0, "right"),
        (2.65, "Pololu 37D 70:1 stall", 0.4, "left"),
        (2.00, "Waveshare DDSM115 stall", 20.0, "right"),
    ]:
        emphasized = "selected" in name
        ax.axhline(stall, color=INK if emphasized else MUTED,
                   linestyle=(0, (5, 4)), linewidth=1.4 if emphasized else 1.0, zorder=3)
        ax.text(label_x, stall + 0.05, name, fontsize=9, ha=ha,
                color=INK if emphasized else MUTED, zorder=4,
                fontweight="bold" if emphasized else "normal")

    # Computed envelope curves (SF 2.0, eta 0.75 included)
    ax.plot(ramps, t_accel, color=SERIES_1, linewidth=2, zorder=5,
            label=f"climb + {ACCEL} m/s² accel (SF {SF:g})")
    ax.plot(ramps, t_steady, color=SERIES_2, linewidth=2, zorder=5,
            label=f"steady climb (SF {SF:g})")
    # v0.1 design point: 5 deg ramp + accel
    t_design = torque_nm(MASS_KG, WHEEL_R, DRIVEN, ACCEL, 5.0, CRR, EFF, SF)
    ax.plot([5.0], [t_design], marker="o", markersize=9, color=SERIES_1,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=6)
    ax.annotate(f"v0.1 design case\n5° ramp: {t_design:.2f} N·m", (5.0, t_design),
                xytext=(6.2, 0.85), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

    ax.set_xlim(0, 20)
    ax.set_ylim(0, 4.4)
    ax.set_xlabel("Ramp angle (deg)", fontsize=10, color=MUTED)
    ax.set_ylabel("Torque per wheel (N·m)", fontsize=10, color=MUTED)
    ax.set_title("Buddy v0.1 per-wheel torque envelope — 20 kg, r = 0.06 m, 4 driven wheels",
                 fontsize=12, color=INK, pad=14, loc="left")
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(AXIS)
    ax.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=INK)

    out = REPO / "assets" / "figures" / "torque_envelope.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="svg", bbox_inches="tight", facecolor=SURFACE)
    print(f"wrote {out.relative_to(REPO)}")
    if len(sys.argv) > 1 and sys.argv[1] == "--png":
        png = Path(sys.argv[2]) if len(sys.argv) > 2 else out.with_suffix(".png")
        fig.savefig(png, format="png", dpi=160, bbox_inches="tight", facecolor=SURFACE)
        print(f"wrote {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
