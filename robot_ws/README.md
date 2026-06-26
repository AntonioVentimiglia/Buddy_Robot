# ROS 2 Workspace

This is the ROS 2 workspace for Buddy. The package layout is designed so simulation, hardware, perception, navigation, manipulation, diagnostics, and mission logic can evolve independently.

Build intent:

```bash
cd robot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Many starter files are marked `(_IP)`, so the first build may require promoting or excluding unfinished files. That is intentional: incomplete code/config is visibly marked.
