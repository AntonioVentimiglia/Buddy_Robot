# ADR-0008: In-House 3D Printing as the Fabrication Method, QIDI Plus 4 Selected

- Status: Proposed
- Date: 2026-07-31

## Context

Chassis dimensions, motor mounts, battery tray, and sensor mounts are all still
undecided (TODO Phase 2), and no fabrication method had been chosen. The
alternatives were goBILDA channel (matches the drivetrain hardware already
bought), laser-cut/machined aluminium, or in-house 3D printing.

Two things forced the decision now rather than at chassis CAD:

1. **The arms.** The roadmap adds two 6-DOF arms whose structure will be printed
   (ADR-0009). Fabrication method is therefore a project-level choice, not a
   chassis-level one.
2. **Lead time.** The drivetrain is in transit. Mechanical work is the critical
   path once it lands, and a printer bought at that point delays assembly by its
   own shipping time.

Budget was explicitly removed as a constraint on tool quality by the project
owner: this is a capital tool expected to serve future projects, so it is scored
on capability and service life, not on fitting the remaining v0.1 pot.

Research: [`printer_selection.md`](../research/hardware/fabrication/printer_selection.md).

## Decision

- **Fabrication method: in-house FDM printing** for chassis structure, motor
  mounts, battery tray, sensor mounts, and future arm structure.
- **Printer: QIDI Plus 4, ~$800.**
- **Material plan:** PA-CF or ASA for motor mounts and load paths, ASA for
  chassis structure, PETG for non-structural mounts, PLA for fit checks only —
  **never on a load path**.
- Purchased as a **capital tool**, tracked outside the v0.1 robot BOM
  (see the budget split in `design_conflicts.md` #4).

Selected against six requirements derived from the robot. Two were binding:

- **R1 — ≥280 mm on-axis build volume.** The chassis is 0.28 × 0.22 m with a
  0.3 × 0.3 m footprint target. The Plus 4 (305 × 305 × 280) is the only
  candidate that takes a full-size chassis part on-axis.
- **R2 — actively heated chamber ≥55 °C.** A ~280 mm flat ASA/ABS plate is the
  warp-prone geometry. Passive enclosures manage this failure mode; active
  chambers remove it. The Plus 4 holds 65 °C with a 400 W insulated chamber.

## Consequences

**What improves**

- Structural parts can be printed in ASA and PA-CF, which is what the load cases
  actually require: motor mounts see 3.73 N·m stall reaction on every carpet
  pivot, and they bolt to gearboxes running at the 8 A design limit. PLA's ~60 °C
  glass transition makes it unusable there; PA-CF's is ~180 °C.
- Mechanical iteration cost drops to filament and time, which suits a chassis
  whose dimensions are still provisional and a track width still unlocked.
- The arms become buildable at all (ADR-0009).

**What gets harder**

- **A new failure mode enters the robot: anisotropic, creep-prone structure.**
  FDM parts are weakest in layer adhesion, and the pivot load case is cyclic.
  Print orientation becomes a design parameter that must be recorded per part,
  not left to the slicer.
- Printed parts need a first-article check. The ±0.1 mm accuracy figure in the
  research doc is a *review claim about the model*, not a measurement of the
  machine that will arrive.
- **Effective heated build height is ~268 mm, not 280** — the bed occludes the
  chamber heater outlet above that and Klipper trips thermal protection. No
  current Buddy part is affected; this constrains future ones.
- Firmware must stay on 5.0 (5.1 has reported Plus 4 issues), so auto-update
  should be off.

**What must be updated**

- `PROJECT_CONTEXT.md` §1 — fabrication method and printer in the hardware list.
- `TODO/00_master_todo.md` — Phase 2 chassis items now have a fabrication method.
- `docs/requirements/design_conflicts.md` #4 — budget pots split.
- `docs/financials/Buddy_BOM.xlsx` — printer + initial filament, as a capital line.
- Chassis CAD must adopt printed-part design rules (bosses, ribs, print
  orientation on load paths, metal inserts at fastener and bearing interfaces).

## Alternatives considered

- **goBILDA channel** — matches the drivetrain ecosystem already purchased, needs
  no tool and no fab skill, and would have been the fastest path to a rolling
  base. Rejected because it does not solve the arms, it constrains geometry to
  the vendor's hole pattern, and per-part cost stays high forever.
- **Laser-cut / machined aluminium** — stiffest and lightest against the 20 kg
  ceiling. Rejected on iteration economics: every revision costs money and
  vendor turnaround, which is the wrong trade while chassis dimensions are still
  provisional and design conflict #2 (footprint vs mass) is unresolved.
- **Elegoo Centauri Carbon (~$299)** — the recommendation while a hard budget
  ceiling was in force, and it returns immediately if that ceiling comes back.
  Rejected on R2: passive chamber.
- **Bambu Lab P1S (~$699)** — best measured accuracy in the set (±0.05 mm) and
  the deepest ecosystem. Rejected on R2 (passive chamber) and R3 (300 °C hotend
  closes the door on PA-CF).
- **Prusa CORE One (~$1,099+)** — best openness, support, and expected service
  life; satisfies R2. Rejected on R1: 250 × 220 mm is the smallest build area in
  the comparison at the highest price.
- **QIDI Q1 Pro (~$599)** — materially equivalent (60 °C chamber, 350 °C hotend,
  120 °C bed) in a 245 mm envelope; the Plus 4's premium buys only on-axis
  capacity for a full-size chassis part. Rejected as a deliberate choice to keep
  monolithic chassis sections available as a design option rather than
  pre-committing to bolted subassemblies.

## What would change this decision

- First-article measurement showing the machine cannot hold ±0.15 mm on bores →
  metal inserts become mandatory everywhere rather than case-by-case.
- A printed motor mount failing in fatigue on the bench → revisit aluminium for
  the four mounts specifically, keeping printing for everything else.

## Update requirements

- [ ] Update `PROJECT_CONTEXT.md`.
- [ ] Update `TODO/00_master_todo.md` Phase 2.
- [ ] Update `design_conflicts.md` #4 and the shopping list.
- [ ] Record purchase in `Buddy_BOM.xlsx` (capital tool line), commit immediately.
- [ ] On arrival: dimensional-accuracy coupon → `assets/evidence/`.
