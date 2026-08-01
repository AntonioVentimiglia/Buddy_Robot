#!/usr/bin/env bash
# Buddy — run the buddy_base bridge against the REAL drive MCU.
#
# Until now the bridge has only ever talked to mock_mcu.py over a pty. This is
# the same code path (by design) pointed at /dev/buddy_drive_mcu, which is where
# mock-vs-reality mismatches live: real interrupt latency, real USB CDC timing,
# real ADC noise, a real state machine that can refuse things the mock allowed.
#
#   ./devops/jetson/verify_bridge_vs_real_mcu.sh
#
# SAFETY: no motor drivers are wired and no motors are attached, so nothing can
# move. The MCU also refuses motion without an explicit ARM. Do not run this
# with motors connected until the bench drive loop has been commissioned.
#
# What it can and cannot prove with no encoders attached:
#   CAN  - telemetry parses into /odom, /joint_states, /battery_state
#   CAN  - the bridge drives the MCU state machine (auto-arm, CMD_VEL accepted)
#   CAN  - the 200 ms watchdog (REQ_SAFE_002) fires on real silicon
#   CANNOT - odometry motion: wheel_pos comes from encoders that do not exist
#            yet, so /odom stays at zero. That is correct behaviour, not a bug.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

set +u
source /opt/ros/jazzy/setup.bash
source "$REPO_ROOT/robot_ws/install/setup.bash"
set -u
export ROS_DOMAIN_ID=42

PORT="${PORT:-/dev/buddy_drive_mcu}"
DRIVE_SECONDS=3
PASS=0; FAIL=0

check() {
  if [ "$2" = "1" ]; then echo "ok   $1${3:+   [$3]}"; PASS=$((PASS+1));
  else echo "FAIL $1${3:+   [$3]}"; FAIL=$((FAIL+1)); fi
}

topic_field() {  # $1 topic, $2 field — filter numeric, see zero-hardware script
  timeout 10 ros2 topic echo "$1" --once --field "$2" 2>/dev/null \
    | grep -E '^[-+]?[0-9]+\.?[0-9]*([eE][-+]?[0-9]+)?$' | head -1
}

cleanup() {
  pkill -f "[b]ase.launch.py" 2>/dev/null || true
  pkill -f "[r]os2 topic pub" 2>/dev/null || true
  pkill -f "[b]ridge_node" 2>/dev/null || true
}
trap cleanup EXIT
cleanup; sleep 1

echo "== 0/5 preflight =="
check "MCU device present" "$([ -e "$PORT" ] && echo 1 || echo 0)" "$PORT"
check "port readable/writable by $(whoami)" \
      "$([ -r "$PORT" ] && [ -w "$PORT" ] && echo 1 || echo 0)"
[ -e "$PORT" ] || { echo "no MCU at $PORT - is it plugged in?"; exit 1; }
HOLDER=$(fuser "$PORT" 2>/dev/null | tr -d ' ')
check "port not already held by another process" \
      "$([ -z "$HOLDER" ] && echo 1 || echo 0)" "${HOLDER:-free}"

echo "== 1/5 start bridge against real MCU =="
rm -f /tmp/buddy_realbridge.log
setsid nohup ros2 launch buddy_bringup base.launch.py \
  port:="$PORT" auto_arm:=true > /tmp/buddy_realbridge.log 2>&1 < /dev/null &
sleep 12

grep -q "bridge up on $PORT" /tmp/buddy_realbridge.log && B=1 || B=0
check "bridge opened the real port" "$B" "$(grep -o 'bridge up on.*' /tmp/buddy_realbridge.log | head -1)"
if [ "$B" != "1" ]; then echo "--- bridge log ---"; tail -30 /tmp/buddy_realbridge.log; exit 1; fi

# auto-arm only fires when the bridge has parsed a real SAFE_IDLE from telemetry,
# so this line is itself evidence that real MCU state reached BaseCore.
grep -q "auto-arm: requesting ARM" /tmp/buddy_realbridge.log && A=1 || A=0
check "bridge parsed real MCU state and auto-armed" "$A"

