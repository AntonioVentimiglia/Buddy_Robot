#!/usr/bin/env bash
# Buddy — flash the drive MCU firmware to a NUCLEO-G474RE.
#
#   tools/flash/flash_drive_mcu.sh            build + upload
#   tools/flash/flash_drive_mcu.sh --build    build only, no hardware needed
#   tools/flash/flash_drive_mcu.sh --probe    just report what is attached
#
# Works from macOS or Linux (the Jetson). Upload goes through the on-board
# ST-LINK over USB; there is no separate programmer to configure.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FW_DIR="$REPO_ROOT/firmware/drive_mcu"

# PlatformIO is commonly a user install and not on a non-interactive PATH.
PIO="$(command -v pio 2>/dev/null || true)"
[ -n "$PIO" ] || { [ -x "$HOME/.local/bin/pio" ] && PIO="$HOME/.local/bin/pio"; } || true
[ -n "$PIO" ] || { [ -x "$HOME/.platformio/penv/bin/pio" ] && PIO="$HOME/.platformio/penv/bin/pio"; } || true
if [ -z "$PIO" ]; then
  echo "ERROR: PlatformIO not found. Install with:  pip install --user platformio" >&2
  exit 1
fi

probe() {
  echo "== attached ST devices =="
  if command -v lsusb >/dev/null 2>&1; then
    lsusb | grep -iE "0483|st-?link" || echo "  none (lsusb)"
  elif command -v system_profiler >/dev/null 2>&1; then
    system_profiler SPUSBDataType 2>/dev/null \
      | grep -iE "st-?link|STM32|0x0483" || echo "  none (system_profiler)"
  fi
  echo "== serial ports =="
  ls /dev/tty.usbmodem* /dev/ttyACM* /dev/buddy_drive_mcu 2>/dev/null || echo "  none"
}

case "${1:-}" in
  --probe) probe; exit 0 ;;
  --build) echo "== build only =="; cd "$FW_DIR"; "$PIO" run; exit 0 ;;
esac

probe
echo
echo "== build =="
cd "$FW_DIR"
"$PIO" run

echo
echo "== upload =="
# ST-LINK enumerates as both a debug probe and a VCP. If the bridge or a serial
# monitor is holding the VCP open, upload can fail with a busy port — close them
# first rather than power-cycling the board.
"$PIO" run -t upload

echo
echo "== post-flash =="
sleep 2
probe
echo
echo "Flashed. The MCU boots SELF_TEST -> SAFE_IDLE and will NOT move without an"
echo "explicit ARM (see firmware/drive_mcu/docs/state_machine.md)."
