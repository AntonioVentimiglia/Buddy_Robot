#!/usr/bin/env python3
"""Generate the drive-MCU wiring schematic (KiCAD 10, format 20260306).

Block-level harness diagram: NUCLEO-G474RE <-> 4x VNH5019 <-> 4x goBILDA 5203
motors/encoders, plus power rails, current-sense, faults, E-stop and Vbat
divider. Connectivity is by named nets (global labels placed on pin ends),
matching firmware/drive_mcu/docs/pin_map.md and include/pins.h — change those
and this together.

    python3 tools/kicad/gen_drive_wiring.py
    # validate + render:
    kicad-cli sch export svg -o <outdir> electronics/KiCAD/drive_mcu_wiring/drive_mcu_wiring.kicad_sch

Output: electronics/KiCAD/drive_mcu_wiring/drive_mcu_wiring.kicad_sch (+ .kicad_pro)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "electronics" / "KiCAD" / "drive_mcu_wiring"

FONT = "(effects (font (size 1.27 1.27)))"
FONT_S = "(effects (font (size 1.016 1.016)))"


def u() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------- symbols --
# pins: (name, side, slot) — side L/R/T/B, slot = position index on that side
WHEELS = ["LF", "LR", "RF", "RR"]

NUCLEO_PINS = [
    # encoders (left side)
    ("PA0 TIM2_CH1", "L", 0), ("PA1 TIM2_CH2", "L", 1),
    ("PA6 TIM3_CH1", "L", 2), ("PA7 TIM3_CH2", "L", 3),
    ("PB6 TIM4_CH1", "L", 4), ("PB7 TIM4_CH2", "L", 5),
    ("PC6 TIM8_CH1", "L", 6), ("PC7 TIM8_CH2", "L", 7),
    # ADC + safety (left, lower group)
    ("PC0 ADC1_IN6", "L", 9), ("PC1 ADC1_IN7", "L", 10),
    ("PC2 ADC1_IN8", "L", 11), ("PC3 ADC1_IN9", "L", 12),
    ("PC4 ADC2_IN5", "L", 13), ("PB12 ESTOP_IN", "L", 14),
    # PWM + direction + faults (right side)
    ("PA8 TIM1_CH1", "R", 0), ("PA9 TIM1_CH2", "R", 1),
    ("PA10 TIM1_CH3", "R", 2), ("PA11 TIM1_CH4", "R", 3),
    ("PB0", "R", 5), ("PB1", "R", 6), ("PB2", "R", 7), ("PB10", "R", 8),
    ("PB4", "R", 9), ("PB5", "R", 10), ("PB13", "R", 11), ("PB14", "R", 12),
    ("PC10", "R", 14), ("PC11", "R", 15), ("PC12", "R", 16), ("PD2", "R", 17),
    # power (top)
    ("E5V", "T", 0), ("3V3", "T", 1), ("GND", "T", 2),
]

VNH_PINS = [
    ("VDD", "L", 0), ("INA", "L", 1), ("INB", "L", 2), ("PWM", "L", 3),
    ("EN/DIAG", "L", 4), ("CS", "L", 5), ("GND", "L", 6),
    ("VIN", "R", 0), ("OUTA", "R", 2), ("OUTB", "R", 3), ("GND_P", "R", 5),
]

MOTOR_PINS = [
    ("M+", "L", 0), ("M-", "L", 1),
    ("ENC_3V3", "L", 3), ("ENC_A", "L", 4), ("ENC_B", "L", 5), ("ENC_GND", "L", 6),
]

R_PINS = [("1", "T", 0), ("2", "B", 0)]

PITCH = 2.54


def snap(v: float) -> float:
    """Snap to KiCAD's 1.27 mm connection grid (off-grid pins break netlisting)."""
    return round(v / 1.27) * 1.27


def sym_def(name: str, pins: list, half_w: float, half_h: float) -> str:
    """Symbol library entry: rectangle body + line pins on a 2.54 grid."""
    body = []
    for i, (pname, side, slot) in enumerate(pins, start=1):
        if side == "L":
            x, y, ang = -half_w - PITCH, -half_h + PITCH * (slot + 1), 0
        elif side == "R":
            x, y, ang = half_w + PITCH, -half_h + PITCH * (slot + 1), 180
        elif side == "T":
            x, y, ang = -half_w + PITCH * (slot + 2), -half_h - PITCH, 270
        else:
            x, y, ang = -half_w + PITCH * (slot + 2), half_h + PITCH, 90
        body.append(
            f'(pin passive line (at {x:g} {y:g} {ang}) (length {PITCH:g}) '
            f'(name "{pname}" {FONT_S}) (number "{i}" {FONT_S}))')
    return f'''    (symbol "Buddy:{name}" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 {-half_h - 2 * PITCH:g} 0) {FONT})
      (property "Value" "{name}" (at 0 {half_h + 2 * PITCH:g} 0) {FONT})
      (symbol "{name}_0_1"
        (rectangle (start {-half_w:g} {-half_h:g}) (end {half_w:g} {half_h:g})
          (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "{name}_1_1"
        {chr(10).join("        " + p for p in body)})
    )'''


