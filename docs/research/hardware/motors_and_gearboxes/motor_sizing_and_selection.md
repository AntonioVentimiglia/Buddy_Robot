# Motor Sizing and Selection — Buddy v0.1 Drive Base

**Last updated:** 2026-07-11
**Status:** sizing complete, candidates shortlisted, purchase decision pending
**Tool:** `robot_ws/tools/torque_sweep.py` (straight-line cases) + pivot math below
**Derivations:** full first-principles treatment (symbol tables, substitutions,
free-body diagrams, limits of validity) in
[`docs/analysis/drive_torque_and_pivot_scrub.md`](../../../analysis/drive_torque_and_pivot_scrub.md)

## 1. Inputs (from `docs/requirements/buddy_v0_1_requirements.yaml` and `design_params.yaml`)

| Parameter | Value | Source |
|---|---|---|
| Gross design mass | 20 kg | requirements (`design_gross_mass_limit_kg`) |
| Wheel radius | 0.048 m (96 mm goBILDA Hogback, ADR-0004; was 0.06 m placeholder during initial sizing) | `design_params.yaml` |
| Driven wheels | 4 (one motor each, paired L/R channels) | clarifications #11 |
| Track / wheelbase | 0.26 m / 0.18 m | `design_params.yaml` |
| v0.1 max speed (teleop) | 0.75 m/s → **149 wheel RPM** | requirements |
| v0.1 autonomous speed | 0.25–0.50 m/s → 40–80 RPM | requirements |
| v0.1 ramp | 5° | requirements (`ramp_angle_v0_1_deg`) |
| Rolling resistance (carpet) | crr ≈ 0.05 | estimate |
| Drivetrain efficiency | 0.75 | estimate |
| Safety factor | 2.0 | convention |

## 2. Torque envelope per motor (r = 0.048 m, 4 driven; updated per ADR-0004)

| Case | Command | Torque per wheel | Nature |
|---|---|---|---|
| Flat cruise (crr 0.05) | steady state | **0.16 Nm** | continuous (thermal) |
| 5° ramp + 0.5 m/s² accel, SF 2.0 | design case | **1.18 Nm** | rated / short-duty target |
| Emergency stop 0.75→0 in 0.25 m | transient | 1.58 Nm | brief peak |
| **Pivot-in-place on carpet** (μ 0.6–0.8) | worst case | **2.29–3.05 Nm** | peak / near-stall |
| Future goal: 2.5 m/s + 20° ramp | out of scope v0.1 | 2.76 Nm @ 497 RPM | see §5 |

(Initial sizing used the 0.06 m URDF placeholder radius — those numbers were
1.47 / 2.9–3.8 Nm; the motor decision was made against the harsher placeholder
case, so the selected motor gained margin when real wheels were chosen.)

Reproduce the straight-line cases:

```bash
python3 robot_ws/tools/torque_sweep.py --mass-kg 20 --wheel-radius-m 0.048 \
  --driven-wheels 4 --speed-mps 0.75 --ramp-deg 5 --accel-mps2 0.5 \
  --crr 0.05 --efficiency 0.75 --safety-factor 2.0 --stopping-distance-m 0.25
```

Pivot-in-place (skid-steer scrub, not in the tool): resisting yaw moment
`M = 4·μ·(mg/4)·d` with contact radius `d = √(wheel_x² + wheel_y²) = 0.158 m`;
per-wheel force `F = M / (4·wheel_y)`; torque `T = F·r/η`. On carpet (μ≈0.6) this
gives **2.29 Nm per wheel** at r = 0.048 — pivot turns, not straight-line
driving, size the stall requirement for a 20 kg skid-steer robot.

### Selection targets per motor (at r = 0.048 m)

- **Loaded speed ≥ 149 RPM** (no-load ≥ ~200 RPM at 12 V)
- **Rated/continuous torque ≥ 0.6 Nm** (covers ramp+accel without SF; SF-2.0 target 1.18 Nm short-duty)
- **Stall torque ≥ 3.1 Nm (~31 kg·cm)** so carpet pivots (μ up to 0.8) don't stall the drivetrain
- Quadrature encoder included; 12 V class; mounting face + shaft that fit a 0.30 m footprint

## 3. Candidate shortlist (specs verified 2026-07-11)

