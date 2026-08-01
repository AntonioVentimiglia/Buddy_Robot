# 3D Printer Selection — In-House Fabrication for Chassis, Mounts, and Arms

**Date:** 2026-07-31 · **Status:** selected, recommendation in ADR-0008
**Why this document exists:** ADR-0008 commits Buddy's mechanical structure to
printed parts. The printer therefore stops being a convenience purchase and
becomes a **process constraint** — it sets the maximum part size, the available
material set, and therefore the achievable stiffness and service temperature of
every structural component on the robot.

Treated as a capital tool with a service life beyond Buddy, so the scoring below
weighs material capability and serviceability above purchase price.

## 1. Requirements, derived from the robot (not from printer marketing)

| # | Requirement | Value | Source |
|---|---|---|---|
| R1 | Build volume, on-axis | **≥ 280 mm** in X and Y | `design_params.yaml → chassis` is 0.28 × 0.22 m; footprint target 0.3 × 0.3 m (`TODO/01_clarifications_needed.md` Q9) |
| R2 | Chamber temperature control | **actively heated, ≥ 55 °C** | a ~280 mm flat ASA/ABS plate is the warp-prone geometry: long, flat, high aspect ratio, high shrink |
| R3 | Hotend temperature + nozzle | **≥ 300 °C, hardened** | PA-CF / PC for motor mounts; abrasive fill destroys brass |
| R4 | Bed temperature | **≥ 100 °C** | ABS/ASA/PC first-layer adhesion |
| R5 | Dimensional accuracy | **~±0.1 mm** | 8 mm REX hub bores, bearing seats, servo pockets (ADR-0009) |
| R6 | Serviceability | open firmware, obtainable spares | capital tool — must outlive this project |

### Why R2 is the binding requirement

The temptation is to score on price and build volume and treat the chamber as a
nice-to-have. That inverts the actual risk. Two independent load cases drive the
material choice, and both land outside PLA:

**Service temperature.** The drive motor mounts bolt directly to goBILDA 5203
gearboxes operating at the 8 A per-motor design limit (ADR-0005). PLA's glass
transition is ~60 °C. A mount that creeps at its clamping interface does not fail
visibly — it relaxes, the motor shifts a fraction of a degree, and the symptom
presented to the operator is **drifting odometry**, diagnosed as a firmware or
calibration problem for weeks. PETG (~80 °C) is the minimum defensible choice and
PA-CF (~180 °C) is the correct one.

**Structural load.** Each wheel can deliver 3.73 N·m stall
(`docs/analysis/drive_torque_and_pivot_scrub.md`); carpet pivot demands
2.29–3.06 N·m. That reaction passes through the mount into the chassis on every
pivot-in-place manoeuvre — a fatigue load case, not a static one, and layer
adhesion is the weak axis in FDM.

ASA/ABS/PA-CF all require an enclosure to print without warping, and at 280 mm
part length a **passive** enclosure is documented as marginal: Bambu's own wiki
prescribes preheating the bed at maximum for ~15 minutes before ABS/ASA prints in
cool ambient, and the community warp threads for the P1S/X1C are extensive.
Active chamber control removes the failure mode rather than managing it.

## 2. Candidates

| | Elegoo Centauri Carbon | Bambu Lab P1S | Prusa CORE One | QIDI Q1 Pro | **QIDI Plus 4** |
|---|---|---|---|---|---|
| Build volume (mm) | 256³ | 256³ | 250×220×270 | 245³ | **305×305×280** |
| Chamber | passive enclosure | passive enclosure | active 55 °C | active 60 °C | **active 65 °C, 400 W, insulated** |
| Hotend max | 350 °C, hardened | 300 °C | ~290 °C | 350 °C | **370 °C** |
| Bed max | — | 100 °C | 120 °C | 120 °C | 120 °C |
| Kinematics | CoreXY | CoreXY | CoreXY | CoreXY, dual-Z, 4 linear rails | CoreXY |
| Measured accuracy | — | **±0.05 mm** (20 mm cube 19.98–20.02) | — | — | ±0.1 mm typical; 0.075 mm separation clearance |
| Engineering materials | ABS, ASA, CF | ABS/ASA with mitigation | ABS/ASA/PC | ABS, PAHT, PC + CF variants | **ABS, ASA, PC, PA, PPS-CF** |
| Firmware | closed | closed / cloud-coupled | **fully open source** | Klipper, open config | Klipper, open config |
| Price | ~$299 | ~$699 | ~$1,099–1,199 | ~$599 | ~$800 |
| **R1** ≥280 on-axis | ✗ (256, diagonal only) | ✗ | ✗ (220 in Y) | ✗ | **✓** |
| **R2** active chamber | ✗ | ✗ | ✓ | ✓ | **✓** |
| **R3** ≥300 °C hardened | ✓ | ✗ | ✗ | ✓ | **✓** |
| **R4** ≥100 °C bed | ? | ✓ | ✓ | ✓ | **✓** |

## 3. Scoring against the requirements

**Eliminated on R2 (passive chamber):**

- **Elegoo Centauri Carbon (~$299)** — an enclosed CoreXY with a 350 °C hardened
  nozzle at this price is a genuine outlier, and it was the correct
  recommendation while a hard budget ceiling was in force. It is eliminated only
  because the ceiling was lifted; on a constrained rebuild it returns immediately.
