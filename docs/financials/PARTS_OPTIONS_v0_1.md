# Buddy v0.1 — Remaining Parts: Options and Alternatives

**Compiled:** 2026-08-01 · **Status:** research, nothing ordered
**Scope:** every line still unbought — power, protection, wiring, sensors, and the
3D printer. Supersedes the "Power" and "Sensors" sections of
[`SHOPPING_LIST_v0_1.md`](SHOPPING_LIST_v0_1.md), which lists specs but not
sourced candidates.

> **Prices and stock are as searched on 2026-08-01 and must be verified at
> checkout.** Where a specific product could not be confirmed, this document
> gives a search link and the exact spec to match rather than inventing a part
> number. Nothing here is an order.

**Constraints these parts must satisfy** (from the ADRs, not negotiable without
amending them):

| Constraint | Value | Source |
|---|---|---|
| Bus | 3S Li-ion, 12.6 V full → 11.1 V nom → 9.0 V cutoff | ADR-0005 |
| Capacity | ≥ 14 Ah (~155 Wh) | ADR-0005 amendment (sized for future arms) |
| BMS | ≥ 50 A continuous | ADR-0005 amendment |
| Designed peak | 47 A incl. arm branch | `power.py::validate` |
| Main fuse | 60 A slow-blow | ADR-0005 amendment |
| Arm branch fuse | 15 A | ADR-0009 — now the *primary* limiter |
| Bus wiring | 8 AWG (or 2× 10 AWG) | must exceed the 60 A fuse |
| LiDAR / camera | ≤ 5 W each | ADR-0005 reserves, build-enforced |
| E-stop | must interrupt **motor power**, not just logic | REQ_SAFE_001 |

---

## ⚠ Two findings to settle before ordering anything

### Finding 1 — the "12 V buck" for the Jetson cannot work as specified

`SHOPPING_LIST_v0_1.md` calls for a *"12 V regulated buck ≥ 5 A for Jetson
(e.g. Pololu D24V50F12-class)"*. Two problems:

1. **A buck cannot produce 12 V from this bus.** A step-down converter needs
   input above output. The 3S bus is 12.6 V only at full charge and spends
   almost its whole discharge below 12 V, bottoming at 9.0 V. A 12 V buck would
   drop out almost immediately.
2. **`D24V50F12` does not appear to exist.** Pololu's fixed 12 V step-downs are
   low current (`D24V5F12`, 500 mA); the 5 A `D24V50F5` is a **5 V** part.

**Three ways out, and it is a real decision:**

| Option | How | Verdict |
|---|---|---|
| **A. Buck-boost to 12 V** | converter that steps up *or* down as the pack sags | Correct topology. Pololu's 12 V buck-boost is only **2.5 A** — and the Jetson's own allocation is 30 W = 2.5 A at 12 V, i.e. **zero margin**. Needs a ~10 A class module instead. |
| **B. Feed the Jetson straight off the bus** | no converter at all | The dev-kit input range is **9–20 V** and the bus is 9.0–12.6 V, so it *nominally* fits — but with **0 V of margin at the bottom**. A 37 A motor peak sagging the bus 0.5 V browns out the computer. Would need bulk capacitance and a raised cutoff (~10.5 V), costing usable capacity. |
| **C. Change chemistry to 12 V LiFePO4** | 4S LiFePO4: 14.6 V full → 12.8 V nom → 10.0 V cutoff | Sits **comfortably inside 9–20 V**, so option B becomes safe with real margin and the converter disappears. Requires amending ADR-0005. See Finding 2 — the two are connected. |

### Finding 2 — a 3S Li-ion pack with a ≥50 A BMS is genuinely hard to buy

