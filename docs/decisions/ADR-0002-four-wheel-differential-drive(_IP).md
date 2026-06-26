# ADR-0002: Four-Wheel Differential Drive

- Status: Proposed
- Date: 2026-06-26

## Context

Buddy will use a four-wheel differential drive. Left wheels share one commanded side velocity and right wheels share the other commanded side velocity.

## Proposed decision

Model the base as a differential drive with four wheel links:

- `left_front_wheel_link`
- `left_rear_wheel_link`
- `right_front_wheel_link`
- `right_rear_wheel_link`

The base controller may command one motor per wheel or one driver per side depending on selected hardware.

## Consequences

- Nav2 can use standard differential-drive assumptions.
- Turning may involve tire scrub; motor sizing must include extra turning/current margin.
- Odometry may be worse than ideal differential drive if slip is high.
- IMU fusion is strongly recommended.
