# Firmware Protocol Design

The protocol must be simple, timestamped, fault-aware, and recoverable.

## Required properties

- Sequence numbers or timestamps.
- CRC/checksum for custom binary protocols.
- Explicit command timeout behavior.
- E-stop state reporting.
- Fault code reporting.
- Version query.
- Safe boot state.
- Update/recovery mode that disables motion.

## Transport — decided 2026-07-14

**USB serial (ST-LINK VCP) + custom framed protocol** for v0.1, with CAN-FD as
the reserved growth path — rationale in
[ADR-0006](../../../../docs/decisions/ADR-0006-mcu-jetson-bus-usb-serial.md).

The protocol itself is fully specified and implemented:

- Wire spec: [`firmware/shared_protocol/drive_protocol.md`](../../../../firmware/shared_protocol/drive_protocol.md)
- C implementation (firmware + host tests): `firmware/shared_protocol/buddy_protocol/`
- Python implementation (Jetson bridge + mock MCU): [`../python/`](../python/)

All properties listed above are satisfied: sequence numbers, CRC-16, explicit
200 ms timeout (REQ_SAFE_002), E-stop + fault reporting, version query
(PING/PONG), safe boot state, and motion disabled outside ACTIVE.