- **Bambu Lab P1S (~$699)** — the best measured dimensional accuracy in the set
  (±0.05 mm) and the deepest ecosystem. Its passive chamber makes a 280 mm ASA
  plate a per-print fight, and its 300 °C hotend closes the door on PA-CF.
  The popular default is the wrong tool for this specific part mix.

**Eliminated on R1 (build volume):**

- **Prusa CORE One (~$1,099–1,199)** — best openness, support, and expected
  service life of anything here, and it satisfies R2. But at 250 × 220 mm it has
  the **smallest build area in the comparison** while costing the most: it fails
  R1 harder than the $299 machine at 3.7× the price. Would be the pick if
  long-term open-source serviceability outweighed part size.
- **QIDI Q1 Pro (~$599)** — materially equivalent to the Plus 4 (60 °C active
  chamber, 350 °C hotend, 120 °C bed, CoreXY with dual-Z on 4 linear rails) in a
  245 mm envelope. The **only** thing the Plus 4's $200 premium buys is the
  ability to print a chassis section on-axis rather than splitting it. Correct
  choice if the chassis is designed as bolted subassemblies from the start.

**Selected: QIDI Plus 4 (~$800)** — the only candidate satisfying R1 and R2
simultaneously. 305 × 305 × 280 mm takes the full-size chassis plate on-axis;
the 400 W insulated 65 °C chamber removes the warp failure mode rather than
mitigating it; 370 °C hotend and 120 °C bed open ABS, ASA, PC, PA and PPS-CF,
covering both the service-temperature and structural load cases above. Runs open
Klipper, so the configuration is inspectable and modifiable. Independent review
reports 300+ hours with minimal issues.

## 4. Known limitations of the selected machine

Bought with eyes open; these are documented, not discovered:

| Issue | Consequence for Buddy |
|---|---|
| **Chamber heater thermal protection trips on prints ≥ 268 mm tall** — the bed blocks the heater outlet at high Z, Klipper faults with "heating gain too low" | Effective *heated* Z is **~268 mm, not 280**. Tall parts must print unheated or be re-oriented. No current Buddy part approaches this. |
| CPU resource contention can stutter or halt mid-print | Long chassis prints carry a restart risk; keep the print server otherwise idle |
| Z-axis motor driver failures reported by some users (boards replaced free under warranty) | Register the machine; keep the warranty claim path known |
| Loud with chamber heater + auxiliary fan + hotend fan at 100% | Siting constraint if it shares a room with the workspace |
| Firmware 5.1 has reported Plus 4 compatibility issues | **Stay on 5.0**; do not auto-update |
| X/Y/Z linear rails require periodic lubrication | Add to a maintenance note when the machine arrives |

## 5. Material plan (initial)

| Part class | Material | Rationale |
|---|---|---|
| Motor mounts, wheel-adjacent brackets | **PA-CF** or ASA | service temperature at the gearbox interface; stiffness per mass |
| Chassis plate / structure | **ASA** | warp-controlled in the heated chamber; UV/temperature stable; tougher than PETG |
| Sensor mounts, trays, non-structural | PETG | cheap, easy, adequate |
| Prototype/fit-check iterations | PLA | fast and cheap — **fit checks only, never load paths** |

Hardened nozzle is stock on this machine, so CF-filled material needs no upgrade.

## 6. Open items

- [ ] Verify at checkout: current price, included spares, warranty terms.
- [ ] Confirm bed adhesion surface type and whether spare plates are stocked.
- [ ] On arrival: print a dimensional-accuracy coupon (20 mm cube + bore gauge)
      and record the measured deviation in `assets/evidence/` — the ±0.1 mm
      figure above is a review claim, not a measurement on *this* machine.
- [ ] Establish whether the 8 mm REX hub bore is printable to fit or needs a
      metal insert. **Assume insert until measured.**

## Sources

- [QIDI Plus 4 review — 3DPrint.com](https://3dprint.com/313877/qidi-plus-4-3d-printer-review-hotter-than-the-competition-is-it-safe/)
- [QIDI Plus4 review — Tom's Hardware](https://www.tomshardware.com/3d-printing/qidi-plus4-review)
- [QIDI Plus 4 vs Bambu P1S — 3DTechValley](https://www.3dtechvalley.com/qidi-tech-plus-4-review/)
- [Plus4 troubleshooting (chamber heater ≥268 mm, CPU contention) — qidi-community Plus4 Wiki](https://deepwiki.com/qidi-community/Plus4-Wiki/9.3-troubleshooting-guide)
- [QIDI Q1 Pro review — 3DPrint.com](https://3dprint.com/313192/qidi-q1-pro-review-a-heated-value/)
- [ABS / ASA / PC usage guide (passive-chamber preheat workaround) — Bambu Lab Wiki](https://wiki.bambulab.com/en/filament/abs_asa_pc)
- [Elegoo Centauri Carbon review — Tom's Hardware](https://www.tomshardware.com/3d-printing/elegoo-centauri-carbon-review)
- [Prusa CORE One specs & review — Slice Lab](https://slice-lab.com/en/guide-prusa-core-one)
- [Engineering filament properties (PA vs PETG glass transition)](https://3dprinting.com/filament/engineering-filaments/)
