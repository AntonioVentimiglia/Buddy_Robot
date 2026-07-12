# Fault State Model

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
