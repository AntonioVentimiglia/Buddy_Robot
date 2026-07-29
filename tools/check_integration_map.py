#!/usr/bin/env python3
"""Assert that the integration map still agrees with the rest of the repo.

The integration diagrams are only worth drawing if they cannot quietly go stale.
This is the mechanism that makes that true: every fact the diagrams draw is
checked against the file that actually owns it.

    A  structure      ids unique, every cross-reference lands, every
                      `param:`/`req:` reference resolves in the parameter files
    B  pin_map.md     <-> firmware/drive_mcu/include/pins.h
    C  pin_map.md     <-> the KiCAD generator's net table (NUC_NETS)
    D  drive_protocol.md states + fault bits <-> integration_map.yaml
    E  ros_bridge_node.py publishers/subscribers <-> the map's topic table
    F  every ADR referenced by a block or link exists

Run standalone, or automatically as the first step of `python3 tools/build.py`:

    python3 tools/check_integration_map.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "kicad"))

from buddy_calcs import integration as im  # noqa: E402
from pin_map import WHEELS, parse, parse_pins_h  # noqa: E402

import gen_drive_wiring as gdw  # noqa: E402

PROTOCOL_MD = ROOT / "firmware" / "shared_protocol" / "drive_protocol.md"
BRIDGE_PY = (ROOT / "robot_ws" / "src" / "buddy_base" / "buddy_base"
             / "ros_bridge_node.py")
DECISIONS = ROOT / "docs" / "decisions"


def check_structure() -> list[str]:
    return [f"integration_map.yaml: {p}" for p in im.validate()]


def check_pin_map_vs_firmware() -> list[str]:
    doc, fw = parse(), parse_pins_h()
    problems = []
    for w in WHEELS:
        for key in ("ina", "inb", "fault", "cs_ch"):
            a, b = doc["drivers"][w][key], fw["drivers"][w][key]
            if a != b:
                problems.append(
                    f"pin_map.md says {w} {key}={a}, pins.h says {b}")
    if doc["misc"]["E-stop chain state"]["pin"] != fw["misc"]["estop"]:
        problems.append("pin_map.md and pins.h disagree on the E-stop pin")
    if doc["misc"]["Status LED"]["pin"] != fw["misc"]["led"]:
        problems.append("pin_map.md and pins.h disagree on the status LED pin")
    return problems


def check_pin_map_vs_schematic() -> list[str]:
    """The KiCAD net table must name the same MCU pins the pin map assigns."""
    doc = parse()
    by_net = {net: fn.split()[0] for fn, net in gdw.NUC_NETS.items()}
    problems = []
    for w in WHEELS:
        expected = {
            f"{w}_ENC_A": doc["encoders"][w]["a"],
            f"{w}_ENC_B": doc["encoders"][w]["b"],
            f"{w}_PWM": doc["drivers"][w]["pwm"],
            f"{w}_INA": doc["drivers"][w]["ina"],
            f"{w}_INB": doc["drivers"][w]["inb"],
            f"{w}_FLT": doc["drivers"][w]["fault"],
            f"{w}_CS": doc["drivers"][w]["cs"],
        }
        for net, pin in expected.items():
            got = by_net.get(net)
            if got != pin:
                problems.append(
                    f"schematic net {net} is on {got}, pin_map.md says {pin}")
    for net, key in (("VBAT_SENSE", "Vbat sense"),
                     ("ESTOP_STATE", "E-stop chain state")):
        if by_net.get(net) != doc["misc"][key]["pin"]:
            problems.append(
                f"schematic net {net} is on {by_net.get(net)}, "
                f"pin_map.md says {doc['misc'][key]['pin']}")
    return problems


def check_protocol() -> list[str]:
    """States and fault bits are the protocol's; the map only mirrors them."""
    text = PROTOCOL_MD.read_text(encoding="utf-8")
    problems = []

    spec_states = {int(v): n for v, n in
                   re.findall(r"`?(\d) ([A-Z_]+)", _section(text, "State machine values"))}
    map_states = {s["value"]: s["id"] for s in im.MAP["state_machine"]["states"]}
    if spec_states != map_states:
        problems.append(
            f"state machine differs from drive_protocol.md: "
            f"spec {sorted(spec_states.items())} vs map {sorted(map_states.items())}")

    spec_bits = {int(m, 16): n for m, n in
                 re.findall(r"(0x[0-9A-Fa-f]{4}) ([A-Z_]+)", _section(text, "Fault bits"))}
    map_bits = {b["mask"]: b["id"] for b in im.MAP["state_machine"]["fault_bits"]}
    if spec_bits != map_bits:
        problems.append(
            f"fault bits differ from drive_protocol.md: "
            f"spec {sorted(spec_bits.items())} vs map {sorted(map_bits.items())}")

    for t in im.MAP["state_machine"]["transitions"]:
        for end in ("from", "to"):
            if t[end] not in map_states.values():
                problems.append(f"transition references unknown state {t[end]!r}")
    return problems


