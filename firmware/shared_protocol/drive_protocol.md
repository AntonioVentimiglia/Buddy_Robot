# Drive Protocol

The protocol must be documented before coding both ends.

## Required command fields

- Sequence number.
- Timestamp or timeout basis.
- Wheel velocity setpoints or left/right velocity setpoints.
- Enable/armed mode.
- CRC/checksum if custom binary.

## Required status fields

- Sequence echo.
- Firmware version.
- State machine state.
- E-stop state.
- Watchdog status.
- Encoder ticks or positions.
- Wheel velocities.
- Fault code.
- Battery or rail telemetry if available.
