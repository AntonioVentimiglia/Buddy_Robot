# Safety and Commissioning TODO

## Before applying battery power

- [ ] Verify polarity and continuity.
- [ ] Verify fuses installed close to battery/source.
- [ ] Verify wire gauge against expected current.
- [ ] Verify no exposed conductors.
- [ ] Verify E-stop interrupts motor enable or motor power.
- [ ] Current-limit first power-up with bench supply when possible.

## Before first motor spin

- [ ] Wheels off ground.
- [ ] Motor driver current limit set low.
- [ ] Encoder direction verified.
- [ ] Command timeout verified.
- [ ] E-stop verified while motor spinning slowly.

## Before first rolling drive

- [ ] Person holds physical E-stop.
- [ ] Speed limit conservative.
- [ ] Base is mechanically stable.
- [ ] Battery secured.
- [ ] `/odom` direction matches real motion.
- [ ] Bag recording ready.

## Before first autonomous Nav2 run

- [ ] Clear test area.
- [ ] Soft obstacles only.
- [ ] Footprint in Nav2 matches real robot.
- [ ] LiDAR scan aligns with robot body in RViz.
- [ ] Localization stable.
- [ ] E-stop tested during autonomous command.

## Before arm motion on base

- [ ] Arm tested on bench.
- [ ] Base disabled or physically restrained during first arm tests.
- [ ] MoveIt collision geometry includes base, mast, sensors, and arm mount.
- [ ] Tipping calculation completed.
- [ ] Cables checked through full joint range.
