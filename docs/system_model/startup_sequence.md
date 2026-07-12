# Startup Sequence

1. Linux boots on Jetson.
2. Systemd starts safe bringup service.
3. MCU bridge starts with motors disabled.
4. `robot_state_publisher` starts and publishes static frames.
5. Sensor drivers start.
6. Base controller starts but remains unarmed.
7. Diagnostics aggregator starts.
8. Localization/SLAM starts.
9. Nav2 lifecycle manager configures and activates navigation stack.
10. Motion becomes allowed only when E-stop clear, battery healthy, transforms valid, sensors active, and operator arms the robot.

## Rule

After reboot or OTA update, Buddy must boot into safe idle, not armed motion.
