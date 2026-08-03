#!/usr/bin/env python3
"""Buddy — measure encoder counts per output revolution, by hand, on real motors.

WHY THIS EXISTS
`design_params.yaml → drive_motor.encoder_counts_per_rev_output` is 753.2, and it
is the most suspect number in the parameter file:

  * It already caused a shipped bug. On 2026-07-16 the value was 4x wrong; every
    odometry estimate downstream inherited the error.
  * The datasheet itself is wrong in a related place. goBILDA's sheet carries a
    companion line reading "(134.4 Cycles)", but 134.4 = 7 x 19.2 belongs to the
    19.2:1 motor, not our 26.9:1. A vendor error in the same table as the number
    we depend on.
  * design_params.yaml has said "Verify empirically at bench" ever since.

This is that verification, and it is the cheapest one available: it needs NO
motor power. The encoder is a separate circuit from the motor windings, so the
shaft is turned by hand and the counts are read from the telemetry the firmware
already sends at 100 Hz.

WIRING (one motor at a time, motor POWER LEADS LEFT DISCONNECTED)
Encoder 4-pin JST-XH -> breakout -> Nucleo, per firmware/drive_mcu/docs/pin_map.md:

    wheel 0  LF   TIM2   A->PA0   B->PA1
    wheel 1  LR   TIM3   A->PA6   B->PA7
    wheel 2  RF   TIM4   A->PB6   B->PB7
    wheel 3  RR   TIM8   A->PC6   B->PC7

    encoder VCC -> 3.3V on the Nucleo   (goBILDA encoder accepts 3.3-5 V)
    encoder GND -> GND

SAFETY
Nothing here drives a motor. The MCU is never armed and no CMD_VEL is sent. Keep
the motor's two power leads unconnected for the whole test — with them floating,
the motor cannot move even if something else went wrong.

    ./devops/jetson/verify_encoder_counts.py                # wheel 0, 5 turns
    ./devops/jetson/verify_encoder_counts.py --wheel 2 --turns 10
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(
    REPO, "robot_ws", "src", "buddy_firmware_interfaces", "python"))

import serial  # noqa: E402
import buddy_protocol as bp  # noqa: E402
from buddy_calcs import P  # noqa: E402

WHEELS = ["LF (left front)", "LR (left rear)", "RF (right front)", "RR (right rear)"]
PINS = ["TIM2  A=PA0  B=PA1", "TIM3  A=PA6  B=PA7",
        "TIM4  A=PB6  B=PB7", "TIM8  A=PC6  B=PC7"]

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"ok   {name}" + (f"   [{detail}]" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL {name}" + (f"   [{detail}]" if detail else ""))


def read_pos(ser, wheel, seconds=1.0):
    """Latest wheel_pos[wheel] from telemetry, or None if the link is quiet."""
    parser = bp.Parser()
    ser.reset_input_buffer()
    last, t_end = None, time.time() + seconds
    while time.time() < t_end:
        data = ser.read(4096)
        if data:
            for f in parser.feed(data):
                if f.type == bp.T_TELEMETRY:
                    last = bp.Telemetry.unpack(f.payload).wheel_pos[wheel]
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/buddy_drive_mcu")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--wheel", type=int, default=0, choices=range(4),
                    help="0=LF 1=LR 2=RF 3=RR (see pin_map.md)")
    ap.add_argument("--turns", type=float, default=5.0,
                    help="whole output-shaft turns to rotate by hand. More turns "
                         "divides your hand-positioning error by the turn count")
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="fractional agreement required, default 5%%")
    args = ap.parse_args()

    expected = float(P["drive_motor"]["encoder_counts_per_rev_output"])
    ratio = P["drive_motor"]["part"]

    print("=" * 70)
    print(f"Encoder count verification — wheel {args.wheel}: {WHEELS[args.wheel]}")
    print(f"  motor            {ratio}")
    print(f"  design_params    {expected} counts per OUTPUT revolution")
    print(f"  wiring           {PINS[args.wheel]}  (+3.3V, GND)")
    print("=" * 70)
    print()
    print("SAFETY: leave the motor's POWER leads disconnected. Only the 4-pin")
    print("        encoder connector should be attached. Nothing will be driven.")
    print()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL cannot open {args.port}: {e}")
        return 1

    start = read_pos(ser, args.wheel)
    check("telemetry readable", start is not None)
    if start is None:
        print("\nNo telemetry — is the Nucleo flashed and connected?")
        return 1
    print(f"     starting count: {start}")
    print()

    # A stationary shaft must read a stationary count. If this drifts, the input
    # is floating or picking up noise, and every later number is meaningless.
    time.sleep(1.5)
    idle = read_pos(ser, args.wheel)
    check("count is stable while the shaft is still", idle == start,
          f"{start} -> {idle}")
    if idle != start:
        print("     Drifting while stationary means a floating or noisy input:")
        print("     check GND, check A/B are not swapped onto the same pin, and")
        print("     confirm the encoder is powered from 3.3 V.")

    print()
    print(f">>> Mark the OUTPUT shaft (the 8 mm REX hex, not the motor can).")
    print(f">>> Rotate it exactly {args.turns:g} full turns, in the direction that")
    print(f">>> would drive the robot FORWARD. Then press Enter.")
    input()

    end = read_pos(ser, args.wheel)
    if end is None:
        print("FAIL lost telemetry mid-test")
        return 1

    delta = end - start
    measured = abs(delta) / args.turns
    err = (measured - expected) / expected

    print()
    print(f"     counts moved   {delta:+d} over {args.turns:g} turns")
    print(f"     measured       {measured:.1f} counts/rev")
    print(f"     expected       {expected:.1f} counts/rev")
    print(f"     error          {err * 100:+.1f}%")
    print()

    check("shaft actually moved", abs(delta) > 10, f"{delta:+d} counts")
    # Sign convention: forward rotation must increase the count, or odometry runs
    # backwards. Cheap to fix here (swap A/B), expensive to debug on the floor.
    check("forward rotation increases the count", delta > 0,
          "positive" if delta > 0 else "NEGATIVE — swap A/B for this wheel")
    check(f"within {args.tolerance * 100:g}% of design_params",
          abs(err) <= args.tolerance, f"{measured:.1f} vs {expected:.1f}")

    # The specific failure this test was written to catch.
    scale = measured / expected if expected else 0
    for factor, note in ((4.0, "counts are 4x our assumption — goBILDA's 'pulses' "
                               "are CYCLES, not 4x-decoded counts"),
                         (0.25, "counts are 1/4 of our assumption — we are "
                                "double-counting the quadrature decode"),
                         (2.0, "counts are 2x our assumption"),
                         (0.5, "counts are 1/2 our assumption")):
        if abs(scale - factor) < 0.1:
            print()
            print(f"  >>> SCALING FACTOR {factor}x DETECTED: {note}.")
            print(f"  >>> Set encoder_counts_per_rev_output to {measured:.1f} in")
            print(f"  >>> design_params.yaml and re-run `python3 tools/build.py`.")
            print(f"  >>> This is the 2026-07-16 bug class — do not hand-patch it")
            print(f"  >>> anywhere else; the value flows from the yaml.")

    ser.close()
    print()
    print(f"passed: {PASS}   failed: {FAIL}")
    if FAIL == 0:
        print("ENCODER SCALING VERIFIED — design_params.yaml matches hardware.")
    else:
        print("VERIFICATION FAILED — see above before trusting any odometry.")
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
