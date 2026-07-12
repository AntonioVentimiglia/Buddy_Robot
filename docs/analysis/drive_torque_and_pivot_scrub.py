"""Drive Torque and Pivot Scrub — parametric derivation (marimo notebook).

This notebook IS the source of docs/analysis/drive_torque_and_pivot_scrub.md.
Every substituted number is computed from design_params.yaml + the requirements
yaml via buddy_calcs — edit those files (or explore live with `marimo edit`)
and every value below updates. Export happens in tools/build.py.

    marimo edit docs/analysis/drive_torque_and_pivot_scrub.py   # live editing
    python3 tools/build.py                                       # regenerate .md
"""

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import math
    import sys
    from pathlib import Path

    import marimo as mo

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from buddy_calcs import P, R
    from buddy_calcs.drive import G, summary

    d = summary()
    a = P["assumptions"]
    w = P["wheels"]
    mu = a["scrub_mu"]
    theta = math.radians(d.ramp_deg)
    return G, P, R, a, d, math, mo, mu, theta, w


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Drive Torque and Pivot Scrub — Derivations

    This is the methods document behind
    [`motor_sizing_and_selection.md`](../research/hardware/motors_and_gearboxes/motor_sizing_and_selection.md)
    and milestone [M01](../portfolio/milestones/M01-drive-motor-selection.md). Every
    result is derived from first principles, substituted numerically so it can be
    checked by hand, and bounded by its stated limits of validity. **Every number in
    this document is computed live from `design_params.yaml` and the requirements
    yaml** (this page is exported from a marimo notebook — prose, code, figures, and
    the URDF share one parameter source and cannot disagree).
    """
    )
    return


@app.cell(hide_code=True)
def _(a, d, mo, mu, w):
    mo.md(
        rf"""
    ## 1. Notation

    | Symbol | Meaning | Current value | Units |
    |---|---|---|---|
    | $m$ | gross robot mass (design ceiling) | {d.mass_kg:g} | kg |
    | $g$ | gravitational acceleration | 9.80665 | m/s² |
    | $\theta$ | ramp angle | {d.ramp_deg:g} (v0.1), 0–20 swept | deg |
    | $a$ | commanded forward acceleration | {d.accel:g} | m/s² |
    | $C_{{rr}}$ | rolling resistance coefficient | {d.crr:g} (carpet, high end) | — |
    | $r$ | wheel radius | {d.wheel_radius_m:g} ({w["part"]}) | m |
    | $n$ | driven wheels (one motor each) | {d.driven:g} | — |
    | $\eta$ | drivetrain efficiency | {d.eta:g} | — |
    | $S$ | safety factor (applied to demand) | {d.sf:g} | — |
    | $v$ | ground speed (teleop max) | {d.v_teleop:g} | m/s |
    | $\mu$ | lateral scrub friction coefficient | {mu["carpet_low"]:g}–{mu["carpet_high"]:g} (carpet), ~{mu["marble"]:g} (marble) | — |
    | $x_w,\ y_w$ | wheel contact offsets from chassis center | {w["x_offset_m"]:g}, {w["y_offset_m"]:g} | m |

    Design values come from `design_params.yaml` (single source of truth, which
    also generates `buddy_params.xacro`); requirement values from
    `buddy_v0_1_requirements.yaml`. Assumptions are justified and stress-tested in
    §7. (Assumption dict this run: crr={a["crr_carpet"]:g}, η={a["drivetrain_efficiency"]:g},
    S={a["safety_factor"]:g}.)
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2. Straight-line tractive force

    Newton's second law along the ramp surface (see FBD, left panel). Three forces
    oppose forward motion, so the required tractive force at the tire–ground
    interface is their sum:

    $$F = \underbrace{ma}_{\text{inertia}} + \underbrace{mg\sin\theta}_{\text{grade}} + \underbrace{C_{rr}\,mg\cos\theta}_{\text{rolling resistance}}$$

    - **Inertia** $ma$: accelerating the full mass at the commanded rate.
    - **Grade** $mg\sin\theta$: the weight component parallel to the ramp.
    - **Rolling resistance** $C_{rr}mg\cos\theta$: proportional to the normal load
      $mg\cos\theta$, which is why it shrinks slightly as the ramp steepens.
    """
    )
    return


@app.cell(hide_code=True)
def _(G, d, math, mo, theta):
    _ma = d.mass_kg * d.accel
    _grade = d.mass_kg * G * math.sin(theta)
    _roll = d.crr * d.mass_kg * G * math.cos(theta)
    mo.md(
        rf"""
    Substituting the v0.1 design case ($m={d.mass_kg:g}$, $a={d.accel:g}$,
    $\theta={d.ramp_deg:g}°$, $C_{{rr}}={d.crr:g}$):

    $$F = {d.mass_kg:g}({d.accel:g}) + {d.mass_kg:g}(9.80665)\sin {d.ramp_deg:g}° + {d.crr:g}({d.mass_kg:g})(9.80665)\cos {d.ramp_deg:g}°$$
    $$F = {_ma:.2f} + {_grade:.2f} + {_roll:.2f} = {d.force_design:.2f}\ \text{{N}}$$
    """
    )
    return


@app.cell(hide_code=True)
def _(d, mo):
    mo.md(
        rf"""
    ## 3. From force to per-motor torque

    The force is shared by $n$ driven wheels; each wheel converts force to shaft
    torque through the radius $r$. Losses mean the motor must supply *more* than
    the ideal torque, so efficiency divides; the safety factor multiplies the
    demand (we inflate the requirement, never the motor's claimed capability):

    $$T = \frac{{F\,r}}{{n}}\cdot\frac{{S}}{{\eta}}$$

    $$T = \frac{{{d.force_design:.2f} \times {d.wheel_radius_m:g}}}{{{d.driven:g}}}\cdot\frac{{{d.sf:g}}}{{{d.eta:g}}} = {d.force_design * d.wheel_radius_m / d.driven:.3f} \times {d.sf / d.eta:.3f} = {d.t_design:.2f}\ \text{{N·m per motor}}$$

    Units check: $[\text{{N}}][\text{{m}}] = \text{{N·m}}$; $S$ and $\eta$ are
    dimensionless. ✓
    """
    )
    return


@app.cell(hide_code=True)
def _(d, mo):
    mo.md(
        rf"""
    ## 4. Wheel speed

    Rolling without slip, $v = \omega r$, converted to RPM:

    $$\text{{RPM}} = \frac{{v}}{{2\pi r}}\times 60 = \frac{{{d.v_teleop:g}}}{{2\pi({d.wheel_radius_m:g})}}\times 60 = {d.rpm_teleop:.1f}$$

    This is a *loaded* speed target — compare against a motor's speed under load,
    not its no-load rating (brushed DC speed droops roughly linearly with torque).
    """
    )
    return


@app.cell(hide_code=True)
def _(R, d, mo):
    _s = R["mobility"]["stopping_distance_target_m"]
    mo.md(
        rf"""
    ## 5. Braking as an acceleration case

    Stopping from $v$ in distance $s$ (constant deceleration, from $v^2 = 2as$):

    $$a_{{stop}} = \frac{{v^2}}{{2s}} = \frac{{{d.v_teleop:g}^2}}{{2({_s:g})}} = {d.a_stop:.2f}\ \text{{m/s}}^2$$

    Fed back into §2–3 in place of $a$, this gives {d.t_stop:.2f} N·m — a brief
    transient, not a thermal (continuous) requirement.
    """
    )
    return


@app.cell(hide_code=True)
def _(G, d, mo, mu, w):
    _M = mu["carpet_low"] * d.mass_kg * G * d.contact_radius
    _F = _M / (4 * w["y_offset_m"])
    mo.md(
        rf"""
    ## 6. Pivot-in-place scrub — the requirement that actually sized the motors

    A skid-steer robot has no steering axis: to yaw, the wheels must drag sideways
    across the floor. During a pivot about the chassis center, each contact patch
    moves on a circle of radius

    $$d = \sqrt{{x_w^2 + y_w^2}} = \sqrt{{{w["x_offset_m"]:g}^2 + {w["y_offset_m"]:g}^2}} = {d.contact_radius:.3f}\ \text{{m}}$$

    Kinetic friction opposes each patch's sliding direction — i.e., acts
    *tangentially*, resisting the rotation (see FBD, right panel). With weight
    split evenly ($N = mg/4$ per wheel), the total resisting yaw moment about the
    pivot center is:

    $$M = \sum_{{i=1}}^{{4}} \mu \frac{{mg}}{{4}} d = \mu\, m g\, d = {mu["carpet_low"]:g}\,({d.mass_kg:g})(9.80665)({d.contact_radius:.3f}) = {_M:.1f}\ \text{{N·m}} \quad (\mu = {mu["carpet_low"]:g})$$

    The drive wheels generate yaw moment through their *longitudinal* forces acting
    at the lateral offset $y_w$ (the fore-aft offset $x_w$ contributes no moment
    from a longitudinal force). Left wheels drive one way, right wheels the other;
    all four contribute:

    $$M_{{drive}} = 4 F_{{wheel}}\, y_w \;\;\Rightarrow\;\; F_{{wheel}} = \frac{{M}}{{4 y_w}} = \frac{{{_M:.1f}}}{{4({w["y_offset_m"]:g})}} = {_F:.1f}\ \text{{N}}$$

    $$T_{{pivot}} = \frac{{F_{{wheel}}\, r}}{{\eta}} = \frac{{{_F:.1f} \times {d.wheel_radius_m:g}}}{{{d.eta:g}}} = {d.t_pivot["carpet_low"]:.2f}\ \text{{N·m per motor}} \quad (\mu = {mu["carpet_low"]:g})$$

    Repeating for the $\mu$ range: **{d.t_pivot["marble"]:.2f} N·m** at
    $\mu={mu["marble"]:g}$ (marble), **{d.t_pivot["carpet_low"]:.2f} N·m** at
    $\mu={mu["carpet_low"]:g}$, **{d.t_pivot["carpet_high"]:.2f} N·m** at
    $\mu={mu["carpet_high"]:g}$ (thick carpet). No safety factor is applied here —
    this is already a worst-case peak demand and is carried as a range; it sets the
    motor's **stall** requirement, not its continuous rating. The selected motor's
    stall is {d.motor_stall:g} N·m —
    **{(d.motor_stall / d.t_pivot["carpet_high"] - 1) * 100:.0f}% margin at the
    worst-case $\mu$**.

    ![Free-body diagrams](../../assets/figures/drive_fbd.svg)

    *Left: ramp FBD behind §2. Right: pivot kinematics behind §6 — friction acts
    tangentially on each patch (radius $d$), drive forces act longitudinally at
    lateral offset $y_w$. Regenerate: `python3 tools/figures/plot_drive_fbd.py`.*
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7. Limits of validity — where these models stop being true

    1. **Rigid-body, quasi-static, even weight split.** No load transfer under
       acceleration or on ramps; at the design accel and ramp the shift is a few
       percent of $mg$ — negligible for sizing, not for traction-limit analysis at
       higher accelerations.
    2. **Point-contact Coulomb friction.** Carpet actually deforms (pile plowing),
       which behaves partly like added rolling resistance rather than pure Coulomb
       sliding — this is why $\mu$ is carried as a range to be **measured on the
       real floor before buying four motors** (single-motor drag test). The
       selected wheel (Hogback, ADR-0004) has a crowned tread that shrinks the
       contact patch during pivots specifically to reduce scrub; the model ignores
       this, which adds conservatism in the direction of safety.
    3. **Pivot about the geometric center.** True for symmetric commands and mass
       distribution; a payload shifting the CG moves the pivot point and
       redistributes normal loads.
    4. **Static vs kinetic friction.** Breakaway (static) torque exceeds the
       kinetic value computed here; the mitigation (driver current limiting +
       arc turns in software) is sized against the kinetic estimate at high $\mu$.
    5. **No suspension compliance.** A rigid 4-wheel chassis on uneven floor can
       unload a wheel entirely; the moment balance then loses that wheel's
       contribution on both the resisting and driving side.

    ## 8. Verification plan (closes the loop on the estimates)

    - Bench: stall-torque spot check of one purchased motor against datasheet
      before buying four.
    - Floor: powered drag test to back out effective $\mu$ on the actual carpet
      and marble (log driver current at known PWM).
    - Ramp: REQ_MOB-style ramp start test with current logging — measured current
      maps back through the motor's torque constant to validate §2–3 end to end.
    """
    )
    return


if __name__ == "__main__":
    app.run()
