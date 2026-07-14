# Buddy v0.1 Shopping List — TEMPORARY

> **WIP: temporary purchasing checklist.** Review each line, buy, then: record
> purchases in `Buddy_BOM.xlsx` (commit after every BOM edit), flip the matching
> ADR to Accepted, and delete this file. Prices as researched 2026-07-11/12 —
> verify at checkout.

## Drivetrain (ADR-0003, ADR-0004)

| ✔ | Item | Qty | Unit | Ext. | Link / note |
|---|---|---|---|---|---|
| ☐ | goBILDA 5203 Yellow Jacket 26.9:1, 223 RPM, 8 mm REX (5203-2402-0027) | 4 | $54.99 | $219.96 | [product](https://www.gobilda.com/5203-series-yellow-jacket-planetary-gear-motor-26-9-1-ratio-24mm-length-8mm-rex-shaft-223-rpm-3-3-5v-encoder/) |
| ☐ | goBILDA Hogback Traction Wheel 96 mm, 50A (3626-0014-0096) | 4 | $9.99 | $39.96 | [product](https://www.gobilda.com/hogback-traction-wheel-96mm-diameter-50a-durometer/) |
| ☐ | goBILDA hub, 8 mm REX bore, pattern matching Hogback M4 holes (Sonic Hub class, e.g. 1309-0016-4008) | 4 | ~$8 | ~$32 | **verify bolt-pattern fit before ordering** (ADR-0004 open item) |

## Drive electronics (ADR-0005, driver research doc)

| ✔ | Item | Qty | Unit | Ext. | Link / note |
|---|---|---|---|---|---|
| ☐ | Pololu VNH5019 motor driver carrier | 4 | $24.95 | $99.80 | [product](https://www.pololu.com/product/1451) — recommended; alternates in `driver_selection.md` |
| ☐ | NUCLEO-G474RE (drive MCU dev board) | 1 | ~$27 | ~$27 | ST/Mouser/DigiKey (STM32 selection doc) |
| ☐ | *(optional, bench phase)* Pololu Dual VNH5019 Arduino shield — stacks directly on the Nucleo for the first bench loop | 1 | $49.95 | — | [product](https://www.pololu.com/product/2507) — skip if going straight to 4 carriers |

## Power (ADR-0005)

| ✔ | Item | Qty | Unit | Ext. | Link / note |
|---|---|---|---|---|---|
| ☐ | 3S Li-ion pack, **≥ 14 Ah (≈ 155 Wh), BMS ≥ 50 A continuous** (ADR-0005 amendment: sized for future dual 6-DOF arms so the v0.1 purchase isn't wasted) | 1 | $100–140 | ~$120 | verify the BMS continuous rating explicitly — most cheap "12 V" packs are 10–15 A and will trip on pivots |
| ☐ | Li-ion charger for 3S pack (matched to pack/BMS) | 1 | ~$20 | ~$20 | |
| ☐ | 12 V regulated buck ≥ 5 A for Jetson (e.g. Pololu D24V50F12-class) | 1 | ~$30 | ~$30 | isolates compute from motor sag |
| ☐ | 5 V buck ≥ 3 A (LiDAR / logic rail) | 1 | ~$10 | ~$10 | |
| ☐ | 60 A slow-blow fuse (MIDI/ANL) + holder (ADR-0005 amendment) | 1 | ~$12 | ~$12 | |
| ☐ | XT60 connector pairs, 8 AWG silicone wire for the bus (~2 m each color) + 10 AWG branch wire | — | ~$28 | ~$28 | bus wiring ampacity must exceed the 60 A fuse |
| ☐ | E-stop mushroom switch + motor-power relay/contactor (~40 A) | 1 | ~$25 | ~$25 | REQ_SAFE_001: E-stop interrupts motor power |
| ☐ | Misc: inline fuse for logic rail, heat shrink, standoffs, JST leads | — | ~$15 | ~$15 | |

## Totals

- Drivetrain: **~$292**
- Electronics + power: **~$297** (excl. optional bench shield; battery re-sized 2026-07-14 for future dual arms, +$40, wiring +$8)
- **Grand total: ~$590** against the $300–600 budget (excl. Jetson, already owned)
  — top of band, as flagged in `design_conflicts.md` #4. Trim options: BTS7960
  drivers (−$65), smaller battery accepting <60 min allocation-guaranteed runtime
  (−$20), defer E-stop contactor to bench-supply phase (not recommended past bench).

## Already owned (not in totals)

Jetson Orin Nano Super (flashed, running), bench power supply, adapters/HDMI/storage.

## Deferred (blocked or later phase)

2D LiDAR (≤ 5 W reserve), RGB-D camera (≤ 5 W reserve), IMU, chassis material —
sensor selection is the next research task after drive electronics are proven.
