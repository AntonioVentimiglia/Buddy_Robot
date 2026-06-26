# Architecture Overview

Buddy uses ROS 2 for high-level integration and a dedicated MCU layer for low-level control and safety.

```text
Developer/operator tools
  - VS Code Remote SSH
  - RViz / Foxglove
  - ros2 CLI
  - CI and release scripts

Jetson Orin Nano Super
  - ROS 2 Jazzy baseline
  - robot_state_publisher and tf2
  - Nav2
  - SLAM/localization
  - RGB-D and 2D LiDAR drivers
  - diagnostics
  - bag recording
  - mission logic

Hardware bridge layer
  - ros2_control hardware plugin, CAN/serial bridge, or micro-ROS agent

MCU layer
  - encoder acquisition
  - motor driver commands
  - velocity/current loops or smart-driver setpoints
  - E-stop state
  - watchdog stop
  - power/fault telemetry
```

## Control loop placement

| Loop | Owner | Reason |
|---|---|---|
| Motor PWM/current/FOC | Motor driver or MCU | High rate and safety-critical |
| Wheel velocity loop | MCU or smart motor controller | Deterministic timing |
| Command watchdog | MCU | Must work when Linux is busy or down |
| Odometry fusion | ROS 2 EKF node | Sensor fusion and frame publishing |
| Path planning | Nav2 | High-level autonomy |
| Object detection | ROS 2 perception node / Isaac ROS | GPU/CPU-heavy processing |
| Arm trajectory planning | MoveIt 2 | High-level manipulation planning |
