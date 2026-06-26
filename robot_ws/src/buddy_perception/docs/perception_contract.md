# Perception Contract

## Inputs

- RGB image.
- Depth image or registered point cloud.
- Camera info.
- TF from camera to base.
- Optional LiDAR scan.

## Outputs

- Detections with timestamp and frame ID.
- Object poses when calibrated and stable.
- Diagnostics: frame rate, latency, dropped frames, model version.

## Deployment rule

Measure latency on the Jetson, not only on a laptop. Version models and labels.
