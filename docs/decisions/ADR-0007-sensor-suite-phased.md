# ADR-0007: Sensor Suite — LD19 LiDAR + BNO086 IMU Now, OAK-D Lite Deferred

- Status: Proposed
- Date: 2026-07-15

## Context

The last undecided v0.1 hardware: 2D LiDAR, RGB-D camera, IMU. Binding
constraints from prior decisions: ≤ 5 W reserves each (ADR-0005, enforced by the
build validator), ROS 2 Jazzy drivers, and a budget already at ~$590 of the
$300–600 band. Research: [`sensor_selection.md`](../research/hardware/electronics/sensors/sensor_selection.md).

## Decision

- **2D LiDAR: LDROBOT LD19 (D300 kit), ~$60–75.** ToF, 12 m, 0.9 W (18% of its
  reserve), 30 klux, active ROS 2 driver. Buy with the current order.
- **IMU: BNO085/BNO086 breakout, ~$25.** On-chip fusion; Jetson 40-pin I²C.
  Buy with the current order.
- **RGB-D: Luxonis OAK-D Lite, ~$130–150 — selected but DEFERRED** to when
  perception work starts (nothing in TODO Phases 5–7 needs it). Its on-camera
  VPU offloads the Orin Nano; 4.5 W fits the reserve.
- Total sensor spend ~$220 pushes the project to ~$810 — an explicit **budget
  extension** of design conflict #4, softened by phasing (+$90 now).

## Consequences

- Teleop → SLAM → Nav2 milestone is fully unblocked by Phase A (LiDAR + IMU);
  the camera gates only perception work.
- Power reserves hold without amendment (0.9 W and 4.5 W vs 5 W each).
- Passive stereo (OAK) is weaker on textureless walls — acceptable because the
  LiDAR owns navigation; revisit RealSense D435 only if manipulation-grade
  depth disappoints.
- URDF sensor frames (`base_laser`, `front_camera_link`, `imu_link`) get real
  extrinsics at mounting; requirements REQ_PER_001 resolution/fps TBDs fill in
  from the OAK-D Lite datasheet when purchased.

## What would change this decision

- Measured LD19 performance on the actual dark carpet < 8 m usable → RPLIDAR C1.
- Budget relief or an early manipulation push → pull OAK-D Lite into Phase A.
