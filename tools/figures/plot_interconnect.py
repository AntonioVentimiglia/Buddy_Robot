#!/usr/bin/env python3
"""Render the Buddy interconnect — every cable, connector, and pin assignment.

The question this answers is the assembly-day one: what plugs into what, with
which connector, and which wire lands on which pin. The pin table is parsed from
firmware/drive_mcu/docs/pin_map.md rather than retyped, and the connector and
cable details come from the integration map's link records, so the drawing, the
KiCAD schematic, the firmware header, and the shopping list all describe one
harness.

    python3 tools/figures/plot_interconnect.py

Output: assets/figures/interconnect.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import integration as im  # noqa: E402
from pin_map import WHEELS, parse  # noqa: E402
from blockdiagram import Canvas  # noqa: E402
from palette import (  # noqa: E402
    BLUE, CRITICAL, GREEN, GREY, INK, MUTED, PINK, PURPLE,
)

W, H = 1400, 1000


def main() -> int:
    pm = parse()
    c = Canvas(W, H,
               title="Buddy interconnect — what plugs into what, and which pin it lands on",
               subtitle="Pin table parsed from firmware/drive_mcu/docs/pin_map.md; "
                        "connectors and cables from the integration map · "
                        "blue = logic, green = power, pink = sensing")

    # ---- compute, control, actuation --------------------------------------
    jetson = c.box(44, 108, 250, 120, "Jetson Orin Nano Super",
                   "ROS 2 Jazzy · Ubuntu",
                   ["USB-A ×4 host · 40-pin header"], accent=BLUE)
    mcu = c.box(414, 108, 270, 140, "NUCLEO-G474RE",
                "drive MCU · STM32G474RET6",
                ["ST-LINK V3E → USB micro-B",
                 "morpho headers carry every",
                 "driver and encoder signal"],
                accent=CRITICAL)
    drv = c.box(804, 108, 230, 104, "VNH5019 ×4", "one carrier per wheel",
                ["OUT A / OUT B → motor"], accent=GREEN)
    mot = c.box(1124, 108, 232, 104, "goBILDA 5203 ×4",
                "motor + quadrature encoder", accent=GREEN)

    lidar = c.box(804, 300, 230, 92, "LDROBOT LD19", "2D LiDAR · 12 m ToF",
                  ["USB adapter (D300 kit)"], accent=PINK, planned=True)
    imu = c.box(804, 410, 230, 92, "BNO086 breakout", "IMU · on-chip fusion",
                ["I²C, 3.3 V"], accent=PINK, planned=True)
    cam = c.box(1124, 300, 232, 92, "OAK-D Lite", "RGB-D — deferred",
                ["USB 3.0"], accent=PURPLE, planned=True)

    # ---- links (short labels here; the cable list carries the detail) ------
    c.edge(jetson.r(0.35), mcu.l(0.35), color=BLUE, both=True)
    c.tag(354, 138, "USB", color=BLUE, size=9.4)
    c.edge(mcu.r(0.3), drv.l(0.35), color=BLUE)
    c.tag(744, 145, "logic ×4", color=BLUE, size=9.4)
    c.edge(drv.r(0.4), mot.l(0.4), color=GREEN, width=2.2)
    c.tag(1079, 143, "power", color=GREEN, size=9.4)

    # encoders return to the MCU, not to the driver — the rule worth drawing
    c.edge(mot.b(0.5), mcu.b(0.7), color=BLUE, style="vhv", mid=282)
    c.tag(900, 282, "4-pos JST XH breakout → 4 × TJC8", color=BLUE, size=9.4)

    c.edge(lidar.l(0.5), jetson.b(0.6), color=PINK, dash=True,
           via=[(760, lidar.cy), (760, 322), (194, 322)])
    c.tag(500, 322, "USB-A · UART 230400", color=PINK, size=9.4)

    c.edge(imu.l(0.5), jetson.b(0.82), color=PINK, dash=True,
           via=[(740, imu.cy), (740, 382), (249, 382)])
    c.tag(500, 382, "I²C · 40-pin pins 3/5", color=PINK, size=9.4)

    c.edge(cam.l(0.5), lidar.r(0.5), color=PURPLE, dash=True, style="straight")
    c.tag(1079, 346, "USB 3.0", color=PURPLE, size=9.4)

    # ---- the rule ----------------------------------------------------------
    c.label(44, 462,
            "Motor power goes to the DRIVER; the encoder goes to the MCU. "
            "The motor's 8 A power leads never touch a microcontroller pin.",
            size=10.8, color=CRITICAL, weight="600")
    c.rule(44, 480, 1356, GREY, 1.0, dash=True)

    # ---- pin table (parsed, never retyped) --------------------------------
    c.section(44, 512, "drive harness pin assignment — parsed from pin_map.md")
    cols = [("wheel", 44), ("timer", 134), ("ENC A", 232), ("ENC B", 326),
            ("PWM", 432), ("INA", 556), ("INB", 652), ("EN/DIAG", 752),
            ("CS", 872), ("nets", 992)]
    for name, x in cols:
        c.label(x, 542, name, size=9.4, color=MUTED, mono=True, weight="600",
                letter_spacing=0.5)
    c.rule(44, 554, 1070, GREY, 1.0)

    for i, wheel in enumerate(WHEELS):
        y = 574 + i * 26
        e, d = pm["encoders"][wheel], pm["drivers"][wheel]
        cells = [wheel, e["timer"], e["a"], e["b"],
                 f"{d['pwm']} ({d['pwm_ch']})", d["ina"], d["inb"],
                 d["fault"], f"{d['cs']} ({d['cs_ch']})", f"{wheel}_*"]
        for (name, x), val in zip(cols, cells):
            c.label(x, y, val, size=10, mono=True,
                    color=INK if name == "wheel" else MUTED,
                    weight="600" if name == "wheel" else "400")
        c.rule(44, y + 13, 1070, GREY, 0.6)

    c.label(44, 692, "wheel index order everywhere: 0 = LF, 1 = LR, 2 = RF, "
                     "3 = RR — the order the protocol's CMD_VEL payload uses",
            size=9.6, color=MUTED)

    # ---- safety / sense / service pins -------------------------------------
    c.section(44, 726, "safety, sense and service pins")
    for i, (name, v) in enumerate(pm["misc"].items()):
        y = 752 + i * 23
        c.label(44, y, name, size=9.9, color=INK)
        c.label(232, y, v["pin"], size=9.9, color=MUTED, mono=True)
        c.label(326, y, v["direction"], size=9.9, color=MUTED)

    # ---- the cable each link needs ----------------------------------------
    c.section(1096, 512, "the cable each link needs")
    y = 542
    for lid in ("jetson_mcu", "motor_mcu_enc", "driver_motor", "jetson_imu",
                "jetson_lidar"):
        link = im.link(lid)
        c.label(1096, y, f"{link['from']} → {link['to']}", size=9.5, color=INK,
                mono=True)
        c.label(1096, y + 15, link["connector"], size=9.4, color=MUTED)
        y += 15
        if link.get("cable"):
            c.label(1096, y + 15, link["cable"], size=9.4, color=MUTED)
            y += 15
        y += 40

    # ---- footer ------------------------------------------------------------
    c.note(44, 898, [
        "The encoder cable is the BREAKOUT version on purpose: the four encoder pairs "
        "land on TIM2/3/4/8 pins that are deliberately not adjacent, and the encoder's "
        "3.3 V has to reach a different header entirely.",
        "A straight 4-pin-to-4-pin cable physically cannot make this harness.",
        "Assembly-day checks (wiring_harness.md §5): encoders must count up when the "
        "wheel is pushed forward · a wheel spinning backwards is fixed by swapping its "
        "two bullets, never by a sign in firmware ·",
        "every encoder is verified with the motor bus unpowered, before the drivers are "
        "ever energised.",
    ], size=9.7, gap=15)

    c.section(44, 976, "sources")
    c.label(108, 976, "pin_map.md · wiring_harness.md · electrical_interfaces.md · "
                      "electronics/KiCAD/drive_mcu_wiring/ (pin-level schematic)",
            size=9.7, color=MUTED)

    out = REPO / "assets" / "figures" / "interconnect.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
