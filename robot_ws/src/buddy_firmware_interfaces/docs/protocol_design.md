# Firmware Protocol Design

The protocol must be simple, timestamped, fault-aware, and recoverable.

## Required properties

- Sequence numbers or timestamps.
- CRC/checksum for custom binary protocols.
- Explicit command timeout behavior.
- E-stop state reporting.
- Fault code reporting.
- Version query.
- Safe boot state.
- Update/recovery mode that disables motion.

## Current open question

Choose one of:

- CAN/CAN-FD + custom protocol.
- RS485 + custom protocol.
- USB serial + custom protocol for early prototype.
- micro-ROS transport if embedded ROS graph is worth the complexity.
