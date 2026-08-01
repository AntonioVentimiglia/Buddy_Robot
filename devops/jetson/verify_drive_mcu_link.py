#!/usr/bin/env python3
"""Buddy — verify the link to a REAL drive MCU over the ST-LINK VCP (ADR-0006).

First contact with actual silicon: proves the flashed firmware boots, speaks
drive protocol v1 on the wire, and lands in the safe state. Uses the repo's own
protocol implementation, so a decode failure here means the firmware and the
Jetson genuinely disagree - not that this script has its own idea of the format.

    ./devops/jetson/verify_drive_mcu_link.py [--port /dev/buddy_drive_mcu]

Exits non-zero if any check fails. Sends no motion commands: the MCU is expected
to sit in SAFE_IDLE throughout, and this script never arms it.
"""
import argparse
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "robot_ws", "src", "buddy_firmware_interfaces", "python"))

import serial  # noqa: E402  (python3-serial, installed by setup_ros2_jazzy.sh)
import buddy_protocol as bp  # noqa: E402

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"ok   {name}" + (f"   [{detail}]" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL {name}" + (f"   [{detail}]" if detail else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/buddy_drive_mcu")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--seconds", type=float, default=2.0)
    args = ap.parse_args()

    print(f"== opening {args.port} @ {args.baud} ==")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL cannot open port: {e}")
        return 1
    check("serial port opened", True, args.port)

    parser = bp.Parser()
    telem, pongs = [], []

    # --- 1. passive listen: is it talking at all? ---
    print(f"== 1/4 listening {args.seconds}s for telemetry ==")
    ser.reset_input_buffer()
    t_end = time.time() + args.seconds
    while time.time() < t_end:
        data = ser.read(4096)
        if data:
            for f in parser.feed(data):
                if f.type == bp.T_TELEMETRY:
                    telem.append(bp.Telemetry.unpack(f.payload))

    rate = len(telem) / args.seconds
    check("telemetry frames received", len(telem) > 0, f"{len(telem)} frames")
    check("no CRC errors", parser.crc_errors == 0, f"crc_errors={parser.crc_errors}")
    check("no version errors", parser.version_errors == 0,
          f"version_errors={parser.version_errors}")
    # Firmware targets 100 Hz; allow generous slack for USB scheduling.
    check("telemetry rate near 100 Hz", 60 <= rate <= 140, f"{rate:.1f} Hz")

    if not telem:
        print("\nNo telemetry - cannot continue.")
        return 1

    # --- 2. is it in the safe state? ---
    print("== 2/4 safety state ==")
    last = telem[-1]
    states = {t.state for t in telem}
    check("state is SAFE_IDLE", last.state == bp.STATE_SAFE_IDLE,
          bp.STATE_NAMES[last.state] if last.state < len(bp.STATE_NAMES) else str(last.state))
    check("never entered ACTIVE unprompted", bp.STATE_ACTIVE not in states,
          "states seen: " + ",".join(sorted(
              bp.STATE_NAMES[s] if s < len(bp.STATE_NAMES) else str(s) for s in states)))
    # CMD_TIMEOUT is a recoverable stop flag, not a latched fault (state_machine.c
    # sm_tick drops to SAFE_IDLE, not FAULT). It is EXPECTED to be set after any
    # session where commands stopped - e.g. a prior bridge run - and clears on the
    # next ARM. Asserting fault_bits == 0 here assumed a freshly booted MCU and
    # failed the moment this script ran after the bridge. Everything else in the
    # mask means something actually broke.
    latching = last.fault_bits & ~bp.FAULT_CMD_TIMEOUT
    check("no latching fault bits", latching == 0, f"0x{last.fault_bits:04x}")
    if last.fault_bits & bp.FAULT_CMD_TIMEOUT:
        print("     note: CMD_TIMEOUT flagged by an earlier session; clears on next ARM")
    check("wheels report zero velocity", all(v == 0 for v in last.wheel_vel),
          str(last.wheel_vel))

    # --- 3. PING/PONG round trip ---
    # Per drive_protocol.md the PONG payload is {fw_major, fw_minor, fw_patch,
    # protocol_version} and the spec defines NO seq echo for it - the MCU stamps
    # its own TX seq. Only TELEMETRY.cmd_seq_echo echoes, and only for CMD_VEL.
    # Matching PONG.seq against PING.seq is therefore wrong, and cost an hour.
    # Read granularity matters too: a blocking read(512) does not return until
    # 512 bytes accumulate, which at ~4.7 kB/s of telemetry is ~110 ms and
    # swamps the quantity being measured.
    print("== 3/4 PING -> PONG round trip ==")
    pong_payload = None
    for seq in range(1, 11):
        ser.reset_input_buffer()
        rt_parser = bp.Parser()
        t0 = time.perf_counter()
        ser.write(bp.encode(bp.T_PING, seq))
        ser.flush()
        while time.perf_counter() - t0 < 0.5:
            waiting = ser.in_waiting
            data = ser.read(waiting if waiting else 1)
            if not data:
                continue
            hit = False
            for f in rt_parser.feed(data):
                if f.type == bp.T_PONG:
                    pongs.append((time.perf_counter() - t0) * 1000.0)
                    pong_payload = f.payload
                    hit = True
            if hit:
                break
    check("PONG received for every PING", len(pongs) == 10, f"{len(pongs)}/10")
    if pongs:
        print(f"     round trip: min {min(pongs):.2f} ms  "
              f"median {statistics.median(pongs):.2f} ms  max {max(pongs):.2f} ms")
        # The 200 ms watchdog (REQ_SAFE_002) needs the link to be far faster.
        check("round trip << 200 ms watchdog budget", max(pongs) < 20.0,
              f"max {max(pongs):.2f} ms")
    if pong_payload and len(pong_payload) == 4:
        fw = f"{pong_payload[0]}.{pong_payload[1]}.{pong_payload[2]}"
        proto = pong_payload[3]
        # Spec rule 4: PING/PONG is how the Jetson detects a protocol mismatch.
        check("MCU protocol version matches host", proto == bp.VERSION,
              f"mcu=0x{proto:02x} host=0x{bp.VERSION:02x}")
        print(f"     firmware v{fw}, protocol v{proto}")
    else:
        check("PONG payload is 4 bytes per spec", False,
              f"got {len(pong_payload) if pong_payload else 0}")

    # --- 4. telemetry sanity ---
    print("== 4/4 telemetry field sanity ==")
    check("E-stop line readable", last.estop in (0, 1), f"estop={last.estop}")
    print(f"     vbat={last.vbat_mv} mV  currents={last.motor_cur_ma} mA  "
          f"pos={last.wheel_pos}")
    print("     (no battery or drivers connected - vbat/current are expected"
          " near zero or floating)")

    ser.close()
    print(f"\npassed: {PASS}   failed: {FAIL}")
    print("DRIVE MCU LINK VERIFIED" if FAIL == 0 else "VERIFICATION FAILED")
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
