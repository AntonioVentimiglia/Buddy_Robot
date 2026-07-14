# Buddy Project Context for AI Prompts

**Last updated:** 2026-07-11

> This is the single canonical context file. Paste it into any AI prompt to
> orient it. The only other top-level doc you need is the runbook
> `robot_ws/SIMULATION_START_HERE.md`. (The old `MANIFEST.md` file index was
> deleted — it went stale instantly and duplicated this file.)

## 0. Reality check — what actually exists today

The package list in section 6 is the *intended* architecture. As of this writing
only a few packages have working content; the rest are empty scaffolds. Do not
assume a package does anything until you have opened it.

| Package | State |
|---|---|
| `buddy_description` | **Working.** Single URDF entry `buddy.urdf.xacro`; geometry in `buddy_params.xacro`; loads in RViz. |
| `buddy_simulation` | **Working.** `gazebo_lab.launch.py` spawns the URDF in Gazebo (diff drive + 2D LiDAR), no separate SDF. |
| `tools` (`robot_ws/tools/torque_sweep.py`) | **Working.** Standalone torque/RPM sizing, no ROS needed. |
| `buddy_base` | Skeleton. `ros2_control` hardware interface is a stub (transport now decided: USB serial, ADR-0006 — bridge node is the next software task, developed against `mock_mcu.py`). |
| `buddy_bringup` | Skeleton. Launch files are stubs (marked `WIP:` in-file). |
| `buddy_firmware_interfaces` | **Working (host-tested).** Drive protocol v1 spec + Python implementation + mock MCU (`python/`); golden-vector cross-checked against the C implementation. Run all tests: `tools/run_protocol_tests.sh`. |
| `firmware/drive_mcu` (not a ROS pkg) | **Compiles** for NUCLEO-G474RE via PlatformIO (16 kB flash): pure-C safety state machine (host-tested), HAL layer per `docs/pin_map.md`, constants generated from `design_params.yaml` (`include/buddy_config.h`). Velocity PID + mid-pulse current sampling are bench-phase TODOs. |
| `buddy_navigation`, `buddy_perception`, `buddy_manipulation`, `buddy_mission`, `buddy_diagnostics`, `buddy_operator`, `buddy_tests` | **Deleted 2026-07-11.** They were empty scaffolds full of stub files that only added noise. Recreate each package (`ros2 pkg create`) when its build phase is actually reached; the intended responsibilities are listed in section 6. |

**To start working right now:** read `robot_ws/SIMULATION_START_HERE.md`. Design
values are changed in exactly one file: `design_params.yaml` at the repo root,
followed by `python3 tools/build.py` (regenerates the URDF params file, analysis
docs, figures, and CSV together). `buddy_params.xacro` is a **generated file** —
never edit it directly.

Buddy v0.1 is an indoor autonomous mobile base using:
- Jetson Orin Nano Super
- ROS 2 Jazzy
- four-wheel differential/skid-steer geometry
- 2D LiDAR
- RGB-D camera
- wheel encoders
- IMU
- no arm in v1
- no autonomous charging dock in v1
- no high-speed autonomous operation in v1

## 1. Project identity

- Project name: **Buddy**
- Repository purpose: master ROS 2 design/development repository for an autonomous mobile robot.
- Current hardware choices already made:
  - Main compute: **NVIDIA Jetson Orin Nano Super**.
  - Drive style: **four-wheel differential drive** with left/right wheel groups.
  - Primary navigation sensor: **2D LiDAR**.
  - Primary vision sensor: **RGB-D camera**.
  - Drive motors: **4× goBILDA 5203 Yellow Jacket 26.9:1** (proposed, ADR-0003; buy pending).
  - Wheels: **4× goBILDA Hogback 96 mm + 8 mm REX hubs** (proposed, ADR-0004; buy pending.
    Ground-clearance requirement amended 0.05 → 0.038 m as part of this decision).
  - Power architecture: **3S Li-ion + BMS ≥ 50 A, ≥ 14 Ah, driver current limit
    8 A/motor, 60 A main fuse** (proposed, ADR-0005 as amended 2026-07-14: battery
    sized for the future dual 6-DOF arm version so the v0.1 purchase isn't wasted.
    Camera/LiDAR carry ≤ 5 W reserved allocations as selection constraints).
  - Motor drivers: **4× Pololu VNH5019** (recommended; 8 A firmware limit on the
    G474 from current-sense — see `driver_selection.md`). Drive MCU confirmed:
    **NUCLEO-G474RE**. Purchases pending: `docs/financials/SHOPPING_LIST_v0_1.md`.
  - MCU↔Jetson bus: **USB serial via ST-LINK VCP** (ADR-0006; CAN-FD reserved
    for the arm era). Drive protocol v1 specified + implemented + host-tested.
