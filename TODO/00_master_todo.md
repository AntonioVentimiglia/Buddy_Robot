# Master TODO

## Phase 0 - Requirements and assumptions

- [ ] Fill `docs/requirements/requirements(_IP).yaml`.
- [ ] Fill `docs/requirements/mission_profile(_IP).md`.
- [ ] Decide indoor/outdoor/mixed operating environment.
- [ ] Decide speed, acceleration, stopping distance, ramp angle, and runtime targets.
- [ ] Estimate mass budget including 20-30% future growth.
- [ ] Decide whether a robot arm is required for prototype v1.
- [ ] Create first hardware budget range.
- [ ] Create first safety envelope: people nearby, pets, supervised operation, speed limit.

## Phase 1 - Development baseline

- [ ] Select JetPack version after verifying current NVIDIA support for Jetson Orin Nano Super.
- [ ] Select ROS 2 baseline: Jazzy first unless a critical driver forces another distro.
- [ ] Install ROS 2 on Jetson or Linux development machine.
- [ ] Confirm `colcon build` works for package skeletons after incomplete `(_IP)` files are promoted or excluded.
- [ ] Set up VS Code Remote SSH from Mac/Windows host.
- [ ] Set up Foxglove/RViz visualization path.

## Phase 2 - Robot model

- [ ] Choose provisional chassis dimensions.
- [ ] Choose provisional wheel diameter and track width.
- [ ] Validate `base_link`, `base_footprint`, wheel frames, LiDAR frame, camera frames, and IMU frame in RViz.
- [ ] Create simple collision geometry.
- [ ] Add inertial placeholders and replace later with measured/calculated values.

## Phase 3 - Simulation

- [ ] Bring up Gazebo world with differential drive.
- [ ] Publish simulated `/scan`, `/odom`, `/tf`, `/joint_states`.
- [ ] Teleop simulated robot.
- [ ] Run Nav2 in simulation.
- [ ] Record first simulated bag.

## Phase 4 - Hardware research and purchasing gate

- [ ] Complete motor torque worksheet.
- [ ] Complete power budget and battery sizing.
- [ ] Shortlist motors, motor drivers, encoders, drive MCU, battery/BMS, 2D LiDAR, RGB-D camera, IMU.
- [ ] Score each candidate in `docs/hardware/hardware_scoring_matrix(_IP).md`.
- [ ] Reject any candidate with unclear power, mounting, modeling, communication, or safety behavior.

## Phase 5 - Electronics bench

- [ ] Build bench drive loop: MCU + motor driver + one motor + encoder.
- [ ] Verify encoder direction and scaling.
- [ ] Verify command watchdog stops motor.
- [ ] Verify E-stop removes motor enable/power.
- [ ] Log voltage/current under step command.

## Phase 6 - Rolling base

- [ ] Mount motors, encoders, battery, fuses, DC/DC rails, Jetson, drive MCU, E-stop.
- [ ] Add udev rules for stable device naming.
- [ ] Teleop at low speed.
- [ ] Verify odometry direction and scale.
- [ ] Verify diagnostics and bag profiles.

## Phase 7 - Real sensors and autonomy

- [ ] Mount 2D LiDAR and camera rigidly.
- [ ] Measure sensor extrinsics and update URDF.
- [ ] Validate scan and camera frame IDs/timestamps/rates.
- [ ] Map with SLAM Toolbox.
- [ ] Localize and navigate with Nav2 at conservative speed.

## Phase 8 - Manipulation path

- [ ] Decide whether arm is v1 or v2.
- [ ] If v1: choose ROS 2-supported arm and gripper.
- [ ] Validate arm on bench before mobile mounting.
- [ ] Update URDF/SRDF/MoveIt collision geometry.
