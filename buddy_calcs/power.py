"""Power budget and battery sizing equations for Buddy.

Pure functions + `summary()` evaluating the whole budget from the loaded
parameters. Derivations and limits of validity:
docs/analysis/power_budget_and_battery.py (marimo notebook, exported to .md).
"""

from __future__ import annotations

import math
from types import SimpleNamespace

from . import P, R
from . import drive


def motor_current(torque_nm: float, stall_torque_nm: float, stall_current_a: float,
                  no_load_current_a: float) -> float:
    """Linear brushed-DC model: I = I0 + (Istall - I0) * T / Tstall."""
    return no_load_current_a + (stall_current_a - no_load_current_a) * torque_nm / stall_torque_nm


def torque_at_current_limit(limit_a: float, stall_torque_nm: float, stall_current_a: float,
                            no_load_current_a: float) -> float:
    """Torque available when the driver caps current at limit_a (inverse model)."""
    return stall_torque_nm * (limit_a - no_load_current_a) / (stall_current_a - no_load_current_a)


def summary() -> SimpleNamespace:
    pw = P["power"]
    m = P["drive_motor"]
    d = drive.summary()
    v = pw["bus"]["v_nominal"]
    i0 = pw["motor_no_load_current_a"]
    i_lim = pw["driver_current_limit_a"]
    loads = pw["loads_w"]
    duty = pw["duty_cycle"]
    sizing = pw["battery_sizing"]

    def i_motor(t: float) -> float:
        return motor_current(t, m["stall_torque_nm"], m["stall_current_a"], i0)

    # --- peak current scenarios (12 V bus amps) ---
    system_w = sum(loads.values())
    system_a = system_w / v
    scen = {
        "flat cruise": 4 * i_motor(d.t_cruise_flat),
        "ramp + accel (design)": 4 * i_motor(d.t_design),
        "pivot breakaway (mu=0.8)": 4 * min(i_motor(d.t_pivot["carpet_high"]), i_lim),
        "all-motor stall, driver-limited": 4 * i_lim,
        "all-motor stall, UNLIMITED (fault)": 4 * m["stall_current_a"],
    }
    scen_total = {k: a + system_a for k, a in scen.items()}
    peak_designed = 4 * i_lim + system_a

    # --- average power (normal-duty mission model) ---
    omega_cruise = drive.wheel_rpm(R["mobility"]["autonomous_empty_room_max_mps"],
                                   d.wheel_radius_m) * 2 * math.pi / 60
    p_drive_cruise = 4 * d.t_cruise_flat * omega_cruise / sizing["drive_electrical_efficiency"]
    p_drive_avg = duty["moving_fraction"] * duty["maneuver_power_factor"] * p_drive_cruise
    p_avg_expected = (duty["jetson_average_w"]
                      + loads["rgbd_camera_reserve"] + loads["lidar_2d_reserve"]
                      + loads["mcu_drivers_logic"] + p_drive_avg)
    p_avg_allocation = system_w + p_drive_avg  # every load at full allocation

    # --- energy / capacity for the runtime requirement ---
    runtime_h = R["power"]["runtime_target_min"] / 60.0
    denom = sizing["usable_fraction"] * sizing["conversion_efficiency"]
    wh_expected = p_avg_expected * runtime_h / denom
    wh_allocation = p_avg_allocation * runtime_h / denom
    ah_expected = wh_expected / v
    ah_allocation = wh_allocation / v

    # --- future dual 6-DOF arms provision (requirements: manipulation_future) ---
    arms = pw["future_arms"]
    peak_with_arms = peak_designed + arms["peak_current_a"]
    p_avg_future = p_avg_allocation + arms["avg_power_w"]
    wh_future = p_avg_future * runtime_h / denom
    ah_future = wh_future / v

    # --- check the driver limit still permits the pivot ---
    t_available = torque_at_current_limit(i_lim, m["stall_torque_nm"], m["stall_current_a"], i0)

    return SimpleNamespace(
        arms=dict(arms), peak_with_arms=peak_with_arms,
        p_avg_future=p_avg_future, wh_future=wh_future, ah_future=ah_future,
        ah_target=ah_future, wh_target=wh_future,
        v=v, i_lim=i_lim, i0=i0, system_w=system_w, system_a=system_a,
        loads=dict(loads), duty=dict(duty), sizing=dict(sizing),
        scen_motor=scen, scen_total=scen_total, peak_designed=peak_designed,
        p_drive_cruise=p_drive_cruise, p_drive_avg=p_drive_avg,
        p_avg_expected=p_avg_expected, p_avg_allocation=p_avg_allocation,
        runtime_h=runtime_h, wh_expected=wh_expected, wh_allocation=wh_allocation,
        ah_expected=ah_expected, ah_allocation=ah_allocation,
        t_available_at_limit=t_available, t_pivot_worst=d.t_pivot["carpet_high"],
        bms_min_a=P["power"]["protection"]["bms_min_continuous_a"],
        fuse_a=P["power"]["protection"]["main_fuse_a"],
    )


def validate() -> list[str]:
    """Power-architecture consistency checks (called by tools/build.py)."""
    s = summary()
    problems = []
    if s.t_available_at_limit < s.t_pivot_worst:
        problems.append(
            f"driver current limit {s.i_lim} A only allows "
            f"{s.t_available_at_limit:.2f} N·m — below the worst pivot demand "
            f"{s.t_pivot_worst:.2f} N·m; raise the limit or accept slower pivots")
    if s.bms_min_a < s.peak_with_arms:
        problems.append(
            f"BMS spec {s.bms_min_a} A is below the designed peak including the "
            f"future arm branch {s.peak_with_arms:.1f} A")
    if s.fuse_a <= s.peak_with_arms:
        problems.append(
            f"main fuse {s.fuse_a} A would blow at the designed peak including "
            f"the future arm branch {s.peak_with_arms:.1f} A")
    return problems
