# ADR-0005: Power Architecture — 3S Li-ion Bus with Designed Current Ceiling

- Status: Proposed
- Date: 2026-07-12

## Context

Four drive motors at 9.2 A stall each (36.8 A naive worst case) plus a Jetson
Orin Nano, RGB-D camera, 2D LiDAR, and drive MCU raised the fear that battery
sizing was impossible or unaffordable. The analysis
([`power_budget_and_battery.md`](../analysis/power_budget_and_battery.md))
showed the fear dissolves once stall is treated as a **fault condition capped
by design** rather than an operating point: the motor drivers' current limit
makes the worst case a chosen number.

The camera and LiDAR are not selected yet, so their power figures are **reserved
allocations** that become hard selection constraints.

## Decision

- **Bus:** 3S Li-ion (9.0–12.6 V, 11.1 V nominal) with integrated **BMS ≥ 40 A
  continuous** — chosen over RC LiPo for the hardware overcurrent/overdischarge
  protection layer, appropriate for a robot operating near people and pets.
- **Designed current ceiling:** motor drivers must provide an adjustable
  per-channel current limit, set to **8 A/motor**. This allows 3.23 N·m — above
  the 3.05 N·m worst-case carpet pivot — while capping the designed peak at
  **37 A** (4 × 8 A + 5 A system). Adjustable current limiting is now a
  **mandatory** requirement for motor driver selection, not a preference.
- **Protection chain:** driver limits (8 A) → BMS (≥ 40 A) → 50 A slow-blow main
  fuse on ≥ 10 AWG bus wiring → E-stop interrupting motor power upstream of the
  drivers.
- **Rails:** motors direct on the battery bus; Jetson behind a regulated 12 V
  buck (dev kit input range is 9–20 V, so 3S is in-window, but regulation
  isolates compute from pivot-sag brownouts); 5 V buck for LiDAR/logic.
- **Battery capacity target:** **3S ≥ 8 Ah (≈ 92 Wh), BMS ≥ 40 A** — guarantees
  the 60-minute runtime even with every reserve fully consumed (allocation
  model 66 W avg); expected usage (46 W avg) gives ~85 min. Peak demand is a
  mild ≈ 4.5C. $60–100 class. Exact SKU selected at purchase.
- **Power allocations** (from `design_params.yaml`, enforced as selection
  constraints): Jetson 30 W, RGB-D camera ≤ 5 W, 2D LiDAR ≤ 5 W, MCU + driver
  logic 5 W, expansion 10 W.

## Consequences

- Motor driver research (next task) inherits hard requirements: 4 brushed
  channels, 12 V class, ≥ 10 A capability, **adjustable ~8 A current limit**
  (in-driver, or implementable in the MCU from driver current-sense feedback),
  current telemetry to the MCU preferred.
- A candidate camera or LiDAR exceeding its reserve triggers a budget re-run
  (`tools/build.py` validates the protection-chain inequalities automatically).
- The 8 A limit means a true four-wheel blocked stall produces 37 A until
  firmware or the operator reacts — thermally fine briefly for motors specced
  at 9.2 A stall, and below BMS/fuse thresholds by design.
- Budget: battery $60–100 + drivers + DC-DC converters (~$20–30) stack onto the
  $300 motors+wheels; total build tracks toward the top of the $300–600 band —
  consistent with design conflict #4, no new violation.

## Open items before this moves to Accepted

- Measure motor no-load current (shifts the torque-at-limit margin).
- Select driver (validates that an 8 A limit is actually settable).
- Select battery SKU meeting ≥ 8 Ah / ≥ 40 A BMS; verify BMS trip behavior on
  the bench before first rolling drive.
