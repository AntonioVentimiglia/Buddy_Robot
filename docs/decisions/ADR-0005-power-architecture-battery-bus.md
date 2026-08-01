# ADR-0005: Power Architecture — Battery Bus, Driver-Limited Current, Fused Protection

- Status: Proposed
- Date: 2026-07-12
- Amended: 2026-07-14 (future dual-arm provision — see bottom section)

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
- Select battery SKU meeting the spec as twice amended — **4S LiFePO4,
  ≥ 12.1 Ah (buy 20 Ah, the next standard size), BMS ≥ 50 A continuous** —
  and verify BMS trip behaviour on the bench before first rolling drive.

## Amendment 2026-07-14 — future dual-arm provision

The robot's roadmap adds **two 6-DOF arms** in a later version, sharing the
main battery (requirements: `manipulation_future`). Buying an 8 Ah pack for
v0.1 would waste that money when the arms arrive, so the battery spec is
re-sized against the future load while everything else in this ADR stands:

- Arm provision (documented placeholder, XM430-class): 12 joints, **+45 W
  average** at manipulation duty, **+10 A peak** burst — refine in
  `design_params.yaml → power.future_arms` when arms are actually selected.
- Designed peak becomes **47 A** (37 A drive+system + 10 A arms) → **BMS ≥ 50 A
  continuous**, **main fuse 50 → 60 A slow-blow**, bus wiring 8 AWG (or
  2×10 AWG). Future arm branch separately fused at 15 A.
- Battery capacity: future allocation 111 W avg × 60 min → **≥ 14 Ah
  (≈ 155 Wh), $100–140 class** (was ≥ 8 Ah). C-rate stays mild (≈ 3.4C).
  In v0.1 the same pack simply runs ~90+ min at expected load.
- Mass cost ≈ 0.6–0.8 kg — absorbed by the 20 kg design ceiling already used in
  the torque envelope; no drive re-sizing is triggered.
- The build validator now checks BMS and fuse against the arms-inclusive peak.

## Amendment 2026-08-01 — chemistry changed to 4S LiFePO4

**3S Li-ion is replaced by 4S LiFePO4 (10.0 V – 12.8 V nom – 14.6 V).** The
architecture in this ADR is otherwise unchanged: driver-limited current, BMS,
fused protection chain, E-stop cutting motor power. This is a sourcing and
topology correction, not a change of philosophy.

### Why — two problems found while sourcing, both fatal to the original spec

1. **The ≥50 A BMS could not be bought.** A 3S Li-ion pack with a ≥50 A
   *continuous* BMS is not a consumer product; stock "12 V" packs ship 10–30 A
   boards. Against a 46 A designed peak that is a pack which trips on the first
   carpet pivot — the exact failure this ADR's protection chain exists to avoid.
   Remaining routes were "buy a bare pack and fit your own BMS" or "build from
   cells", neither of which is a purchase.
2. **The Jetson 12 V rail could not be built.** The original shopping list
   specified a *12 V buck*, but a step-down needs input above output and a 3S
   bus is 12.6 V only at full charge, spending most of its discharge below 12 V
   and bottoming at 9.0 V. The named example part (`D24V50F12`) does not exist.
   Feeding the dev kit directly was the fallback, but its 9–20 V window against
   a 9.0 V cutoff left **zero margin** — a motor peak sagging the bus 0.5 V
   browns out the computer mid-drive.

LiFePO4 answers both at once: **10.0–14.6 V sits inside the Jetson's 9–20 V
window with margin at both ends**, so the computer feeds straight off the bus
and the converter is deleted rather than re-specified; and a **100 A BMS is the
default** in this category rather than something to hunt for.

### What the numbers do (recomputed, `buddy_calcs/power.py`)

| | 3S Li-ion | 4S LiFePO4 |
|---|---|---|
| Bus nominal | 11.1 V | **12.8 V** |
| System current | 4.95 A | **4.30 A** |
| Designed peak | 37.0 A | **36.3 A** |
| Peak incl. future arms | 47.0 A | **46.3 A** |
| Energy target | 155 Wh | 155 Wh (unchanged) |
| **Capacity target** | ≥ 14 Ah | **≥ 12.1 Ah** |
| Torque at the 8 A limit | 3.23 N·m | 3.23 N·m (unchanged) |

Higher bus voltage means **less current for the same power**, so every
protection element gains margin. **BMS ≥ 50 A and the 60 A slow-blow fuse both
stand unchanged** — checked, not assumed; `power.py::validate` passes. The
capacity requirement falls to ≥ 12.1 Ah because the energy target is unchanged
and the volts went up. Practical purchase is a **12 V 20 Ah** pack (≈ 256 Wh,
the next standard size up, 65 % over spec) — a 12 Ah pack lands at 154 Wh,
about 1 % under, so it is not the safe choice.

### Consequences

**Improves**

- The Jetson rail is now *no component at all*: fewer parts, no conversion
  losses on a 30 W load, one less thing to fail.
- Protection margins widen across the board (see table).
- LiFePO4 is the safest common chemistry near people and pets — no thermal
  runaway propagation, which is the concern that made this ADR reject raw LiPo
  in the first place.
- Roughly **$70 cheaper** overall, mostly from deleting the converter.

**Costs**

- **Mass ≈ +1.3 kg** (a 12 V 20 Ah LiFePO4 is ~2.1 kg against ~0.8 kg for an
  equal-energy 3S Li-ion). The 2026-07-14 amendment absorbed +0.6–0.8 kg into
  the 20 kg ceiling; this is larger. **The torque envelope is computed at the
  20 kg ceiling, so drive sizing is unaffected as long as the finished robot
  stays under it — but the headroom is now materially smaller, and chassis CAD
  is where that gets settled rather than assumed.**
- **Motors run above their 12 V nominal**: ~238 RPM at 12.8 V and ~271 RPM at
  14.6 V, versus 223 RPM rated. That is spare speed headroom, not a violation —
  required wheel RPM comes from the speed requirements, never from the motor's
  no-load figure. Stall *current* scales the same way (9.2 → ~11.2 A at full
  charge), which moves only the "unlimited stall" fault scenario; every
  operating case is capped by the 8 A driver limit, and torque per amp is
  voltage-independent so the pivot check does not move.
- Charger must be **LiFePO4-specific** (14.6 V absorb). A 12.6 V Li-ion charger
  will never fill the pack; a Li-ion charger set higher would be dangerous.

### What would change this decision

- Chassis CAD showing the mass budget cannot absorb +1.3 kg → revisit 3S Li-ion
  with a self-fitted 50 A BMS and a 10 A buck-boost for the Jetson.
- A 3S Li-ion pack appearing with a verified ≥50 A continuous BMS *and* a
  solution for the Jetson rail → the energy-density argument returns.
