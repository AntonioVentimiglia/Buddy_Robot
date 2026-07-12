"""Drive-base sizing equations for Buddy.

Pure functions (explicit arguments) so they are checkable in isolation, plus
`summary()` which evaluates the whole v0.1 envelope from the loaded parameters.
Derivations, symbol definitions, and limits of validity:
docs/analysis/drive_torque_and_pivot_scrub.py (marimo notebook, exported to .md).
"""

from __future__ import annotations

import math
from types import SimpleNamespace

from . import P, R

G = 9.80665


def required_force(mass_kg: float, accel_mps2: float, ramp_deg: float, crr: float) -> float:
    """Tractive force: F = m*a + m*g*sin(theta) + Crr*m*g*cos(theta)."""
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
    """Per-motor torque demand: T = (F*r/n) * SF / eta."""
    force_n = required_force(mass_kg, accel_mps2, ramp_deg, crr)
    return (force_n * wheel_radius_m / driven_wheels) * safety_factor / drivetrain_efficiency


def wheel_rpm(speed_mps: float, wheel_radius_m: float) -> float:
    """Wheel speed for a ground speed, rolling without slip."""
    return speed_mps / (2.0 * math.pi * wheel_radius_m) * 60.0


def stop_accel(speed_mps: float, stopping_distance_m: float) -> float:
    """Constant deceleration to stop from v in distance s: a = v^2 / (2s)."""
    if stopping_distance_m <= 0:
        raise ValueError("stopping_distance_m must be greater than zero")
    return speed_mps * speed_mps / (2.0 * stopping_distance_m)


def pivot_torque(
    mu: float,
    mass_kg: float,
    wheel_radius_m: float,
    x_offset_m: float,
    y_offset_m: float,
    drivetrain_efficiency: float,
) -> float:
    """Per-motor torque to pivot in place against tire scrub (peak/stall).

    Resisting yaw moment M = mu*m*g*d with contact radius d = hypot(x, y);
    four longitudinal drive forces act at lateral offset y: F = M/(4y);
    T = F*r/eta. No safety factor — this is already a worst-case peak.
    """
    d = math.hypot(x_offset_m, y_offset_m)
    resist_moment = mu * mass_kg * G * d
    force_per_wheel = resist_moment / (4.0 * y_offset_m)
    return force_per_wheel * wheel_radius_m / drivetrain_efficiency


def summary() -> SimpleNamespace:
    """Evaluate the full v0.1 envelope from the loaded P (design) and R (reqs)."""
    a = P["assumptions"]
    w = P["wheels"]
    mob = R["mobility"]
    m = R["mass"]["design_gross_mass_limit_kg"]
    r = w["radius_m"]
    n = P["drive_motor"]["count"]
    crr, eta, sf = a["crr_carpet"], a["drivetrain_efficiency"], a["safety_factor"]
    v_teleop = mob["teleop_commissioning_max_mps"]
    ramp = mob["ramp_angle_v0_1_deg"]
    accel = a["accel_design_mps2"]

    common = dict(mass_kg=m, wheel_radius_m=r, driven_wheels=n, crr=crr,
                  drivetrain_efficiency=eta, safety_factor=sf)
    a_stop = stop_accel(v_teleop, mob["stopping_distance_target_m"])
    return SimpleNamespace(
        mass_kg=m, wheel_radius_m=r, driven=n, crr=crr, eta=eta, sf=sf,
        ramp_deg=ramp, accel=accel, v_teleop=v_teleop,
        force_design=required_force(m, accel, ramp, crr),
        t_cruise_flat=torque_nm(accel_mps2=0.0, ramp_deg=0.0, **common) / sf,  # continuous, no SF
        t_design=torque_nm(accel_mps2=accel, ramp_deg=ramp, **common),
        t_steady_ramp=torque_nm(accel_mps2=0.0, ramp_deg=ramp, **common),
        a_stop=a_stop,
        t_stop=torque_nm(accel_mps2=a_stop, ramp_deg=ramp, **common),
        rpm_teleop=wheel_rpm(v_teleop, r),
        rpm_future=wheel_rpm(mob["future_top_speed_goal_mps"], r),
        t_future=torque_nm(accel_mps2=accel, ramp_deg=mob["future_ramp_angle_goal_deg"], **common),
        contact_radius=math.hypot(w["x_offset_m"], w["y_offset_m"]),
        t_pivot={name: pivot_torque(mu, m, r, w["x_offset_m"], w["y_offset_m"], eta)
                 for name, mu in a["scrub_mu"].items()},
        motor_stall=P["drive_motor"]["stall_torque_nm"],
    )
