#!/usr/bin/env bash
# Buddy — ROS 2 Jazzy bring-up on the Jetson Orin Nano (Ubuntu 24.04, arm64).
# Idempotent: safe to re-run. Takes ~15-30 min mostly waiting on apt.
#
#   git clone <this repo> ~/Buddy_Robot     (or pull latest)
#   cd ~/Buddy_Robot && ./devops/jetson/setup_ros2_jazzy.sh
#
# Afterwards, prove the whole drive stack with ZERO purchased hardware:
#   Terminal A:  python3 robot_ws/src/buddy_firmware_interfaces/python/mock_mcu.py
#   Terminal B:  ros2 launch buddy_bringup base.launch.py port:=<pty from A> auto_arm:=true
#   Terminal C:  ros2 run teleop_twist_keyboard teleop_twist_keyboard
#                ros2 topic echo /odom     <- odometry moves as you "drive"
set -euo pipefail

echo "== 1/6 locale + apt sources =="
sudo apt update && sudo apt install -y locales curl gnupg lsb-release software-properties-common
sudo locale-gen en_US en_US.UTF-8
sudo add-apt-repository -y universe
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F tag_name | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo "$VERSION_CODENAME")_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

echo "== 2/6 ROS 2 Jazzy + tools =="
sudo apt update
sudo apt install -y ros-jazzy-ros-base ros-dev-tools python3-colcon-common-extensions \
  python3-rosdep python3-serial python3-yaml \
  ros-jazzy-teleop-twist-keyboard ros-jazzy-tf2-ros ros-jazzy-robot-state-publisher \
  ros-jazzy-xacro ros-jazzy-joint-state-publisher
sudo rosdep init 2>/dev/null || true
rosdep update

echo "== 3/6 environment =="
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
grep -q "ros/jazzy/setup.bash" ~/.bashrc || {
  echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
  echo "export ROS_DOMAIN_ID=42   # keep fixed per network_plan.md" >> ~/.bashrc
  echo "[ -f $REPO_ROOT/robot_ws/install/setup.bash ] && source $REPO_ROOT/robot_ws/install/setup.bash" >> ~/.bashrc
}
# ROS's setup.bash reads variables it never sets (AMENT_TRACE_SETUP_FILES,
# AMENT_CURRENT_PREFIX, ...). Under `set -u` that is fatal, so the script died
# here on first real run. Relax -u for the sourcing only, then restore it.
set +u
source /opt/ros/jazzy/setup.bash
set -u

echo "== 4/6 udev rule (stable MCU device name) =="
sudo cp "$REPO_ROOT/devops/udev/99-buddy-robot.rules" /etc/udev/rules.d/ 2>/dev/null || true
sudo udevadm control --reload-rules || true

echo "== 5/6 host-side tests (no hardware, no ROS needed) =="
"$REPO_ROOT/tools/run_protocol_tests.sh"

echo "== 6/6 build the workspace =="
cd "$REPO_ROOT/robot_ws"
colcon build --symlink-install --packages-select buddy_base buddy_bringup buddy_description
set +u  # same unbound-variable issue as above
source install/setup.bash
set -u

echo
echo "DONE. Try the zero-hardware drive stack (see header of this script)."