| Candidate | Price ×4 | No-load speed | Stall torque | Rated torque | Encoder | Driver needed | Verdict |
|---|---|---|---|---|---|---|---|
| **goBILDA 5203 Yellow Jacket 26.9:1** ([product](https://www.gobilda.com/5203-series-yellow-jacket-planetary-gear-motor-26-9-1-ratio-24mm-length-8mm-rex-shaft-223-rpm-3-3-5v-encoder/)) | $220 ($54.99 ea) | 223 RPM | **3.73 Nm** (38 kg·cm), 9.2 A | not published (~1/3 stall ⇒ ~1.2 Nm) | 751.8 PPR at output | yes, 4 brushed channels | **Best fit.** Meets stall, speed, encoder targets; swappable gear cartridges (13.7:1 = 435 RPM later); FTC ecosystem mounting. |
| **Pololu 37D 70:1 w/ 64 CPR encoder** ([specs](https://www.pololu.com/product/4754/specs)) | $244 ($60.95 ea) | 150 RPM | 2.65 Nm (27 kg·cm), 5.5 A | 0.98 Nm continuous (10 kg·cm) | 4480 CPR at output | yes | Good quality, documented ratings, but stall covers pivots only up to μ ≈ 0.7 and no-load 150 RPM ≈ the loaded target — no speed margin; pricier than goBILDA. |
| **JGB37-520 12 V 178 RPM w/ Hall encoder** (e.g. [Amazon listing](https://www.amazon.com/JGB37-520-Encoder-7-960RPM-Adjustable-Forward/dp/B0GYRMRZD2)) | ~$60–80 (~$15–20 ea) | 178 RPM | listings claim 25 kg·cm class but specs are inconsistent between sellers | ~0.3–0.5 Nm | ~11 PPR × ratio | yes | **Budget fallback.** Spec variance and QC risk; likely stalls/overheats in carpet pivots at 20 kg. Acceptable only if gross mass drops to ~10 kg. |
| **Waveshare DDSM115 hub servo (RS485, integrated driver+encoder)** ([wiki](https://www.waveshare.com/wiki/DDSM115)) | ~$230–260 | 115 RPM rated | 2.0 Nm locked-rotor | 0.96 Nm | integrated | **no** (RS485 bus) | Massive electronics simplification (no drivers, no encoder wiring), but stall 2.0 Nm < 2.9 Nm pivot need and ~0.6 m/s top speed with its integrated wheel. Underpowered for 20 kg on carpet. |

## 4. Recommendation

**4× goBILDA 5203-2402-0027 (26.9:1, 223 RPM, $54.99 each).** It is the only
candidate that clears the carpet-pivot stall requirement with margin, the encoder
is high-resolution and 3.3 V-logic friendly, and the swappable gear cartridge
gives an upgrade path toward the future speed goal without changing mounts.

Consequences to carry forward:

- **Motor drivers:** 4 brushed-DC channels, ≥10 A peak each (9.2 A stall), current
  sensing strongly preferred for pivot current limiting. Research next in
  `docs/research/hardware/electronics/motor_drivers/`.
- **Drive MCU:** 4× quadrature encoders + 4× PWM pairs + current ADCs confirms the
  **STM32G474 / NUCLEO-G474RE** recommendation in
  `docs/research/hardware/electronics/microcontrollers_and_bus/stm32_drive_controller_selection.md`.
  (If the DDSM115 path were chosen instead, the MCU would shrink to an RS485
  safety bridge — one more reason motors had to be decided first.)
- **Battery:** resolved by ADR-0005 (2026-07-12): 3S Li-ion ≥ 8 Ah with ≥ 40 A
  BMS; driver current limit 8 A/motor caps the designed peak at 37 A. Full
  analysis in `docs/analysis/power_budget_and_battery.md`.
- **Budget:** $220 of the $300–600 v0.1 budget. This collides with LiDAR + RGB-D +
  battery costs — already logged in `docs/requirements/design_conflicts.md`
  (conflict #4). If the budget can't stretch, drop gross mass to ~10 kg and
  re-run this document with JGB37-520.

## 5. Explicitly out of scope for v0.1

Sizing for the future goals (2.5 m/s, 20° ramp) simultaneously requires ~497 RPM
**and** 2.76 Nm per wheel at the 96 mm wheel — still a ~140 W-class demand per
corner, incompatible with the $300–600 budget and 0.30 m footprint. v0.1 sizes
for ≤ 0.9 m/s and 5° ramps; the goBILDA cartridge swap (26.9:1 → 13.7:1,
435 RPM ≈ 2.2 m/s) gets close to the speed goal *if* mass comes down or ramps
stay shallow — re-evaluate wheel diameter together with any future re-gear.
This supersedes nothing — it implements conflict #1/#3 in `design_conflicts.md`.

## 6. Iteration loop

When any input changes (mass, wheel radius, surfaces, budget):

1. Edit the parameter in `design_params.yaml` (design choices/assumptions) or the
   requirements yaml (requirements).
2. Run `python3 tools/build.py` — regenerates the URDF params, the derivation
   doc's substituted numbers, both figures, and the sweep CSV in one pass.
3. Re-check the four selection targets in §2 against the shortlist (the numbers
   in *this* file's tables are prose — update them from the rebuilt derivation
   doc, or explore live with `marimo edit docs/analysis/drive_torque_and_pivot_scrub.py`).
4. When a purchase is made: record it in the BOM (`docs/financials/Buddy_BOM.xlsx`),
   update the ADR status, and update `PROJECT_CONTEXT.md` section 1 (hardware chosen).
