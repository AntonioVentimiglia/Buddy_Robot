# Frame Tree

Initial Buddy frame tree:

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
        -> arm_base_link
```

## Frame responsibilities

| Frame | Owner | Notes |
|---|---|---|
| `map` | SLAM/localization | Global map frame; may jump after corrections |
| `odom` | odometry/EKF | Locally smooth, drifts over time |
| `base_footprint` | robot model/localization | 2D ground projection |
| `base_link` | URDF | Main body reference |
| `base_laser` | URDF/calibration | 2D LiDAR frame |
| `front_camera_link` | URDF/calibration | Physical camera body frame |
| `front_camera_optical_frame` | camera driver/URDF | Optical frame convention |
| `imu_link` | URDF/calibration | IMU mounting frame |
| `arm_base_link` | URDF/MoveIt | Placeholder until arm selected |

## Update checklist

- [ ] Update Xacro files.
- [ ] Update `robot_ws/src/buddy_description/config/frames.yaml`.
- [ ] Update simulation plugins.
- [ ] Update calibration notes.
- [ ] Verify in RViz.
