# Sensor Selection — 2D LiDAR, RGB-D Camera, IMU

**Date:** 2026-07-15 · **Status:** shortlisted, recommendation in ADR-0007; purchase phased
**Constraints (binding):** LiDAR ≤ 5 W and camera ≤ 5 W (power reserves, ADR-0005 —
a candidate exceeding its reserve triggers a budget re-run) · ROS 2 Jazzy driver ·
indoor ranges per requirements · budget: the v0.1 cart is already ~$590 of the
$300–600 band, so sensors are honestly a **budget extension** (see phasing below).

## 2D LiDAR (SLAM + Nav2, `/scan`)

| Candidate | Price | Range/rate | Power | ROS 2 | Verdict |
|---|---|---|---|---|---|
| **LDROBOT LD19 / FHL-LD19 (D300 kit)** ([spec](https://www.youyeetoo.com/products/fhl-ld19-lidar-sensor-12meter-39ft-360%C2%B0-ranging)) | ~$60–75 | 12 m ToF, 360°, 10 Hz, 4.5 kHz samples | **0.9 W** ✓ | `ldlidar` node, active; also [`lds2d`](https://makerspet.com/blog/lds2d-python-2d-lidar-library-live-browser-radar/) | **Recommended.** ToF (stable on dark surfaces), 30 klux resistant, well under reserve, cheapest per spec. |
| SLAMTEC RPLIDAR C1 | ~$70–90 | 12 m@70% refl. (6 m@10%), 10 Hz, 5 kHz | ~2 W ✓ | `sllidar_ros2` | Solid alternative; weaker on low-reflectivity range, slightly pricier. |
| RPLIDAR A1M8 | ~$99 | 12 m, 8 kHz | ~2.5 W ✓ | `sllidar_ros2` | Older triangulation design; superseded at this price. |

## RGB-D camera (`/camera/...`, perception + future manipulation)

| Candidate | Price | Depth | Power | ROS 2 | Verdict |
|---|---|---|---|---|---|
| **Luxonis OAK-D Lite** ([comparison](https://docs.luxonis.com/hardware/platform/comparison/vs-realsense), [robotics take](https://fictionlab.pl/blog/intel-realsense-d435-vs-oak-d-lite-which-depth-camera-for-mobile-robotics-research/)) | ~$130–150 | passive stereo + on-board VPU (runs NNs at the camera) | ~4.5 W ✓ (at reserve edge) | `depthai-ros`, active with Jazzy support | **Recommended when bought.** The on-camera VPU offloads the Orin Nano; passive stereo is weaker on textureless walls — acceptable indoors with LiDAR carrying navigation. |
| Intel RealSense D435/D435i | ~$280+ (refurb ~$280) | active IR stereo, dense 0.3–3 m | ~3.5 W ✓ | `realsense-ros` (Jazzy per release) | Better metric depth on textureless surfaces, but ~2× the price — kills the budget. Revisit if manipulation-grade depth disappoints on OAK. |
| Orbbec Gemini 2 | ~$200+ | active stereo | ~4 W | `orbbec_ros2` | Middle path; weaker ecosystem fit than the two above. |

## IMU (`/imu/data`, EKF fusion with odometry)

| Candidate | Price | Notes | Verdict |
|---|---|---|---|
| **CEVA/Hillcrest BNO085/BNO086 breakout** (Adafruit/SparkFun) | ~$25 | on-chip sensor fusion (quaternion out), I²C/SPI/UART-RVC; ROS 2 drivers exist; connect to the Jetson 40-pin I²C | **Recommended** — fusion on-chip means usable orientation before any calibration heroics. Verify current price/stock at checkout. |
| MPU-6050/9250 class | ~$5–15 | raw only, driver quality varies, magnetometer calibration pain | Budget fallback; costs its savings in tuning time. |

## Budget reality and phasing (the honest part)

LD19 + OAK-D Lite + BNO086 ≈ **$220**, on top of the ~$590 cart → **~$810 total**,
clearly beyond the $300–600 band (design conflict #4 again). Recommendation:

- **Phase A (add to the current order, +$90):** LD19 + BNO086. With drive
  electronics these complete the *teleop + SLAM + Nav2* milestone — LiDAR-only
  navigation is fully functional indoors.
- **Phase B (when perception work actually starts):** OAK-D Lite. Nothing in
  Phases 5–7 of the TODO needs the camera; buying it with Phase A would have it
  idle for weeks. Reserve stays enforced at ≤ 5 W.

Both sensors fit their power reserves with margin (0.9 + 4.5 W vs 5 + 5 W
allocated), so **no power-budget amendment is required** — the reserves did
their job.
