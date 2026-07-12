"""Power Budget and Battery Sizing — parametric derivation (marimo notebook).

Source of docs/analysis/power_budget_and_battery.md. All numbers computed from
design_params.yaml + requirements yaml via buddy_calcs.

    marimo edit docs/analysis/power_budget_and_battery.py   # live editing
    python3 tools/build.py                                   # regenerate .md
"""

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from buddy_calcs import P, R
    from buddy_calcs import power
    from buddy_calcs.drive import summary as drive_summary

    s = power.summary()
    d = drive_summary()
    m = P["drive_motor"]
    pw = P["power"]
    return P, R, d, m, mo, pw, s


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Power Budget and Battery Sizing

    Methods document for the power architecture ([ADR-0005](../decisions/ADR-0005-power-architecture-3s-liion.md)).
    The driving concern: four drive motors with 9.2 A stall each *looks* like an
    impossible worst case. This document shows why it is not — stall current is a
    **fault condition converted into a designed ceiling** by the motor drivers'
    current limit — and derives the battery that covers both the peaks and the
    60-minute runtime requirement. Every number is computed from
    `design_params.yaml` + the requirements yaml.
    """
    )
    return


@app.cell(hide_code=True)
def _(m, mo, pw, s):
    mo.md(
        rf"""
    ## 1. Notation and allocations

    | Symbol / item | Meaning | Current value | Units |
    |---|---|---|---|
    | $V$ | bus voltage, 3S Li-ion nominal | {s.v:g} (range {pw["bus"]["v_cutoff"]:g}–{pw["bus"]["v_full"]:g}) | V |
    | $I_{{stall}}$ | motor stall current | {m["stall_current_a"]:g} | A |
    | $T_{{stall}}$ | motor stall torque | {m["stall_torque_nm"]:g} | N·m |
    | $I_0$ | motor no-load current (estimate) | {s.i0:g} | A |
    | $I_{{lim}}$ | driver per-motor current limit | {s.i_lim:g} | A |
    | Jetson Orin Nano | 25 W super mode + carrier overhead | {s.loads["jetson_orin_nano"]:g} | W |
    | RGB-D camera | **reserve** — selection constraint | {s.loads["rgbd_camera_reserve"]:g} | W |
    | 2D LiDAR | **reserve** — selection constraint | {s.loads["lidar_2d_reserve"]:g} | W |
    | MCU + driver logic | NUCLEO-G474 + encoders + E-stop | {s.loads["mcu_drivers_logic"]:g} | W |
    | Expansion | unallocated headroom | {s.loads["expansion_reserve"]:g} | W |

    The camera and LiDAR are **not chosen yet** — their rows are *reserved
    allocations*, upper bounds that become hard selection constraints. A candidate
    sensor exceeding its reserve triggers a budget re-run before purchase. Total
    system (non-drive) allocation: **{s.system_w:g} W = {s.system_a:.1f} A** at
    {s.v:g} V.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2. Motor current model

    A brushed DC motor's current is linear in torque between the no-load and stall
    points:

    $$I(T) = I_0 + (I_{stall} - I_0)\,\frac{T}{T_{stall}}$$

    The driver's current limit inverts this: capping current at $I_{lim}$ caps the
    torque the motor can produce at

    $$T(I_{lim}) = T_{stall}\,\frac{I_{lim} - I_0}{I_{stall} - I_0}$$

    This is the central design move: **the stall current is what flows when
    control has already failed; the driver limit makes the worst case a chosen
    number instead of a physical accident.**
    """
    )
    return


@app.cell(hide_code=True)
def _(m, mo, s):
    mo.md(
        rf"""
    Substituting the chosen limit $I_{{lim}} = {s.i_lim:g}$ A:

    $$T({s.i_lim:g}) = {m["stall_torque_nm"]:g}\,\frac{{{s.i_lim:g} - {s.i0:g}}}{{{m["stall_current_a"]:g} - {s.i0:g}}} = {s.t_available_at_limit:.2f}\ \text{{N·m}}$$

    which exceeds the worst-case pivot demand ({s.t_pivot_worst:.2f} N·m at
    $\mu = 0.8$, from the [drive derivation](drive_torque_and_pivot_scrub.md)) —
    so even thick-carpet pivots complete under the limit. This inequality is
    enforced automatically: `tools/build.py` fails if a parameter change breaks it.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, s):
    _rows = "\n".join(
        f"    | {name} | {a - s.system_a:.1f} | {a:.1f} |"
        for name, a in s.scen_total.items()
    )
    mo.md(
        rf"""
    ## 3. Peak-current scenarios (bus amps at {s.v:g} V)

    | Scenario | Drive (A) | Total incl. system (A) |
    |---|---|---|
{_rows}

    The **designed peak is {s.peak_designed:.1f} A** (all four drivers
    simultaneously at their limit — already a pathological command). The
    unlimited-stall row exists only to size the fault protection; it is not an
    operating point.

    ![Power budget](../../assets/figures/power_budget.svg)

    *Left: peak bus current by scenario against the protection chain. Right:
    average-power stack for the two mission models, with the resulting battery
    capacity. Regenerate: `python3 tools/figures/plot_power_budget.py`.*

    ## 4. Protection chain

    Ordered so each layer only sees what the previous one failed to stop:
    driver limits ({s.i_lim:g} A/motor) → BMS overcurrent
    (≥ {s.bms_min_a:g} A continuous, above the {s.peak_designed:.1f} A designed
    peak) → main fuse ({s.fuse_a:g} A slow-blow, below wiring ampacity — wire the
    bus for ≥ 50 A: 10 AWG) → E-stop interrupts motor power upstream of the
    drivers per REQ_SAFE.
    """
    )
    return


