# Safety Architecture

## Minimum physical safety chain

```text
E-stop button(s)
  -> safety relay or motor-enable interruption
  -> motor drivers disabled or commanded safe stop
  -> MCU observes E-stop state
  -> ROS diagnostics reports E-stop state
```

## Independent watchdogs

- MCU command timeout stops motors.
- Linux heartbeat monitored by MCU/bridge.
- Battery/BMS fault inhibits motion.
- Motor driver fault inhibits motion.
- Arm fault prevents coordinated base-arm task when arm exists.

## Non-negotiable rule

ROS 2 can request motion. ROS 2 must not be the only thing preventing unsafe motion.
