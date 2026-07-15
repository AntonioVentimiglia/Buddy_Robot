"""Mock drive MCU — speaks the Buddy drive protocol over a pseudo-terminal.

Lets the Jetson-side bridge be developed and integration-tested with zero
hardware: implements the state machine (BOOT→SELF_TEST→SAFE_IDLE→ARMED→ACTIVE,
FAULT), the 200 ms command watchdog, telemetry at 100 Hz, and a simple
first-order wheel model so velocities/positions look plausible.

Run standalone:            python3 mock_mcu.py         (prints its pty path)
Self-test (no terminal):   python3 mock_mcu.py --selftest
"""

from __future__ import annotations

import os
import pty
import sys
import threading
import time

import buddy_protocol as bp

FW_VERSION = (0, 1, 0)
TELEMETRY_HZ = 100.0
VEL_LIMIT_MMPS = 750  # firmware clamp = teleop max from requirements


class MockMcu:
    def __init__(self, clock=time.monotonic):
        self.now = clock  # injectable clock so tests can drive simulated time
        self.state = bp.STATE_BOOT
        self.fault_bits = 0
        self.estop = 0
        self.cmd_seq_echo = 0
        self.target = [0, 0, 0, 0]
        self.vel = [0.0, 0.0, 0.0, 0.0]
        self.pos = [0.0, 0.0, 0.0, 0.0]
        self.vbat_mv = 11700
        self.last_cmd_time = None
        self.seq = 0
        self.parser = bp.Parser()
        self.tx = bytearray()
        # boot sequence completes immediately in the mock
        self.state = bp.STATE_SAFE_IDLE

    # --- protocol input ---------------------------------------------------
    def handle_bytes(self, data: bytes) -> None:
        for f in self.parser.feed(data):
            self.handle_frame(f)

    def handle_frame(self, f: bp.Frame) -> None:
        if f.type == bp.T_PING:
            self.tx += bp.encode(bp.T_PONG, f.seq,
                                 bytes([*FW_VERSION, bp.VERSION]))
        elif f.type == bp.T_CMD_MODE and len(f.payload) == 1:
            self._handle_mode(f.payload[0])
        elif f.type == bp.T_CMD_VEL and len(f.payload) == 8:
            self._handle_cmd_vel(f)

    def _handle_mode(self, mode: int) -> None:
        if self.estop:
            return  # E-stop dominates
        if mode == bp.MODE_ARM and self.state == bp.STATE_SAFE_IDLE:
            self.state = bp.STATE_ARMED
        elif mode == bp.MODE_SAFE_IDLE and self.state in (bp.STATE_ARMED,
                                                          bp.STATE_ACTIVE):
            self._stop(bp.STATE_SAFE_IDLE)
        elif mode == bp.MODE_CLEAR_FAULT and self.state == bp.STATE_FAULT:
            self.fault_bits = 0
            self._stop(bp.STATE_SAFE_IDLE)

    def _handle_cmd_vel(self, f: bp.Frame) -> None:
        if self.state == bp.STATE_ARMED:
            self.state = bp.STATE_ACTIVE
        if self.state != bp.STATE_ACTIVE:
            return
        import struct
        vals = struct.unpack("<4h", f.payload)
        self.target = [max(-VEL_LIMIT_MMPS, min(VEL_LIMIT_MMPS, v)) for v in vals]
        self.cmd_seq_echo = f.seq
        self.last_cmd_time = self.now()

    def _stop(self, new_state: int) -> None:
        self.target = [0, 0, 0, 0]
        self.state = new_state

    def set_estop(self, active: bool) -> None:
        self.estop = 1 if active else 0
        if active:
            self.fault_bits |= bp.FAULT_ESTOP
            self._stop(bp.STATE_FAULT)
            self.tx += bp.encode(bp.T_FAULT_EVT, self._next_seq(),
                                 self.fault_bits.to_bytes(2, "little")
                                 + bytes([self.state]))
        else:
            self.fault_bits &= ~bp.FAULT_ESTOP

    # --- periodic ----------------------------------------------------------
    def tick(self, dt: float) -> None:
        # watchdog (REQ_SAFE_002)
        if (self.state == bp.STATE_ACTIVE and self.last_cmd_time is not None
                and self.now() - self.last_cmd_time > bp.WATCHDOG_TIMEOUT_S):
            self.fault_bits |= bp.FAULT_CMD_TIMEOUT
            self._stop(bp.STATE_SAFE_IDLE)
            self.tx += bp.encode(bp.T_FAULT_EVT, self._next_seq(),
                                 self.fault_bits.to_bytes(2, "little")
                                 + bytes([self.state]))
        # first-order wheel model (tau = 100 ms), integrate position
        for i in range(4):
            self.vel[i] += (self.target[i] - self.vel[i]) * min(1.0, dt / 0.1)
            self.pos[i] += self.vel[i] * dt * 9.97  # ticks/mm (3007 cpr / 301.6 mm)
        self.tx += bp.encode_telemetry(self._next_seq(), self.telemetry())

    def telemetry(self) -> bp.Telemetry:
        return bp.Telemetry(
            state=self.state, fault_bits=self.fault_bits, estop=self.estop,
            cmd_seq_echo=self.cmd_seq_echo,
            wheel_pos=tuple(int(p) for p in self.pos),
            wheel_vel=tuple(int(v) for v in self.vel),
            motor_cur_ma=tuple(min(8000, abs(int(v)) * 4) for v in self.vel),
            vbat_mv=self.vbat_mv)

    def _next_seq(self) -> int:
        self.seq = (self.seq + 1) & 0xFF
        return self.seq


