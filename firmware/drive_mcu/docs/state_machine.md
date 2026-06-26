# Drive MCU State Machine

```text
BOOT -> SELF_TEST -> SAFE_IDLE -> ARMED -> ACTIVE
                 \-> FAULT
ACTIVE -> SAFE_IDLE on command timeout
ANY -> FAULT on E-stop, driver fault, encoder fault, overcurrent, overtemperature
FAULT -> SAFE_IDLE only after reset policy is met
```

Motion must be disabled in BOOT, SELF_TEST, SAFE_IDLE, FAULT, and UPDATE states.