def _section(text: str, heading: str) -> str:
    """The body of the markdown section whose heading contains `heading`.

    The heading line is matched with [^\\n]* rather than .* — under re.S a dot
    would swallow every preceding line and return the whole document.
    """
    m = re.search(rf"^#+[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^#+ |\Z)",
                  text, re.M | re.S)
    return m.group(1) if m else ""


def check_bridge_topics() -> list[str]:
    """What the bridge node actually creates vs what the map claims it does."""
    src = BRIDGE_PY.read_text(encoding="utf-8")
    published = {"/" + n for n in re.findall(r'create_publisher\([^,]+,\s*"([^"]+)"', src)}
    subscribed = {"/" + n for n in re.findall(r'create_subscription\([^,]+,\s*"([^"]+)"', src)}
    if "TransformBroadcaster" in src:
        published.add("/tf")

    # A topic the map marks `planned` is allowed to be absent from the node —
    # that is what planned means. The reverse is never allowed: anything the
    # node really does must appear on the diagram.
    claimed_pub, claimed_sub = set(), set()
    live_pub, live_sub = set(), set()
    for t in im.MAP["ros"]["topics"]:
        live = t["status"] == "working"
        if "bridge" in (t.get("from") or []):
            claimed_pub.add(t["name"])
            if live:
                live_pub.add(t["name"])
        if "bridge" in (t.get("to") or []):
            claimed_sub.add(t["name"])
            if live:
                live_sub.add(t["name"])

    problems = []
    for name in sorted(live_pub - published):
        problems.append(f"map says the bridge publishes {name}, the node does not")
    for name in sorted(published - claimed_pub):
        problems.append(f"the bridge publishes {name}, the map does not list it")
    for name in sorted(live_sub - subscribed):
        problems.append(f"map says the bridge subscribes {name}, the node does not")
    for name in sorted(subscribed - claimed_sub):
        problems.append(f"the bridge subscribes {name}, the map does not list it")
    return problems


def check_adrs() -> list[str]:
    known = {f.stem.split("-")[0] + "-" + f.stem.split("-")[1]
             for f in DECISIONS.glob("ADR-*.md")}
    problems = []
    for kind in ("blocks", "links"):
        for item in im.MAP[kind]:
            adr = item.get("adr")
            if adr and adr not in known:
                problems.append(f"{kind[:-1]} {item['id']}: unknown {adr}")
    return problems


CHECKS = [
    ("A structure           ", check_structure),
    ("B pin_map <-> pins.h  ", check_pin_map_vs_firmware),
    ("C pin_map <-> KiCAD   ", check_pin_map_vs_schematic),
    ("D protocol <-> map    ", check_protocol),
    ("E bridge node <-> map ", check_bridge_topics),
    ("F ADR references      ", check_adrs),
]


def problems() -> list[str]:
    out: list[str] = []
    for _label, fn in CHECKS:
        out.extend(fn())
    return out


def main() -> int:
    failures = 0
    for label, fn in CHECKS:
        found = fn()
        failures += len(found)
        print(f"{'FAIL' if found else 'ok  '} {label}")
        for p in found:
            print(f"       {p}")
    print("\n" + ("INTEGRATION MAP: ALL CHECKS PASSED" if not failures
                  else f"{failures} INTEGRATION MAP FAILURES"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