@app.cell(hide_code=True)
def _(R, mo, s):
    mo.md(
        rf"""
    ## 5. Mission energy model

    Drive power at cruise ({R["mobility"]["autonomous_empty_room_max_mps"]:g} m/s,
    flat carpet) from the drive derivation's torque, through the electrical
    efficiency of motor + driver ({s.sizing["drive_electrical_efficiency"]:g}):

    $$P_{{drive,cruise}} = \frac{{4\,T_{{cruise}}\,\omega}}{{\eta_{{elec}}}} = {s.p_drive_cruise:.1f}\ \text{{W}}$$

    scaled by the duty model (moving {s.duty["moving_fraction"]:.0%} of the
    mission, maneuver factor {s.duty["maneuver_power_factor"]:g}×):
    $P_{{drive,avg}} = {s.p_drive_avg:.1f}$ W. Two mission totals:

    - **Expected**: Jetson at its typical {s.duty["jetson_average_w"]:g} W +
      sensor/MCU loads + drive → **{s.p_avg_expected:.1f} W**
    - **Allocation** (everything at its full reserve simultaneously):
      **{s.p_avg_allocation:.1f} W** — the conservative bound the battery must
      honor to *guarantee* the runtime requirement.

    ## 6. Battery capacity

    For runtime $t = {s.runtime_h * 60:.0f}$ min, usable fraction
    {s.sizing["usable_fraction"]:g} (Li-ion depth-of-discharge for cycle life) and
    conversion efficiency {s.sizing["conversion_efficiency"]:g}:

    $$E = \frac{{P_{{avg}}\, t}}{{f_{{usable}}\ \eta_{{conv}}}}$$

    | Mission model | Energy | Capacity @ {s.v:g} V |
    |---|---|---|
    | Expected | {s.wh_expected:.0f} Wh | {s.ah_expected:.1f} Ah |
    | Allocation (guarantee) | {s.wh_allocation:.0f} Wh | {s.ah_allocation:.1f} Ah |

    **Target: 3S Li-ion, ≥ {s.ah_allocation:.0f} Ah (≈ {s.wh_allocation:.0f} Wh),
    BMS ≥ {s.bms_min_a:g} A continuous.** E.g. a 3S3P–3S4P pack of high-drain
    21700 cells, or an equivalent prebuilt pack — $60–100 class, not exotic. The
    C-rate demand is mild: {s.peak_designed:.1f} A peak on ≥ {s.ah_allocation:.0f} Ah
    is ≈ {s.peak_designed / s.ah_allocation:.1f}C.

    ## 7. Limits of validity

    1. **$I_0$ is an estimate** — measure no-load current on the first purchased
       motor; it shifts the torque-at-limit inequality in §2.
    2. **Reserves are allocations, not physics.** The expected-vs-allocation gap
       ({s.p_avg_expected:.0f} vs {s.p_avg_allocation:.0f} W) is the price of
       deferring sensor selection; it shrinks as real parts replace reserves.
    3. **The duty model is assumed** (moving fraction, maneuver factor, Jetson
       average) — replace with logged power data from the first teleop sessions.
    4. **Battery capacity fades** with cycles and cold; the usable-fraction
       derating covers early life, not end-of-life.
    5. **Voltage sag** under the designed peak briefly lowers available motor
       torque (T ∝ V at fixed PWM); the Jetson is isolated behind a regulated
       buck so sag cannot brown out compute.

    ## 8. Verification plan

    - Bench-measure motor no-load current and stall current against datasheet.
    - Log battery voltage/current through the MCU during first teleop; replace
      the duty model with measured averages.
    - Verify BMS overcurrent trip point and fuse behavior before first rolling
      drive (REQ_SAFE bench checklist).
    """
    )
    return


if __name__ == "__main__":
    app.run()
