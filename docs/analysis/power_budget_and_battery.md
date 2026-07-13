---
title: Analysis — Power Budget and Battery Sizing
date: 2026-07-12
type: analysis
tags: [mechanical, electrical]
summary: Why 4x 9.2 A stall is a designed ceiling, not a battery requirement — peak scenarios, protection chain, and capacity sizing with reserves for unchosen hardware.
figures: [assets/figures/power_budget.svg]
---
<!-- GENERATED from power_budget_and_battery.py by tools/build.py — edit the notebook (marimo edit docs/analysis/power_budget_and_battery.py) or design_params.yaml, then rebuild. -->

# Power Budget and Battery Sizing

Methods document for the power architecture ([ADR-0005](../decisions/ADR-0005-power-architecture-3s-liion.md)).
The driving concern: four drive motors with 9.2 A stall each *looks* like an
impossible worst case. This document shows why it is not — stall current is a
**fault condition converted into a designed ceiling** by the motor drivers'
current limit — and derives the battery that covers both the peaks and the
60-minute runtime requirement. Every number is computed from
`design_params.yaml` + the requirements yaml.

## 1. Notation and allocations

| Symbol / item | Meaning | Current value | Units |
|---|---|---|---|
| $V$ | bus voltage, 3S Li-ion nominal | 11.1 (range 9–12.6) | V |
| $I_{stall}$ | motor stall current | 9.2 | A |
| $T_{stall}$ | motor stall torque | 3.73 | N·m |
| $I_0$ | motor no-load current (estimate) | 0.25 | A |
| $I_{lim}$ | driver per-motor current limit | 8 | A |
| Jetson Orin Nano | 25 W super mode + carrier overhead | 30 | W |
| RGB-D camera | **reserve** — selection constraint | 5 | W |
| 2D LiDAR | **reserve** — selection constraint | 5 | W |
| MCU + driver logic | NUCLEO-G474 + encoders + E-stop | 5 | W |
| Expansion | unallocated headroom | 10 | W |

The camera and LiDAR are **not chosen yet** — their rows are *reserved
allocations*, upper bounds that become hard selection constraints. A candidate
sensor exceeding its reserve triggers a budget re-run before purchase. Total
system (non-drive) allocation: **55 W = 5.0 A** at
11.1 V.

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

Substituting the chosen limit $I_{lim} = 8$ A:

$$T(8) = 3.73\,\frac{8 - 0.25}{9.2 - 0.25} = 3.23\ \text{N}\cdot\text{m}$$

which exceeds the worst-case pivot demand (3.05 N·m at
$\mu = 0.8$, from the [drive derivation](drive_torque_and_pivot_scrub.md)) —
so even thick-carpet pivots complete under the limit. This inequality is
enforced automatically: `tools/build.py` fails if a parameter change breaks it.

## 3. Peak-current scenarios (bus amps at 11.1 V)

| Scenario | Drive (A) | Total incl. system (A) |
|---|---|---|
    | flat cruise | 2.5 | 7.5 |
    | ramp + accel (design) | 12.3 | 17.3 |
    | pivot breakaway (mu=0.8) | 30.3 | 35.3 |
    | all-motor stall, driver-limited | 32.0 | 37.0 |
    | all-motor stall, UNLIMITED (fault) | 36.8 | 41.8 |

The **designed peak is 37.0 A** (all four drivers
simultaneously at their limit — already a pathological command). The
unlimited-stall row exists only to size the fault protection; it is not an
operating point.

![Power budget](../../assets/figures/power_budget.svg)

*Left: peak bus current by scenario against the protection chain. Right:
average-power stack for the two mission models, with the resulting battery
capacity. Regenerate: `python3 tools/figures/plot_power_budget.py`.*

## 4. Protection chain

Ordered so each layer only sees what the previous one failed to stop:
driver limits (8 A/motor) → BMS overcurrent
(≥ 40 A continuous, above the 37.0 A designed
peak) → main fuse (50 A slow-blow, below wiring ampacity — wire the
bus for ≥ 50 A: 10 AWG) → E-stop interrupts motor power upstream of the
drivers per REQ_SAFE.

## 5. Mission energy model

Drive power at cruise (0.5 m/s,
flat carpet) from the drive derivation's torque, through the electrical
efficiency of motor + driver (0.6):

$$P_{drive,cruise} = \frac{4\,T_{cruise}\,\omega}{\eta_{elec}} = 10.9\ \text{W}$$

scaled by the duty model (moving 70% of the
mission, maneuver factor 1.5×):
$P_{drive,avg} = 11.4$ W. Two mission totals:

- **Expected**: Jetson at its typical 20 W +
  sensor/MCU loads + drive → **46.4 W**
- **Allocation** (everything at its full reserve simultaneously):
  **66.4 W** — the conservative bound the battery must
  honor to *guarantee* the runtime requirement.

## 6. Battery capacity

For runtime $t = 60$ min, usable fraction
0.8 (Li-ion depth-of-discharge for cycle life) and
conversion efficiency 0.9:

$$E = \frac{P_{avg}\, t}{f_{usable}\ \eta_{conv}}$$

| Mission model | Energy | Capacity @ 11.1 V |
|---|---|---|
| Expected | 65 Wh | 5.8 Ah |
| Allocation (guarantee) | 92 Wh | 8.3 Ah |

**Target: 3S Li-ion, ≥ 8 Ah (≈ 92 Wh),
BMS ≥ 40 A continuous.** E.g. a 3S3P–3S4P pack of high-drain
21700 cells, or an equivalent prebuilt pack — $60–100 class, not exotic. The
C-rate demand is mild: 37.0 A peak on ≥ 8 Ah
is ≈ 4.4C.

## 7. Limits of validity

1. **$I_0$ is an estimate** — measure no-load current on the first purchased
   motor; it shifts the torque-at-limit inequality in §2.
2. **Reserves are allocations, not physics.** The expected-vs-allocation gap
   (46 vs 66 W) is the price of
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
