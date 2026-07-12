#!/usr/bin/env python3
"""Torque and speed sizing CLI for Buddy's differential/skid-steer base.

Thin wrapper over buddy_calcs.drive — the single source of the equations.
Defaults come from design_params.yaml + the requirements yaml, so running with
no flags evaluates the current v0.1 design case. Flags override for what-ifs.

Full derivations: docs/analysis/drive_torque_and_pivot_scrub.md
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from buddy_calcs import P, R  # noqa: E402
from buddy_calcs.drive import stop_accel, torque_nm, wheel_rpm  # noqa: E402


def main() -> int:
    a, w, mob = P["assumptions"], P["wheels"], R["mobility"]
    parser = argparse.ArgumentParser(description="Estimate drive torque and wheel RPM for Buddy.")
    parser.add_argument("--mass-kg", type=float, default=R["mass"]["design_gross_mass_limit_kg"],
                        help="Gross mass including payload")
    parser.add_argument("--wheel-radius-m", type=float, default=w["radius_m"])
    parser.add_argument("--driven-wheels", type=int, default=P["drive_motor"]["count"], choices=(2, 4))
    parser.add_argument("--speed-mps", type=float, default=mob["teleop_commissioning_max_mps"])
    parser.add_argument("--ramp-deg", type=float, default=mob["ramp_angle_v0_1_deg"])
    parser.add_argument("--accel-mps2", type=float, default=a["accel_design_mps2"],
                        help="Forward acceleration target")
    parser.add_argument("--crr", type=float, default=a["crr_carpet"],
                        help="Rolling resistance coefficient estimate")
    parser.add_argument("--efficiency", type=float, default=a["drivetrain_efficiency"],
                        help="Drivetrain efficiency estimate")
    parser.add_argument("--safety-factor", type=float, default=a["safety_factor"])
    parser.add_argument("--stopping-distance-m", type=float, default=mob["stopping_distance_target_m"])
    parser.add_argument("--csv", type=Path, default=None, help="Optional CSV output path for ramp/accel sweep")
    args = parser.parse_args()

    def torque(accel: float, ramp: float) -> float:
        return torque_nm(args.mass_kg, args.wheel_radius_m, args.driven_wheels, accel,
                         ramp, args.crr, args.efficiency, args.safety_factor)

    cruise_torque = torque(args.accel_mps2, args.ramp_deg)
    climb_no_accel_torque = torque(0.0, args.ramp_deg)
    braking_accel = stop_accel(args.speed_mps, args.stopping_distance_m)
    aggressive_torque = torque(braking_accel, args.ramp_deg)
    rpm = wheel_rpm(args.speed_mps, args.wheel_radius_m)

    print("Buddy torque estimate (defaults from design_params.yaml + requirements)")
    print("-----------------------------------------------------------------------")
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
    print("Treat aggressive_stop_case_Nm as a warning about the stop target, not as a normal motor target.")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ramp_deg", "accel_mps2", "torque_nm_each", "wheel_rpm"])
            for ramp in [0, 5, 10, 15, 20]:
                for accel in [0.0, 0.25, 0.5, 1.0, braking_accel]:
                    writer.writerow([ramp, accel, round(torque(accel, ramp), 3), round(rpm, 1)])
        print(f"CSV written: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
