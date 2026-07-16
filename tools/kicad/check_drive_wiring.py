#!/usr/bin/env python3
"""Verify the drive-MCU wiring schematic's electrical connectivity.

Exports the netlist with kicad-cli and asserts the exact expected topology —
every MCU pin to its driver/encoder counterpart per
firmware/drive_mcu/docs/pin_map.md. This turns "the schematic is checked"
from a visual claim into a mechanical one.

    python3 tools/kicad/check_drive_wiring.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCH = ROOT / "electronics" / "KiCAD" / "drive_mcu_wiring" / "drive_mcu_wiring.kicad_sch"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

WHEELS = ["LF", "LR", "RF", "RR"]
PWM_PINFN = {"LF": "PA8 TIM1_CH1", "LR": "PA9 TIM1_CH2",
             "RF": "PA10 TIM1_CH3", "RR": "PA11 TIM1_CH4"}
INA_PINFN = {"LF": "PB0", "LR": "PB2", "RF": "PB4", "RR": "PB13"}
INB_PINFN = {"LF": "PB1", "LR": "PB10", "RF": "PB5", "RR": "PB14"}
FLT_PINFN = {"LF": "PC10", "LR": "PC11", "RF": "PC12", "RR": "PD2"}
CS_PINFN = {"LF": "PC0 ADC1_IN6", "LR": "PC1 ADC1_IN7",
            "RF": "PC2 ADC1_IN8", "RR": "PC3 ADC1_IN9"}
ENC_PINFN = {("LF", "A"): "PA0 TIM2_CH1", ("LF", "B"): "PA1 TIM2_CH2",
             ("LR", "A"): "PA6 TIM3_CH1", ("LR", "B"): "PA7 TIM3_CH2",
             ("RF", "A"): "PB6 TIM4_CH1", ("RF", "B"): "PB7 TIM4_CH2",
             ("RR", "A"): "PC6 TIM8_CH1", ("RR", "B"): "PC7 TIM8_CH2"}
VNH_REF = {"LF": "U2", "LR": "U3", "RF": "U4", "RR": "U5"}
MOT_REF = {"LF": "M1", "LR": "M2", "RF": "M3", "RR": "M4"}


def netlist() -> dict[str, set]:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "n.xml"
        subprocess.run([KICAD_CLI, "sch", "export", "netlist",
                        "--format", "kicadxml", "-o", str(out), str(SCH)],
                       check=True, capture_output=True)
        xml = out.read_text()
    nets: dict[str, set] = {}
    for m in re.finditer(r'<net code="\d+" name="([^"]+)"[^>]*>(.*?)</net>',
                         xml, re.S):
        nets[m.group(1)] = {
            (r, fn.split("_" + p)[0] if False else fn)
            for r, p, fn in re.findall(
                r'node ref="([^"]+)" pin="([^"]+)"(?: pinfunction="([^"]*)")?',
                m.group(2))
        }
    return nets


def main() -> int:
    nets = netlist()
    failures = 0

    def norm(fn: str) -> str:
        # netlister suffixes pinfunction with _<pinnumber>; strip it
        return re.sub(r"_\d+$", "", fn)

    def members(net: str) -> set:
        return {(r, norm(fn)) for r, fn in nets.get(net, set())}

    def check(net: str, expected: set) -> None:
        nonlocal failures
        expected = {(r, fn.replace(" ", "_")) for r, fn in expected}
        got = members(net)
        if got == expected:
            print(f"ok   {net:12s} {sorted(expected)}")
        else:
            failures += 1
            print(f"FAIL {net}: got {sorted(got)}\n     expected {sorted(expected)}")

    for w in WHEELS:
        check(f"{w}_PWM", {("U1", PWM_PINFN[w]), (VNH_REF[w], "PWM")})
        check(f"{w}_INA", {("U1", INA_PINFN[w]), (VNH_REF[w], "INA")})
        check(f"{w}_INB", {("U1", INB_PINFN[w]), (VNH_REF[w], "INB")})
        check(f"{w}_FLT", {("U1", FLT_PINFN[w]), (VNH_REF[w], "EN/DIAG")})
        check(f"{w}_CS", {("U1", CS_PINFN[w]), (VNH_REF[w], "CS")})
        check(f"{w}_M+", {(VNH_REF[w], "OUTA"), (MOT_REF[w], "M+")})
        check(f"{w}_M-", {(VNH_REF[w], "OUTB"), (MOT_REF[w], "M-")})
        check(f"{w}_ENC_A", {("U1", ENC_PINFN[(w, 'A')]), (MOT_REF[w], "ENC_A")})
        check(f"{w}_ENC_B", {("U1", ENC_PINFN[(w, 'B')]), (MOT_REF[w], "ENC_B")})

    check("+3V3", {("U1", "3V3")}
          | {(VNH_REF[w], "VDD") for w in WHEELS}
          | {(MOT_REF[w], "ENC_3V3") for w in WHEELS})
    check("GND", {("U1", "GND"), ("R2", "2")}
          | {(VNH_REF[w], "GND") for w in WHEELS}
          | {(MOT_REF[w], "ENC_GND") for w in WHEELS})
    check("+12V_BUS", {("R1", "1")} | {(VNH_REF[w], "VIN") for w in WHEELS})
    check("GND_PWR", {(VNH_REF[w], "GND_P") for w in WHEELS})
    check("VBAT_SENSE", {("U1", "PC4 ADC2_IN5"), ("R1", "2"), ("R2", "1")})
    check("ESTOP_STATE", {("U1", "PB12 ESTOP_IN")})
    check("+5V_RAIL", {("U1", "E5V")})

    print("\n" + ("SCHEMATIC CONNECTIVITY: ALL CHECKS PASSED" if not failures
                  else f"{failures} CONNECTIVITY FAILURES"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
