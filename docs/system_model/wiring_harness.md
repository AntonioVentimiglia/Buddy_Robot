# Wiring Harness — Connectors, Cables, and What to Buy

**Date:** 2026-07-16 · **Status:** connector types confirmed from the motor spec
sheet + vendor pages; two items flagged "verify at purchase"
**Companion docs:** [`electrical_interfaces.md`](electrical_interfaces.md) (does it
interface?) · [`pin_map.md`](../../firmware/drive_mcu/docs/pin_map.md) (which pin?) ·
[`interconnect.svg`](../../assets/figures/interconnect.svg) (the picture, with the
pin table) · `electronics/KiCAD/drive_mcu_wiring/` + `system_wiring/` (the
schematics) · [`system_integration.md`](system_integration.md) (index to all of it)

This document exists because "the parts interface correctly" and "I have the
cables to connect them" are different claims. The first was verified earlier;
this is the second.

## 1. The rule that determines everything: two separate circuits

The single most important thing to get right when wiring a motor:

```
 POWER PATH (amps):    battery → fuse → E-stop → VNH5019 driver → MOTOR
 SIGNAL PATH (mA):     NUCLEO ←→ VNH5019 logic
                       NUCLEO ←  MOTOR ENCODER
```

**The motor's power wires never touch the Nucleo.** They carry up to 8 A (design
limit) and would destroy a microcontroller pin, which sources ~20 mA. The Nucleo
only ever sees:

- **logic signals to the driver** (PWM, direction, fault, current-sense) — the
  driver is the thing that switches the actual motor current, and
- **the encoder's four low-current wires** from the back of the motor.

So the answer to "what cables do I need to connect motor power to the Nucleo" is:
none — that connection must not exist. You need motor power cables to the
**driver**, and encoder cables to the **Nucleo**.

## 2. goBILDA's connector notation (MH-FC / FH-MC)

Connector gender is two independent things, and goBILDA labels both:

| Code | Means | Plain English |
|---|---|---|
| **FH-MC** | **F**emale **H**ousing, **M**ale **C**ontact | outer shell is the socket; the metal pins inside stick out |
| **MH-FC** | **M**ale **H**ousing, **F**emale **C**ontact | outer shell is the plug; the metal contacts inside are sockets |

They mate as opposites: **FH-MC ↔ MH-FC**. This is why a "female connector" can
still have pins in it — the housing and the contacts are described separately.
(A standard Dupont jumper that slips over a header pin is MH-FC: plug-shaped
shell, socket contact inside.)

## 3. What is on the motor (5203-2402-0027)

From the [spec sheet](../research/hardware/motors_and_gearboxes/5203-2402-0027_spec_sheet.pdf)
and the [product page](https://www.gobilda.com/5203-series-yellow-jacket-planetary-gear-motor-26-9-1-ratio-24mm-length-8mm-rex-shaft-223-rpm-3-3-5v-encoder/):

| Interface | On the motor | Detail |
|---|---|---|
| Motor power (M+, M−) | 2 × **3.5 mm bullet, FH-MC** | on 470 mm flying leads |
| Encoder | 1 × **4-pos JST XH, FH-MC** | VCC, GND, Ch.A, Ch.B; **3.3–5 VDC** |

Both motor-side connectors are FH-MC, so **everything you buy to mate with the
motor is MH-FC.**

Encoder pinout: VCC and GND power the encoder's Hall sensors (we supply **3.3 V**
from the Nucleo so the A/B outputs come back at 3.3 V logic — no level shifting
anywhere in the robot). Ch.A and Ch.B are the two quadrature channels; their
90°-out-of-phase relationship is what lets the STM32's timer count direction as
well as distance.

## 4. What you must buy

### Encoder → Nucleo (4 needed)

**[goBILDA Encoder Breakout Cable, 4-Pos JST XH [MH-FC] → 4 × 1-Pos TJC8 [MH-FC], 300 mm](https://www.gobilda.com/encoder-breakout-cable-4-pos-jst-xh-mh-fc-to-4-x-1-pos-tjc8-mh-fc-300mm-length/)** — $3.99 each, 22 AWG.

This is the correct part and not the obvious one. The **breakout** version splits
into four *individual* female Dupont leads, so each signal can go to whatever
Nucleo pin the pin map assigns — our four encoder pairs land on TIM2/3/4/8 pins
that are **not adjacent** (PA0/PA1, PA6/PA7, PB6/PB7, PC6/PC7), and VCC has to
reach the 3V3 pin on a different header entirely. A straight 4-pin-to-4-pin cable
could not do this.

- ⚠ **Reach check:** 300 mm from a corner motor to a centrally-mounted Nucleo is
  adequate on a 0.30 m chassis but not generous. If the layout puts the Nucleo
  off-center, add [300 mm extensions](https://www.gobilda.com/encoder-cable-extension-4-pos-jst-xh-300mm-length/).
- ⚠ **Verify at purchase:** whether an encoder cable ships in the motor box.
  Vendor pages don't state it. If they do ship, you may only need extensions.
  Buying 4 breakouts is the safe assumption (~$16 total).

### Motor power → VNH5019 driver (4 needed)

The motor's 470 mm leads end in 3.5 mm FH-MC bullets. The Pololu VNH5019 carrier
has plated through-holes for OUT A / OUT B — you solder wire in. So each motor
needs a short pigtail: **3.5 mm bullet MH-FC on one end**, bare wire soldered
into the driver on the other.

- **8 × 3.5 mm bullet connectors, female-contact (MH-FC)** — sold as
  "3.5 mm bullet connector pairs" in the RC/hobby world; goBILDA also stocks the
  matching style. ~$10–15 for a set with heat-shrink.
- **16 AWG silicone wire**, ~2 m red + 2 m black — sized for the 8 A design limit
  with margin (18 AWG would pass, 16 AWG runs cool and is easier to strain-relieve).
- Optional but recommended: **5 mm screw terminal blocks** for the driver outputs,
  so a motor can be swapped without a soldering iron.

⚠ **Check on receipt:** the gauge of the motor's own 470 mm leads sets the real
ceiling — if they are thinner than 18 AWG, that's the limiting element, not your
pigtail, and it's worth noting for the current-limit bench test.

### Not motor-related but in the same harness

Already on the shopping list: XT60 pack connector, 8 AWG bus wire, 60 A fuse,
E-stop and its contactor. The Nucleo needs **one USB-A → micro/mini-B cable** to
the Jetson (check which the Nucleo board uses — ST-LINK V3E boards are typically
USB micro-B) and **5 V from the buck to its E5V pin** (JP3 set to E5V) — two
jumper wires, not a purchased assembly.

## 5. Assembly-day sanity checks

1. **Encoder direction:** with the wheel pushed forward by hand, counts must
   increase. If a wheel counts backwards, swap Ch.A/Ch.B *in the pin map and
   rebuild* rather than crossing wires — keep the harness symmetric.
2. **Motor direction:** if a wheel spins the wrong way for a positive command,
   swap its two bullet connectors (this is what bullets are for) — the firmware
   should not have to carry per-wheel sign hacks.
3. **Encoder before power:** verify all four encoders count correctly with the
   motor bus unpowered (spin by hand) before ever energizing the drivers.
