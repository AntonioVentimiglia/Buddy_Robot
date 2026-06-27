# ADR-0001: ROS 2 and JetPack Baseline

- Status: Proposed
- Date: 2026-06-26

## Context

Buddy will use an NVIDIA Jetson Orin Nano Super as the onboard compute. The repository should start with a stable ROS 2 and Jetson software baseline while leaving room for driver constraints.

## Proposed decision

Default to:

- JetPack 7.x / Ubuntu 24.04 path when compatible with selected sensors and tools.
- ROS 2 Jazzy as first physical integration baseline.
- Keep migration notes for ROS 2 Lyrical after vendor support is verified.

## Why

- Jetson Orin Nano Super is the selected compute platform.
- Ubuntu 24.04 aligns with ROS 2 Jazzy.
- NVIDIA Isaac ROS documentation currently targets ROS 2 Jazzy.

## Consequences

- Use Jazzy package names and examples first.
- Vendor drivers must be checked for Jazzy and Jetson compatibility.
- If a critical driver supports only Humble or Lyrical, revisit this ADR.

## Open questions

- Exact JetPack version installed on the Jetson.
- Whether all selected camera/LiDAR drivers support Jazzy on ARM64.
- Whether Isaac ROS packages are needed in v1.
