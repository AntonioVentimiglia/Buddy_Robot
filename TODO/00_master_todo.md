# Master TODO

> Status: the robot model (`buddy_description`) and Gazebo sim (`buddy_simulation`)
> are wired up and runnable — see `robot_ws/SIMULATION_START_HERE.md`. Phases 2-3
> below are now about refining a working setup, not building it from scratch.

## Phase 0 - Requirements and assumptions

- [x] Fill `docs/requirements/buddy_v0_1_requirements.yaml` (canonical requirements file).
- [x] Decide indoor/outdoor/mixed operating environment (indoor, carpet + marble).
- [x] Decide speed, stopping distance, ramp angle, and runtime targets (see requirements yaml).
- [x] Estimate mass budget including growth (20 kg gross design limit).
- [x] Decide whether a robot arm is required for prototype v1 (no arm in v0.1).
- [ ] Create first hardware budget range.
- [ ] Create first safety envelope: people nearby, pets, supervised operation, speed limit.

## Phase 1 - Development baseline

- [ ] Select JetPack version after verifying current NVIDIA support for Jetson Orin Nano Super.
- [ ] Select ROS 2 baseline: Jazzy first unless a critical driver forces another distro.
- [ ] Install ROS 2 on Jetson or Linux development machine.
- [ ] Confirm `colcon build` works for package skeletons after stub files are completed or excluded.
- [ ] Set up VS Code Remote SSH from Mac/Windows host.
- [ ] Set up Foxglove/RViz visualization path.

## Phase 2 - Robot model

- [ ] Choose provisional chassis dimensions.
- [x] Wheel diameter locked: 96mm Hogback (ADR-0004). Track width still provisional.
- [x] Frame tree, wheels, LiDAR/camera/IMU/arm placeholders modeled (`buddy.urdf.xacro`). Validate in RViz.
- [x] Simple collision geometry present (boxes/cylinders).
- [x] Inertial placeholders auto-computed from mass/dims in xacro. Replace with measured values later.

## Phase 3 - Simulation

- [x] Gazebo world with differential drive wired up (`gazebo_lab.launch.py`).
- [x] Bridge configured for `/scan`, `/odom`, `/tf`, `/joint_states`, `/clock`, `/cmd_vel`.
- [ ] Teleop simulated robot (verify it drives).
- [ ] Run Nav2 in simulation.
- [ ] Record first simulated bag.

## Phase 4 - Hardware research and purchasing gate

- [x] Complete motor torque worksheet (`docs/research/hardware/motors_and_gearboxes/motor_sizing_and_selection.md`).
- [x] Shortlist + select motors — 4× goBILDA 5203 26.9:1 (ADR-0003). Purchase + BOM entry pending.
- [x] Select wheels — 4× goBILDA Hogback 96mm + 8mm REX hubs (ADR-0004; clearance requirement amended 0.05→0.038 m). Purchase + hub SKU verification pending.
- [ ] Complete power budget and battery sizing (`tools/calculators/battery_sizing.py`, blocked on motor decision).
- [ ] Shortlist motor drivers (4 brushed ch, ≥10 A peak, current sense), drive MCU (STM32G474 pre-selected, confirm after drivers), battery/BMS, 2D LiDAR, RGB-D camera, IMU.
- [ ] Score each hardware candidate (comparison table in each research doc, as in the motor sizing doc).
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
