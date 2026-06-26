# MCU OTA Strategy

Start with wired flashing and keep physical recovery access. Add OTA only after bench validation.

## Recovery requirements

- Physical debug/programming header accessible after assembly.
- Bootloader update mode disables motion.
- Failed firmware update cannot arm motors.
- Firmware version reported to ROS diagnostics.