def pin_pos(inst_x, inst_y, pins, half_w, half_h, pname):
    """Connection-point coordinates of a pin on a placed instance (angle 0).
    Schematic y grows downward, so the symbol-space y is mirrored."""
    for (name, side, slot) in pins:
        if name != pname:
            continue
        if side == "L":
            sx, sy = -half_w - PITCH, -half_h + PITCH * (slot + 1)
        elif side == "R":
            sx, sy = half_w + PITCH, -half_h + PITCH * (slot + 1)
        elif side == "T":
            sx, sy = -half_w + PITCH * (slot + 2), -half_h - PITCH
        else:
            sx, sy = -half_w + PITCH * (slot + 2), half_h + PITCH
        return inst_x + sx, inst_y - sy, side
    raise KeyError(pname)


PROJECT = "drive_mcu_wiring"
ROOT_UUID = u()


def instance(lib: str, ref: str, value: str, x: float, y: float,
             npins: int, half_h: float = 12.7) -> str:
    pins = "\n".join(f'    (pin "{i}" (uuid "{u()}"))' for i in range(1, npins + 1))
    return f'''  (symbol (lib_id "Buddy:{lib}") (at {x:g} {y:g} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")
    (property "Reference" "{ref}" (at {x:g} {y - half_h - 5.08:g} 0) {FONT})
    (property "Value" "{value}" (at {x:g} {y + half_h + 5.08:g} 0) {FONT})
{pins}
    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))
  )'''


def glabel(net: str, x: float, y: float, side: str) -> str:
    ang, justify = (0, "left") if side in ("R", "T") else (180, "right")
    if side == "T":
        ang, justify = 90, "left"
    if side == "B":
        ang, justify = 270, "right"
    return (f'  (global_label "{net}" (shape input) (at {x:g} {y:g} {ang}) '
            f'(fields_autoplaced yes) (effects (font (size 1.27 1.27)) '
            f'(justify {justify})) (uuid "{u()}"))')


def text(s: str, x: float, y: float, size: float = 1.5) -> str:
    return (f'  (text "{s}" (exclude_from_sim no) (at {x:g} {y:g} 0) '
            f'(effects (font (size {size:g} {size:g})) (justify left)) (uuid "{u()}"))')


