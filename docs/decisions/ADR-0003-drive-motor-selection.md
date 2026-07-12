# ADR-0003: Drive Motor Selection

- Status: Proposed
- Date: 2026-07-11

## Context

Buddy v0.1 is a ~20 kg indoor four-wheel skid-steer base (one motor per wheel, see
[ADR-0002](ADR-0002-four-wheel-differential-drive.md)) on carpet and marble, with a
0.12 m wheel diameter, ≤1.0 m/s v0.1 speed, and a 5° ramp requirement. Motors must
be chosen before drivers, drive MCU, and the power budget can be finalized.

Full sizing is in
[`docs/research/hardware/motors_and_gearboxes/motor_sizing_and_selection.md`](../research/hardware/motors_and_gearboxes/motor_sizing_and_selection.md).
Key finding: for a 20 kg skid-steer robot, **turning in place on carpet sets the
stall requirement** (2.9–3.8 Nm per wheel at μ = 0.6–0.8), which is higher than any
straight-line driving or braking case. Per-motor targets: ≥120 RPM loaded, ≥3 Nm
stall, ≥0.75 Nm continuous, integrated quadrature encoder, 12 V class.

Four candidates were compared: goBILDA 5203 (26.9:1), Pololu 37D (70:1), JGB37-520,
and Waveshare DDSM115 hub servos.

## Proposed decision

Use **4× goBILDA 5203 Yellow Jacket planetary gearmotors, 26.9:1 (223 RPM, 3.73 Nm
stall, 751.8 PPR output encoder, $54.99 each)**.

It is the only candidate that clears the carpet-pivot stall requirement with margin
while also meeting the speed and encoder targets. The Pololu 37D's 2.65 Nm stall is
below the pivot requirement; the JGB37-520 has inconsistent vendor specs and QC
risk; the DDSM115's 2.0 Nm stall is underpowered for 20 kg on carpet.

## Consequences

- **Cost:** $220 of the $300–600 v0.1 budget — collides with LiDAR + RGB-D +
  battery (design conflict #4). Mitigation if budget can't stretch: cut gross mass
  toward ~10 kg and re-run sizing with the JGB37-520.
- **Motor drivers:** need 4 brushed-DC channels, ≥10 A peak each (9.2 A stall), with
  per-channel current sensing for pivot current limiting. Next research task.
- **Drive MCU:** 4× quadrature encoders + 4× PWM pairs + current ADCs confirms the
  STM32G474 / NUCLEO-G474RE pre-selection.
- **Power:** 12 V rail; worst-case pivot stall draw ≈ 4 × 9.2 A, so driver current
  limiting is mandatory and the drive rail should be budgeted at ~10 A continuous.
- **Future speed path:** the 5203 gearbox cartridge can be swapped to 13.7:1
  (435 RPM) later without changing motor mounts, addressing the 2.5 m/s future goal
  if mass stays low or ramps stay shallow.
- **Mounting/CAD:** goBILDA uses a 32 mm-pitch pattern and 8 mm REX output shaft;
  chassis mounting and wheel-coupling must be designed to that ecosystem.

## Open items before this moves to Accepted

- Confirm final wheel/hub coupling to the 8 mm REX shaft.
- Confirm purchase and update `docs/financials/Buddy_BOM.xlsx`.
