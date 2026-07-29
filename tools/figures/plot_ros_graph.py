#!/usr/bin/env python3
"""Render the Buddy ROS 2 graph — nodes, topics, and the hardware boundary.

Content comes from docs/system_model/integration_map.yaml (topology) and
design_params.yaml (numbers); only the layout lives here. Node status is drawn,
not described: solid = running and tested today, dashed = planned or deferred,
so the figure doubles as a build-progress chart.

    python3 tools/figures/plot_ros_graph.py

Output: assets/figures/ros_graph.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import integration as im  # noqa: E402
from blockdiagram import Canvas  # noqa: E402
from palette import AMBER, BLUE, CRITICAL, GREY, MUTED, PURPLE  # noqa: E402

W, H = 1340, 928
LANE = {0: 60, 1: 320, 2: 580, 3: 840}
LANE_W = 228
# band -> group top. Boxes sit BOX_DY below it; the gaps between bands are
# routing channels wide enough for a labelled edge.
BAND = {"A": 72, "B": 218, "C": 394, "D": 544, "E": 694}
BOX_DY, BOX_H, BAND_H = 30, 74, 116
GROUP_X, GROUP_W = 44, 1046
CH_AB, CH_BC1, CH_BC2, CH_CD, CH_DE = 203, 350, 378, 527, 677

PLACE = {  # node id -> (band, lane). Layout is presentation; content is the map.
    "teleop": ("A", 0),
    "nav2": ("B", 1), "slam": ("B", 2), "diag": ("B", 3),
    "rsp": ("C", 0), "ekf": ("C", 1),
    "bridge": ("D", 0), "imu_drv": ("D", 1), "lidar_drv": ("D", 2),
    "cam_drv": ("D", 3),
}

STATUS_STYLE = {
    "working": (BLUE, False),
    "planned": (AMBER, True),
    "deferred": (PURPLE, True),
    "proposed": (BLUE, True),
}

# Short forms for the diagram. The map's `role` is prose for documents; a box
# 228 px wide needs a phrase, and the layout audit enforces that it fits.
ROLE = {
    "teleop": "commissioning input",
    "nav2": "planning + control",
    "slam": "map building, pose",
    "diag": "health rollup",
    "rsp": "URDF → transforms",
    "ekf": "wheel odom + IMU fusion",
    "bridge": "the ROS ↔ MCU boundary",
    "imu_drv": "BNO086 driver",
    "lidar_drv": "LD19 driver",
    "cam_drv": "OAK-D Lite driver",
}


def main() -> int:
    hz = im.resolve("param:firmware.telemetry_hz")
    wd = im.resolve("param:firmware.watchdog_ms")
    c = Canvas(W, H,
               title="Buddy ROS 2 graph — information flow and the hardware boundary",
               subtitle="Generated from docs/system_model/integration_map.yaml · "
                        "solid = working and host-tested today, dashed = planned "
                        "or deferred · the bottom band is outside ROS 2 entirely")

    for band, label in [("A", "operator / dev host"),
                        ("B", "autonomy"),
                        ("C", "state estimation"),
                        ("D", "hardware-facing ROS nodes"),
                        ("E", "hardware — outside ROS 2")]:
        c.group(GROUP_X, BAND[band], GROUP_W, BAND_H, label,
                color=GREY if band == "E" else MUTED)

    boxes = {}
    for nid, (band, lane) in PLACE.items():
        n = im.node(nid)
        accent, planned = STATUS_STYLE[n["status"]]
        boxes[nid] = c.box(LANE[lane], BAND[band] + BOX_DY, LANE_W, BOX_H,
                           n["name"], ROLE[nid], accent=accent, planned=planned)

    hw = {}
    for bid, lane, sub in [("drive_mcu", 0, "watchdog · current limit"),
                           ("imu", 1, "on-chip fusion"),
                           ("lidar", 2, "360° ToF, 12 m"),
                           ("camera", 3, "deferred (ADR-0007)")]:
        b = im.block(bid)
        hw[bid] = c.box(LANE[lane], BAND["E"] + BOX_DY, LANE_W, BOX_H,
                        b["name"], sub,
                        accent=CRITICAL if bid == "drive_mcu" else GREY,
                        planned=b["status"] == "deferred")

    br, rsp, ekf = boxes["bridge"], boxes["rsp"], boxes["ekf"]
    nav2, slam, diag = boxes["nav2"], boxes["slam"], boxes["diag"]
    lidar_drv, imu_drv, cam_drv = boxes["lidar_drv"], boxes["imu_drv"], boxes["cam_drv"]

    # ---- command path ------------------------------------------------------
    c.edge(boxes["teleop"].r(), br.t(0.20), color=BLUE,
           via=[(302, boxes["teleop"].cy), (302, CH_CD),
                (LANE[0] + LANE_W * 0.20, CH_CD)])
    c.tag(302 + 74, CH_CD, "/cmd_vel", color=BLUE)

    c.edge(nav2.l(0.80), br.l(0.30), color=BLUE, dash=True,
           via=[(34, nav2.y + BOX_H * 0.80), (34, br.y + BOX_H * 0.30)])
    c.tag(76, CH_CD, "/cmd_vel", color=BLUE)

    # ---- what the bridge publishes ----------------------------------------
    c.edge(br.t(0.55), rsp.b(0.5), color=BLUE, style="vhv", mid=CH_CD)
    c.tag(LANE[0] + LANE_W * 0.5, CH_CD - 17, "/joint_states", color=BLUE)

    c.edge(br.t(0.85), ekf.b(0.25), color=BLUE, style="vhv", mid=CH_CD + 17)
    c.tag(LANE[1] + 44, CH_CD + 17, "/odom", color=BLUE)

    c.edge(br.b(0.55), diag.r(0.55), color=BLUE,
           via=[(br.cx + 24, CH_DE), (1122, CH_DE),
                (1122, diag.y + BOX_H * 0.55)])
    c.tag(1122, CH_BC1, "/battery_state", color=BLUE)

    # ---- sensing path ------------------------------------------------------
    c.edge(imu_drv.t(0.5), ekf.b(0.75), color=BLUE, dash=True)
    c.tag(LANE[1] + LANE_W * 0.5, CH_CD, "/imu/data", color=BLUE)

    c.edge(lidar_drv.t(0.5), slam.b(0.5), color=BLUE, dash=True)
    c.tag(LANE[2] + LANE_W * 0.5, CH_CD, "/scan", color=BLUE)

    c.edge(lidar_drv.r(0.30), nav2.b(0.85), color=BLUE, dash=True,
           via=[(1090, lidar_drv.y + BOX_H * 0.30), (1090, CH_BC2),
                (LANE[1] + LANE_W * 0.85, CH_BC2)])
    c.tag(900, CH_BC2, "/scan → local costmap", color=BLUE)

    # ---- estimation → autonomy --------------------------------------------
    c.edge(ekf.t(0.5), nav2.b(0.5), color=BLUE, dash=True)
    c.tag(LANE[1] + LANE_W * 0.5, CH_BC1, "/tf", color=BLUE)

    c.edge(rsp.t(0.5), nav2.b(0.18), color=BLUE,
           via=[(LANE[0] + LANE_W * 0.5, CH_BC1),
                (LANE[1] + LANE_W * 0.18, CH_BC1)])
    c.tag(LANE[0] + LANE_W * 0.5 + 74, CH_BC1, "/tf_static", color=BLUE)

    c.edge(slam.l(0.5), nav2.r(0.5), color=BLUE, dash=True)

    # ---- the boundary: leaving ROS ----------------------------------------
    c.edge(br.b(0.18), hw["drive_mcu"].t(0.18), color=CRITICAL, both=True)
    c.tag(LANE[0] + LANE_W * 0.18 + 82, CH_DE, "USB · drive protocol v1",
          color=CRITICAL)
    c.edge(hw["imu"].t(0.5), imu_drv.b(0.5), color=GREY, dash=True)
    c.tag(LANE[1] + LANE_W * 0.5, CH_DE, "I²C · 40-pin", color=GREY)
    c.edge(hw["lidar"].t(0.5), lidar_drv.b(0.5), color=GREY, dash=True)
    c.tag(LANE[2] + LANE_W * 0.5, CH_DE, "USB · UART 230400", color=GREY)
    c.edge(hw["camera"].t(0.5), cam_drv.b(0.5), color=GREY, dash=True)
    c.tag(LANE[3] + LANE_W * 0.5, CH_DE, "USB 3.0", color=GREY)

    # ---- legend ------------------------------------------------------------
    c.section(1148, 96, "legend")
    c.legend(1148, 122, [
        (BLUE, "working today"),
        (AMBER, "planned"),
        (PURPLE, "deferred"),
        (CRITICAL, "safety-owning path"),
        (GREY, "non-ROS transport"),
    ], gap=18)

    # ---- footer ------------------------------------------------------------
    c.label(GROUP_X + 4, 838,
            "The Jetson asks for motion; it never owns motor safety.", size=11,
            color=CRITICAL, weight="600")
    c.note(GROUP_X + 4, 858, [
        f"Below the boundary the MCU stops the wheels on a stale command "
        f"({wd:g} ms watchdog), an E-stop, or a driver fault — with ROS 2 absent, "
        f"crashed, or still booting. Telemetry returns at {hz:g} Hz.",
        "The bridge runs identically against the real MCU (/dev/buddy_drive_mcu) "
        "and against mock_mcu.py's pty, which is why 13 host tests cover the drive "
        "stack with no hardware present.",
        "/diagnostics is published by every hardware-facing node once those nodes "
        "exist; those edges are omitted to keep the graph readable. Message types "
        "and QoS: docs/system_model/interface_contract.md.",
    ], size=9.7, gap=15)

    out = REPO / "assets" / "figures" / "ros_graph.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