- Major hardware still undecided:
  - Exact battery SKU (spec locked by amended ADR-0005: 3S ≥ 14 Ah, BMS ≥ 50 A).
  - 2D LiDAR, RGB-D camera (≤ 5 W reserves each), IMU.
  - Chassis dimensions, track width, suspension/skid behavior.
  - Exact 2D LiDAR model and RGB-D camera model.
  - IMU model and mounting.
  - Robot arm type, gripper, payload, mounting, and whether manipulation is an early or later milestone.

## 2. Architectural north star

Buddy is a distributed robot system:

```text
Operator/dev tools
  -> SSH / VS Code Remote / Foxglove / RViz / ros2 CLI / CI
Jetson Orin Nano Super running Linux + ROS 2
  -> bringup, robot_state_publisher, tf2, Nav2, localization, perception, diagnostics, logging, mission logic
Hardware bridge layer
  -> ros2_control hardware interface, CAN/serial bridge, or micro-ROS agent
Embedded layer
  -> drive MCU, power monitor MCU, motor driver control, encoder acquisition, watchdogs, E-stop state
Physical layer
  -> motors, encoders, motor drivers, battery/BMS, 2D LiDAR, RGB-D camera, IMU, future arm
```

The Jetson runs high-level autonomy and data processing. It **does not** own hard real-time motor safety. The drive MCU must stop motion when commands become stale, when E-stop is active, or when critical power/driver faults appear.

## 3. Software baseline

Preferred current baseline:

- Jetson path: JetPack 7.x / Ubuntu 24.04 if compatible with selected peripherals.
- ROS 2 path: ROS 2 Jazzy first.
- Keep repository design clean enough to evaluate ROS 2 Lyrical later.
- Simulation: Gazebo first, with optional Isaac Sim/Isaac ROS branch for GPU-heavy perception.
- Development hosts:
  - macOS: VS Code Remote SSH into Jetson/Linux dev box; Docker for non-hardware work.
  - Windows: VS Code Remote SSH and WSL2 for local ROS CLI experiments.
  - Linux desktop/laptop: preferred full-stack dev/simulation environment.

## 4. ROS graph target

Core ROS concepts to preserve:

- `/cmd_vel`: high-level velocity command from Nav2 or teleop to base controller.
- `/odom`: odometry from base/odometry estimator.
- `/scan`: 2D LiDAR LaserScan.
- RGB-D camera topics under `/camera/...` once the model is chosen.
- `/tf` and `/tf_static`: canonical transform tree.
- `/diagnostics`: every hardware-facing node reports health.
- `/battery_state`: power telemetry.
- Nav2 actions such as `/navigate_to_pose`.
- Future MoveIt 2 action path: `/arm_controller/follow_joint_trajectory`.

## 5. Frame tree contract

Initial frame tree:

```text
map
  -> odom
    -> base_footprint
      -> base_link
        -> left_front_wheel_link
        -> left_rear_wheel_link
        -> right_front_wheel_link
        -> right_rear_wheel_link
        -> base_laser
        -> front_camera_link
          -> front_camera_optical_frame
        -> imu_link
        -> arm_base_link  # placeholder until arm selected
```

Frame changes must update:

- `docs/system_model/frame_tree.md`
- `design_params.yaml` (dimensions — regenerates `buddy_params.xacro` via `tools/build.py`) and the relevant macro file
- `robot_ws/src/buddy_description/config/frames.yaml`
- `robot_ws/src/buddy_description/urdf/buddy.gazebo.xacro` (sim sensor frames)
- Calibration notes

## 6. Package strategy

ROS workspace path: `robot_ws/`. This is the **intended** package layout — see
section 0 for which packages actually exist today (most placeholder packages were
deleted 2026-07-11 and will be recreated when reached).

Packages:

- `buddy_description`: URDF/Xacro, meshes, frames, RViz.
- `buddy_bringup`: top-level launch and parameters.
- `buddy_base`: base controller, hardware interface, bridge skeletons.
- `buddy_firmware_interfaces`: MCU protocol, messages, services, schema docs.
- `buddy_navigation`: Nav2, SLAM/localization, maps, behavior trees.
- `buddy_perception`: 2D LiDAR + RGB-D camera pipelines, detection placeholders.
- `buddy_simulation`: Gazebo worlds and sim launch files.
- `buddy_manipulation`: MoveIt 2 placeholder package until arm selected.
- `buddy_diagnostics`: health aggregation and dashboards.
- `buddy_mission`: task/behavior orchestration beyond Nav2.
- `buddy_tests`: launch tests, bag replay tests, sim scenarios, hardware smoke tests.
- `buddy_operator`: operator UI/dashboard notes and future UI nodes.

