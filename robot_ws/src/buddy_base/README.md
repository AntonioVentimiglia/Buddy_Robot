# buddy_base

The bridge between ROS 2 and the drive MCU (protocol per
[ADR-0006](../../../docs/decisions/ADR-0006-mcu-jetson-bus-usb-serial.md) and
`firmware/shared_protocol/drive_protocol.md`).

**Architecture:** all drive logic — skid-steer kinematics, odometry integration,
velocity clamping, keep-alive pacing against the MCU's 200 ms watchdog — lives
in [`buddy_base/base_core.py`](buddy_base/base_core.py) as plain Python with
**no ROS dependency**, fully tested on any machine:

```bash
cd test
python3 test_base_core.py          # kinematics + odometry units (8 tests)
python3 test_integration_mock.py   # end-to-end vs the mock MCU (5 tests)
```

[`buddy_base/ros_bridge_node.py`](buddy_base/ros_bridge_node.py) is the thin
rclpy shell: `/cmd_vel` in; `/odom` + TF, `/joint_states`, `/battery_state`
out; serial I/O to `/dev/ttyACM*` (real MCU) or the pty printed by
`mock_mcu.py` — identical code path either way.

Geometry/limits come from the repo's `design_params.yaml` via `buddy_calcs`
(`params_from_design()`), not from hand-kept yaml. Build the workspace with
`colcon build --symlink-install` so in-repo imports (shared protocol lib)
resolve.

**v0.1 approach note:** this is a custom bridge node, not a `ros2_control`
hardware interface — simpler, fully host-testable, and sufficient while the
velocity loop lives on the MCU. Revisit `ros2_control` when Nav2 tuning or the
future arms demand controller-manager integration.
