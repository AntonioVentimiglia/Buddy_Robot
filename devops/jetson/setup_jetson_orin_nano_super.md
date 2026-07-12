# Jetson Orin Nano Super Setup

## Baseline assumption

- JetPack 7.x / Ubuntu 24.04 path when compatible with selected peripherals.
- ROS 2 Jazzy first.
- NVMe storage strongly preferred for bags, builds, and model files.

## First setup checklist

- [ ] Install/flash official Jetson image.
- [ ] Enable max appropriate power mode only after cooling is installed.
- [ ] Install NVMe and configure storage.
- [ ] Update packages.
- [ ] Install ROS 2 Jazzy.
- [ ] Install colcon, rosdep, vcs, build tools.
- [ ] Configure SSH keys.
- [ ] Configure `ROS_DOMAIN_ID`.
- [ ] Configure udev rules for MCU/sensors.
- [ ] Test camera, LiDAR, and MCU one at a time.
- [ ] Confirm thermal behavior under CPU/GPU load.