def serve_pty() -> None:
    mcu = MockMcu()
    controller_fd, peripheral_fd = pty.openpty()
    print(f"mock MCU on {os.ttyname(peripheral_fd)}  (Ctrl-C to stop)")

    def reader():
        while True:
            data = os.read(controller_fd, 256)
            if data:
                mcu.handle_bytes(data)

    threading.Thread(target=reader, daemon=True).start()
    period = 1.0 / TELEMETRY_HZ
    try:
        while True:
            mcu.tick(period)
            if mcu.tx:
                os.write(controller_fd, bytes(mcu.tx))
                mcu.tx.clear()
            time.sleep(period)
    except KeyboardInterrupt:
        pass


def selftest() -> int:
    """Exercise arm → drive → watchdog → E-stop → recover, no terminal needed."""
    mcu = MockMcu()
    ok = True

    def expect(cond, name):
        nonlocal ok
        print(("ok   " if cond else "FAIL ") + name)
        ok = ok and cond

    expect(mcu.state == bp.STATE_SAFE_IDLE, "boots to SAFE_IDLE")
    mcu.handle_bytes(bp.encode_cmd_vel(1, (500, 500, 500, 500)))
    expect(mcu.target == [0, 0, 0, 0], "CMD_VEL ignored while not armed")
    mcu.handle_bytes(bp.encode_cmd_mode(2, bp.MODE_ARM))
    expect(mcu.state == bp.STATE_ARMED, "arms on request")
    mcu.handle_bytes(bp.encode_cmd_vel(3, (500, 500, 500, 500)))
    expect(mcu.state == bp.STATE_ACTIVE and mcu.target[0] == 500,
           "first CMD_VEL activates")
    mcu.handle_bytes(bp.encode_cmd_vel(4, (9000, 0, 0, 0)))
    expect(mcu.target[0] == VEL_LIMIT_MMPS, "velocity clamped to firmware limit")
    for _ in range(30):
        mcu.tick(0.01)
    expect(mcu.vel[0] > 300, "wheel model spins up")
    mcu.last_cmd_time -= 0.3  # simulate 300 ms silence
    mcu.tick(0.01)
    expect(mcu.state == bp.STATE_SAFE_IDLE
           and mcu.fault_bits & bp.FAULT_CMD_TIMEOUT,
           "watchdog stops motion at 200 ms (REQ_SAFE_002)")
    mcu.set_estop(True)
    mcu.handle_bytes(bp.encode_cmd_mode(5, bp.MODE_ARM))
    expect(mcu.state == bp.STATE_FAULT, "E-stop dominates mode requests")
    mcu.set_estop(False)
    mcu.handle_bytes(bp.encode_cmd_mode(6, bp.MODE_CLEAR_FAULT))
    expect(mcu.state == bp.STATE_SAFE_IDLE, "fault clears after E-stop release")
    # telemetry sanity through a real parse
    p = bp.Parser()
    mcu.tick(0.01)
    frames = p.feed(bytes(mcu.tx))
    expect(any(f.type == bp.T_TELEMETRY for f in frames), "telemetry emitted")
    print("all mock MCU self-tests passed" if ok else "MOCK MCU SELF-TEST FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else serve_pty())
