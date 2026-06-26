# buddy_base

Owns the mobile-base hardware interface/bridge. The exact implementation depends on selected motor drivers, MCU, and bus.

Current assumption: four driven wheels grouped into left and right differential-drive sides. The MCU reads encoders, enforces watchdog/E-stop, and exposes wheel state/fault telemetry to ROS 2.