Off-the-shelf "12 V" Li-ion packs almost universally ship **10–30 A** BMS
boards. Buddy's designed peak is **47 A**. A pack whose BMS trips at 30 A will
shut the robot down on its first carpet pivot — which is exactly the failure
`SHOPPING_LIST_v0_1.md` already warns about ("most cheap 12 V packs are 10–15 A
and will trip on pivots").

Searching for a ready-made 3S ≥14 Ah pack with a ≥50 A BMS returned **no
credible consumer product**. The realistic routes:

| Route | Cost | Effort / risk |
|---|---|---|
| Bare 3S pack + **separate 50 A BMS** | ~$90 pack + ~$15 BMS | Needs wiring the BMS yourself; you have the soldering kit. Most control over spec. |
| **Build from 18650/21700 cells** | ~$70–110 | Needs a spot welder you don't own. Out of scope. |
| **12 V LiFePO4 with 100 A BMS** | ~$60–130 | Trivially available, BMS massively over-spec, safest chemistry. **Costs mass** and needs an ADR-0005 amendment. |

**Why LiFePO4 deserves a real look, despite ADR-0005 choosing Li-ion for energy density:**

- **Solves Finding 1 for free.** 10.0–14.6 V sits inside the Jetson's 9–20 V with
  margin at both ends. No converter, no dropout, no brownout risk.
- **Solves the BMS problem.** 100 A BMS is the *default* in this category, not a
  hunt.
- **Lowers bus current.** Same power at 12.8 V instead of 11.1 V: the 47 A
  designed peak becomes ≈ **41 A**, easing BMS, fuse and wiring margins.
- **Safest chemistry near people and pets** — no thermal-runaway propagation of
  the kind that made ADR-0005 reject raw LiPo.

**What it costs:**

- **Mass: roughly +1.3 kg** (a 12 V 20 Ah LiFePO4 is ~2.1 kg vs ~0.8 kg for a
  3S 14 Ah Li-ion of equal energy). The 07-14 amendment absorbed +0.6–0.8 kg
  into the 20 kg ceiling; **+1.3 kg needs re-checking, not assuming.**
- **Motors run above nominal at full charge.** The goBILDA 5203 is a 12 V motor
  rated 223 RPM. At 14.6 V it would spin ~22% faster (≈272 RPM) with ~22% higher
  stall current (9.2 → 11.2 A). The firmware's 8 A limit and velocity clamp both
  still hold, but the sizing analysis assumed 12 V and would want a re-run.
  (For contrast, 3S Li-ion at 11.1 V runs the motors *below* nominal, ~206 RPM —
  still well clear of the ≥120 RPM loaded requirement.)
- Driver headroom is fine either way: the VNH5019 operates to 24 V.

**Recommendation: decide Finding 2 first — it determines Finding 1.**

---

## A. Fabrication (capital tool, outside the robot BOM — ADR-0008)

### A1. 3D printer — **decided: QIDI Plus 4**

| Option | Build volume | Chamber | Hotend / bed | Price | Link |
|---|---|---|---|---|---|
| **QIDI Plus 4** ✅ | 305×305×280 | **active 65 °C**, 400 W | 370 °C / 120 °C | ~$800 | [qidi3d.com](https://us.qidi3d.com/products/plus4-3d-printer) |
| QIDI Q1 Pro | 245³ | active 60 °C | 350 °C / 120 °C | ~$599 | [Amazon](https://www.amazon.com/QIDI-High-Speed-Leveling-Printers-Detection/dp/B0CSDB9QTF) |
| Elegoo Centauri Carbon | 256³ | passive | 350 °C hardened | ~$299 | — |
| Bambu Lab P1S | 256³ | passive | 300 °C | ~$699 | — |
| Prusa CORE One | 250×220×270 | active 55 °C | ~290 °C | ~$1,099+ | — |

Rationale and rejections are in
[ADR-0008](../decisions/ADR-0008-in-house-3d-printing-and-printer-selection.md).
**Verify at checkout:** current price, included spares, warranty terms, and that
the bundle is the printer alone (not a Combo you don't need).
**On arrival:** stay on firmware 5.0 (5.1 has reported Plus 4 issues).

### A2. Filament and consumables

| Item | Spec that matters | Est. | Note |
|---|---|---|---|
| **ASA**, 2 spools | chassis, structural | ~$50 | warp-controlled by the heated chamber; this is the reason for the Plus 4 |
| **PA-CF (nylon-carbon)**, 1 spool | motor mounts, load paths | ~$40 | Tg ~180 °C vs PETG ~80 °C — the whole service-temperature argument |
| **PETG**, 1 spool | trays, sensor mounts | ~$20 | non-structural only |
| PLA, 1 spool | fit checks | ~$20 | **never on a load path** |
| **Heat-set threaded inserts**, M3/M4 assortment + soldering tip | fastener bosses | ~$25 | [search](https://www.amazon.com/s?k=heat+set+threaded+inserts+M3+M4+assortment+soldering+tip) — printed threads are not load-bearing |
| Hardened nozzle | — | $0 | **already stock** on the Plus 4; needed for CF-filled |

**Subtotal, fabrication: ~$955**

---

## B. Battery and charging

### B1. Path 1 — stay 3S Li-ion (honours ADR-0005 as written)

| Item | Spec to match | Est. | Link |
|---|---|---|---|
| 3S Li-ion pack, ≥14 Ah, **XT60** | verify BMS continuous rating **explicitly**; assume 30 A unless stated | ~$90–140 | [search](https://www.amazon.com/s?k=3S+12V+lithium+ion+battery+pack+15Ah+XT60) |
| **Separate 3S 50–60 A BMS** (if pack BMS is under-spec) | 50 A continuous, balance leads | ~$12–20 | [Amazon 3S 50 A](https://www.amazon.com/Lithium-Protection-Integrated-Circuits-Equalization/dp/B08GBZC8JW) · [LLT 50 A](https://www.lithiumbatterypcb.com/product/3s-4s-6s-li-ion-bms-with-50a-constant-charge-and-discharge-current-for-electric-tool-electric-vacuum-cleanerelectric-drill12-6v-16-8v-25-2v-lithium-battery-pcb/) |
| 12.6 V Li-ion charger, 2–3 A | matched to pack **and** BMS | ~$20 | [search](https://www.amazon.com/s?k=12.6V+3A+lithium+ion+battery+charger+3S) |

⚠ **The single most common failure mode here is a mislabelled BMS.** Sellers
quote *peak* current. If the listing does not state **continuous** amps, treat it
as unproven and plan on fitting your own.

### B2. Path 2 — 12 V LiFePO4 (needs an ADR-0005 amendment)

| Option | Capacity | BMS | Mass | Price | Link |
|---|---|---|---|---|---|
| **WattCycle 12 V 20 Ah** | 256 Wh | ~100 A | ~2.1 kg | ~$60–80 | [wattcycle.com](https://www.wattcycle.com/products/wattcycle-12v-20ah-lifepo4-battery) |
| Battle Born Base 12 V 20 Ah | 256 Wh | integrated | ~2.5 kg | ~$180 | [battlebornbatteries.com](https://battlebornbatteries.com/product/base-series-20ah-12v-lifepo4-deep-cycle-battery/) |
| Generic 12 V 20 Ah, 100 A BMS | 256 Wh | 100 A | ~2.1 kg | ~$60–90 | [search](https://www.amazon.com/s?k=12V+20Ah+LiFePO4+battery+100A+BMS) |

Charger must be **LiFePO4-specific** (14.6 V absorb, *not* a 12.6 V Li-ion
charger): [search](https://www.amazon.com/s?k=14.6V+LiFePO4+battery+charger+4S+5A) · ~$25

> Capacity note: 20 Ah at 12.8 V is 256 Wh against a 155 Wh requirement — 65%
> more than needed. A 12 V **12 Ah** LiFePO4 (~154 Wh, ~1.4 kg) meets spec
> exactly and saves ~0.7 kg. Worth pricing before defaulting to 20 Ah.

---

## C. Power conversion

### C1. Jetson rail — **depends entirely on Finding 1**

| Option | Part | Spec | Price | Link |
|---|---|---|---|---|
| **Buck-boost, high current** | Cllena 8–40 V → 12 V | **10 A**, 120 W, sealed, 95% | ~$25 | [Amazon](https://www.amazon.com/Cllena-Automatic-Converter-Regulator-Waterproof/dp/B08KZPXK63) |
| Buck-boost, name brand | Pololu **S13V25F12** | 12 V, **2.5 A only**, 2.8–22 V in | $18.95 | [Pololu family](https://www.pololu.com/category/288/s13vxfx-step-up-step-down-voltage-regulators) |
| Boost only | Pololu U3V50F12 | 12 V step-**up** | ~$25 | [Pololu 2568](https://www.pololu.com/product/2568) — wrong when the pack is above 12 V |
| **None** | direct from bus | only sane with LiFePO4 | $0 | — |

**Verdict:** if you stay 3S Li-ion, buy the **10 A buck-boost** — the Pololu part
is under-sized for a 30 W allocation. If you move to LiFePO4, buy nothing here.

### C2. 5 V logic / sensor rail

| Option | Spec | Price | Link |
|---|---|---|---|
| **Pololu D24V50F5** ✅ | 5 V **5 A**, in to 38 V, 85–95% | ~$25 | [Pololu 2851](https://www.pololu.com/product/2851) |
| Generic 5 V 5 A buck | same, unbranded | ~$10 | [search](https://www.amazon.com/s?k=5V+5A+DC+DC+buck+converter+module) |

A true buck works fine here — output is far below the bus under all conditions.
Pololu is worth the premium on a rail feeding the LiDAR and logic.

> Per the 07-28 KiCAD work: the **LD19 draws from a Jetson USB port**, not this
> rail, and the **BNO086 sits on the Jetson's 3.3 V**, not the Nucleo's. This
> rail is lighter loaded than the original budget implied.

---

## D. Protection and safety

| Item | Spec that matters | Est. | Link |
|---|---|---|---|
| **60 A slow-blow fuse + holder** (MIDI/AMI or ANL) | slow-blow is required — motor inrush will nuisance-trip a fast fuse | ~$12–18 | [search](https://www.amazon.com/s?k=ANL+fuse+holder+60A+slow+blow+marine) |
| **15 A arm-branch fuse + holder** | ADR-0009 made this the arm's **primary** current limiter | ~$8 | [search](https://www.amazon.com/s?k=inline+blade+fuse+holder+15A+12AWG) |
| **E-stop mushroom, latching, NC** | must be **NC** and latching (twist-to-release) | ~$10 | [uxcell NC latching](https://www.amazon.com/Latching-Mushroom-Emergency-Button-Switch/dp/B00N429U1G) · [22 mm NO+NC](https://www.amazon.com/uxcell-Mushroom-Emergency-Button-Switch/dp/B00548585A) |
| **Motor-power contactor / relay, ≥40 A, 12 V DC coil** | must switch **DC** at ≥40 A — an AC-only relay will weld shut | ~$15–30 | [search](https://www.amazon.com/s?k=12V+DC+contactor+relay+80A+continuous+duty) |
| Logic-rail inline fuse, 3–5 A | protects the 5 V branch | ~$6 | with the above |

⚠ **The E-stop button alone does not satisfy REQ_SAFE_001.** The button is rated
for a few amps; it must switch the **coil** of a contactor that carries motor
current. Buying only the mushroom head and wiring it in series with the motor
bus will destroy the switch and fail unsafe. Buy both.

⚠ **DC rating, not AC.** Most cheap "40 A" relays are AC-rated. DC arcs do not
self-extinguish at a zero crossing; an AC-rated contact can weld closed on a
DC motor bus — the exact failure an E-stop must not have. Look for
"continuous duty" **DC** contactors.

---

## E. Wiring and connectors

| Item | Spec | Est. | Link |
|---|---|---|---|
| **8 AWG silicone wire**, ~2 m red + 2 m black | ampacity must exceed the 60 A fuse | ~$20 | [search](https://www.amazon.com/s?k=8+AWG+silicone+wire+red+black) |
| 10 AWG silicone, ~2 m each | branch runs | ~$12 | same vendors |
| 16 AWG silicone, ~2 m each | motor ↔ driver at the 8 A limit | ~$10 | already partly covered in the harness order |
| **XT60 pairs** ×4 | pack, main, spares | ~$10 | [search](https://www.amazon.com/s?k=XT60+connector+pairs+male+female) |
| Ring terminals for 8 AWG, heat shrink, spiral wrap | fuse holder + contactor lugs | ~$15 | — |
| **Crimper for 8 AWG lugs** | soldered high-current lugs are a fire risk | ~$25 | [search](https://www.amazon.com/s?k=hydraulic+lug+crimper+8+AWG+battery+cable) — skip only if you already own one |

**Subtotal, wiring: ~$70–95**

---

## F. Sensors (ADR-0007 Phase A)

### F1. 2D LiDAR — LD19 / D300

| Vendor | Note | Price | Link |
|---|---|---|---|
| **youyeetoo FHL-LD19 (Amazon)** | fastest shipping, includes USB adapter | ~$75–100 | [Amazon](https://www.amazon.com/youyeetoo-D300-Resistant-Raspberry-Tutorial/dp/B0B1QCV4XR) |
| Hiwonder LD19 D300 | vendor direct | ~$80 | [hiwonder.com](https://www.hiwonder.com/products/ld19-d300-lidar) |
| ozrobotics D300 kit | US distributor | ~$90 | [ozrobotics](https://ozrobotics.com/shop/ld19-d300-lidar-developer-kit-360-dtof-laser-scanner-support-ros1-ros2-raspberry-pi-jetson-nano/) |
| AliExpress D300 | cheapest, slow shipping | ~$99 | [AliExpress](https://www.aliexpress.com/item/1005003012681021.html) |
| **D500 (upgrade)** | supersedes D300, same size/mount | ~$110–130 | [RobotShop](https://www.robotshop.com/products/hiwonder-ld19-d500-lidar-developer-kit-360-dtof-laser-scanner-supports-ros1-2-raspberry-pi-jetson-nano) |

**Worth a decision:** the **D500 replaces the D300** with better performance in
the same footprint. ADR-0007 selected the LD19/D300 on 0.9 W and 12 m ToF; if the
D500 holds the ≤5 W reserve it is a drop-in improvement for ~$30. **Verify its
power draw before substituting** — the reserve is a build-enforced constraint,
not a guideline.

### F2. IMU — BNO085 / BNO086

| Option | Note | Price | Link |
|---|---|---|---|
| **Adafruit BNO085** ✅ | STEMMA QT, best-documented, mature driver | ~$25 | [adafruit.com/product/4754](https://www.adafruit.com/product/4754) |
| SparkFun BNO086 (Qwiic) | newer part, same fusion core | ~$30 | [Amazon](https://www.amazon.com/SparkFun-IMU-Breakout-Accelerometer-Magnetometer/dp/B0CG5XXQ5Y) |
| Adafruit BNO055 | older, easier, weaker fusion | ~$30 | [adafruit.com/product/4646](https://www.adafruit.com/product/4646) |

Connects to the **Jetson 40-pin I²C** on `+3V3_JETSON` — a different rail from
the encoders, per the 07-28 wiring work.

### F3. Deferred (do not buy yet)

**OAK-D Lite RGB-D**, ~$140 — ADR-0007 defers it to the perception phase.
Nothing in Phases 5–7 needs it.

---

## G. Budget rollup

Remaining of the $2,000 programme budget: **$826.15**
(`design_conflicts.md` #4).

| Group | Path 1 (3S Li-ion) | Path 2 (LiFePO4) |
|---|---|---|
| Battery + BMS + charger | ~$150 | ~$105 |
| Jetson rail | ~$25 (10 A buck-boost) | **$0** (direct) |
| 5 V rail | ~$25 | ~$25 |
| Protection + E-stop + contactor | ~$60 | ~$60 |
| Wiring + connectors + crimper | ~$85 | ~$85 |
| LD19 + BNO086 | ~$110 | ~$110 |
| **v0.1 subtotal** | **~$455** | **~$385** |
| Remaining after v0.1 | ~$371 | ~$441 |
| *Still owed from the pot:* OAK-D (~$140) + arm servos (~$240–420) | **over by ~$10–190** | **over by ~$0–120** |
| **Fabrication (capital, outside the pot)** | ~$955 | ~$955 |

**Reading:** v0.1 closes comfortably on either path. The programme budget is
tight at the far end, and **LiFePO4 saves roughly $70** mostly by deleting the
Jetson converter. Neither path changes the printer decision.

---

## H. Decisions needed from you

1. **Battery chemistry — 3S Li-ion or 12 V LiFePO4?** Everything else in the
   power chain follows. LiFePO4 is cheaper, safer, easier to source at the
   required current, and removes the converter; it costs ~+1.3 kg and needs an
   ADR-0005 amendment plus a re-run of the mass budget and the motor RPM
   assumption.
2. **If staying Li-ion:** buy a pack with a proven ≥50 A BMS, or a bare pack plus
   your own BMS? The second is more certain and needs soldering.
3. **LD19 D300 or the newer D500?** Only if D500 power draw is confirmed ≤5 W.
4. **Do you already own an 8 AWG lug crimper?** If not it is ~$25 and not
   optional — soldered high-current lugs are a fire risk.
5. **LiFePO4 capacity: 12 Ah (meets spec, ~1.4 kg) or 20 Ah (65% over, ~2.1 kg)?**

Answer 1 and I will amend the ADRs, re-run `power.py::validate`, update the
shopping list, and cut this down to a single ordered list.
