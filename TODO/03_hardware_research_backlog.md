# Hardware Research Backlog

Use the folders under `research/` to store notes, datasheets, links, dimensions, mounting sketches, and final decisions.

## Compute

- [ ] Jetson Orin Nano Super storage: NVMe vs SD.
- [ ] JetPack version and Ubuntu base.
- [ ] Cooling and power input.
- [ ] USB and Ethernet topology.
- [ ] Camera interface: USB, CSI, Ethernet, or vendor bridge.

## Drive base

- [ ] Wheel diameter.
- [ ] Track width and wheelbase.
- [ ] Four driven wheels vs two driven plus passive support.
- [ ] Tire material and surface compatibility.
- [ ] Skid scrub current draw.
- [ ] Suspension or compliance strategy.

## Motors and drivers

- [ ] DC gearmotor vs BLDC with FOC vs integrated servo.
- [ ] Encoder CPR after gearbox.
- [ ] Continuous and stall current.
- [ ] Motor driver current/voltage margin.
- [ ] Enable/fault/watchdog behavior.
- [ ] Regenerative braking behavior.

## Power

- [ ] Battery chemistry.
- [ ] Nominal voltage.
- [ ] BMS current rating.
- [ ] Fuse strategy.
- [ ] DC/DC rails: motors, Jetson, sensors, logic, fans.
- [ ] Main switch, contactor, E-stop path.

## Sensors

- [ ] 2D LiDAR range, scan rate, FOV, ROS 2 driver.
- [ ] RGB-D camera range, lighting, ROS 2 driver, Jetson compatibility.
- [ ] IMU noise, mounting, ROS 2 driver.
- [ ] Calibration target and workflow.

## Arm

- [ ] Whether arm is v1 or future.
- [ ] Payload/reach/DOF.
- [ ] Mounting and tipping calculation.
- [ ] MoveIt 2 support.
- [ ] Power and E-stop integration.
