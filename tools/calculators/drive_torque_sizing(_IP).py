#!/usr/bin/env python3
'''Drive torque sizing helper for Buddy.

Edit inputs below or turn this into a CLI later.
'''
import math


def required_wheel_torque(m_kg, wheel_radius_m, accel_mps2, ramp_deg, crr, driven_wheels, efficiency, safety_factor):
    g = 9.81
    theta = math.radians(ramp_deg)
    force = m_kg * accel_mps2 + m_kg * g * math.sin(theta) + crr * m_kg * g * math.cos(theta)
    return (force * wheel_radius_m / driven_wheels) * safety_factor / efficiency


def wheel_rpm(linear_speed_mps, wheel_radius_m):
    return (linear_speed_mps / (2 * math.pi * wheel_radius_m)) * 60.0


if __name__ == "__main__":
    print("Edit inputs in this file or convert to argparse when ready.")
    print("Example torque Nm:", required_wheel_torque(25, 0.08, 0.5, 5, 0.03, 4, 0.75, 2.0))
    print("Example wheel RPM:", wheel_rpm(1.0, 0.08))
