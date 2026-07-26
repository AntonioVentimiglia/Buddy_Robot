"""End-to-end integration: BaseCore <-> wire bytes <-> mock MCU.

This is the whole v0.1 drive stack minus physics: body commands become
protocol frames, the mock MCU runs the real state machine + watchdog + wheel
model, telemetry frames come back, and BaseCore integrates odometry. If this
passes, bench day is about electrons, not logic.

Run:  python3 test_integration_mock.py     (from this directory)
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[2] / "buddy_firmware_interfaces" / "python"))

import buddy_protocol as bp  # noqa: E402
from buddy_base.base_core import BaseCore, BaseParams  # noqa: E402
from mock_mcu import MockMcu  # noqa: E402

PARAMS = BaseParams(wheel_radius_m=0.048, track_m=0.26,
                    counts_per_rev=753.2, vel_limit_mmps=750)
DT = 0.01  # 100 Hz sim tick


class Loop:
    """Wire both ends together in-process; advance simulated time."""

    def __init__(self):
        self.core = BaseCore(PARAMS)
        self.t = 0.0
        self.mcu = MockMcu(clock=lambda: self.t)  # simulated time
        self.parser = bp.Parser()

    def run(self, seconds, send_cmds=True, resend_every=0.05):
        next_send = 0.0
        for _ in range(round(seconds / DT)):
            self.t += DT
            if send_cmds and self.t >= next_send:
                self.mcu.handle_bytes(self.core.next_cmd_frame())
                next_send = self.t + resend_every
            self.mcu.tick(DT)
            for f in self.parser.feed(bytes(self.mcu.tx)):
                if f.type == bp.T_TELEMETRY:
                    self.core.handle_telemetry(bp.Telemetry.unpack(f.payload),
                                               self.t)
            self.mcu.tx.clear()

    def arm(self):
        self.mcu.handle_bytes(self.core.mode_frame(bp.MODE_ARM))


class TestDriveStack(unittest.TestCase):
    def test_straight_drive_odometry(self):
        loop = Loop()
        loop.arm()
        loop.core.set_cmd(0.3, 0.0)  # 0.3 m/s forward
        loop.run(2.0)
        self.assertEqual(loop.core.state_name(), "ACTIVE")
        # first-order wheel model (tau=100 ms) eats ~0.03 m of the ideal 0.6 m
        self.assertAlmostEqual(loop.core.odom.x, 0.57, delta=0.05)
        self.assertAlmostEqual(loop.core.odom.y, 0.0, places=3)
        self.assertAlmostEqual(loop.core.odom.theta, 0.0, places=3)
        self.assertAlmostEqual(loop.core.odom.v, 0.3, delta=0.02)

    def test_pivot_odometry(self):
        loop = Loop()
        loop.arm()
        loop.core.set_cmd(0.0, 1.0)  # 1 rad/s CCW
        loop.run(1.0)
        self.assertAlmostEqual(loop.core.odom.theta, 0.9, delta=0.1)
        self.assertAlmostEqual(loop.core.odom.x, 0.0, places=2)

    def test_watchdog_stops_without_commands(self):
        loop = Loop()
        loop.arm()
        loop.core.set_cmd(0.3, 0.0)
        loop.run(0.5)
        self.assertEqual(loop.core.state_name(), "ACTIVE")
        loop.run(0.8, send_cmds=False)  # bridge dies: no keep-alives
        self.assertEqual(loop.core.state_name(), "SAFE_IDLE")
        self.assertTrue(loop.core.fault_bits & bp.FAULT_CMD_TIMEOUT)
        self.assertLess(abs(loop.core.odom.v), 0.01)  # rolled to a stop
        # watchdog fired at +200 ms, so total distance is bounded
        self.assertLess(loop.core.odom.x, 0.5 * 0.3 + 0.3 * 0.35)

    def test_estop_visible_at_ros_level(self):
        loop = Loop()
        loop.arm()
        loop.core.set_cmd(0.2, 0.0)
        loop.run(0.3)
        loop.mcu.set_estop(True)
        loop.run(0.3)
        self.assertTrue(loop.core.estop)
        self.assertFalse(loop.core.motion_ok())
        self.assertEqual(loop.core.state_name(), "FAULT")

    def test_wheel_positions_for_joint_states(self):
        loop = Loop()
        loop.arm()
        loop.core.set_cmd(0.3, 0.0)
        loop.run(1.0)
        pos = loop.core.wheel_positions_rad()
        # ~0.27 m traveled -> ~5.6 rad of wheel rotation, all wheels equal
        self.assertGreater(pos[0], 4.0)
        self.assertAlmostEqual(pos[0], pos[2], delta=0.01)


if __name__ == "__main__":
    unittest.main(verbosity=1)
