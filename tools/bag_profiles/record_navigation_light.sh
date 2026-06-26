#!/usr/bin/env bash
set -euo pipefail
mkdir -p bags
ros2 bag record -o "bags/nav_$(date +%Y%m%d_%H%M%S)" /tf /tf_static /odom /scan /cmd_vel /diagnostics
