# Buddy simulation start file

This workspace is intentionally reduced to the files needed to start modeling and torque testing.

Use only these packages first:

- `buddy_description`: URDF/Xacro model for RViz.
- `buddy_simulation`: Gazebo Harmonic world and SDF model.
- `buddy_bringup`: later integration launch files.
- `tools`: engineering calculators that do not require ROS.

Ignore these for now: `buddy_navigation`, `buddy_perception`, `buddy_manipulation`, `buddy_mission`, `buddy_diagnostics`, `buddy_operator`, `buddy_tests`, and `buddy_firmware_interfaces`.

## Assumed v0.1 geometry

All of these live in ONE file — `src/buddy_description/urdf/buddy_params.xacro`.
Edit there and RViz, Gazebo physics, and the diff-drive plugin all update together.

- Four-wheel differential / skid-steer layout.
- Body box: 0.28 m long, 0.22 m wide, 0.10 m tall.
- Wheel radius: 0.06 m, width 0.035 m.
- Wheelbase: 0.18 m (front-to-rear centers). Track width: 0.26 m (left-to-right centers).
- Gross mass for torque calculations: start with 30 kg = 20 kg robot + 10 kg payload.

> Reality note: a 0.28 m body at 30 kg gross is physically very dense and is almost
> certainly a placeholder that's too small. It's kept only because the sim and torque
> defaults already used it. When you pick real chassis dimensions, change them in
> `buddy_params.xacro` (the single source) — nothing else needs editing.

## Install the simulation dependencies on Ubuntu 24.04 + ROS 2 Jazzy

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-rviz2 \
  ros-jazzy-ros-gz \
  ros-jazzy-teleop-twist-keyboard
```

## Build

```bash
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## First modeling test: RViz only

```bash
ros2 launch buddy_description view_model.launch.py
```

You should see the base, four wheels, 2D LiDAR frame, RGB-D camera frame, optical frame, IMU frame, and placeholder arm mount.

## First physics test: Gazebo teleop

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

Terminal 3, verify simulated topics:

```bash
ros2 topic list
ros2 topic echo /odom --once
ros2 topic echo /scan --once
```

## Torque sweep

This does not require ROS:

```bash
cd ~/robot_ws
python3 tools/torque_sweep.py --mass-kg 30 --wheel-radius-m 0.06 --driven-wheels 4 --speed-mps 1.5 --ramp-deg 20
```

For two side motors instead of four individual wheel motors:

```bash
python3 tools/torque_sweep.py --mass-kg 30 --wheel-radius-m 0.06 --driven-wheels 2 --speed-mps 1.5 --ramp-deg 20
```

Use this workflow before buying motors:

1. Change wheel radius.
2. Change mass.
3. Change ramp angle.
4. Compare torque per motor and wheel RPM.
5. Only shortlist motors that beat the calculated continuous torque and RPM with margin.
