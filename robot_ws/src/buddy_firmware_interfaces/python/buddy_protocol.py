"""Buddy drive protocol v1 — Python reference implementation.

Mirror of firmware/shared_protocol/buddy_protocol/buddy_protocol.c, cross-checked
against it by golden vectors (test_protocol.py asserts the exact bytes the C
tests print). Used by the future Jetson-side bridge node and by mock_mcu.py.
Spec: firmware/shared_protocol/drive_protocol.md. No dependencies.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

VERSION = 0x01
SYNC = b"\xb5\xdd"
MAX_PAYLOAD = 64

T_CMD_VEL = 0x01
T_CMD_MODE = 0x02
T_PING = 0x03
T_TELEMETRY = 0x10
T_PONG = 0x11
T_FAULT_EVT = 0x12

STATE_BOOT, STATE_SELF_TEST, STATE_SAFE_IDLE, STATE_ARMED, STATE_ACTIVE, \
    STATE_FAULT, STATE_UPDATE = range(7)
STATE_NAMES = ["BOOT", "SELF_TEST", "SAFE_IDLE", "ARMED", "ACTIVE", "FAULT", "UPDATE"]

FAULT_ESTOP = 0x0001
FAULT_CMD_TIMEOUT = 0x0002
FAULT_DRIVER = 0x0004
FAULT_OVERCURRENT = 0x0008
FAULT_ENCODER = 0x0010
FAULT_UNDERVOLT = 0x0020
FAULT_OVERTEMP = 0x0040
FAULT_INTERNAL = 0x8000

MODE_SAFE_IDLE, MODE_ARM, MODE_CLEAR_FAULT = 0, 1, 2

WATCHDOG_TIMEOUT_S = 0.200  # REQ_SAFE_002


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF (check('123456789')=0x29B1)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1) & 0xFFFF
    return crc


def encode(ftype: int, seq: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload too large")
    body = bytes([VERSION, ftype, seq & 0xFF, len(payload)]) + payload
    return SYNC + body + struct.pack("<H", crc16(body))


def encode_cmd_vel(seq: int, vel_mmps: tuple[int, int, int, int]) -> bytes:
    """Wheel order LF, LR, RF, RR in mm/s."""
    return encode(T_CMD_VEL, seq, struct.pack("<4h", *vel_mmps))


def encode_cmd_mode(seq: int, mode: int) -> bytes:
    return encode(T_CMD_MODE, seq, bytes([mode]))


@dataclass
class Frame:
    type: int
    seq: int
    payload: bytes


@dataclass
class Telemetry:
    state: int
    fault_bits: int
    estop: int
    cmd_seq_echo: int
    wheel_pos: tuple
    wheel_vel: tuple
    motor_cur_ma: tuple
    vbat_mv: int

    _FMT = "<BHBB4i4h4hH"  # 39 bytes

    def pack(self) -> bytes:
        return struct.pack(self._FMT, self.state, self.fault_bits, self.estop,
                           self.cmd_seq_echo, *self.wheel_pos, *self.wheel_vel,
                           *self.motor_cur_ma, self.vbat_mv)

    @classmethod
    def unpack(cls, payload: bytes) -> "Telemetry":
        v = struct.unpack(cls._FMT, payload)
        return cls(state=v[0], fault_bits=v[1], estop=v[2], cmd_seq_echo=v[3],
                   wheel_pos=v[4:8], wheel_vel=v[8:12], motor_cur_ma=v[12:16],
                   vbat_mv=v[16])


assert struct.calcsize(Telemetry._FMT) == 39, "telemetry layout drifted from spec"


def encode_telemetry(seq: int, t: Telemetry) -> bytes:
    return encode(T_TELEMETRY, seq, t.pack())


@dataclass
class Parser:
    """Resynchronizing byte-stream parser; mirror of bp_parser_t."""

    crc_errors: int = 0
    version_errors: int = 0
    resyncs: int = 0
    frames_ok: int = 0
    _buf: bytearray = field(default_factory=bytearray)

    def feed(self, data: bytes) -> list[Frame]:
        """Feed any number of bytes; return completed valid frames."""
        self._buf.extend(data)
        out: list[Frame] = []
        while True:
            i = self._buf.find(SYNC)
            if i < 0:
                # keep a possible trailing 0xB5
                del self._buf[:max(0, len(self._buf) - 1)]
                return out
            if i > 0:
                self.resyncs += 1
                del self._buf[:i]
            if len(self._buf) < 6:
                return out
            ver, ftype, seq, length = self._buf[2:6]
            if ver != VERSION:
                self.version_errors += 1
                del self._buf[:2]
                continue
            if length > MAX_PAYLOAD:
                self.resyncs += 1
                del self._buf[:2]
                continue
            total = 6 + length + 2
            if len(self._buf) < total:
                return out
            body = bytes(self._buf[2:6 + length])
            rx_crc = struct.unpack("<H", self._buf[6 + length:total])[0]
            if crc16(body) == rx_crc:
                self.frames_ok += 1
                out.append(Frame(ftype, seq, body[4:]))
                del self._buf[:total]
            else:
                self.crc_errors += 1
                del self._buf[:2]
