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
- [x] Create first hardware budget range. **$2000 programme budget**, split into
  v0.1 / future-phase pots with tooling tracked separately — `design_conflicts.md` #4
  (revised 2026-07-31).
- [ ] Create first safety envelope: people nearby, pets, supervised operation, speed limit.

## Phase 1 - Development baseline

- [x] Select JetPack version after verifying current NVIDIA support for Jetson Orin Nano Super.
- [x] Select ROS 2 baseline: Jazzy first unless a critical driver forces another distro.
- [x] **Install ROS 2 on the Jetson** — done 2026-07-31 via
  `devops/jetson/setup_ros2_jazzy.sh`, driven over SSH. Zero-hardware milestone
  verified: `devops/jetson/verify_zero_hardware_stack.sh` passes 9/9.
- [x] Confirm `colcon build` works — 3 packages build on the Jetson in 5.5 s.
- [ ] Set up VS Code Remote SSH from Mac/Windows host.
- [ ] Set up Foxglove/RViz visualization path.

## Phase 2 - Robot model

- [x] Fabrication method locked: **in-house FDM printing** (ADR-0008, QIDI Plus 4).
  Chassis CAD must follow printed-part design rules — print orientation on load
  paths, metal inserts at bearing/fastener interfaces, ASA/PA-CF on structure.
- [ ] Choose provisional chassis dimensions. **Constraint from ADR-0008:**
  305 × 305 mm bed, effective heated Z ~268 mm — parts above 280 mm must be split.
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
- [x] Complete power budget and battery sizing (`docs/analysis/power_budget_and_battery.md`, ADR-0005: 3S Li-ion ≥8 Ah, BMS ≥40 A, driver limit 8 A/motor). Battery SKU purchase pending.
- [x] Shortlist motor drivers — 4× Pololu VNH5019 recommended (12 A/30 A, current sense → 8 A firmware limit on G474); alternates documented. Purchase pending.
- [x] Confirm drive MCU: NUCLEO-G474RE (VNH5019 telemetry/PWM needs match the G474 exactly; dual-VNH5019 shield stacks on it for bench phase).
- [ ] **BUY: work through `docs/financials/SHOPPING_LIST_v0_1.md` (~$540), then update BOM, flip ADR-0003/4/5 to Accepted, delete the list.**
- [x] Select sensors (ADR-0007, phased): LD19 LiDAR + BNO086 IMU now (+$90); OAK-D Lite selected, deferred to perception phase. Reserves hold — no power amendment.
- [ ] Score each hardware candidate (comparison table in each research doc, as in the motor sizing doc).
- [ ] Reject any candidate with unclear power, mounting, modeling, communication, or safety behavior.

## Phase 4.5 - Pre-bench software (done while parts ship)

- [x] Decide MCU↔Jetson bus: USB serial via ST-LINK VCP (ADR-0006; CAN-FD reserved).
- [x] Drive protocol v1: wire spec + C and Python implementations, golden-vector
  cross-checked; mock MCU with state machine + watchdog (`tools/run_protocol_tests.sh`).
- [x] Pin map for NUCLEO-G474RE (4× encoder timers, TIM1 PWM, CS ADC, faults, E-stop).
- [x] Firmware skeleton compiles (PlatformIO, 16 kB): host-tested safety state
  machine, HAL layer, constants generated from `design_params.yaml`.
- [x] Jetson-side bridge node (`buddy_base`): core host-tested (13 tests incl. end-to-end vs mock MCU); thin rclpy shell + real base.launch.py ready for the Jetson.
- [x] System integration drawn and machine-checked (M03): six generated figures
  indexed from `docs/system_model/system_integration.md`, topology in
  `integration_map.yaml`, drift checker wired into `tools/build.py`, second KiCAD
  sheet (`system_wiring`) for power distribution + Jetson/sensor interconnect.
- [ ] Velocity PID + mid-pulse current sampling (bench phase, needs motors).

## Phase 5 - Electronics bench

- [x] **Flash the drive MCU and verify the Jetson↔MCU link** (2026-07-31).
  `tools/flash/flash_drive_mcu.sh`; `devops/jetson/verify_drive_mcu_link.py`
  passes 13/13 — 102 Hz telemetry, 0 CRC errors, SAFE_IDLE, PING/PONG 10/10,
  0.49 ms median round trip vs the 200 ms watchdog.
- [x] **Run the bridge against the real MCU** (2026-07-31).
  `devops/jetson/verify_bridge_vs_real_mcu.sh` 13/13: real telemetry into
  `/odom`/`/joint_states`/`/battery_state`, auto-arm off genuine MCU state,
  `cmd_seq_echo=71` (ROS `/cmd_vel` accepted by real silicon), watchdog fired.
  Found and fixed a latched-CMD_TIMEOUT firmware bug in the process.
- [x] **`HAL_UART_ErrorCallback` added** (2026-08-01) — re-arms
  `HAL_UART_Receive_IT` after a blocking error. Narrower than originally filed:
  per the G4 HAL source only **ORE/RTO** abort reception (FE/NE/PE self-recover),
  and ORE could not be provoked from the host — a 128 kB flood at line rate never
  overran the ISR. Insurance against on-board causes (long ISR, critical section,
  motor EMI), not a repair of an observed failure.
  Check: `devops/jetson/verify_uart_error_recovery.py`.
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