def main() -> int:
    parts: list[str] = []
    labels: list[str] = []

    # ---- NUCLEO instance
    NUC_W, NUC_H = 27.94, 25.4
    nx, ny = snap(90), snap(130)
    parts.append(instance("NUCLEO_G474RE", "U1", "NUCLEO-G474RE (drive MCU)",
                          nx, ny, len(NUCLEO_PINS), NUC_H))
    nuc_nets = {
        "PA0 TIM2_CH1": "LF_ENC_A", "PA1 TIM2_CH2": "LF_ENC_B",
        "PA6 TIM3_CH1": "LR_ENC_A", "PA7 TIM3_CH2": "LR_ENC_B",
        "PB6 TIM4_CH1": "RF_ENC_A", "PB7 TIM4_CH2": "RF_ENC_B",
        "PC6 TIM8_CH1": "RR_ENC_A", "PC7 TIM8_CH2": "RR_ENC_B",
        "PC0 ADC1_IN6": "LF_CS", "PC1 ADC1_IN7": "LR_CS",
        "PC2 ADC1_IN8": "RF_CS", "PC3 ADC1_IN9": "RR_CS",
        "PC4 ADC2_IN5": "VBAT_SENSE", "PB12 ESTOP_IN": "ESTOP_STATE",
        "PA8 TIM1_CH1": "LF_PWM", "PA9 TIM1_CH2": "LR_PWM",
        "PA10 TIM1_CH3": "RF_PWM", "PA11 TIM1_CH4": "RR_PWM",
        "PB0": "LF_INA", "PB1": "LF_INB", "PB2": "LR_INA", "PB10": "LR_INB",
        "PB4": "RF_INA", "PB5": "RF_INB", "PB13": "RR_INA", "PB14": "RR_INB",
        "PC10": "LF_FLT", "PC11": "LR_FLT", "PC12": "RF_FLT", "PD2": "RR_FLT",
        "E5V": "+5V_RAIL", "3V3": "+3V3", "GND": "GND",
    }
    for pname, net in nuc_nets.items():
        x, y, side = pin_pos(nx, ny, NUCLEO_PINS, NUC_W, NUC_H, pname)
        labels.append(glabel(net, x, y, side))

    # ---- 4x VNH5019 + motors
    VNH_W, VNH_H = 17.78, 11.43
    MOT_W, MOT_H = 20.32, 11.43
    for i, w in enumerate(WHEELS):
        vy = snap(55 + i * 55)
        parts.append(instance("VNH5019_CARRIER", f"U{i + 2}",
                              f"VNH5019 ({w})", snap(210), vy, len(VNH_PINS), VNH_H))
        vnh_nets = {"VDD": "+3V3", "INA": f"{w}_INA", "INB": f"{w}_INB",
                    "PWM": f"{w}_PWM", "EN/DIAG": f"{w}_FLT", "CS": f"{w}_CS",
                    "GND": "GND", "VIN": "+12V_BUS", "GND_P": "GND_PWR",
                    "OUTA": f"{w}_M+", "OUTB": f"{w}_M-"}
        for pname, net in vnh_nets.items():
            x, y, side = pin_pos(snap(210), vy, VNH_PINS, VNH_W, VNH_H, pname)
            labels.append(glabel(net, x, y, side))

        parts.append(instance("GOBILDA_5203", f"M{i + 1}",
                              f"goBILDA 5203 ({w})", snap(330), vy, len(MOTOR_PINS), MOT_H))
        mot_nets = {"M+": f"{w}_M+", "M-": f"{w}_M-", "ENC_3V3": "+3V3",
                    "ENC_A": f"{w}_ENC_A", "ENC_B": f"{w}_ENC_B",
                    "ENC_GND": "GND"}
        for pname, net in mot_nets.items():
            x, y, side = pin_pos(snap(330), vy, MOTOR_PINS, MOT_W, MOT_H, pname)
            labels.append(glabel(net, x, y, side))

    # ---- Vbat divider (10:1 into PC4)
    RW, RH = 2.54, 5.08
    parts.append(instance("R_DIV", "R1", "90k (10:1 upper)", snap(60), snap(215), 2, RH))
    parts.append(instance("R_DIV", "R2", "10k (10:1 lower)", snap(60), snap(240), 2, RH))
    for ref, ry, nets in (("R1", snap(215), ("+12V_BUS", "VBAT_SENSE")),
                          ("R2", snap(240), ("VBAT_SENSE", "GND"))):
        for pname, net in zip(("1", "2"), nets):
            x, y, side = pin_pos(snap(60), ry, R_PINS, RW, RH, pname)
            labels.append(glabel(net, x, y, side))

    # ---- notes
    notes = [
        ("Buddy drive MCU wiring — block-level harness (nets by label)", 20, 20, 2.5),
        ("Source of truth: firmware/drive_mcu/docs/pin_map.md + include/pins.h;", 20, 26, 1.5),
        ("generated by tools/kicad/gen_drive_wiring.py — regenerate, don't hand-edit.", 20, 30, 1.5),
        ("PA2/PA3 = USART2 -> ST-LINK VCP -> Jetson USB (on-board, not wired here). ADR-0006.", 20, 36, 1.5),
        ("Power: +12V_BUS via 60 A fuse from 3S pack (ADR-0005); +5V_RAIL buck powers Nucleo E5V (JP3=E5V);", 20, 40, 1.5),
        ("+3V3 from Nucleo LDO feeds encoders + VNH5019 logic. GND_PWR = motor return, star at battery.", 20, 44, 1.5),
        ("ESTOP_STATE: contact off the E-stop chain, reporting only — E-stop cuts +12V_BUS upstream.", 20, 48, 1.5),
        ("EN/DIAG lines need 3V3 pull-ups (VNH5019 carrier has them); CS valid only while driving.", 20, 52, 1.5),
    ]
    note_parts = [text(s, x, y, sz) for s, x, y, sz in notes]

    libs = "\n".join([
        sym_def("NUCLEO_G474RE", NUCLEO_PINS, NUC_W, NUC_H),
        sym_def("VNH5019_CARRIER", VNH_PINS, VNH_W, VNH_H),
        sym_def("GOBILDA_5203", MOTOR_PINS, MOT_W, MOT_H),
        sym_def("R_DIV", R_PINS, RW, RH),
    ])

    sch = f'''(kicad_sch
  (version 20260306)
  (generator "gen_drive_wiring")
  (generator_version "10.0")
  (uuid "{ROOT_UUID}")
  (paper "A3")
  (title_block
    (title "Buddy drive MCU wiring")
    (date "2026-07-15")
    (rev "A")
    (company "Buddy robot project")
  )
  (lib_symbols
{libs}
  )
{chr(10).join(parts)}
{chr(10).join(labels)}
{chr(10).join(note_parts)}
  (sheet_instances (path "/" (page "1")))
  (embedded_fonts no)
)
'''
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{PROJECT}.kicad_sch").write_text(sch)
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps({
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "sheets": [[ROOT_UUID, "Root"]],
    }, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)}/{PROJECT}.kicad_sch "
          f"({len(labels)} net labels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
