#!/usr/bin/env bash
# Run every host-side firmware test (no hardware, no PlatformIO needed):
# shared C protocol, Python protocol (golden-vector cross-check), mock MCU
# behavior, and the drive MCU safety state machine.
set -euo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== C protocol tests =="
cc -Wall -Wextra -Werror -Ifirmware/shared_protocol/buddy_protocol \
   firmware/shared_protocol/buddy_protocol/buddy_protocol.c \
   firmware/shared_protocol/tests/test_protocol.c -o "$TMP/tp"
"$TMP/tp"

echo "== C state machine tests =="
cc -Wall -Wextra -Werror -Ifirmware/drive_mcu/src \
   -Ifirmware/shared_protocol/buddy_protocol \
   firmware/drive_mcu/src/state_machine.c \
   firmware/shared_protocol/buddy_protocol/buddy_protocol.c \
   firmware/drive_mcu/tests/test_state_machine.c -o "$TMP/tsm"
"$TMP/tsm"

echo "== Python protocol tests =="
(cd robot_ws/src/buddy_firmware_interfaces/python && python3 test_protocol.py)

echo "== Mock MCU self-test =="
(cd robot_ws/src/buddy_firmware_interfaces/python && python3 mock_mcu.py --selftest)

echo
echo "ALL HOST-SIDE FIRMWARE TESTS PASSED"
