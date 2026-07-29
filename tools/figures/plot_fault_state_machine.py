#!/usr/bin/env python3
"""Render the drive MCU's safety state machine and its fault bits.

States, transitions and fault bits are read from the integration map, which
`tools/check_integration_map.py` asserts against the protocol spec on every
build — so this drawing cannot disagree with the wire format the firmware and
the bridge actually implement.

    python3 tools/figures/plot_fault_state_machine.py

Output: assets/figures/fault_state_machine.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import P  # noqa: E402
from buddy_calcs import integration as im  # noqa: E402
from blockdiagram import Canvas, Port  # noqa: E402
from palette import BLUE, CRITICAL, GREEN, GREY, INK, MUTED  # noqa: E402

W, H = 1340, 812
CHAIN_Y, BOX_H = 158, 92
CHAIN = {  # state id -> (x, width)
    "BOOT": (60, 170), "SELF_TEST": (280, 190), "SAFE_IDLE": (520, 190),
    "ARMED": (760, 170), "ACTIVE": (970, 190),
}
FAULT_XY = (520, 408)
UPDATE_XY = (60, 408)


def main() -> int:
    sm = im.MAP["state_machine"]
    detail = {s["id"]: s["detail"] for s in sm["states"]}
    value = {s["id"]: s["value"] for s in sm["states"]}
    wd = P["firmware"]["watchdog_ms"]

    c = Canvas(W, H,
               title="Drive MCU safety state machine — the only state that moves the robot",
               subtitle="States, transitions and fault bits read from the integration map, "
                        "machine-checked against firmware/shared_protocol/drive_protocol.md "
                        "on every build")

    boxes = {}
    for sid, (x, w) in CHAIN.items():
        boxes[sid] = c.box(x, CHAIN_Y, w, BOX_H, sid,
                           f"state {value[sid]}", [detail[sid]],
                           accent=GREEN if sid == "ACTIVE" else BLUE,
                           mono_rows=False)
    boxes["FAULT"] = c.box(*FAULT_XY, 190, BOX_H, "FAULT",
                           f"state {value['FAULT']}", [detail["FAULT"]],
                           accent=CRITICAL, mono_rows=False)
    boxes["UPDATE"] = c.box(*UPDATE_XY, 190, BOX_H, "UPDATE",
                            f"state {value['UPDATE']}", [detail["UPDATE"]],
                            accent=GREY, planned=True, mono_rows=False)

    # ---- the normal path ---------------------------------------------------
    order = ["BOOT", "SELF_TEST", "SAFE_IDLE", "ARMED", "ACTIVE"]
    labels = {("SAFE_IDLE", "ARMED"): "CMD_MODE(ARM)",
              ("ARMED", "ACTIVE"): "first valid CMD_VEL",
              ("BOOT", "SELF_TEST"): "reset complete",
              ("SELF_TEST", "SAFE_IDLE"): "self-test pass"}
    for a, b in zip(order, order[1:]):
        c.edge(boxes[a].r(), boxes[b].l(), color=BLUE)
        c.tag((boxes[a].x + boxes[a].w + boxes[b].x) / 2, CHAIN_Y - 18,
              labels[(a, b)], color=BLUE, size=9.4)

    # ---- watchdog: ACTIVE falls back without becoming a latched fault ------
    c.edge(boxes["ACTIVE"].t(0.5), boxes["SAFE_IDLE"].t(0.72), color=CRITICAL,
           via=[(boxes["ACTIVE"].cx, 112), (boxes["SAFE_IDLE"].x + 190 * 0.72, 112)])
    c.tag(830, 112, f"watchdog: no CMD_VEL for {wd:g} ms", color=CRITICAL,
          size=9.4)

    # ---- anything faulty latches ------------------------------------------
    for sid, frac in (("SELF_TEST", 0.5), ("ARMED", 0.5), ("ACTIVE", 0.5)):
        c.edge(boxes[sid].b(frac), boxes["FAULT"].t(
            {"SELF_TEST": 0.2, "ARMED": 0.62, "ACTIVE": 0.85}[sid]),
            color=CRITICAL, style="vhv", mid=330)
    c.tag(375, 330, "any fault bit set", color=CRITICAL, size=9.4)

    # ---- recovery is deliberate -------------------------------------------
    c.edge(boxes["FAULT"].r(0.5), boxes["SAFE_IDLE"].b(0.25), color=GREEN,
           via=[(770, boxes["FAULT"].cy), (770, 372),
                (boxes["SAFE_IDLE"].x + 190 * 0.25, 372)])
    c.tag(660, 372, "CMD_MODE(CLEAR) and the cause is gone", color=GREEN,
          size=9.4)

    c.label(UPDATE_XY[0], UPDATE_XY[1] + BOX_H + 18,
            "reserved in the protocol; no transition implemented yet",
            size=9.5, color=MUTED)

    # ---- fault bits --------------------------------------------------------
    c.section(60, 548, "fault bits — TELEMETRY offset 1, uint16 bitmask")
    for i, bit in enumerate(sm["fault_bits"]):
        col, row = divmod(i, 4)
        x = 60 + col * 640
        y = 578 + row * 26
        c.label(x, y, f"0x{bit['mask']:04X}", size=10, color=INK, mono=True,
                weight="600")
        c.label(x + 78, y, bit["id"], size=10, color=CRITICAL, mono=True)
        c.label(x + 250, y, bit["detail"], size=10, color=MUTED)

    # ---- footer ------------------------------------------------------------
    c.label(60, 706, "Two properties this machine exists to guarantee:",
            size=11, color=CRITICAL, weight="600")
    c.note(60, 728, [
        "releasing the E-stop does not restart motion — recovery needs an explicit "
        "CMD_MODE(CLEAR) and then an explicit ARM, and the robot cannot be armed "
        "straight out of FAULT.",
        "Both are asserted in the C host tests (19 checks) before any of this runs "
        "on hardware. E-stop dominance is physical as well as logical: the contactor "
        "removes motor power upstream of the drivers.",
    ], size=9.7)

    c.section(60, 788, "sources")
    c.label(124, 788, "drive_protocol.md · firmware/drive_mcu/src/state_machine.c · "
                      "fault_state_model.md · REQ_SAFE_001 / REQ_SAFE_002",
            size=9.7, color=MUTED)

    out = REPO / "assets" / "figures" / "fault_state_machine.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
