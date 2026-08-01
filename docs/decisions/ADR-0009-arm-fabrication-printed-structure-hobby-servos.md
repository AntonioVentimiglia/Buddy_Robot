# ADR-0009: Future Arms — Printed Structure with Hobby Servos

- Status: Proposed
- Date: 2026-07-31

## Context

ADR-0005 (amended 2026-07-14) sized the battery, BMS, and main fuse to carry two
future 6-DOF arms so the v0.1 pack purchase would not be wasted. That amendment
recorded an explicit placeholder in `design_params.yaml → power.future_arms`:
**12 XM430-class joints, 45 W average, 10 A peak**, with instructions to replace
it with real specs at arm selection.

The arm approach has now been chosen — **printed structure driven by hobby
servos** — which is not the same class of actuator the placeholder assumed. The
choice is driven by cost: with LiDAR, RGB-D, and both arms inside the $2000
programme budget, Dynamixel-class smart servos (~$260+ each, ~$3,100 for twelve)
are unreachable by an order of magnitude. Printed structure follows directly from
ADR-0008.

This ADR is recorded **before** the battery SKU is purchased, because the actuator
class changes the shape of the arm load in a way that touches the protection
chain.

## Decision

- **Arm structure: 3D printed** (ASA / PA-CF), on the printer selected in
  ADR-0008.
- **Actuators: hobby servos** — digital metal-gear class, ~20–60 kg·cm at
  6–7.4 V. Specific SKU deferred to arm selection.
- **Consequence accepted:** payload, reach, repeatability, and duty cycle will be
  materially below a Dynamixel-class arm. The arms are a capability
  demonstration, not a precision manipulator.
- **The `power.future_arms` placeholder stays in place for now**, with the
  bounding analysis below recorded against it. It is refined — not replaced — at
  servo selection.

## The consequence that matters: stall is no longer a designed ceiling

ADR-0005's central insight was that **motor stall current is a fault condition,
not an operating point**, because the VNH5019 drivers have an adjustable current
limit that turns the worst case into a chosen number (8 A/motor). That reasoning
is what made the power budget close.

**That trick does not transfer to hobby servos.** A dumb PWM servo has no
programmable current limit and no telemetry — commanded into a stall, it draws
stall current until something else stops it. The ceiling has to be imposed
externally.

Bounding estimates, 12 joints on a ~6.5 V servo rail (assumptions stated, to be
replaced at servo selection):

| Case | Per-servo | Rail load | Referred to 11.1 V bus (buck η ≈ 0.85) | vs placeholder |
|---|---|---|---|---|
| Manipulation average | ~0.5 A | ~39 W | ~4 A | 45 W placeholder **holds** |
| Realistic peak (8 joints loaded) | ~2 A | ~104 W | **~11 A** | 10 A placeholder **marginal** |
| All 12 stalled simultaneously | ~3.5 A | ~273 W | **~29 A** | ~3× the placeholder |

The 29 A case would push the arms-inclusive designed peak from 47 A to ~66 A,
which would exceed both the BMS ≥50 A and the 60 A main fuse chosen in ADR-0005.

**Resolution — the existing branch fuse already contains it.**
`power.protection.arm_branch_fuse_a = 15` caps the arm branch at ~166 W at the
bus, i.e. ~21.7 A at the servo rail. That sits deliberately between the realistic
peak (holds) and the all-stalled case (blows). So the ADR-0005 protection chain
survives this actuator change **unmodified**.

What changes is the *role* of that fuse. It was specified as a backstop against a
fault in a system whose actuators limited their own current. It is now the
**primary current-limiting element** for the arm branch. That is a meaningful
downgrade in behaviour — the drive side responds to overload by quietly limiting
torque, whereas the arm side will respond by blowing a fuse and requiring manual
intervention. It is safe, but it is not graceful, and it should be improved by a
current-limited servo rail supply at arm build time rather than left as-is.

## Consequences

**What improves**

- The arms become affordable within the programme budget at all.
- Structure and actuators are both in-house/hobby-grade, so iteration is cheap
  and the arms can be redesigned without vendor lead time.
- The v0.1 battery/BMS/fuse selection is **confirmed unchanged** by this
  decision — the imminent pack purchase is not blocked.

**What gets harder**

- **No joint feedback.** Standard hobby servos are open-loop from the
  controller's perspective. MoveIt 2 and any meaningful trajectory execution
  expect joint state. Either servos with position feedback output must be
  selected, or external encoders added — this is a real design task, not a detail.
- **Bus architecture changes.** Hobby servos are PWM, not a smart serial bus, so
  the arms need a PCA9685-class 16-channel PWM driver or a dedicated MCU.
  **This weakens ADR-0006's rationale for reserving CAN-FD "for the arm era"** —
  the reservation is still harmless, but its stated justification no longer holds
  and should be amended when the arm phase begins.
- Printed structure plus geared hobby servos means backlash and compliance at
  every joint; positional repeatability will be poor by manipulator standards.
- Servo rail is a new regulated rail (~6–7.4 V, several amps) not currently in
  the power one-line or `integration_map.yaml`.

**What must be updated**

- `design_params.yaml → power.future_arms` — comment updated to name the actuator
  class and cite this ADR. **Numeric values unchanged pending servo selection**;
  the bounding table above is the interim record.
- `docs/requirements/buddy_v0_1_requirements.yaml → manipulation_future` — payload
  and precision expectations lowered to match a hobby-servo arm.
- ADR-0006 — amend the CAN-FD reservation rationale at arm phase start.
- `integration_map.yaml` — servo rail + PWM driver when the arm phase begins.

## Alternatives considered

- **Dynamixel XM430-class smart servos** — programmable current limits, position
  feedback, daisy-chained bus, first-class ROS 2 support. This is the technically
  correct answer and it is what the ADR-0005 placeholder assumed. Rejected purely
  on cost: ~$3,100 for twelve against a $2000 programme budget.
- **Cheap smart-servo alternatives (e.g. Feetech STS/SCS bus servos)** — serial
  bus with position feedback at hobby prices, and a genuine middle path.
  **Not yet properly evaluated** — see open item below; this ADR should be
  revisited before servos are actually bought.
- **Purchased arm kit** — rejected on cost and on losing the design exercise that
  is the point of the project.
- **Defer the arm decision entirely** — rejected because the battery purchase is
  imminent and the actuator class affects the protection chain.

## What would change this decision

- A bus-servo option with position feedback landing near hobby-servo prices →
  switch, and recover both joint feedback and current limiting.
- Bench measurement showing printed joints cannot hold the arm's own weight
  without unacceptable droop → structure moves to aluminium at the proximal
  joints.

## Open items

- [ ] **Evaluate Feetech STS/SCS-class bus servos before buying anything.**
      Position feedback and a serial bus would eliminate two of the three
      "what gets harder" items above at close to hobby-servo cost.
- [ ] Refine `power.future_arms` with measured servo specs once selected, then
      re-run `python3 tools/build.py` so the validator re-checks the chain.
- [ ] Decide joint feedback strategy before arm CAD starts.

## Update requirements

- [ ] Update `PROJECT_CONTEXT.md` §1 (arm approach) and §"still undecided".
- [ ] Update `docs/requirements/design_conflicts.md` (#4 budget split).
- [ ] Amend ADR-0006 CAN-FD rationale at arm phase start.
