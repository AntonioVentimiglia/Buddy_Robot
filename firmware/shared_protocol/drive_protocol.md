# Buddy Drive Protocol v1 — Wire Specification

**Date:** 2026-07-14 · **Transport:** USB serial 921600-8N1 ([ADR-0006](../../docs/decisions/ADR-0006-mcu-jetson-bus-usb-serial.md)), transport-agnostic framing
**Reference implementations (single source of truth, cross-checked by golden vectors):**
C: [`buddy_protocol/buddy_protocol.c`](buddy_protocol/buddy_protocol.c) (compiled into firmware *and* host tests) ·
Python: [`buddy_protocol.py`](../../robot_ws/src/buddy_firmware_interfaces/python/buddy_protocol.py) (Jetson bridge + mock MCU)

## Frame format

```
offset  size  field
0       2     sync      0xB5 0xDD
2       1     version   0x01 (protocol version; receiver rejects mismatches)
3       1     type      see table
4       1     seq       uint8, rolling; sender increments per frame
5       1     len       payload length in bytes (0–64)
6       len   payload   little-endian fields
6+len   2     crc16     CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over
                        bytes 2..6+len-1 (version through payload), little-endian
```

Parser is a resynchronizing byte-stream state machine: any CRC/sync/version/length
failure drops bytes until the next `0xB5 0xDD` — a corrupted frame can never
produce motion, only a lost frame (and the watchdog bounds the cost of loss).

## Frame types

| Type | Name | Direction | Payload |
|---|---|---|---|
| 0x01 | `CMD_VEL` | Jetson → MCU | 4 × `int16` wheel rim velocity [mm/s], order **LF, LR, RF, RR** (8 B) |
| 0x02 | `CMD_MODE` | Jetson → MCU | 1 × `uint8`: 0 = request SAFE_IDLE, 1 = request ARM, 2 = CLEAR_FAULT (1 B) |
| 0x03 | `PING` | Jetson → MCU | empty (0 B) |
| 0x10 | `TELEMETRY` | MCU → Jetson, 100 Hz | see below (39 B) |
| 0x11 | `PONG` | MCU → Jetson | fw_major, fw_minor, fw_patch, protocol_version (4 × `uint8`) |
| 0x12 | `FAULT_EVT` | MCU → Jetson, on transition | fault_bits `uint16`, state `uint8` (3 B) |

### TELEMETRY payload (39 B)

| offset | field | type | units |
|---|---|---|---|
| 0 | state | `uint8` | state machine (below) |
| 1 | fault_bits | `uint16` | bitmask (below) |
| 3 | estop | `uint8` | 0 = clear, 1 = active |
| 4 | cmd_seq_echo | `uint8` | seq of last **accepted** `CMD_VEL` |
| 5 | wheel_pos[4] | `int32` × 4 | encoder counts (LF, LR, RF, RR) |
| 21 | wheel_vel[4] | `int16` × 4 | mm/s at rim |
| 29 | motor_cur[4] | `int16` × 4 | mA (8 A limit = 8000, fits) |
| 37 | vbat | `uint16` | mV |

### State machine values (mirrors `firmware/drive_mcu/docs/state_machine.md`)

`0 BOOT · 1 SELF_TEST · 2 SAFE_IDLE · 3 ARMED · 4 ACTIVE · 5 FAULT · 6 UPDATE`

### Fault bits

`0x0001 ESTOP · 0x0002 CMD_TIMEOUT · 0x0004 DRIVER_FAULT · 0x0008 OVERCURRENT ·
0x0010 ENCODER_FAULT · 0x0020 UNDERVOLT · 0x0040 OVERTEMP · 0x8000 INTERNAL`

## Behavioral rules

1. **Watchdog (REQ_SAFE_002):** in ACTIVE, if no valid `CMD_VEL` arrives for
   **200 ms**, transition to SAFE_IDLE and set `CMD_TIMEOUT` in the next
   `FAULT_EVT`/`TELEMETRY`. Motion is only produced in ACTIVE.
2. **Arming:** SAFE_IDLE → ARMED requires `CMD_MODE(1)`; ARMED → ACTIVE occurs on
   the first valid `CMD_VEL`. Any fault → FAULT; FAULT → SAFE_IDLE only via
   `CMD_MODE(2)` *and* the fault cause cleared.
3. **E-stop dominates:** while `estop = 1`, mode requests are ignored and state
   is FAULT (`ESTOP` bit set). Physical E-stop also interrupts motor power
   upstream — this protocol path is reporting, not the safety mechanism.
4. **Version gate:** receiver silently drops frames whose `version` ≠ its own and
   raises a diagnostics counter; `PING`/`PONG` lets the Jetson detect mismatch.
5. Velocities are clamped by the MCU to the firmware limit (from
   `design_params.yaml` teleop max), not trusted from the wire.

## Golden vectors (both implementations must reproduce exactly)

Asserted in `test_protocol.py` (Python) and `test_protocol.c` (C); each was
computed independently by both implementations and they match byte-for-byte:

```
PING seq=7:                              b5dd01030700b332
CMD_VEL seq=1, (100,-100,250,-250) mm/s: b5dd0101010864009cfffa0006fff247
CRC-16/CCITT-FALSE check("123456789") =  0x29B1
```

Run all protocol tests (no hardware):

```bash
cc -Wall -Wextra -Werror -Ifirmware/shared_protocol/buddy_protocol \
   firmware/shared_protocol/buddy_protocol/buddy_protocol.c \
   firmware/shared_protocol/tests/test_protocol.c -o /tmp/tp && /tmp/tp
python3 robot_ws/src/buddy_firmware_interfaces/python/test_protocol.py
python3 robot_ws/src/buddy_firmware_interfaces/python/mock_mcu.py --selftest
```
