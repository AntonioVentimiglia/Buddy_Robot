#!/usr/bin/env python3
"""Render the Buddy command/telemetry loop and the safety interlocks around it.

One picture for the question "what happens between Nav2 asking for motion and a
wheel turning, and what stops it": the forward path, the measurement path that
closes it, and the four interlocks that override both.

Every number is read live — firmware rates and limits from design_params.yaml,
the keep-alive and ROS-side dead-man from the bridge's own BaseParams, the
teleop ceiling from the requirements yaml. Nothing here is retyped.

    python3 tools/figures/plot_control_safety_loop.py

Output: assets/figures/control_safety_loop.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "robot_ws" / "src" / "buddy_base"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import P, R  # noqa: E402
from buddy_base.base_core import params_from_design  # noqa: E402
from blockdiagram import Canvas  # noqa: E402
from palette import BLUE, CRITICAL, GREEN, GREY, MUTED  # noqa: E402

W, H = 1380, 812
COLS = [(48, 190), (268, 214), (512, 190), (732, 214), (976, 336)]
ROW1_Y, ROW3_Y, BOX_H = 100, 500, 104
SAFE_GY, SAFE_GH = 262, 192
SAFE_Y, SAFE_H = 298, 140
SAFE_COLS = [(60, 286), (374, 286), (688, 286), (1002, 300)]
BUS_Y = 234
LEFT_RAIL, RIGHT_RAIL = 20, 1348


def main() -> int:
    fw = P["firmware"]
    bp_ = params_from_design(REPO)
    i_lim = P["power"]["driver_current_limit_a"]
    cpr = P["drive_motor"]["encoder_counts_per_rev_output"]
    v_max = R["mobility"]["teleop_commissioning_max_mps"]

    c = Canvas(W, H,
               title="Buddy control and safety loop — /cmd_vel to wheel, and what stops it",
               subtitle="Rates and limits read live from design_params.yaml, the "
                        "requirements yaml, and the bridge's own BaseParams · "
                        "blue = command, green = measurement, red = safety override")

    # ---- forward path ------------------------------------------------------
    fwd = []
    for (x, w), (title, sub, rows) in zip(COLS, [
        ("/cmd_vel", "geometry_msgs/Twist",
         ["v [m/s], ω [rad/s]", "from Nav2 or teleop"]),
        ("buddy_base bridge", "Jetson · plain Python, host-tested",
         ["skid-steer kinematics",
          "ratio-preserving clamp",
          f"keep-alive {bp_.cmd_resend_hz:g} Hz",
          f"zeroes after {bp_.cmd_vel_timeout_s:g} s silence"]),
        ("CMD_VEL frame", "drive protocol v1",
         ["0xB5DD · ver · seq · CRC-16", "4 × int16 mm/s", "order LF LR RF RR"]),
        ("drive MCU", f"STM32G474 · {fw['control_hz'] / 1000:g} kHz loop",
         ["CRC + version gate",
          f"clamp to {v_max:g} m/s",
          "motion only in ACTIVE"]),
        ("VNH5019 ×4  →  motors + wheels", f"{fw['pwm_hz'] / 1000:g} kHz PWM, ultrasonic",
         ["PWM + INA/INB per wheel",
          "the only high-current path in the robot"]),
    ]):
        fwd.append(c.box(x, ROW1_Y, w, BOX_H, title, sub, rows, accent=BLUE))

    for a, b in zip(fwd, fwd[1:]):
        c.edge(a.r(), b.l(), color=BLUE)

    # ---- measurement path (right to left) ----------------------------------
    ret = []
    for (x, w), (title, sub, rows) in zip(COLS, [
        ("consumers", "EKF · Nav2 · diagnostics",
         ["/odom  /joint_states", "/battery_state"]),
        ("bridge odometry", "midpoint integration",
         ["diff-drive pose", "publishes /odom + TF"]),
        ("TELEMETRY frame", f"39 B @ {fw['telemetry_hz']:g} Hz",
         ["state · fault bits · estop",
          "pos ×4 · vel ×4 · cur ×4", "vbat"]),
        ("MCU sampling", "hardware timers + ADC",
         ["rim velocity per wheel",
          "CS current, sampled mid-pulse", "Vbat via 10:1 divider"]),
        ("encoders ×4", "quadrature, 3.3 V native",
         [f"TIM2/3/4/8 hardware decode · {cpr:g} counts/rev at the output shaft"]),
    ]):
        ret.append(c.box(x, ROW3_Y, w, BOX_H, title, sub, rows, accent=GREEN))

    for a, b in zip(ret, ret[1:]):
        c.edge(b.l(), a.r(), color=GREEN)

    # motion becomes measured motion; the estimate becomes the next command
    c.edge(fwd[4].r(), ret[4].r(), color=GREEN,
           via=[(RIGHT_RAIL, fwd[4].cy), (RIGHT_RAIL, ret[4].cy)])
    c.tag(RIGHT_RAIL - 58, 477, "wheels turn", color=GREEN)
    c.edge(ret[0].l(), fwd[0].l(), color=BLUE, dash=True,
           via=[(LEFT_RAIL, ret[0].cy), (LEFT_RAIL, fwd[0].cy)])
    c.tag(LEFT_RAIL + 76, 477, "closes the loop", color=BLUE)

    # ---- safety interlocks -------------------------------------------------
    c.group(36, SAFE_GY, 1288, SAFE_GH,
            "safety interlocks — owned by the MCU, not by ROS", color=CRITICAL)

    for (x, w), (title, rows) in zip(SAFE_COLS, [
        ("command watchdog", [
            f"no valid CMD_VEL for {fw['watchdog_ms']:g} ms",
            "→ SAFE_IDLE, motors off",
            "REQ_SAFE_002 · bounds runaway distance"]),
        ("current limit", [
            f"CS above {i_lim:g} A per motor",
            "→ chop PWM for the rest of the",
            "control period · ADR-0005"]),
        ("driver fault", [
            "VNH5019 EN/DIAG pulled low",
            "→ FAULT, latched",
            "over-current / over-temperature"]),
        ("E-stop", [
            "opens the contactor: motor power",
            "is gone regardless of firmware",
            "state reported on PB12 only"]),
    ]):
        s = c.box(x, SAFE_Y, w, SAFE_H, title, "", rows, accent=CRITICAL,
                  mono_rows=False)
        c.edge(s.t(0.5), Port_at(s.cx, BUS_Y), color=CRITICAL, arrow=False)

    # the shared consequence: any interlock removes motion
    c.edge(Port_at(60, BUS_Y, "R"), Port_at(1302, BUS_Y, "L"), color=CRITICAL,
           arrow=False, style="straight")
    c.edge(Port_at(800, BUS_Y, "T"), fwd[3].b(0.32), color=CRITICAL)
    c.edge(Port_at(1144, BUS_Y, "T"), fwd[4].b(0.5), color=CRITICAL)
    c.tag(455, BUS_Y, "any interlock → state machine leaves ACTIVE → PWM off",
          color=CRITICAL, mono=False, size=10)

    # ---- footer ------------------------------------------------------------
    c.label(48, 648, "The loop can be run end-to-end today with no hardware.",
            size=11, color=BLUE, weight="600")
    c.note(48, 670, [
        "mock_mcu.py implements this same state machine and wheel model behind a "
        "pty, so the bridge exercises real protocol bytes in host tests: straight-line "
        "and pivot odometry within model tolerance,",
        "watchdog stop with bounded runaway distance, E-stop visibility, joint states. "
        "The C and Python protocol implementations are cross-checked by golden vectors, "
        "so the two ends cannot drift apart.",
        "",
        "Still open at the bench: the velocity PID and mid-pulse current sampling are "
        "written but unverified against real motors — the current limit sits on the "
        "safety path and must be measured before the base rolls.",
    ], size=9.7, gap=15)

    c.section(48, 764, "sources")
    c.label(112, 764, "drive_protocol.md · pin_map.md · electrical_interfaces.md · "
                      "ADR-0005 (current limit) · ADR-0006 (bus)",
            size=9.7, color=MUTED)

    out = REPO / "assets" / "figures" / "control_safety_loop.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


def Port_at(x: float, y: float, side: str = "B"):
    """A bare coordinate used as an edge endpoint (bus taps have no box)."""
    from blockdiagram import Port
    return Port(x, y, side)


if __name__ == "__main__":
    raise SystemExit(main())
