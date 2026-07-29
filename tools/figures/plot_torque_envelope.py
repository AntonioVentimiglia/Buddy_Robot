#!/usr/bin/env python3
"""Render the Buddy v0.1 per-wheel torque envelope figure.

Equations and every parameter come from buddy_calcs (design_params.yaml +
requirements yaml), so the figure cannot drift from the analysis. Regenerated
by tools/build.py, or directly:

    python3 tools/figures/plot_torque_envelope.py

Output: assets/figures/torque_envelope.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from buddy_calcs import P, R  # noqa: E402
from buddy_calcs.drive import pivot_torque as _pivot, torque_nm  # noqa: E402

# v0.1 design parameters — all from design_params.yaml / requirements yaml
MASS_KG = R["mass"]["design_gross_mass_limit_kg"]
WHEEL_R = P["wheels"]["radius_m"]
DRIVEN = P["drive_motor"]["count"]
CRR = P["assumptions"]["crr_carpet"]
EFF = P["assumptions"]["drivetrain_efficiency"]
SF = P["assumptions"]["safety_factor"]
ACCEL = P["assumptions"]["accel_design_mps2"]
WHEEL_X = P["wheels"]["x_offset_m"]
WHEEL_Y = P["wheels"]["y_offset_m"]
MU_LO = P["assumptions"]["scrub_mu"]["carpet_low"]
MU_HI = P["assumptions"]["scrub_mu"]["carpet_high"]
STALL_SELECTED = P["drive_motor"]["stall_torque_nm"]
RAMP_DESIGN = R["mobility"]["ramp_angle_v0_1_deg"]

# Palette — one definition for every Buddy figure (tools/figures/palette.py)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import AXIS, BAND, GRID, INK, MPL_SANS, MUTED, SURFACE  # noqa: E402
from palette import BLUE as SERIES_1  # climb + accel (design case)  # noqa: E402
from palette import GREEN as SERIES_2  # steady climb (direct-labeled)


def pivot_torque(mu: float) -> float:
    """Per-wheel torque to pivot in place against tire scrub (peak/stall)."""
    return _pivot(mu, MASS_KG, WHEEL_R, WHEEL_X, WHEEL_Y, EFF)


def main() -> int:
    ramps = [r / 2 for r in range(0, 41)]  # 0..20 deg
    t_accel = [torque_nm(MASS_KG, WHEEL_R, DRIVEN, ACCEL, r, CRR, EFF, SF) for r in ramps]
    t_steady = [torque_nm(MASS_KG, WHEEL_R, DRIVEN, 0.0, r, CRR, EFF, SF) for r in ramps]
    piv_lo, piv_hi = pivot_torque(MU_LO), pivot_torque(MU_HI)

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": MPL_SANS,
        "svg.fonttype": "none",
        "svg.hashsalt": "buddy",
    })
    fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=100)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # Pivot-in-place requirement band (dominant constraint)
    ax.axhspan(piv_lo, piv_hi, color=BAND, zorder=1)
    ax.text(0.4, piv_hi + 0.08, f"pivot-in-place on carpet ($\\mu$ = {MU_LO:g}–{MU_HI:g}) — peak / stall requirement",
            fontsize=9, color=INK, va="bottom", zorder=4)

    # Motor stall reference lines (identity by label, not color)
    for stall, name, label_x, ha in [
        (STALL_SELECTED, "goBILDA 5203 26.9:1 stall — selected", 20.0, "right"),
        (2.65, "Pololu 37D 70:1 stall", 10.4, "left"),
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
    t_design = torque_nm(MASS_KG, WHEEL_R, DRIVEN, ACCEL, RAMP_DESIGN, CRR, EFF, SF)
    ax.plot([RAMP_DESIGN], [t_design], marker="o", markersize=9, color=SERIES_1,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=6)
    ax.annotate(f"v0.1 design case\n{RAMP_DESIGN:g}° ramp: {t_design:.2f} N·m", (RAMP_DESIGN, t_design),
                xytext=(6.2, 0.85), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

    ax.set_xlim(0, 20)
    ax.set_ylim(0, 4.4)
    ax.set_xlabel("Ramp angle (deg)", fontsize=10, color=MUTED)
    ax.set_ylabel("Torque per wheel (N·m)", fontsize=10, color=MUTED)
    ax.set_title(f"Buddy v0.1 per-wheel torque envelope — {MASS_KG:g} kg, "
                 f"r = {WHEEL_R:g} m ({WHEEL_R*2000:g} mm Hogback), {DRIVEN} driven wheels",
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
