# Fault State Model

> Drawn as [`assets/figures/fault_state_machine.svg`](../../assets/figures/fault_state_machine.svg)
> (see [`system_integration.md`](system_integration.md)). The authoritative state
> and fault-bit values are in
> [`drive_protocol.md`](../../firmware/shared_protocol/drive_protocol.md); this
> page is the system-level view, which includes fault sources that live on the
> Jetson rather than the MCU.

## States

```text
BOOT -> SELF_TEST -> SAFE_IDLE -> ARMED -> ACTIVE_MOTION
                 \-> FAULT
ARMED/ACTIVE_MOTION -> FAULT on E-stop, watchdog timeout, power fault, comms fault, localization invalid, motor fault
FAULT -> SAFE_IDLE only after reset conditions are met
```

## Minimum fault sources

- E-stop active.
- Command timeout.
- MCU communication lost.
- Battery/BMS fault.
- Motor driver overcurrent/overtemperature.
- Encoder invalid or missing.
- Odometry invalid.
- Transform tree invalid.
- Localization confidence poor during autonomy.
- Arm fault if manipulation is installed.
