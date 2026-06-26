# ROS 2 Interface Contract

This is the first interface contract. Topic names should remain stable even as vendors/hardware change.

## Mobility

| Interface | Type | Publisher | Subscriber | QoS | Notes |
|---|---|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Nav2 or teleop | base controller / bridge | reliable, depth 1-5 | MCU watchdog stops if stale |
| `/odom` | `nav_msgs/msg/Odometry` | base controller or EKF | Nav2/localization | reliable | Frame `odom -> base_footprint` or `base_link` |
| `/joint_states` | `sensor_msgs/msg/JointState` | ros2_control/joint_state_broadcaster | robot_state_publisher | reliable | Wheel and future arm joints |

## Sensors

| Interface | Type | Publisher | Subscriber | QoS | Notes |
|---|---|---|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | 2D LiDAR driver | SLAM/Nav2 | sensor data | Frame `base_laser` |
| `/camera/color/image_raw` | `sensor_msgs/msg/Image` | RGB-D camera | perception/visualization | sensor data | Exact namespace may change by driver |
| `/camera/depth/image_rect_raw` | `sensor_msgs/msg/Image` | RGB-D camera | perception | sensor data | Use depth alignment when supported |
| `/camera/color/camera_info` | `sensor_msgs/msg/CameraInfo` | camera driver | perception | reliable/sensor | Calibration required |
| `/imu/data` | `sensor_msgs/msg/Imu` | IMU driver | robot_localization | sensor data | Mount rigidly near base center if possible |

## Diagnostics and power

| Interface | Type | Publisher | Subscriber | Notes |
|---|---|---|---|---|
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | hardware-facing nodes | dashboard/logger | Must include status, firmware, comms, fault code |
| `/battery_state` | `sensor_msgs/msg/BatteryState` | power monitor | dashboard/logger/safety monitor | Voltage, current, charge if known |
| `/estop_state` | TBD custom msg or diagnostic | MCU/power bridge | safety monitor/dashboard | Physical E-stop state |

## Navigation actions

| Interface | Type | Owner |
|---|---|---|
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | Nav2 BT Navigator |
| `/follow_waypoints` | `nav2_msgs/action/FollowWaypoints` | Nav2 Waypoint Follower |

## Future manipulation actions

| Interface | Type | Owner |
|---|---|---|
| `/arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | ros2_control or vendor arm driver |
| `/gripper_controller/gripper_cmd` | `control_msgs/action/GripperCommand` | gripper controller |
