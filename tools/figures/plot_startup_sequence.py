#!/usr/bin/env python3
"""Render the Buddy boot-to-motion sequence and the gates along it.

Read from the integration map's `startup` section. The point of the figure is
the last row: every earlier step brings a subsystem up in a state that cannot
move the robot, and motion is unlocked only by an explicit operator action with
four conditions already true.

    python3 tools/figures/plot_startup_sequence.py

Output: assets/figures/startup_sequence.svg
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import integration as im  # noqa: E402
from blockdiagram import Canvas  # noqa: E402
from palette import BLUE, CRITICAL, GREEN, GREY, INK, MUTED  # noqa: E402

W, H = 1180, 980
SPINE_X = 74
BOX_X, BOX_W = 118, 1000
ROW_Y, ROW_H, ROW_GAP = 104, 56, 66

ACTOR_LABEL = {
    "jetson": "Jetson · Linux", "drive_mcu": "drive MCU", "bridge": "buddy_base",
    "rsp": "robot_state_publisher", "sensors": "sensor drivers",
    "diag": "diagnostics", "slam": "localization", "nav2": "Nav2",
    "operator": "operator",
}


def main() -> int:
    startup = im.MAP["startup"]
    steps = startup["sequence"]

    c = Canvas(W, H,
               title="Buddy startup — what comes up, in what order, and what unlocks motion",
               subtitle="From docs/system_model/integration_map.yaml · red rows carry a "
                        "gate condition · nothing on this page can move the robot until "
                        "the last one")

    last_y = ROW_Y
    for i, step in enumerate(steps):
        y = ROW_Y + i * ROW_GAP
        last_y = y
        gate = step.get("gate")
        final = step["step"] == len(steps)
        accent = CRITICAL if final else (GREEN if gate else BLUE)
        rows = [f"gate: {gate}"] if gate else []
        c.box(BOX_X, y, BOX_W, ROW_H, step["action"],
              ACTOR_LABEL.get(step["actor"], step["actor"]), rows,
              accent=accent, mono_rows=False, title_size=11.5)
        c.tag(SPINE_X, y + ROW_H / 2, str(step["step"]), color=accent,
              size=10.5, weight="700")

    # the spine the numbered steps hang from
    c.vrule(SPINE_X, ROW_Y + 6, last_y + ROW_H - 6, GREY, 1.4, dash=True)

    # ---- the rule ----------------------------------------------------------
    rule_y = last_y + ROW_H + 44
    c.label(BOX_X, rule_y, "The rule this ordering exists to enforce:",
            size=11, color=CRITICAL, weight="600")
    for i, line in enumerate(textwrap.wrap(" ".join(startup["rule"].split()), 118)):
        c.label(BOX_X, rule_y + 22 + i * 15, line, size=9.9, color=MUTED)

    c.note(BOX_X, rule_y + 74, [
        "Step 3 is the one that makes the rest safe: the MCU reaches SAFE_IDLE on its "
        "own power, before the Jetson has finished booting and whether or not ROS 2 "
        "ever starts. Powering the Nucleo",
        "from the 5 V rail through E5V rather than from Jetson USB is what makes that "
        "true — the MCU survives a Jetson reboot, and a Jetson that never comes back "
        "simply leaves the wheels stopped.",
    ], size=9.7)

    c.section(BOX_X, rule_y + 130, "sources")
    c.label(BOX_X + 64, rule_y + 130,
            "startup_sequence.md · fault_state_machine.svg · "
            "devops/systemd · ADR-0006",
            size=9.7, color=MUTED)

    out = REPO / "assets" / "figures" / "startup_sequence.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
