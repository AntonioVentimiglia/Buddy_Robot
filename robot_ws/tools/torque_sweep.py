#!/usr/bin/env python3
"""Torque and speed sizing helper for Buddy's differential/skid-steer base.

This is intentionally independent of ROS so you can use it before hardware exists.

Formula:
    F = m*a + m*g*sin(theta) + Crr*m*g*cos(theta)
    T_per_driven_output = (F*r/n) * safety_factor / drivetrain_efficiency
    wheel_rpm = v / (2*pi*r) * 60

Interpretation:
    driven_wheels=4 means one motor/gearbox per wheel.
    driven_wheels=2 means one motor/gearbox per side, each side driving two wheels mechanically.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

G = 9.80665


def required_force(mass_kg: float, accel_mps2: float, ramp_deg: float, crr: float) -> float:
    theta = math.radians(ramp_deg)
    return (
        mass_kg * accel_mps2
        + mass_kg * G * math.sin(theta)
        + crr * mass_kg * G * math.cos(theta)
    )


def torque_nm(
    mass_kg: float,
    wheel_radius_m: float,
    driven_wheels: int,
    accel_mps2: float,
    ramp_deg: float,
    crr: float,
    drivetrain_efficiency: float,
    safety_factor: float,
) -> float:
    force_n = required_force(mass_kg, accel_mps2, ramp_deg, crr)
    return (force_n * wheel_radius_m / driven_wheels) * safety_factor / drivetrain_efficiency


def wheel_rpm(speed_mps: float, wheel_radius_m: float) -> float:
    return speed_mps / (2.0 * math.pi * wheel_radius_m) * 60.0


def stop_accel(speed_mps: float, stopping_distance_m: float) -> float:
    if stopping_distance_m <= 0:
        raise ValueError("stopping_distance_m must be greater than zero")
    return speed_mps * speed_mps / (2.0 * stopping_distance_m)


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate drive torque and wheel RPM for Buddy.")
    parser.add_argument("--mass-kg", type=float, default=30.0, help="Gross mass including payload")
    parser.add_argument("--wheel-radius-m", type=float, default=0.06)
    parser.add_argument("--driven-wheels", type=int, default=4, choices=(2, 4))
    parser.add_argument("--speed-mps", type=float, default=1.5)
    parser.add_argument("--ramp-deg", type=float, default=20.0)
    parser.add_argument("--accel-mps2", type=float, default=0.5, help="Forward acceleration target")
    parser.add_argument("--crr", type=float, default=0.04, help="Rolling resistance coefficient estimate")
    parser.add_argument("--efficiency", type=float, default=0.75, help="Drivetrain efficiency estimate")
    parser.add_argument("--safety-factor", type=float, default=2.0)
    parser.add_argument("--stopping-distance-m", type=float, default=0.25)
    parser.add_argument("--csv", type=Path, default=None, help="Optional CSV output path for ramp/accel sweep")
    args = parser.parse_args()

    cruise_torque = torque_nm(
        args.mass_kg,
        args.wheel_radius_m,
        args.driven_wheels,
        args.accel_mps2,
        args.ramp_deg,
        args.crr,
        args.efficiency,
        args.safety_factor,
    )
    climb_no_accel_torque = torque_nm(
        args.mass_kg,
        args.wheel_radius_m,
        args.driven_wheels,
        0.0,
        args.ramp_deg,
        args.crr,
        args.efficiency,
        args.safety_factor,
    )
    braking_accel = stop_accel(args.speed_mps, args.stopping_distance_m)
    aggressive_torque = torque_nm(
        args.mass_kg,
        args.wheel_radius_m,
        args.driven_wheels,
        braking_accel,
        args.ramp_deg,
        args.crr,
        args.efficiency,
        args.safety_factor,
    )
    rpm = wheel_rpm(args.speed_mps, args.wheel_radius_m)

    print("Buddy torque estimate")
    print("---------------------")
    print(f"gross_mass_kg:              {args.mass_kg:.2f}")
    print(f"wheel_radius_m:             {args.wheel_radius_m:.3f}")
    print(f"driven_outputs:             {args.driven_wheels}")
    print(f"target_speed_mps:           {args.speed_mps:.2f}")
    print(f"wheel_rpm_at_target_speed:  {rpm:.1f}")
    print(f"ramp_deg:                   {args.ramp_deg:.1f}")
    print(f"accel_mps2:                 {args.accel_mps2:.2f}")
    print(f"crr:                        {args.crr:.3f}")
    print(f"efficiency:                 {args.efficiency:.2f}")
    print(f"safety_factor:              {args.safety_factor:.2f}")
    print()
    print(f"torque_no_accel_Nm_each:    {climb_no_accel_torque:.2f}")
    print(f"torque_with_accel_Nm_each:  {cruise_torque:.2f}")
    print(f"stop_accel_mps2:            {braking_accel:.2f}")
    print(f"aggressive_stop_case_Nm:    {aggressive_torque:.2f}")
    print()
    print("Use torque_with_accel_Nm_each for first motor shortlist.")
    print("Treat aggressive_stop_case_Nm as a warning about your 0.25 m stop target, not as a normal motor target.")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ramp_deg", "accel_mps2", "torque_nm_each", "wheel_rpm"])
            for ramp in [0, 5, 10, 15, 20]:
                for accel in [0.0, 0.25, 0.5, 1.0, braking_accel]:
                    writer.writerow([
                        ramp,
                        accel,
                        round(torque_nm(
                            args.mass_kg,
                            args.wheel_radius_m,
                            args.driven_wheels,
                            accel,
                            ramp,
                            args.crr,
                            args.efficiency,
                            args.safety_factor,
                        ), 3),
                        round(rpm, 1),
                    ])
        print(f"CSV written: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
