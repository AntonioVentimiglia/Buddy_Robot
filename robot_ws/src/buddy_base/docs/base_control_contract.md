# Base Control Contract

## Inputs from ROS 2

- `/cmd_vel` velocity command from Nav2 or teleop.
- Optional mode/arm command from safety manager.

## Outputs to ROS 2

- Wheel positions/velocities.
- Odometry or odometry inputs.
- E-stop state.
- Watchdog state.
- Motor driver fault states.
- Battery/power status if provided by drive MCU.
- Diagnostics.

## Firmware safety requirements

- If no valid motion command arrives within configured timeout, stop.
- If E-stop active, disable motion.
- If encoder/fault/current/thermal/BMS fault occurs, enter safe state.
- Linux reboot or ROS crash must not leave motors moving.
