# First 30 Days Plan

## Week 1 - Repository and requirements

- Read `PROJECT_CONTEXT.md`.
- Answer at least the first 15 clarifications in `01_clarifications_needed.md`.
- Fill `docs/requirements/requirements(_IP).yaml`.
- Fill `docs/requirements/mission_profile(_IP).md`.
- Select first software baseline in `docs/decisions/ADR-0001-ros2-jetpack-baseline(_IP).md`.
- Set up GitHub repository and commit this scaffold.

## Week 2 - Robot description

- Edit `robot_ws/src/buddy_description/urdf/buddy_params.xacro` with provisional dimensions (this is the single source of truth).
- Confirm the frame tree in RViz: `ros2 launch buddy_description view_model.launch.py`.
- LiDAR, camera, IMU, and arm placeholders are already wired in.

## Week 3 - Simulation

- Promote simulation launch files when ready by removing `(_IP)` from filenames.
- Bring up Gazebo with differential drive.
- Publish `/tf`, `/odom`, `/scan`, `/joint_states`.
- Teleop the simulated robot.
- Record first simulation bag.

## Week 4 - Hardware shortlist

- Use `robot_ws/tools/torque_sweep.py` (canonical, CLI) and `tools/calculators/battery_sizing(_IP).py`.
- Fill research notes for motors, motor drivers, MCU, LiDAR, camera, IMU, battery, chassis.
- Complete hardware scoring matrix.
- Do not buy high-cost parts until torque, power, mounting, driver support, and safety behavior are checked.
