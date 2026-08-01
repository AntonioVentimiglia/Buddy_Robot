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

## Harness — motor cabling (NEW 2026-07-16; was missed, see `wiring_harness.md`)

Motor ships with 470 mm power leads (3.5 mm bullet, **FH-MC**) and a 4-pos
JST XH **FH-MC** encoder socket. Everything below is the **MH-FC** mating half.
Motor power goes to the **driver**, encoder goes to the **Nucleo** — never mix.

| ✔ | Item | Qty | Unit | Ext. | Link / note |
|---|---|---|---|---|---|
| ☐ | goBILDA Encoder Breakout Cable (4-Pos JST XH [MH-FC] → 4 × 1-Pos TJC8 [MH-FC], 300 mm) | 4 | $3.99 | ~$16 | [product](https://www.gobilda.com/encoder-breakout-cable-4-pos-jst-xh-mh-fc-to-4-x-1-pos-tjc8-mh-fc-300mm-length/) — **breakout**, not straight-through: our encoder pins aren't adjacent. ⚠ check whether a cable ships with the motor |
| ☐ | 3.5 mm bullet connectors, female-contact (MH-FC), set incl. heat-shrink | 8 | — | ~$12 | RC/hobby standard; motor-to-driver pigtails |
| ☐ | 16 AWG silicone wire, ~2 m red + 2 m black | — | ~$14 | ~$14 | motor↔driver runs at the 8 A design limit |
| ☐ | *(optional)* 5 mm screw terminal blocks for VNH5019 outputs | 4 | ~$1.5 | ~$6 | swap a motor without a soldering iron |
| ☐ | USB-A → micro-B cable (Nucleo ST-LINK ↔ Jetson) | 1 | ~$8 | ~$8 | ⚠ confirm the Nucleo's USB connector type on arrival |
| ☐ | *(if Nucleo mounts far from motors)* Encoder cable extension, 4-Pos JST XH, 300 mm | 0–4 | $2.99 | — | [product](https://www.gobilda.com/encoder-cable-extension-4-pos-jst-xh-300mm-length/) — decide at chassis layout |

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

## Fabrication — capital tool (NEW 2026-07-31, ADR-0008)

Tracked **outside the robot BOM**: a tool purchase scoped to serve future
projects, not a v0.1 part. See `design_conflicts.md` #4.

| ✔ | Item | Qty | Unit | Ext. | Link / note |
|---|---|---|---|---|---|
| ☐ | QIDI Plus 4 (305×305×280 mm, 65 °C active chamber, 370 °C hotend, 120 °C bed) | 1 | ~$800 | ~$800 | [product](https://us.qidi3d.com/products/plus4-3d-printer) — verify price/warranty/spares at checkout. **Keep firmware on 5.0**; 5.1 has reported Plus 4 issues |
| ☐ | ASA filament (chassis, structure) | 2 | ~$25 | ~$50 | |
| ☐ | PA-CF filament (motor mounts, load paths) | 1 | ~$40 | ~$40 | hardened nozzle is stock — no upgrade needed |
| ☐ | PETG filament (non-structural mounts) | 1 | ~$20 | ~$20 | |
| ☐ | *(assumed needed)* Heat-set threaded inserts, M3/M4 assortment + installation tip | 1 | ~$25 | ~$25 | printed fastener bosses are not load-bearing on their own |

**Fabrication subtotal: ~$935.**

## Totals

- Drivetrain: **~$292** — **ORDERED 2026-07-31** (in transit)
- Harness/cabling: **~$56** (added 2026-07-16 — previously missed) — partly ordered
- Electronics + power: **~$297** (excl. optional bench shield; battery re-sized 2026-07-14 for future dual arms, +$40, wiring +$8)
- **Robot subtotal: ~$646** (excl. Jetson, already owned)
- Fabrication capital tool: **~$935** (ADR-0008, outside the robot budget)

Budget framing revised 2026-07-31: the $300–600 band is superseded by a **$2000
programme budget** split into pots — see `design_conflicts.md` #4 for the live
tally ($1,173.85 spent, $826.15 remaining, v0.1 needs ~$355 of it). The trim
options below are retained as the fallback if the budget contracts again:
BTS7960 drivers (−$65), smaller battery accepting <60 min allocation-guaranteed
runtime (−$20), Elegoo Centauri Carbon instead of the Plus 4 (−$500, costs the
active chamber — see ADR-0008 alternatives), defer E-stop contactor to
bench-supply phase (not recommended past bench).

## Already owned (not in totals)

Jetson Orin Nano Super (flashed, running), bench power supply, adapters/HDMI/storage.

## Sensors — Phase A (add to this order; ADR-0007)

| ✔ | Item | Qty | Unit | Ext. | Link / note |
|---|---|---|---|---|---|
| ☐ | LDROBOT LD19 / D300 2D LiDAR kit | 1 | ~$70 | ~$70 | ToF 12 m, 0.9 W; `ldlidar` ROS 2 driver |
| ☐ | BNO085/BNO086 IMU breakout (Adafruit/SparkFun) | 1 | ~$25 | ~$25 | on-chip fusion; Jetson 40-pin I²C |

**Running grand total with Phase A: ~$741** — past the $300–600 band per
ADR-0007's explicit budget extension.

## Deferred (selected, buy when the phase is reached)

- **OAK-D Lite RGB-D camera (~$130–150, ADR-0007)** — buy when perception work
  starts; nothing in TODO Phases 5–7 needs it.
- Chassis material (goBILDA channel) — layout study happens with parts in hand.
