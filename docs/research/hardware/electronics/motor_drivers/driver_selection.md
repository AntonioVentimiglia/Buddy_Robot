# Motor Driver Selection — Buddy v0.1 Drive Base

**Last updated:** 2026-07-12
**Status:** shortlisted, recommendation made, purchase pending
**Hard requirements (from [ADR-0005](../../../../decisions/ADR-0005-power-architecture-battery-bus.md)):**
4 brushed-DC channels · 12 V-class bus (10–12.6 V) · ≥ 10 A capable per channel ·
**adjustable ~8 A per-channel current limit** (in-driver, or implementable in the
MCU from driver current-sense feedback) · current telemetry to MCU preferred ·
fault reporting preferred.

Sizing context: cruise 0.6 A/motor, sustained ramp+accel 3.1 A, pivot breakaway
7.6 A (~1 s), designed ceiling 8 A, motor stall 9.2 A (fault).

## Shortlist (specs verified 2026-07-12)

| Candidate | Cost for 4 ch | Continuous / peak per ch | Current limiting | Verdict |
|---|---|---|---|---|
| **4× Pololu VNH5019 carrier** ([carrier](https://www.pololu.com/product/1451), [dual-shield docs](https://www.pololu.com/docs/pdf/0J49/dual_vnh5019_motor_driver_shield.pdf)) | ~$100 ($24.95 ea) | **12 A / 30 A** | firmware: 140 mV/A current-sense pin → STM32 ADC chops PWM at 8 A; chip's own overcurrent protection as hardware backstop | **Recommended.** Covers every operating point with margin; automotive-grade fault behavior; current telemetry is exactly what the G474's ADCs are for. Cost fits budget. |
| 2× RoboClaw 2x15A ([Basicmicro](https://www.basicmicro.com/RoboClaw-2x15A-Motor-Controller_p_10.html), [goBILDA carries it](https://www.gobilda.com/roboclaw-2x15a-motor-controller/)) | ~$260 | 15 A / 30 A | **firmware per-channel limits built in**; onboard encoder inputs + velocity PID; USB/serial | Premium path: offloads the whole low-level loop, proven ROS support. Rejected for v0.1 on cost (~2.6× the VNH5019 path) and because it absorbs the MCU's safety role into a closed product — less learning value. Revisit if firmware becomes the bottleneck. |
| 4× Pololu TB67H420FTG ([product](https://www.pololu.com/product/2999)) | ~$80 ($19.95 ea) | 3.4 A / 9 A (single-ch mode) | **true hardware current chop** via VREF, ~9 A default in single mode | Attractive hardware limiting, but 3.4 A continuous is only 10% above the 3.1 A sustained design case — thermal margin too thin for sustained ramps. |
| 4× BTS7960 "IBT-2" modules | ~$35 | 43 A rated (module-limited lower) | firmware via IS sense pins (coarse) | Budget fallback. Huge current headroom, but crude current sense, no real fault reporting, variable module quality. Use only if budget forces it. |

## Recommendation

**4× Pololu VNH5019 carriers (~$100)** driven by the NUCLEO-G474RE:
PWM + direction per channel, current-sense into 4 ADC channels, firmware current
limit at 8 A (per ADR-0005), driver fault pins into GPIO. The firmware current
limit sits on the safety path, so its behavior is a **mandatory bench test**
before first rolling drive (single motor, current-limited supply, verify the
chop engages at 8 A) — added to the verification plan.

Note on integration: the NUCLEO-G474RE has Arduino Uno V3 headers, so the dual
VNH5019 *shield* ($49.95, 2 channels) stacks directly for the **bench phase** —
one shield + one motor is the cheapest possible first bench loop. The 4-carrier
layout is the rolling-base configuration.

## What would change this decision

- Bench test shows the G474 firmware limit reacts too slowly on breakaway
  transients → move to TB67H420 hardware chop (accepting thermal derating) or
  RoboClaw.
- Budget relief (or firmware time pressure) → RoboClaw 2x15A pair.
