# ADR-0006: MCU↔Jetson Bus — USB Serial (ST-LINK VCP) for v0.1, CAN-FD Path Reserved

- Status: Proposed
- Date: 2026-07-14

## Context

The drive protocol needs a physical transport (open question in
`protocol_design.md`). The hardware is now fixed — NUCLEO-G474RE and Jetson Orin
Nano dev kit — which makes the trade concrete. Candidates: USB serial, CAN/CAN-FD
(needs a transceiver + Jetson-side CAN interface), RS485 (needs transceivers both
ends), micro-ROS (heavy firmware dependency, obscures the safety story).

Bandwidth demand is small: ~39 B telemetry at 100 Hz + ~14 B commands at 50 Hz
≈ 5 kB/s. Latency demand is lax: the safety watchdog granularity is 200 ms.

## Decision

**USB serial via the Nucleo's onboard STLINK-V3E Virtual COM Port** for v0.1:

- Zero additional hardware — one USB cable to a Jetson USB-A port; enumerates as
  `/dev/ttyACM*` via the stock `cdc_acm` driver (udev rule gives a stable name).
- 921600 baud ≈ 92 kB/s usable — ~18× margin over demand.
- The protocol itself is transport-agnostic (framed, CRC-protected, sequenced —
  see [`drive_protocol.md`](../../firmware/shared_protocol/drive_protocol.md)), so
  frames survive a later move unchanged.
- **CAN-FD is the reserved growth path**: the G474 has FDCAN on-chip; when the
  future arms add more MCUs, add transceivers and move the same frames to CAN.
  micro-ROS rejected: it hides the watchdog/safety logic inside a ROS
  abstraction, and the MCU must stay safe with ROS entirely absent.

## Consequences

- Firmware speaks the protocol over USART2 (the pins the ST-LINK VCP bridges);
  no USB stack in our firmware — the ST-LINK does the USB work.
- MCU is powered from the robot's 5 V rail (E5V), not the USB cable, so it
  outlives Jetson reboots; either failure direction lands in SAFE_IDLE
  (verified in [`electrical_interfaces.md`](../system_model/electrical_interfaces.md)).
- Protocol implementation is shared: one C source compiled into firmware **and**
  into host-side tests, plus a byte-identical Python implementation cross-checked
  against golden vectors — the two ends cannot drift.
- Bench-verify: VCP latency jitter at 100 Hz telemetry (open item; expected
  ≤ 2–5 ms, two orders below the watchdog).

## What would change this decision

- Measured VCP jitter approaching the 100 Hz telemetry period → dedicated
  USB-serial adapter on a spare USART, or accelerate the CAN-FD move.
- Second MCU joining the bus (arm controller) → CAN-FD becomes the bus.
