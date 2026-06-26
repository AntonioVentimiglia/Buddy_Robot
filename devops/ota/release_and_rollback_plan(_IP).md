# Release and Rollback Plan

## Prototype path

- Git tag release.
- Pull tagged commit on Jetson.
- Build with colcon.
- Keep previous install directory or image.
- Reboot to safe idle.

## More robust path later

- Debian packages or container images for ROS apps.
- Versioned parameter bundles.
- A/B OS update strategy with rollback.
- MCU firmware update only with physical recovery path.

## Rule

No update should automatically arm the robot after reboot.
