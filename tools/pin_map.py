"""Parse firmware/drive_mcu/docs/pin_map.md into a machine-readable pin map.

The pin map is written for humans (it is the document an engineer reads at the
bench) but three generated things depend on it: the KiCAD harness schematic, the
interconnect figure, and the firmware's `pins.h`. Parsing the document rather
than re-typing it means the drawing and the checker read the same words the
bench reads.

    from pin_map import parse
    pm = parse()
    pm["encoders"]["LF"]   # {'timer': 'TIM2', 'a': 'PA0', 'b': 'PA1'}
    pm["drivers"]["RR"]    # {'pwm': 'PA11', 'pwm_ch': 'CH4', 'ina': 'PB13', ...}
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_MAP_MD = ROOT / "firmware" / "drive_mcu" / "docs" / "pin_map.md"
PINS_H = ROOT / "firmware" / "drive_mcu" / "include" / "pins.h"

WHEELS = ["LF", "LR", "RF", "RR"]  # index order 0..3, protocol order

_PIN = re.compile(r"\bP([A-K])(\d{1,2})\b")
_PAREN = re.compile(r"\(([^)]*)\)")


def _rows(md: str) -> list[list[str]]:
    """Every markdown table row, as stripped cell lists (separators dropped)."""
    out = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        out.append(cells)
    return out


def _pin(cell: str) -> str | None:
    m = _PIN.search(cell)
    return f"P{m.group(1)}{m.group(2)}" if m else None


def _paren(cell: str) -> str | None:
    m = _PAREN.search(cell)
    return m.group(1).strip() if m else None


def parse(md_path: Path = PIN_MAP_MD) -> dict:
    rows = _rows(md_path.read_text(encoding="utf-8"))
    encoders: dict[str, dict] = {}
    drivers: dict[str, dict] = {}
    misc: dict[str, dict] = {}

    for cells in rows:
        head = cells[0]
        if head in WHEELS and len(cells) >= 5 and cells[1].startswith("TIM"):
            encoders[head] = {"timer": cells[1], "a": _pin(cells[2]),
                              "b": _pin(cells[3])}
        elif head in WHEELS and len(cells) >= 6:
            drivers[head] = {
                "pwm": _pin(cells[1]), "pwm_ch": _paren(cells[1]),
                "ina": _pin(cells[2]), "inb": _pin(cells[3]),
                "fault": _pin(cells[4]),
                "cs": _pin(cells[5]), "cs_ch": _paren(cells[5]),
            }
        elif len(cells) >= 3 and _pin(cells[1]) and head not in ("Signal", "Wheel"):
            misc[head] = {"pin": _pin(cells[1]), "detail": _paren(cells[1]),
                          "direction": cells[2]}

    return {"encoders": encoders, "drivers": drivers, "misc": misc}


def parse_pins_h(h_path: Path = PINS_H) -> dict:
    """The firmware's own copy of the map, for cross-checking the document."""
    src = h_path.read_text(encoding="utf-8")

    def arr(name: str) -> list[str]:
        m = re.search(rf"{name}\[4\]\s*=\s*\{{(.*?)\}}", src, re.S)
        if not m:
            raise KeyError(name)
        return [v.strip() for v in m.group(1).split(",")]

    def gpio(port: str, pin: str) -> str:
        return f"P{port.removeprefix('GPIO')}{pin.removeprefix('GPIO_PIN_')}"

    out: dict[str, dict] = {"drivers": {}, "misc": {}}
    for key, prefix in (("ina", "BUDDY_INA"), ("inb", "BUDDY_INB"),
                        ("fault", "BUDDY_FAULT")):
        ports, pins = arr(f"{prefix}_PORT"), arr(f"{prefix}_PIN")
        for w, port, pin in zip(WHEELS, ports, pins):
            out["drivers"].setdefault(w, {})[key] = gpio(port, pin)
    for w, ch in zip(WHEELS, arr("BUDDY_CS_CHANNEL")):
        out["drivers"][w]["cs_ch"] = "IN" + ch.removeprefix("ADC_CHANNEL_")

    for key, prefix in (("estop", "BUDDY_ESTOP"), ("led", "BUDDY_LED")):
        port = re.search(rf"#define {prefix}_PORT (\w+)", src)
        pin = re.search(rf"#define {prefix}_PIN (\w+)", src)
        if port and pin:
            out["misc"][key] = gpio(port.group(1), pin.group(1))
    return out


if __name__ == "__main__":  # quick inspection aid
    import json
    print(json.dumps(parse(), indent=2))
