#!/usr/bin/env python3
"""Verify the system wiring schematic's electrical connectivity.

Same contract as check_drive_wiring.py: export the netlist with kicad-cli and
assert the exact expected topology, so "the power distribution is correct" is a
mechanical claim rather than a visual one. The expectations below are written
independently of the generator — that is the point; if the generator is wrong,
this must not agree with it.

    python3 tools/kicad/check_system_wiring.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_sch import require_kicad_cli  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCH = ROOT / "electronics" / "KiCAD" / "system_wiring" / "system_wiring.kicad_sch"

# Independent statement of the intended topology (ref, pin function).
EXPECTED = {
    # source and protection, in series: pack -> fuse -> contactor -> bus
    "PACK+":        {("BT1", "PACK+"), ("F1", "1")},
    "BUS_FUSED":    {("F1", "2"), ("K1", "IN")},
    "+12V_BUS":     {("K1", "OUT"), ("U10", "VIN"), ("U11", "VIN"),
                     ("F2", "1"), ("SH1", "+12V_BUS")},
    # regulated rails
    "+12V_JETSON":  {("U10", "VOUT"), ("A1", "VIN_12V")},
    "+5V_RAIL":     {("U11", "VOUT"), ("U1", "E5V"), ("SH1", "+5V_RAIL")},
    "+3V3":         {("U1", "3V3_OUT"), ("SH1", "+3V3")},
    "+3V3_JETSON":  {("A1", "HDR_3V3"), ("S2", "VIN")},
    # returns: motor/battery return is separate from logic ground
    "GND_PWR":      {("BT1", "PACK-"), ("U10", "GND_IN"), ("U11", "GND_IN"),
                     ("A9", "GND"), ("SH1", "GND_PWR")},
    "GND":          {("U10", "GND_OUT"), ("U11", "GND_OUT"), ("A1", "GND"),
                     ("A1", "HDR_GND"), ("U1", "GND"), ("S2", "GND"),
                     ("SH1", "GND")},
    # data links
    "USB_MCU":      {("A1", "USB0"), ("U1", "USB_STLINK"), ("SH1", "USB_VCP")},
    "USB_LIDAR":    {("A1", "USB1"), ("S1", "USB")},
    "USB_CAMERA":   {("A1", "USB2"), ("S3", "USB3")},
    "I2C_SDA":      {("A1", "HDR_SDA"), ("S2", "SDA")},
    "I2C_SCL":      {("A1", "HDR_SCL"), ("S2", "SCL")},
    # safety reporting path (the power cut itself is K1 opening +12V_BUS)
    "ESTOP_STATE":  {("K1", "AUX_NC"), ("U1", "ESTOP_IN"), ("SH1", "ESTOP_STATE")},
    # future arm branch, separately fused off the same bus
    "ARM_BRANCH":   {("F2", "2"), ("A9", "V+")},
}


def netlist() -> dict[str, set]:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "n.xml"
        subprocess.run([require_kicad_cli(), "sch", "export", "netlist",
                        "--format", "kicadxml", "-o", str(out), str(SCH)],
                       check=True, capture_output=True)
        xml = out.read_text(encoding="utf-8")
    nets: dict[str, set] = {}
    for m in re.finditer(r'<net code="\d+" name="([^"]+)"[^>]*>(.*?)</net>',
                         xml, re.S):
        nets[m.group(1)] = {
            (r, re.sub(r"_\d+$", "", fn))
            for r, _p, fn in re.findall(
                r'node ref="([^"]+)" pin="([^"]+)"(?: pinfunction="([^"]*)")?',
                m.group(2))
        }
    return nets


def main() -> int:
    nets = netlist()
    failures = 0
    for net, expected in EXPECTED.items():
        want = {(r, fn.replace(" ", "_")) for r, fn in expected}
        got = nets.get(net, set())
        if got == want:
            print(f"ok   {net:14s} {sorted(want)}")
        else:
            failures += 1
            print(f"FAIL {net}: got {sorted(got)}\n     expected {sorted(want)}")

    # A rail that exists in the netlist but nobody declared is a real finding:
    # it means the generator wired something this file does not describe.
    extra = {n for n in nets if not n.startswith("Net-") and n not in EXPECTED}
    if extra:
        failures += 1
        print(f"FAIL undeclared nets present in the schematic: {sorted(extra)}")

    print("\n" + ("SYSTEM SCHEMATIC CONNECTIVITY: ALL CHECKS PASSED" if not failures
                  else f"{failures} CONNECTIVITY FAILURES"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
