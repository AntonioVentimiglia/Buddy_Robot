# Buddy ROS 2 Robot Master Repository

This is the starter GitHub repository for **Buddy**, an autonomous ROS 2 robot using a **Jetson Orin Nano Super**, a **four-wheel differential-drive base**, **2D LiDAR**, and an **RGB-D camera**. It is designed to survive hardware changes while keeping the ROS 2 interfaces, frame tree, simulation, documentation, tests, firmware contracts, and deployment workflow organized from day one.

The root-level source of truth for future AI prompts is:

- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md)

Every structural change to this repository should update `PROJECT_CONTEXT.md` and the affected folder `README.md` files.

## Current design baseline

| Area | Baseline |
|---|---|
| Robot name | Buddy |
| Compute | NVIDIA Jetson Orin Nano Super |
| Robot OS target | Ubuntu 24.04 / JetPack 7.x path unless a selected driver forces another choice |
| ROS 2 target | ROS 2 Jazzy first; keep migration notes for Lyrical |
| Drive | Four-wheel differential drive / skid-differential style with left and right wheel groups |
| Sensors | 2D LiDAR, RGB-D camera, IMU, wheel encoders |
| Low-level control | Dedicated drive MCU; Linux/ROS requests motion but MCU enforces watchdog and safety |
| Navigation | Nav2, SLAM Toolbox or AMCL, robot_localization EKF |
| Simulation | Gazebo first; optional Isaac Sim/Isaac ROS path for NVIDIA acceleration |
| Future manipulation | Leave MoveIt 2-compatible arm placeholder until arm is selected |

## How to use this repository first

1. Read `PROJECT_CONTEXT.md`.
2. Fill `TODO/01_clarifications_needed.md` and `docs/requirements/requirements(_IP).yaml`.
3. Review `docs/system_model/frame_tree.md` and `robot_ws/src/buddy_description/urdf/`.
4. Choose a ROS 2 + JetPack baseline in `docs/decisions/ADR-0001-ros2-jetpack-baseline(_IP).md`.
5. Start simulation before buying major hardware.

## Naming rule for incomplete artifacts

Files ending in `(_IP)` are intentionally **in progress**. When a file becomes a real contract or build artifact, remove `(_IP)` from the filename and update:

- `PROJECT_CONTEXT.md`
- The local folder `README.md`
- Any TODO files that mention the artifact
- Any launch/build references

## Repository map

```text
buddy_ros2_robot/
  PROJECT_CONTEXT.md              Canonical AI/project context
  TODO/                           Next steps, clarifications, milestone plans
  docs/                           Architecture, requirements, interfaces, power, safety, decisions
  research/                       Hardware/software research workspaces
  robot_ws/                       ROS 2 workspace skeleton
  firmware/                       MCU firmware architecture and starter scaffolds
  devops/                         Jetson setup, containers, systemd, udev, OTA, networking
  tools/                          Calculators, helper scripts, bag profiles, checkers
  assets/                         Diagrams, drawings, images, CAD export placeholders
```

## Important safety stance

The software here is a development scaffold, not a certified safety system. Physical E-stop, motor enable interruption, power fusing, current limits, watchdogs, and commissioning procedures must be implemented and tested before autonomous operation.
