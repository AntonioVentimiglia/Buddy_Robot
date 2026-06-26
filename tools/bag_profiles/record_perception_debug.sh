#!/usr/bin/env bash
set -euo pipefail
mkdir -p bags
ros2 bag record -o "bags/perception_$(date +%Y%m%d_%H%M%S)" /tf /tf_static /scan /camera/color/image_raw /camera/depth/image_rect_raw /camera/color/camera_info /diagnostics
