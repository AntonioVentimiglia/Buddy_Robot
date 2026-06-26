#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/jazzy/setup.bash
source "$HOME/robot_ws/install/setup.bash"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}"
ros2 launch buddy_bringup robot.launch.py
