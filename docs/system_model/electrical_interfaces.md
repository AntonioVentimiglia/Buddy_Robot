# Electrical Interface Verification — Drive Chain

**Date:** 2026-07-14 · **Status:** verified on paper; bench-verify items listed at bottom
**Chain:** goBILDA 5203 motors ↔ Pololu VNH5019 drivers ↔ NUCLEO-G474RE ↔ Jetson Orin Nano

Purchases are proceeding on the assumption these parts interface as intended.
This document checks that assumption signal-by-signal, with the numbers.
Sources: [VNH5019 carrier page](https://www.pololu.com/product/1451) (logic ≥ 2.1 V = high,
PWM ≤ 20 kHz, CS ≈ 140 mV/A), goBILDA 5203 product spec (3.3–5 V encoder,
751.8 PPR at output), ST NUCLEO-G474RE / STM32G474 datasheets, Jetson Orin Nano
dev kit carrier spec (9–20 V input, USB-A host ports).

## 1. Motor ↔ Driver (power)

| Check | Requirement | Capability | Verdict |
|---|---|---|---|
| Bus voltage | 3S Li-ion 9.0–12.6 V | VNH5019 operating 5.5–24 V | ✔ |
| Motor stall current | 9.2 A (fault) | 12 A continuous, 30 A peak per channel | ✔ |
| Designed limit | 8 A firmware chop | within continuous rating — no derating needed | ✔ |
| Brushed DC drive | 2-wire brushed motor | full H-bridge per channel | ✔ |

## 2. Driver ↔ MCU (logic)

| Signal | Direction | Levels | Check |
|---|---|---|---|
| INA/INB (direction) ×4 drivers | G474 GPIO → driver | G474 outputs 3.3 V; VNH5019 high ≥ 2.1 V | ✔ 3.3 V-native, no level shifter |
| PWM ×4 | G474 TIM1 CH1–4 → driver | 20 kHz max; TIM1 @ 170 MHz gives 20 kHz with 8500-step (~13-bit) duty resolution | ✔ ultrasonic, quiet |
| Current sense ×4 | driver CS → G474 ADC | 140 mV/A → 1.12 V at the 8 A limit; ADC range 0–3.3 V, 12-bit → ≈ 5.8 mA/LSB | ✔ ample headroom + resolution |
| EN/DIAG fault ×4 | driver → G474 GPIO | open-drain style flag, 3.3 V pull-up | ✔ read as fault input |
| Sense timing | CS valid only while H-bridge driving | sample ADC mid-PWM-on via TIM1 trigger | ✔ hardware-triggered ADC (G474 strength) |

The 8 A limit loop: TIM1-triggered ADC samples CS mid-pulse → firmware
comparator chops PWM for the remainder of the control period when I > 8 A.
The G474's ADC+timer fabric is designed for exactly this (it is ST's
motor-control-oriented part).

## 3. Motor encoders ↔ MCU

| Check | Requirement | Capability | Verdict |
|---|---|---|---|
| Supply | goBILDA encoder 3.3–5 V | run at 3.3 V from Nucleo | ✔ no level shifting anywhere |
| Channels | 4 motors × quadrature A/B | TIM2, TIM3, TIM4, TIM8 in hardware encoder mode | ✔ four true hardware decoders |
| Count rate | 751.8 PPR × 4 edges = 3007 counts/rev; at 223 RPM ≈ 11.2 kcounts/s per wheel | hardware timers count to tens of MHz | ✔ ~3 orders of magnitude margin |
| Wiring | 6-pin JST per motor (pwr, gnd, A, B) | GPIO with input filtering enabled | ✔ enable timer input filter vs brush noise |

## 4. MCU ↔ Jetson (command/telemetry + power)

| Check | Requirement | Capability | Verdict |
|---|---|---|---|
| Physical link | serial, zero extra hardware for v0.1 | Nucleo's STLINK-V3E exposes a USB **Virtual COM Port** wired to G474 USART; Jetson USB-A host | ✔ one USB cable ([ADR-0006](../decisions/ADR-0006-mcu-jetson-bus-usb-serial.md)) |
| Jetson driver | CDC-ACM/VCP enumeration | standard `cdc_acm` in JetPack Linux → `/dev/ttyACM*` | ✔ + udev rule for stable naming (devops/udev) |
| Bandwidth | ~40 B telemetry @ 100 Hz + ~16 B commands @ 50 Hz ≈ 5 kB/s | 921600 baud ≈ 92 kB/s usable | ✔ ~18× margin |
| Latency | watchdog granularity 200 ms | VCP round-trip typically ≤ 2–5 ms | ✔ bench-verify jitter |
| MCU power | Nucleo 5 V | powered from the robot's 5 V rail via E5V (jumper JP3 set accordingly), USB data still connected | ✔ MCU stays alive if Jetson reboots |
| Failure mode | Jetson dies / cable pulled | MCU watchdog times out → SAFE_IDLE; if MCU itself loses power, PWM ceases → VNH5019 outputs off | ✔ fails safe both ways |

## 5. Battery ↔ everything

Verified in [`power_budget_and_battery.md`](../analysis/power_budget_and_battery.md):
drivers direct on the 9.0–12.6 V bus (within 5.5–24 V), Jetson behind a
regulated 12 V buck (dev kit input 9–20 V — even raw bus is in-window),
5 V buck for encoders/Nucleo/logic, protection chain sized against the
arms-inclusive 47 A designed peak.

## Bench-verify list (cannot be closed on paper)

1. VCP latency/jitter under load — measure round-trip at 100 Hz telemetry.
2. CS pin ripple at 20 kHz PWM — confirm mid-pulse ADC sampling window.
3. Encoder signal integrity next to motor leads — twisted pairs, timer input
   filter setting.
4. Nucleo JP3/E5V dual-power behavior with USB connected (ST documents it;
   verify no back-power path).
5. The 8 A firmware chop engagement time on a real stall (single motor,
   current-limited bench supply) — the safety-path test from the driver ADR.
