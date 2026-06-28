# ROS 2 Workspace

This is the ROS 2 workspace for Buddy.

**Starting out? Read [`SIMULATION_START_HERE.md`](SIMULATION_START_HERE.md).** It is the
runbook for modeling in RViz, running Gazebo, and sizing motors with the torque tool.

Only three packages are wired up today: `buddy_description` (the robot model),
`buddy_simulation` (Gazebo), and the standalone `tools/torque_sweep.py`. The other
packages are scaffolds — see the reality-check table in the root `PROJECT_CONTEXT.md`.

Build:

```bash
cd robot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```
