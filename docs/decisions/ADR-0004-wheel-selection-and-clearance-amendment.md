# ADR-0004: Wheel Selection and Ground-Clearance Amendment

- Status: Proposed
- Date: 2026-07-11

## Context

The 0.06 m wheel radius used in motor sizing ([ADR-0003](ADR-0003-drive-motor-selection.md))
was a URDF placeholder — no wheel had been sourced. The selected motors (goBILDA
5203, 8 mm REX shaft) constrain the wheel interface, and goBILDA's traction
wheels top out at 96 mm diameter. Third-party ~125 mm wheels exist but lack
positive REX-shaft engagement, have unknown load ratings, and their full-width
treads *increase* pivot scrub — the load case that sized the motors.

The goBILDA Hogback 96 mm was designed for FTC skid-steer robots: its crowned
tread deliberately minimizes scrub during pivots, directly attacking Buddy's
dominant torque requirement.

## Decision

**4× goBILDA Hogback Traction Wheel (96 mm, 50A, $9.99 each)** mounted on
**4× Sonic Hub-class hubs with 8 mm REX bore** (~$76 all-in), accepting a
**ground-clearance requirement amendment from 0.05 m to 0.038 m**.

The 0.05 m figure was a round-number guess ("enough to get over changes in
surfaces"); indoor thresholds and carpet-to-marble transitions are 5–20 mm, so
38 mm retains ~2× margin on the actual need. No 96 mm wheel can deliver 50 mm
(clearance is capped by wheel radius = 48 mm even with the axle at the lowest
chassis point).

## Consequences

At r = 0.048 m the torque envelope improves everywhere it was tight
(derivations in [`drive_torque_and_pivot_scrub.md`](../analysis/drive_torque_and_pivot_scrub.md)):

| Quantity | @ 120 mm placeholder | @ 96 mm Hogback |
|---|---|---|
| Design-case torque (5° + accel, SF 2) | 1.47 N·m | 1.18 N·m |
| Pivot @ μ = 0.8 vs 3.73 N·m stall | 3.82 (marginal) | 3.05 (22% margin) |
| Wheel RPM @ 0.75 m/s | 119 | 149 (motor: 223 no-load) |
| Loaded top speed (est.) | ~1.1 m/s | ~0.9 m/s |

- The crowned tread reduces effective scrub beyond what the μ-model captures —
  the model conservatively ignores it.
- URDF updated: `wheel_radius` 0.048, `base_center_z` 0.088 (keeps axle height =
  wheel radius so sim wheels touch ground), `wheel_mass` 0.2 kg nominal.
- Requirements yaml: `ground_clearance_m` 0.05 → 0.038 with amendment note.
- Loaded top speed ~0.9 m/s still exceeds every v0.1 speed requirement; the
  future 2.5 m/s goal now needs 497 wheel RPM (13.7:1 cartridge gives 435 —
  close but short; re-evaluate wheel diameter *with* that future re-gear).

## Open items before this moves to Accepted

- Verify exact hub SKU (8 mm REX bore, bolt pattern matching Hogback's M4
  holes) and wheel width/mass at purchase.
- Wheel load rating is unpublished; 20 kg / 4 = 5 kg per wheel — sanity-check
  against FTC usage (~15 kg robots) and inspect for deformation under load.
