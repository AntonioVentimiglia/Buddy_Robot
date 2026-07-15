"""Unit tests for BaseCore (kinematics, clamping, odometry). No ROS needed.

Run:  python3 test_base_core.py     (from this directory)
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from buddy_base.base_core import BaseCore, BaseParams  # noqa: E402

PARAMS = BaseParams(wheel_radius_m=0.048, track_m=0.26,
                    counts_per_rev=3007.2, vel_limit_mmps=750)


def make_telem(counts, estop=0, state=4):
    import buddy_protocol as bp
    return bp.Telemetry(state=state, fault_bits=0, estop=estop, cmd_seq_echo=0,
                        wheel_pos=tuple(counts), wheel_vel=(0, 0, 0, 0),
                        motor_cur_ma=(0, 0, 0, 0), vbat_mv=11100)


class TestKinematics(unittest.TestCase):
    def setUp(self):
        self.core = BaseCore(PARAMS)

    def test_straight(self):
        w = self.core.wheel_targets_mmps(0.5, 0.0)
        self.assertEqual(w, (500, 500, 500, 500))

    def test_pivot_left(self):
        # +w = CCW: right side forward, left side back
        w = self.core.wheel_targets_mmps(0.0, 1.0)
        self.assertEqual(w[0], w[1])
        self.assertEqual(w[2], w[3])
        self.assertEqual(w[0], -130)  # 1.0 rad/s * 0.13 m * 1000
        self.assertEqual(w[2], 130)

    def test_arc(self):
        w = self.core.wheel_targets_mmps(0.3, 0.5)
        self.assertEqual(w[0], 300 - 65)
        self.assertEqual(w[2], 300 + 65)

    def test_clamp_preserves_ratio(self):
        w = self.core.wheel_targets_mmps(2.0, 1.0)  # way over the 750 limit
        self.assertEqual(max(abs(x) for x in w), 750)
        # ratio left/right preserved (2.0∓0.13 vs 2.0±0.13)
        self.assertAlmostEqual(w[0] / w[2], (2.0 - 0.13) / (2.0 + 0.13), places=2)


class TestOdometry(unittest.TestCase):
    def setUp(self):
        self.core = BaseCore(PARAMS)
        self.k = PARAMS.m_per_count

    def test_straight_line(self):
        self.core.handle_telemetry(make_telem([0, 0, 0, 0]), 0.0)
        n = round(1.0 / self.k)  # counts for 1 m
        self.core.handle_telemetry(make_telem([n, n, n, n]), 1.0)
        self.assertAlmostEqual(self.core.odom.x, 1.0, places=3)
        self.assertAlmostEqual(self.core.odom.y, 0.0, places=6)
        self.assertAlmostEqual(self.core.odom.theta, 0.0, places=6)
        self.assertAlmostEqual(self.core.odom.v, 1.0, places=3)

    def test_pivot_in_place(self):
        self.core.handle_telemetry(make_telem([0, 0, 0, 0]), 0.0)
        # quarter turn CCW: each side moves ±(pi/2)*track/2 meters
        arc = (math.pi / 2) * PARAMS.track_m / 2
        n = round(arc / self.k)
        self.core.handle_telemetry(make_telem([-n, -n, n, n]), 1.0)
        self.assertAlmostEqual(self.core.odom.theta, math.pi / 2, places=2)
        self.assertAlmostEqual(self.core.odom.x, 0.0, places=3)

    def test_theta_wraps(self):
        self.core.handle_telemetry(make_telem([0, 0, 0, 0]), 0.0)
        arc = (2.5 * math.pi) * PARAMS.track_m / 2  # 450 degrees
        n = round(arc / self.k)
        self.core.handle_telemetry(make_telem([-n, -n, n, n]), 1.0)
        self.assertLessEqual(abs(self.core.odom.theta), math.pi)

    def test_estop_reflected(self):
        self.core.handle_telemetry(make_telem([0, 0, 0, 0], estop=1, state=5), 0.0)
        self.assertTrue(self.core.estop)
        self.assertFalse(self.core.motion_ok())
        self.assertEqual(self.core.state_name(), "FAULT")


if __name__ == "__main__":
    unittest.main(verbosity=1)
