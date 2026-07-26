"""Base bridge core — pure logic, no ROS, host-testable.

Everything between a (v, w) body command and the wire protocol lives here:
skid-steer kinematics, odometry integration from encoder telemetry, velocity
clamping, and command/telemetry bookkeeping. The rclpy node
(ros_bridge_node.py) is a thin shell around this class, so the whole drive
brain is exercised by test_base_core.py and test_integration_mock.py against
the mock MCU — before any hardware or any ROS installation exists.

Geometry/limits come in through BaseParams, generated from design_params.yaml
into config/base_params.yaml by tools/build.py (single source of truth).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

# shared protocol implementation (single source of truth with the firmware);
# resolvable in-repo — build the workspace with --symlink-install on the Jetson
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "buddy_firmware_interfaces" / "python"))
import buddy_protocol as bp  # noqa: E402


@dataclass
class BaseParams:
    wheel_radius_m: float
    track_m: float                 # left-right wheel center distance
    counts_per_rev: float          # 4x-decoded counts per output-shaft rev
                                   # (goBILDA "PPR" is already 4x - do not scale)
    vel_limit_mmps: int            # firmware clamp mirror (for local clamping)
    cmd_resend_hz: float = 20.0    # keep-alive rate vs the 200 ms MCU watchdog
    cmd_vel_timeout_s: float = 0.5 # ROS-side silence -> command zeros

    @property
    def m_per_count(self) -> float:
        return 2.0 * math.pi * self.wheel_radius_m / self.counts_per_rev


@dataclass
class Odometry:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    v: float = 0.0      # body linear velocity estimate [m/s]
    w: float = 0.0      # body angular velocity estimate [rad/s]


@dataclass
class BaseCore:
    params: BaseParams
    odom: Odometry = field(default_factory=Odometry)
    last_telemetry: bp.Telemetry | None = None
    estop: bool = False
    mcu_state: int = bp.STATE_BOOT
    fault_bits: int = 0
    _seq: int = 0
    _last_counts: tuple | None = None
    _last_telem_time: float | None = None
    _target: tuple = (0, 0, 0, 0)

    # ---------------------------------------------------------- commands --
    def wheel_targets_mmps(self, v_mps: float, w_radps: float) -> tuple:
        """Skid-steer kinematics: body (v, w) -> per-wheel rim speed, protocol
        order LF, LR, RF, RR. Left/right sides move together."""
        half_track = self.params.track_m / 2.0
        v_left = (v_mps - w_radps * half_track) * 1000.0
        v_right = (v_mps + w_radps * half_track) * 1000.0
        lim = self.params.vel_limit_mmps
        # preserve the turn ratio when clamping
        scale = max(1.0, abs(v_left) / lim, abs(v_right) / lim)
        v_left, v_right = v_left / scale, v_right / scale
        return (int(v_left), int(v_left), int(v_right), int(v_right))

    def set_cmd(self, v_mps: float, w_radps: float) -> None:
        self._target = self.wheel_targets_mmps(v_mps, w_radps)

    def stop(self) -> None:
        self._target = (0, 0, 0, 0)

    def next_cmd_frame(self) -> bytes:
        """Frame to put on the wire; call at cmd_resend_hz (keep-alive: the MCU
        watchdog needs a fresh valid CMD_VEL at least every 200 ms)."""
        self._seq = (self._seq + 1) & 0xFF
        return bp.encode_cmd_vel(self._seq, self._target)

    def mode_frame(self, mode: int) -> bytes:
        self._seq = (self._seq + 1) & 0xFF
        return bp.encode_cmd_mode(self._seq, mode)

    # --------------------------------------------------------- telemetry --
    def handle_telemetry(self, t: bp.Telemetry, now_s: float) -> None:
        """Integrate odometry from encoder counts (diff-drive midpoint rule)."""
        self.last_telemetry = t
        self.mcu_state = t.state
        self.fault_bits = t.fault_bits
        self.estop = bool(t.estop)

        counts = t.wheel_pos
        if self._last_counts is not None:
            k = self.params.m_per_count
            d = [(counts[i] - self._last_counts[i]) * k for i in range(4)]
            d_left = (d[0] + d[1]) / 2.0
            d_right = (d[2] + d[3]) / 2.0
            ds = (d_left + d_right) / 2.0
            dtheta = (d_right - d_left) / self.params.track_m
            mid = self.odom.theta + dtheta / 2.0
            self.odom.x += ds * math.cos(mid)
            self.odom.y += ds * math.sin(mid)
            self.odom.theta = math.atan2(math.sin(self.odom.theta + dtheta),
                                         math.cos(self.odom.theta + dtheta))
            if self._last_telem_time is not None:
                dt = now_s - self._last_telem_time
                if dt > 0:
                    self.odom.v = ds / dt
                    self.odom.w = dtheta / dt
        self._last_counts = counts
        self._last_telem_time = now_s

    def wheel_positions_rad(self) -> tuple:
        """Joint positions for /joint_states, LF LR RF RR."""
        if self.last_telemetry is None:
            return (0.0, 0.0, 0.0, 0.0)
        k = 2.0 * math.pi / self.params.counts_per_rev
        return tuple(c * k for c in self.last_telemetry.wheel_pos)

    def motion_ok(self) -> bool:
        return self.mcu_state == bp.STATE_ACTIVE and not self.estop

    def state_name(self) -> str:
        return bp.STATE_NAMES[self.mcu_state] if self.mcu_state < 7 else "?"


def params_from_design(repo_root: Path) -> BaseParams:
    """Load BaseParams straight from the repo's single source of truth."""
    sys.path.insert(0, str(repo_root))
    from buddy_calcs import P, R  # noqa: PLC0415
    return BaseParams(
        wheel_radius_m=P["wheels"]["radius_m"],
        track_m=2.0 * P["wheels"]["y_offset_m"],
        counts_per_rev=P["drive_motor"]["encoder_counts_per_rev_output"],
        vel_limit_mmps=round(
            R["mobility"]["teleop_commissioning_max_mps"] * 1000),
    )
