#!/usr/bin/env bash
# Buddy — zero-hardware drive stack verification on the Jetson.
#
# Proves the full Jetson-side chain with NO purchased hardware:
#   /cmd_vel -> buddy_base bridge -> real protocol bytes over a pty
#            -> mock MCU state machine + wheel model -> telemetry -> /odom
#
# This is the milestone check at the end of setup_ros2_jazzy.sh, run as a
# script instead of three hand-driven terminals so the result is repeatable
# and the pass/fail criteria are written down rather than eyeballed.
#
#   ./devops/jetson/verify_zero_hardware_stack.sh
#
# Exits non-zero if any check fails.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# ROS setup files read variables they never set; -u would make sourcing fatal.
set +u
source /opt/ros/jazzy/setup.bash
source "$REPO_ROOT/robot_ws/install/setup.bash"
set -u
export ROS_DOMAIN_ID=42

DRIVE_SPEED=0.2      # m/s commanded
DRIVE_SECONDS=3      # how long to drive
WATCHDOG_WAIT=1.5    # > 200 ms MCU watchdog (REQ_SAFE_002)
TOL=0.35             # fractional tolerance on distance (model, not metrology)

PASS=0; FAIL=0
check() { # name, condition
  if [ "$2" = "1" ]; then echo "ok   $1"; PASS=$((PASS+1));
  else echo "FAIL $1"; FAIL=$((FAIL+1)); fi
}

# `ros2 topic echo` writes operational chatter to STDOUT, not stderr - notably
# "A message was lost!!!" when DDS drops a sample, which happens once the box is
# busy (e.g. the real MCU streaming telemetry at 100 Hz alongside this test).
# Taking `head -1` blindly captures that text as the measurement and reports a
# failure that is purely a parsing artefact. Filter to a numeric line instead.
odom_field() {
  timeout 10 ros2 topic echo /odom --once --field "$1" 2>/dev/null \
    | grep -E '^[-+]?[0-9]+\.?[0-9]*([eE][-+]?[0-9]+)?$' | head -1
}

cleanup() {
  pkill -f "[m]ock_mcu.py" 2>/dev/null || true
  pkill -f "[b]ase.launch.py" 2>/dev/null || true
  pkill -f "[r]os2 topic pub" 2>/dev/null || true
}
trap cleanup EXIT
cleanup; sleep 1

echo "== 1/5 start mock MCU =="
rm -f /tmp/buddy_mock.log /tmp/buddy_bridge.log
# -u matters: with stdout redirected to a file Python block-buffers, so the
# "mock MCU on /dev/pts/N" line never reaches the log and the pty is unreadable.
setsid nohup python3 -u robot_ws/src/buddy_firmware_interfaces/python/mock_mcu.py \
  > /tmp/buddy_mock.log 2>&1 < /dev/null &
sleep 3
PTY=$(grep -o '/dev/pts/[0-9]*' /tmp/buddy_mock.log | head -1)
echo "   pty: ${PTY:-NONE}"
check "mock MCU allocated a pty" "$([ -n "$PTY" ] && echo 1 || echo 0)"
[ -n "$PTY" ] || { echo "cannot continue without a pty"; cat /tmp/buddy_mock.log; exit 1; }

echo "== 2/5 start buddy_base bridge =="
setsid nohup ros2 launch buddy_bringup base.launch.py \
  port:="$PTY" auto_arm:=true > /tmp/buddy_bridge.log 2>&1 < /dev/null &
sleep 10
TOPICS=$(ros2 topic list 2>/dev/null)
echo "$TOPICS" | grep -q "^/odom$"    && O=1 || O=0
echo "$TOPICS" | grep -q "^/cmd_vel$" && C=1 || C=0
check "/odom advertised"    "$O"
check "/cmd_vel subscribed" "$C"
if [ "$O" != "1" ]; then echo "--- bridge log ---"; tail -30 /tmp/buddy_bridge.log; exit 1; fi

echo "== 3/5 odometry starts at rest =="
X0=$(odom_field pose.pose.position.x)
X0=${X0:-unset}
echo "   x0 = $X0"
check "/odom publishing" "$([ "$X0" != "unset" ] && echo 1 || echo 0)"

echo "== 4/5 drive forward ${DRIVE_SPEED} m/s =="
# Measure STEADY-STATE speed, not distance over the whole window. Node startup,
# DDS discovery, the SAFE_IDLE->ARMED->ACTIVE transition and the mock's wheel-model
# ramp all land in the first ~1 s; integrating across them under-reports by ~35%
# and says nothing about whether the stack tracks the commanded velocity.
setsid nohup ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: $DRIVE_SPEED}, angular: {z: 0.0}}" > /dev/null 2>&1 < /dev/null &
sleep 2.5   # let startup + ramp settle before sampling

VEL=$(odom_field twist.twist.linear.x)
VEL=${VEL:-0}
echo "   reported steady-state velocity: $VEL m/s (commanded $DRIVE_SPEED)"

# Independent cross-check: distance over a timed window that excludes startup.
TA=$(date +%s.%N); XA=$(odom_field pose.pose.position.x)
sleep "$DRIVE_SECONDS"
TB=$(date +%s.%N); XB=$(odom_field pose.pose.position.x)
pkill -f "[r]os2 topic pub" 2>/dev/null || true

MEAS=$(python3 -c "
dx = ${XB:-0} - ${XA:-0}; dt = ${TB:-1} - ${TA:-0}
print(round(dx/dt, 4) if dt > 0 else 0)")
echo "   measured over window: $MEAS m/s"
sleep "$WATCHDOG_WAIT"
X1=$(odom_field pose.pose.position.x)
X1=${X1:-0}

MOVED=$(python3 -c "print(1 if abs($X1 - $X0) > 0.05 else 0)" 2>/dev/null || echo 0)
FWD=$(python3 -c "print(1 if ($X1 - $X0) > 0 else 0)" 2>/dev/null || echo 0)
VOK=$(python3 -c "print(1 if abs($VEL - $DRIVE_SPEED) <= $DRIVE_SPEED * $TOL else 0)" 2>/dev/null || echo 0)
MOK=$(python3 -c "print(1 if abs($MEAS - $DRIVE_SPEED) <= $DRIVE_SPEED * $TOL else 0)" 2>/dev/null || echo 0)
check "odometry advanced"                        "$MOVED"
check "direction is forward (+x)"                "$FWD"
check "reported velocity tracks command"         "$VOK"
check "measured velocity tracks command"         "$MOK"

echo "== 5/5 watchdog stopped the wheels =="
X2=$(odom_field pose.pose.position.x)
sleep 1.5
X3=$(odom_field pose.pose.position.x)
STOPPED=$(python3 -c "print(1 if abs(${X3:-0} - ${X2:-0}) < 0.01 else 0)" 2>/dev/null || echo 0)
echo "   x2 = ${X2:-?}   x3 = ${X3:-?}  (commands stopped; watchdog should hold position)"
check "no motion after command timeout (REQ_SAFE_002)" "$STOPPED"

echo
echo "passed: $PASS   failed: $FAIL"
[ "$FAIL" -eq 0 ] && echo "ZERO-HARDWARE DRIVE STACK VERIFIED" || echo "VERIFICATION FAILED"
exit "$FAIL"
