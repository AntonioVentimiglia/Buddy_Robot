#!/usr/bin/env python3
"""Generate the system wiring schematic — power distribution + interconnect.

Companion sheet to `drive_mcu_wiring` (the drive harness). This one covers
everything that sheet deliberately left out: the pack, the protection chain, the
regulated rails, and every link between the Jetson, the drive MCU and the
sensors. The two sheets meet at shared net names (+12V_BUS, +5V_RAIL, +3V3, GND,
GND_PWR, ESTOP_STATE), so a reader can follow a rail across both.

Ratings in the annotations are read from design_params.yaml — the schematic
cannot print a fuse size the build validator would reject.

    python3 tools/kicad/gen_system_wiring.py
    python3 tools/kicad/check_system_wiring.py    # netlist assertions
    python3 tools/kicad/render_schematics.py      # SVG for the figures/site

Output: electronics/KiCAD/system_wiring/system_wiring.kicad_sch (+ .kicad_pro)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import P  # noqa: E402
from kicad_sch import Sheet  # noqa: E402

OUT = ROOT / "electronics" / "KiCAD" / "system_wiring"

# ---------------------------------------------------------------- symbols --
BATTERY_PINS = [("PACK+", "R", 0), ("PACK-", "R", 2)]
FUSE_PINS = [("1", "L", 0), ("2", "R", 0)]
ESTOP_PINS = [("IN", "L", 0), ("OUT", "R", 0), ("AUX_NC", "R", 3)]
BUCK_PINS = [("VIN", "L", 0), ("GND_IN", "L", 2),
             ("VOUT", "R", 0), ("GND_OUT", "R", 2)]
JETSON_PINS = [
    ("VIN_12V", "L", 0), ("GND", "L", 2),
    ("USB0", "R", 0), ("USB1", "R", 1), ("USB2", "R", 2),
    ("HDR_3V3", "R", 4), ("HDR_SDA", "R", 5), ("HDR_SCL", "R", 6),
    ("HDR_GND", "R", 7),
]
NUCLEO_PINS = [
    ("E5V", "L", 0), ("GND", "L", 2), ("USB_STLINK", "L", 4),
    ("3V3_OUT", "R", 0), ("ESTOP_IN", "R", 2),
]
LD19_PINS = [("USB", "L", 0)]
IMU_PINS = [("VIN", "L", 0), ("GND", "L", 1), ("SDA", "L", 3), ("SCL", "L", 4)]
OAKD_PINS = [("USB3", "L", 0)]
ARMS_PINS = [("V+", "L", 0), ("GND", "L", 2)]
# The drive harness sheet, seen as a block: these are the nets the two sheets
# share. Change a name here and check_drive_wiring.py will disagree.
DRIVE_PINS = [
    ("+12V_BUS", "L", 0), ("GND_PWR", "L", 1), ("+5V_RAIL", "L", 3),
    ("+3V3", "L", 4), ("GND", "L", 5), ("ESTOP_STATE", "L", 7),
    ("USB_VCP", "L", 9),
]


def main() -> int:
    prot = P["power"]["protection"]
    bus = P["power"]["bus"]
    i_lim = P["power"]["driver_current_limit_a"]

    sh = Sheet("system_wiring", "Buddy system wiring — power distribution and interconnect",
               "2026-07-28", paper="A2")

    sh.define("BATTERY_3S", BATTERY_PINS, 24, 14)
    sh.define("FUSE", FUSE_PINS, 16, 8)
    sh.define("ESTOP_CONTACTOR", ESTOP_PINS, 22, 14)
    sh.define("BUCK_12V", BUCK_PINS, 22, 12)
    sh.define("BUCK_5V", BUCK_PINS, 22, 12)
    sh.define("ARM_FUSE", FUSE_PINS, 16, 8)
    sh.define("JETSON_ORIN_NANO", JETSON_PINS, 28, 26)
    sh.define("NUCLEO_G474RE_SYS", NUCLEO_PINS, 26, 18)
    sh.define("LD19_LIDAR", LD19_PINS, 22, 8)
    sh.define("BNO086_IMU", IMU_PINS, 22, 12)
    sh.define("OAKD_LITE", OAKD_PINS, 22, 8)
    sh.define("FUTURE_ARMS", ARMS_PINS, 22, 10)
    sh.define("DRIVE_HARNESS_SHEET", DRIVE_PINS, 30, 22)

    # ---- source and protection chain -------------------------------------
    batt = sh.place("BATTERY_3S", "BT1",
                    f"3S Li-ion + BMS >= {prot['bms_min_continuous_a']:g}A "
                    f"({bus['v_cutoff']:g}-{bus['v_full']:g}V)", 55, 95)
    sh.nets(batt, {"PACK+": "PACK+", "PACK-": "GND_PWR"})

    fuse = sh.place("FUSE", "F1", f"{prot['main_fuse_a']:g}A slow-blow (MIDI/ANL)",
                    135, 95)
    sh.nets(fuse, {"1": "PACK+", "2": "BUS_FUSED"})

    estop = sh.place("ESTOP_CONTACTOR", "K1", "E-stop contactor ~40A", 205, 95)
    sh.nets(estop, {"IN": "BUS_FUSED", "OUT": "+12V_BUS",
                    "AUX_NC": "ESTOP_STATE"})

    # ---- regulated rails ---------------------------------------------------
    b12 = sh.place("BUCK_12V", "U10", "12V buck >=5A (Jetson)", 290, 65)
    sh.nets(b12, {"VIN": "+12V_BUS", "GND_IN": "GND_PWR",
                  "VOUT": "+12V_JETSON", "GND_OUT": "GND"})

    b5 = sh.place("BUCK_5V", "U11", "5V buck >=3A (logic)", 290, 130)
    sh.nets(b5, {"VIN": "+12V_BUS", "GND_IN": "GND_PWR",
                 "VOUT": "+5V_RAIL", "GND_OUT": "GND"})

    af = sh.place("ARM_FUSE", "F2",
                  f"{prot['arm_branch_fuse_a']:g}A arm branch (future)", 290, 195)
    sh.nets(af, {"1": "+12V_BUS", "2": "ARM_BRANCH"})

    # ---- compute, control, sensing ----------------------------------------
    jet = sh.place("JETSON_ORIN_NANO", "A1", "Jetson Orin Nano Super", 400, 80)
    sh.nets(jet, {"VIN_12V": "+12V_JETSON", "GND": "GND",
                  "USB0": "USB_MCU", "USB1": "USB_LIDAR", "USB2": "USB_CAMERA",
                  "HDR_3V3": "+3V3_JETSON", "HDR_SDA": "I2C_SDA",
                  "HDR_SCL": "I2C_SCL", "HDR_GND": "GND"})

    nuc = sh.place("NUCLEO_G474RE_SYS", "U1", "NUCLEO-G474RE (JP3 = E5V)", 400, 175)
    sh.nets(nuc, {"E5V": "+5V_RAIL", "GND": "GND", "USB_STLINK": "USB_MCU",
                  "3V3_OUT": "+3V3", "ESTOP_IN": "ESTOP_STATE"})

    arms = sh.place("FUTURE_ARMS", "A9", "dual 6-DOF arms (later version)", 400, 240)
    sh.nets(arms, {"V+": "ARM_BRANCH", "GND": "GND_PWR"})

    lidar = sh.place("LD19_LIDAR", "S1", "LDROBOT LD19 (D300 USB adapter)", 510, 60)
    sh.nets(lidar, {"USB": "USB_LIDAR"})

    imu = sh.place("BNO086_IMU", "S2", "BNO086 IMU breakout", 510, 110)
    sh.nets(imu, {"VIN": "+3V3_JETSON", "GND": "GND",
                  "SDA": "I2C_SDA", "SCL": "I2C_SCL"})

    cam = sh.place("OAKD_LITE", "S3", "OAK-D Lite (deferred, ADR-0007)", 510, 160)
    sh.nets(cam, {"USB3": "USB_CAMERA"})

    drive = sh.place("DRIVE_HARNESS_SHEET", "SH1",
                     "drive_mcu_wiring sheet (4x VNH5019 + 4x 5203)", 510, 235)
    sh.nets(drive, {"+12V_BUS": "+12V_BUS", "GND_PWR": "GND_PWR",
                    "+5V_RAIL": "+5V_RAIL", "+3V3": "+3V3", "GND": "GND",
                    "ESTOP_STATE": "ESTOP_STATE", "USB_VCP": "USB_MCU"})

    # ---- notes -------------------------------------------------------------
    for s, x, y, size in [
        ("Buddy system wiring - power distribution and interconnect (nets by label)",
         20, 18, 2.5),
        ("Generated by tools/kicad/gen_system_wiring.py from design_params.yaml -"
         " regenerate, don't hand-edit.", 20, 25, 1.6),
        ("Connectivity machine-checked by tools/kicad/check_system_wiring.py.",
         20, 30, 1.6),
        ("Companion sheet: electronics/KiCAD/drive_mcu_wiring/ (pin-level drive"
         " harness). The two sheets share", 20, 37, 1.6),
        ("+12V_BUS, GND_PWR, +5V_RAIL, +3V3, GND and ESTOP_STATE - follow a rail"
         " across both by net name.", 20, 42, 1.6),
        (f"Protection chain: driver limit {i_lim:g}A/motor (firmware) ->"
         f" BMS >= {prot['bms_min_continuous_a']:g}A ->"
         f" fuse {prot['main_fuse_a']:g}A -> E-stop contactor. ADR-0005.",
         20, 49, 1.6),
        ("The E-stop opens +12V_BUS itself; K1's AUX_NC contact only REPORTS the"
         " state to the MCU on PB12.", 20, 54, 1.6),
        ("The LD19 is powered from the Jetson USB port through the D300 adapter,"
         " not from +5V_RAIL.", 20, 59, 1.6),
        ("BNO086 sits on the Jetson 40-pin header (+3V3_JETSON), a different 3.3V"
         " rail from the Nucleo LDO's +3V3.", 20, 64, 1.6),
        ("GND_PWR is the motor/battery return, starred at the pack; GND is the"
         " logic return. Single-point tie at the pack.", 20, 69, 1.6),
    ]:
        sh.text(s, x, y, size)

    sch = sh.write(OUT)
    print(f"wrote {sch.relative_to(ROOT)} ({sh.net_count} net labels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
