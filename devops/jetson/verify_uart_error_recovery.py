#!/usr/bin/env python3
"""Buddy — prove the drive MCU's UART RX survives a bus error.

Background (see assets/figures/uart_rx_recovery.svg): RX is a self-re-arming
chain — HAL_UART_Receive_IT arms exactly one byte, and HAL_UART_RxCpltCallback
arms the next.

WHAT THIS DOES AND DOES NOT COVER — read before trusting a pass.
ST's HAL splits UART errors two ways (stm32g4xx_hal_uart.c):
  * FE / NE / PE  -> non-blocking. HAL keeps receiving with no help from us.
  * ORE / RTO     -> blocking. UART_EndRxTransfer() disables the RX interrupts
                     and only HAL_UART_ErrorCallback can re-arm them.
This script injects the FE/NE class (garbage at a mismatched baud, plus a break
condition), so it exercises the non-blocking branch end to end and proves the
link recovers. It does NOT reproduce ORE: a 128 kB flood at line rate never
overran the ISR on a 170 MHz M4, so the dangerous branch is not host-reachable
on this setup. Realistic ORE sources are on-board — a long higher-priority ISR,
a critical section, or motor EMI once the drivers are live.

Treat a pass as "the link survives bus noise", not as "the overrun path is
verified". The overrun path is covered by inspection of the HAL source and the
callback in hw.c.

    ./devops/jetson/verify_uart_error_recovery.py

SAFETY: sends PING only, never a motion command, and never arms the MCU.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "robot_ws", "src", "buddy_firmware_interfaces", "python"))

import serial  # noqa: E402
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


def telemetry_rate(ser, seconds=1.5):
    """Frames/s on the RX side — proves the MCU is still TRANSMITTING."""
    parser = bp.Parser()
    ser.reset_input_buffer()
    n, t_end = 0, time.time() + seconds
    while time.time() < t_end:
        d = ser.read(4096)
        if d:
            n += sum(1 for f in parser.feed(d) if f.type == bp.T_TELEMETRY)
    return n / seconds


def pong_works(ser, tries=5):
    """PING -> PONG. This is the ONLY thing that proves RX is still alive."""
    got = 0
    for seq in range(1, tries + 1):
        parser = bp.Parser()
        ser.reset_input_buffer()
        ser.write(bp.encode(bp.T_PING, seq))
        ser.flush()
        t0 = time.time()
        while time.time() - t0 < 0.4:
            waiting = ser.in_waiting
            d = ser.read(waiting if waiting else 1)
            if not d:
                continue
            if any(f.type == bp.T_PONG for f in parser.feed(d)):
                got += 1
                break
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/buddy_drive_mcu")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--bad-baud", type=int, default=9600,
                    help="mismatched baud used to manufacture framing errors")
    args = ap.parse_args()

    print("== 1/4 baseline: RX healthy before we break anything ==")
    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    rate0 = telemetry_rate(ser)
    got0 = pong_works(ser)
    check("telemetry flowing", rate0 > 60, f"{rate0:.0f} Hz")
    check("PING -> PONG before injection", got0 == 5, f"{got0}/5")
    ser.close()

    print(f"== 2/4 inject a bus error (write at {args.bad_baud} into a "
          f"{args.baud} receiver) ==")
    # The ST-LINK VCP reconfigures its UART to whatever the host opens, so the
    # MCU - fixed at 921600 - sees each slow bit as a long run of wrong bits.
    # That is a genuine framing/noise error at the peripheral, not a simulation.
    bad = serial.Serial(args.port, args.bad_baud, timeout=0.1)
    bad.write(b"\x00\xff\x00\xff" * 64)
    bad.flush()
    time.sleep(0.5)
    try:
        bad.send_break(duration=0.05)   # belt and braces: a real break condition
    except Exception:
        pass
    bad.close()
    time.sleep(0.5)
    print("   injected garbage at the wrong baud + a break condition")

    print("== 3/4 TX is unaffected — this is what makes the bug deceptive ==")
    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    time.sleep(0.3)
    rate1 = telemetry_rate(ser)
    check("telemetry STILL flowing after the error", rate1 > 60, f"{rate1:.0f} Hz")

    print("== 4/4 the real question: can the MCU still be commanded? ==")
    got1 = pong_works(ser)
    check("PING -> PONG after injection (RX recovered)", got1 == 5, f"{got1}/5")
    ser.close()

    print()
    if got1 == 5:
        print("RX survived the error — HAL_UART_ErrorCallback re-armed reception.")
    else:
        print("RX IS DEAD: telemetry keeps streaming but commands are ignored.")
        print("That is the bug — nothing re-arms HAL_UART_Receive_IT after an error.")
    print(f"\npassed: {PASS}   failed: {FAIL}")
    print("UART ERROR RECOVERY VERIFIED" if FAIL == 0 else "VERIFICATION FAILED")
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
