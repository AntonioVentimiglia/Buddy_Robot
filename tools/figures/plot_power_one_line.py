#!/usr/bin/env python3
"""Render the Buddy power one-line — pack to protection chain to every rail.

`power_budget.svg` answers "how many amps and how many watt-hours". This answers
the different question a wiring diagram has to answer: what is physically in
series with what, which stage protects which, and where each rail actually
comes from.

All ratings come from design_params.yaml through buddy_calcs.power, so the
diagram cannot show a fuse the build validator would reject.

    python3 tools/figures/plot_power_one_line.py

Output: assets/figures/power_one_line.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import P  # noqa: E402
from buddy_calcs import power as bpower  # noqa: E402
from blockdiagram import Canvas, Port  # noqa: E402
from palette import BLUE, CRITICAL, GREEN, GREY, MUTED, PURPLE  # noqa: E402

W, H = 1340, 1064
SPINE_X, SPINE_W = 48, 300
RAIL_X = SPINE_X + SPINE_W / 2
CONV_X, CONV_W = 430, 300
LOAD_X, LOAD_W = 790, 510


def main() -> int:
    s = bpower.summary()
    bus = P["power"]["bus"]
    prot = P["power"]["protection"]
    loads = P["power"]["loads_w"]
    arms = P["power"]["future_arms"]

    c = Canvas(W, H,
               title="Buddy power one-line — pack, protection chain, and every rail",
               subtitle="Ratings from design_params.yaml via buddy_calcs.power — the same "
                        "numbers the build validator enforces · green = power, "
                        "red = protection, purple = provisioned for a later version")

    # ---- source spine ------------------------------------------------------
    batt = c.box(SPINE_X, 104, SPINE_W, 104, "3S Li-ion pack + BMS",
                 f"{bus['v_cutoff']:g}–{bus['v_full']:g} V "
                 f"({bus['v_nominal']:g} V nominal)",
                 [f"≥ {s.ah_target:.0f} Ah (≈ {s.wh_target:.0f} Wh)",
                  f"BMS ≥ {prot['bms_min_continuous_a']:g} A continuous"],
                 accent=GREEN, planned=True, mono_rows=False)
    fuse = c.box(SPINE_X, 244, SPINE_W, 76,
                 f"main fuse {prot['main_fuse_a']:g} A", "slow-blow MIDI/ANL",
                 accent=CRITICAL, planned=True)
    estop = c.box(SPINE_X, 356, SPINE_W, 88, "E-stop contactor",
                  "mushroom switch, ~40 A",
                  ["opens the motor bus in hardware"],
                  accent=CRITICAL, planned=True, mono_rows=False)

    c.edge(batt.b(), fuse.t(), color=GREEN, width=2.4)
    c.edge(fuse.b(), estop.t(), color=GREEN, width=2.4)

    # the bus itself: one rail every branch taps
    c.edge(estop.b(), Port(RAIL_X, 916, "T"), color=GREEN, width=2.6, arrow=False)
    c.tag(RAIL_X, 466, "+12V_BUS", color=GREEN, size=10.5)

    # ---- protection-chain panel -------------------------------------------
    c.group(CONV_X, 104, LOAD_X + LOAD_W - CONV_X, 200,
            "protection chain — each stage must act before the one behind it",
            color=CRITICAL)
    ladder = [
        (f"driver limit\n{P['power']['driver_current_limit_a']:g} A / motor", "firmware chop"),
        (f"BMS ≥ {prot['bms_min_continuous_a']:g} A", "pack protection"),
        (f"fuse {prot['main_fuse_a']:g} A", "slow-blow"),
        ("E-stop", "contactor"),
    ]
    lx, lw, gap = CONV_X + 24, 190, 30
    prev = None
    for i, (title, sub) in enumerate(ladder):
        b = c.box(lx + i * (lw + gap), 152, lw, 74,
                  title.replace("\n", " "), sub, accent=CRITICAL)
        if prev is not None:
            c.edge(prev.r(), b.l(), color=CRITICAL)
        prev = b
    c.note(CONV_X + 24, 258, [
        f"Sized against the {s.peak_with_arms:.0f} A designed peak including the future "
        f"arm branch — not against the {4 * P['drive_motor']['stall_current_a']:.0f} A "
        f"unlimited-stall fault, which the driver current limit makes unreachable.",
        "Stall current is a fault condition, not an operating point. See "
        "power_budget.svg and ADR-0005.",
    ], size=9.8)

    # ---- branches ----------------------------------------------------------
    rows = [
        (486, 92, GREEN, False,
         ("12 V buck", "≥ 5 A regulated", ["isolates compute from motor sag"]),
         ("Jetson Orin Nano Super",
          f"{loads['jetson_orin_nano']:g} W allocation · "
          f"{P['power']['duty_cycle']['jetson_average_w']:g} W typical",
          ["dev-kit input 9–20 V, so even the raw bus is in-window",
           f"also supplies the LD19 over USB ({loads['lidar_2d_reserve']:g} W reserve, 0.9 W actual)"])),
        (598, 124, GREEN, False,
         ("5 V buck", "≥ 3 A", ["logic rail"]),
         ("NUCLEO-G474RE via E5V (JP3 = E5V)",
          f"{loads['mcu_drivers_logic']:g} W allocation for MCU + driver logic + encoders",
          ["the MCU stays alive through a Jetson reboot — USB stays data-only",
           "+3V3 from the Nucleo LDO feeds encoders ×4, VNH5019 logic, BNO086",
           "3.3 V everywhere means no level shifters anywhere in the robot"])),
        (742, 92, GREEN, False,
         ("no converter", "raw, unregulated bus", ["9.0–12.6 V straight to the drivers"]),
         ("VNH5019 ×4  →  goBILDA 5203 ×4",
          f"{P['power']['driver_current_limit_a']:g} A per motor firmware limit "
          f"(device rating 12 A continuous / 30 A peak)",
          ["VNH5019 operating range 5.5–24 V covers the whole discharge curve",
           "motor return GND_PWR stars at the battery, never through the logic ground"])),
        (854, 92, PURPLE, True,
         ("branch fuse", f"{prot['arm_branch_fuse_a']:g} A", ["own protection"]),
         ("dual 6-DOF arms — a later version",
          f"+{arms['avg_power_w']:g} W average, +{arms['peak_current_a']:g} A peak "
          f"(XM430-class placeholder)",
          ["the battery and bus are bought now at this size so the arms cost no rework"])),
    ]

    for y, h, color, planned, (ct, cs, crow), (lt, ls, lrow) in rows:
        conv = c.box(CONV_X, y, CONV_W, h, ct, cs, crow, accent=color,
                     planned=planned, mono_rows=False)
        load = c.box(LOAD_X, y, LOAD_W, h, lt, ls, lrow, accent=color,
                     planned=planned, mono_rows=False)
        c.edge(Port(RAIL_X, y + h / 2, "R"), conv.l(), color=color,
               dash=planned, width=2.0, style="straight")
        c.edge(conv.r(), load.l(), color=color, dash=planned, width=2.0)

    # ---- footer ------------------------------------------------------------
    c.label(SPINE_X, 972,
            "The one rule this diagram exists to make unmissable:", size=11,
            color=CRITICAL, weight="600")
    c.note(SPINE_X, 994, [
        "motor power reaches the MOTORS through the DRIVERS and never touches the "
        "microcontroller. The Nucleo only ever sees logic signals to the driver and "
        "four low-current encoder wires.",
        "Everything on the +12V_BUS is downstream of the E-stop contactor, so the "
        "E-stop removes motion whatever the firmware is doing — the ESTOP_STATE pin "
        "is reporting only.",
    ], size=9.8)

    c.section(SPINE_X, 1036, "sources")
    c.label(SPINE_X + 64, 1036,
            "ADR-0005 (power architecture) · power_budget_and_battery.md · "
            "wiring_harness.md · electrical_interfaces.md",
            size=9.7, color=MUTED)

    out = REPO / "assets" / "figures" / "power_one_line.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