## 7. Repository conventions

- Draft/unverified files carry a one-line `WIP:` note at the top of the file, not a
  filename suffix. (The old `(_IP)` filename convention was removed 2026-07-11: it
  made paths hard to reference and silently broke any code that loaded a file whose
  name later changed.) A topic is "settled" when it has an ADR in `docs/decisions/`.
- **Parametric build (single source of truth):** all design choices and
  assumptions live in `design_params.yaml`; requirements live in
  `docs/requirements/buddy_v0_1_requirements.yaml`; no value may exist in both.
  `python3 tools/build.py` regenerates from them: `buddy_params.xacro`
  (generated — never hand-edit), the analysis notebooks' markdown exports,
  all figures, and the torque sweep CSV. `buddy_calcs/` is the shared loader +
  equation module every consumer imports. Derivation documents are **marimo
  notebooks** (`docs/analysis/*.py`, edit live with `marimo edit <file>`); their
  committed `.md` exports are generated artifacts.
- The robot model has exactly one entry point: `buddy.urdf.xacro`. All dimensions
  flow from `design_params.yaml` through the generated `buddy_params.xacro`.
  There is no separate Gazebo SDF — the sim spawns this URDF. Do not reintroduce
  a parallel model file.
- Folder-level context lives in `README.md` only where a folder has real content or a
  non-obvious convention. Empty scaffold folders intentionally have no README (the
  ~90 placeholder stubs were removed as noise).
- Design decisions live in `docs/decisions/` as ADRs.
- **Portfolio system** (`docs/portfolio/` — see its README): every working session
  gets a dated engineering-log entry (`log/YYYY-MM.md`); every completed phase gets
  an illustrated milestone report (`milestones/Mxx-*.md`); every figure is generated
  by a script in `tools/figures/` (figures-as-code — no hand-made charts); physical
  evidence (photos/traces/test data) is captured same-day in
  `assets/evidence/YYYY-MM-DD_slug/`. The future project website is generated from
  these docs, so their frontmatter/structure is a contract.
- **Calculations are derivations, not results** (`docs/analysis/`, one doc per
  calculation domain): governing equations from first principles with an FBD where
  forces are involved, symbol table with units, numeric substitution checkable by
  hand, units check, and limits of validity. Research docs and milestones cite the
  analysis doc rather than restating math. First instance:
  `docs/analysis/drive_torque_and_pivot_scrub.md`.
- Hardware research lives in `docs/research/`, not scattered through ROS packages.
  Research folders are created **when research actually starts** — the old tree of
  ~19 empty README/notes template pairs was deleted 2026-07-11. Requirements live in
  `docs/requirements/buddy_v0_1_requirements.yaml` (single canonical file; the older
  duplicate `requirements.yaml` and `mission_profile.md` were merged away).
- Build/deploy automation lives in `devops/` and `tools/`.
- Do not hard-code final hardware values until verified by measurement or selected part datasheets.

## 8. Build philosophy

Design in layers:

1. Requirements and system model.
2. URDF/Xacro and frame tree.
3. Simulation base with differential drive and sensors.
4. Nav2 in simulation.
5. Electronics bench: MCU + motor driver + encoder + E-stop.
6. Rolling base teleop.
7. Real sensors and calibration.
8. Real Nav2 autonomy.
9. Arm bench.
10. Arm on base.
11. Perception task.
12. Integrated autonomous behavior.

## 9. Current highest-priority unknowns

Resolve these before buying major hardware:

1. Indoor/outdoor environment and terrain.
2. Target total mass and payload growth margin.
3. Desired speed, acceleration, stopping distance, and ramp angle.
4. Runtime target and charging strategy.
5. Budget range.
6. Maximum robot footprint and height.
7. Whether the arm is required for the first prototype.
8. Required arm payload/reach/precision if manipulation matters.
9. 2D LiDAR range/FOV/indoor-outdoor constraints.
10. RGB-D camera range, lighting, and mounting constraints.
11. Preferred low-level bus: CAN/CAN-FD, RS485, USB serial, or micro-ROS transport.
12. Safety envelope: people/pets nearby, autonomous area, remote operation rules.

## 10. Update rule

When adding, deleting, renaming, or promoting any file:

1. Update this file if the architecture, package list, core assumptions, or workflows change.
2. Update the relevant folder README.
3. Update `TODO/00_master_todo.md` if work status changes.
4. Add or update an ADR when the change locks in a major decision.
