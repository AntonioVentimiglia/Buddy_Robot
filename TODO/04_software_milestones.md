# Software Milestones

## M0 - Empty workspace builds

- [ ] `colcon build` succeeds after incomplete files are excluded or promoted.
- [ ] `pre-commit` passes.
- [ ] CI action runs on GitHub.

## M1 - Description and visualization

- [ ] URDF/Xacro renders in RViz.
- [ ] Frame tree matches `docs/system_model/frame_tree.md`.
- [ ] Wheel rotations are represented correctly.

## M2 - Simulated base

- [ ] Gazebo loads model.
- [ ] Differential drive plugin/controller publishes `/odom`.
- [ ] Simulated LiDAR publishes `/scan`.
- [ ] Teleop works.

## M3 - Simulated Nav2

- [ ] SLAM or static map route works.
- [ ] Nav2 sends `/cmd_vel`.
- [ ] Behavior tree logs are readable.

## M4 - Drive MCU bridge

- [ ] Bridge connects to MCU over chosen bus.
- [ ] `/cmd_vel` becomes wheel setpoints.
- [ ] Encoders produce odometry inputs.
- [ ] Watchdog fault visible in diagnostics.

## M5 - Perception v1

- [ ] Camera driver publishes image/depth/camera_info.
- [ ] LiDAR driver publishes scan with correct frame.
- [ ] Bag profile records synchronized data.
- [ ] First object/marker detection test passes.

## M6 - Release/deploy path

- [ ] systemd bringup service starts robot in safe idle.
- [ ] Versioned parameter bundle is deployed.
- [ ] Rollback procedure is tested.