echo "== 2/5 telemetry reaches ROS topics =="
TOPICS=$(ros2 topic list 2>/dev/null)
for t in /odom /joint_states /battery_state; do
  echo "$TOPICS" | grep -qx "$t" && r=1 || r=0
  check "$t advertised" "$r"
done
VBAT=$(topic_field /battery_state voltage)
check "/battery_state carries a real MCU ADC reading" \
      "$([ -n "$VBAT" ] && echo 1 || echo 0)" "${VBAT:-none} V"

echo "== 3/5 command the MCU through ROS =="
setsid nohup ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}" > /dev/null 2>&1 < /dev/null &
sleep "$DRIVE_SECONDS"
pkill -f "[r]os2 topic pub" 2>/dev/null || true

# Assert on actual fault BITS, not on log-line count. FAULT_EVT is emitted on
# every state transition, so counting those flagged the benign SAFE_IDLE->ARMED
# handover as a failure. Only a "MCU fault:" WARN carries real fault bits.
FAULTS=$(grep -c "MCU fault:" /tmp/buddy_realbridge.log || true)
check "no real MCU faults while commanding" "$([ "$FAULTS" = "0" ] && echo 1 || echo 0)" \
      "$FAULTS faults"
# The positive assertion: the ARM actually took effect on real silicon.
grep -q "MCU state -> ARMED" /tmp/buddy_realbridge.log && ARMED=1 || ARMED=0
check "MCU reached ARMED on real hardware" "$ARMED"

echo "== 4/5 stop the bridge, then interrogate the MCU directly =="
cleanup
sleep 3   # let the port be released and the 200 ms watchdog expire

RES=$(python3 - "$PORT" <<'PY'
import sys, os, time
sys.path.insert(0, os.path.expanduser(
    "~/Buddy_Robot/robot_ws/src/buddy_firmware_interfaces/python"))
import serial, buddy_protocol as bp
ser = serial.Serial(sys.argv[1], 921600, timeout=0.1)
parser = bp.Parser(); last = None
t_end = time.time() + 2.0
while time.time() < t_end:
    d = ser.read(4096)
    if d:
        for f in parser.feed(d):
            if f.type == bp.T_TELEMETRY:
                last = bp.Telemetry.unpack(f.payload)
ser.close()
if last is None:
    print("0|0|0|no-telemetry")
else:
    name = bp.STATE_NAMES[last.state] if last.state < len(bp.STATE_NAMES) else str(last.state)
    print(f"{last.cmd_seq_echo}|{last.state}|{last.fault_bits}|{name}")
PY
)
SEQ=$(echo "$RES" | cut -d'|' -f1)
STATE_N=$(echo "$RES" | cut -d'|' -f2)
BITS=$(echo "$RES" | cut -d'|' -f3)
SNAME=$(echo "$RES" | cut -d'|' -f4)

echo "== 5/5 what the MCU says happened =="
echo "   cmd_seq_echo=$SEQ  state=$SNAME  fault_bits=$BITS"
# cmd_seq_echo is the seq of the last ACCEPTED CMD_VEL. Non-zero proves the real
# MCU state machine accepted commands that originated as ROS /cmd_vel messages.
check "MCU accepted CMD_VEL from the bridge" \
      "$([ "${SEQ:-0}" -gt 0 ] 2>/dev/null && echo 1 || echo 0)" "cmd_seq_echo=$SEQ"
# With commands stopped the 200 ms watchdog must have stopped motion. The MCU
# reports this as the CMD_TIMEOUT fault bit (0x0002) - REQ_SAFE_002 on silicon.
TIMEOUT_BIT=$(( ${BITS:-0} & 2 ))
check "watchdog fired after commands stopped (REQ_SAFE_002)" \
      "$([ "$TIMEOUT_BIT" -ne 0 ] && echo 1 || echo 0)" \
      "fault_bits=0x$(printf '%04x' "${BITS:-0}") state=$SNAME"

echo
echo "passed: $PASS   failed: $FAIL"
[ "$FAIL" -eq 0 ] && echo "BRIDGE VERIFIED AGAINST REAL MCU" || echo "VERIFICATION FAILED"
exit "$FAIL"
