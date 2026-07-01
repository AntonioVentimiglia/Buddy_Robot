# STM32 Selection for 4-Motor Differential Drive Controller

This document summarizes the MCU selection rationale for a robot drive-base controller that separates high-level logic on an SBC from deterministic low-level motor control on microcontrollers.

## Fast Recommendation

Use an **STM32G474** for the 4-motor differential-drive controller.

Recommended starting points:

| Stage | Recommended Part | Why |
|---|---|---|
| Prototype | `NUCLEO-G474RE` | Easy development board with integrated ST-LINK debugger/programmer, Arduino Uno V3 headers, and ST morpho headers. |
| Custom PCB | `STM32G474VET6` or similar 100-pin STM32G474 package | Gives enough pins for 4 encoders, 4 motor outputs, current sensing, fault inputs, CAN, USB, SWD, BOOT0/reset control, and expansion. |
| Possible smaller custom PCB | `STM32G474RET6` or other 64-pin package | Only use if CubeMX confirms all encoder, PWM, ADC, CAN/USB, SWD, and safety pins fit cleanly. |

The short answer: **STM32G474 is a good match because it has the timer, ADC, analog, FDCAN, USB, and debug/programming features needed for a serious 4-wheel motor-control board.**

---

## System Context

The intended architecture is:

```text
SBC / Jetson / mini PC
  - ROS 2
  - perception
  - navigation
  - planning
  - logging
  - user interface
  - high-level robot state machine
        |
        | CAN / CAN-FD / USB / Ethernet
        |
STM32 drive-base controller
  - wheel encoder reading
  - velocity PID loops
  - PWM generation
  - current sensing
  - motor-driver fault handling
  - watchdog timeout behavior
  - emergency stop input handling
  - firmware version reporting
  - bootloader / update handling
        |
        | PWM / DIR / ENABLE / FAULT / current sense
        |
4 motor drivers
        |
4 drive motors with quadrature encoders
```

The MCU should not be responsible for high-level navigation or perception. Its job is to make the motors behave predictably and safely even when the SBC is busy, crashes, reboots, or stops sending commands.

---

## Requirements

For the 4-wheel differential-drive base, the controller should support:

1. **Four motor outputs**
   - PWM + direction, or
   - two-PWM H-bridge control, depending on the motor driver.

2. **Four quadrature encoders**
   - One A/B encoder pair per wheel.
   - Prefer hardware timer encoder mode instead of counting every encoder edge in software interrupts.

3. **Optional current sensing per motor**
   - Four ADC inputs minimum.
   - Extra ADC inputs for battery voltage, board temperature, motor-driver temperature, spare sensors, etc.

4. **Motor-driver safety I/O**
   - Enable pins.
   - Fault pins.
   - Brake pins if supported.
   - Emergency-stop input.

5. **Robot communication bus**
   - CAN or CAN-FD preferred for final robot wiring.
   - USB serial acceptable for early bring-up and debugging.

6. **No-manual-hookup reflashing**
   - SBC should be able to flash/update firmware without opening the robot.
   - SWD should remain available as a recovery path.
   - Runtime bus bootloading is useful, but should not be the only recovery method.

7. **Deterministic control loops**
   - Encoder readout and motor updates at fixed rates, for example 500 Hz to 1 kHz.
   - Watchdog behavior if SBC commands stop arriving.

---

## Recommended MCU: STM32G474

The **STM32G474** is a strong fit because it has:

- Arm Cortex-M4 core with FPU/DSP capability.
- 170 MHz class performance.
- Multiple ADCs for current sensing and other analog measurements.
- Integrated analog features such as comparators and op-amps.
- Advanced timers suitable for motor PWM.
- Multiple timer blocks suitable for quadrature encoder mode.
- FDCAN for robust robot-internal communication.
- USB device support for bring-up, debug, or flashing workflows.
- SWD/JTAG development support.
- Compatibility with STM32CubeIDE, STM32CubeMX, STM32CubeProgrammer, and ST-LINK workflows.

Official ST pages describe the STM32G4 family as 170 MHz Arm Cortex-M4 devices with FPU/DSP instructions, rich analog peripherals, ADC oversampling, and motor-control-oriented capabilities. See the references section at the end of this file.

---

## Why the Encoder Requirement Matters

The most important constraint is the **four quadrature encoders**.

A poor implementation would be:

```text
Every encoder edge triggers an interrupt.
The CPU manually increments or decrements software counters.
At high speed, encoder interrupts consume too much CPU time.
Timing jitter increases.
Motor control becomes less deterministic.
```

The preferred implementation is:

```text
Each encoder A/B pair is connected to a hardware timer in encoder mode.
The timer peripheral counts quadrature transitions automatically.
The control loop reads timer counts periodically.
Software computes wheel velocity from count differences.
The CPU is not interrupted on every encoder edge.
```

For four drive motors, ideally allocate one hardware encoder-capable timer per wheel:

| Motor | Encoder Timer |
|---|---|
| Front left | TIM2 |
| Rear left | TIM5 |
| Front right | TIM3 |
| Rear right | TIM4 |

This is one of the reasons the STM32G474 is more attractive than smaller MCUs with fewer useful timers.

---

## Example Peripheral Allocation

A possible peripheral map for a 4-motor base controller:

```text
Encoders:
  TIM2 CH1/CH2  -> Motor 1 quadrature encoder
  TIM5 CH1/CH2  -> Motor 2 quadrature encoder
  TIM3 CH1/CH2  -> Motor 3 quadrature encoder
  TIM4 CH1/CH2  -> Motor 4 quadrature encoder

Motor PWM:
  TIM1 / TIM8 / TIM20 / other PWM-capable timers

Analog sensing:
  ADC inputs -> Motor 1 current
  ADC inputs -> Motor 2 current
  ADC inputs -> Motor 3 current
  ADC inputs -> Motor 4 current
  ADC input  -> Battery voltage
  ADC input  -> Board temperature or driver temperature
  ADC input  -> Spare analog input

Communication:
  FDCAN1 -> Robot internal bus to SBC
  USB    -> Bring-up, debug, serial console, optional update path

Programming / recovery:
  SWDIO
  SWCLK
  NRST
  BOOT0, if using bootloader entry control

Safety / diagnostics:
  Motor enable pins
  Motor fault pins
  Brake pins, if supported
  Emergency stop input
  Status LEDs
  Firmware version reporting
```

The exact mapping must be validated in **STM32CubeMX** before designing the PCB.

---

## Why Prefer the 100-Pin Package for the Custom PCB

A 64-pin STM32G474 can work, but a 4-motor base controller becomes pin-hungry quickly.

Approximate pin needs:

| Function | Pins Needed |
|---|---:|
| 4 quadrature encoders | 8 |
| 4 PWM outputs | 4 minimum |
| 4 direction pins | 4 |
| 4 enable pins | 4 |
| 4 fault inputs | 4 |
| 4 current-sense ADC inputs | 4 |
| Battery voltage sense | 1 |
| Temperature / spare analog | 1-3 |
| CAN RX/TX | 2 |
| USB D+/D- | 2 |
| SWDIO/SWCLK/NRST | 3 |
| BOOT0 / update-control signals | 1-3 |
| Status LEDs / debug GPIO | 2-4 |
| Emergency stop input | 1 |

That can exceed the comfortable routing and alternate-function flexibility of a smaller package. A **100-pin STM32G474** gives more room for:

- Clean timer pin assignments.
- Dedicated fault inputs.
- Extra ADC channels.
- CAN and USB together.
- Debug/programming pins.
- Future expansion.
- Easier PCB layout.

Rule of thumb: for a first custom robot controller PCB, choose the package that gives design margin. The cost and board-space penalty is usually smaller than the cost of redesigning the board later.

---

## Why Not STM32H7?

STM32H7 is faster, but this drive controller is not primarily a compute problem.

The important requirements are:

- Deterministic encoder counting.
- Reliable PWM generation.
- Good ADC/current-sense support.
- Fast fault response.
- CAN/USB communication.
- Debuggability.
- Safe reflashing and recovery.

STM32G4 is more directly targeted at mixed-signal control and motor-control applications. STM32H7 may be useful for heavier computation, high-bandwidth networking, complex sensor processing, or board-level computing, but it is more complex than needed for this drive-base controller.

---

## Why Not STM32F4?

STM32F4 parts are still useful, but for a new motor-control board the STM32G4 family is usually a better fit.

Reasons to prefer G4 over F4 here:

- Newer motor-control-oriented family.
- Stronger mixed-signal feature set.
- Rich analog peripherals.
- FDCAN availability on relevant G4 parts.
- High-resolution timing support.
- Good match for current sensing, PWM, comparators, and fault handling.

Use STM32F4 only if there is a specific board, library, or existing codebase that makes it significantly easier.

---

## Why Not Teensy, ESP32, or RP2040 for This Specific Board?

### Teensy 4.1

Teensy 4.1 is excellent for fast prototyping, sensor aggregation, and high-speed I/O experiments. However, it is less ideal as the final standard for a custom motor-control PCB because the STM32 ecosystem gives a cleaner path for:

- SWD recovery.
- Custom board design.
- Motor-control timer/ADC allocation.
- ST-LINK / CubeProgrammer workflows.
- Long-term embedded-product style development.

### ESP32

ESP32 is useful for Wi-Fi, BLE, OTA diagnostics, web configuration, and wireless sensor nodes. It is not the best choice for the primary drive-base safety/control loop.

Use ESP32 for:

- Wireless telemetry.
- Web-based configuration.
- Non-critical diagnostics.
- Potential firmware-update gateway.

Avoid using ESP32 as the only controller for safety-critical wheel motion, especially when precise timing and deterministic behavior matter.

### RP2040 / Pico

RP2040 is inexpensive and useful for helper boards, custom timing glue, LEDs, buttons, and small sensor adapters. It is not as compelling as STM32G474 for a 4-motor controller with encoders, current sensing, CAN, and robust update/recovery requirements.

---

## Reflashing and Update Strategy

The robot should support firmware updates without manually plugging a cable into each microcontroller after assembly.

A good design has two update paths:

### 1. Reliable Recovery Path: SWD

Keep SWD physically wired inside the robot.

Recommended approach:

```text
SBC USB port
  -> internal USB hub
  -> ST-LINK / CMSIS-DAP probe
  -> SWDIO, SWCLK, NRST on STM32 drive controller
```

This allows the SBC to recover the MCU even if the application firmware is broken.

The SWD recovery path is the one to trust for worst-case failures.

### 2. Convenient Runtime Update Path: CAN / USB / Bootloader

For normal updates, the SBC can ask the drive controller to enter a bootloader/update mode:

```text
SBC sends ENTER_BOOTLOADER command
Drive controller disables all motor outputs
Drive controller records safe state
Drive controller reboots into bootloader or updater
SBC flashes firmware over CAN, USB DFU, UART, or another supported path
Firmware is verified
Drive controller reboots
Drive controller reports firmware version
Robot remains disarmed until explicitly re-armed
```

Do not rely only on runtime bus updates. Keep SWD as the recovery path.

---

## Firmware Safety Behavior

The drive controller should enforce local safety rules regardless of SBC behavior.

Recommended behaviors:

1. **Do not move on boot**
   - Motors stay disabled until the SBC explicitly arms the controller.

2. **Command timeout**
   - If velocity commands stop arriving, ramp down and disable or brake motors.

3. **Emergency stop handling**
   - E-stop input should immediately disable motor outputs.

4. **Fault input handling**
   - If a driver reports a fault, stop that motor or the whole base depending on severity.

5. **Current limit handling**
   - If current exceeds threshold, reduce command, fault, or shut down.

6. **Firmware update safety**
   - Entering bootloader/update mode must disable all motor outputs first.

7. **Version reporting**
   - The MCU should report firmware name, semantic version, git hash if available, and hardware revision.

8. **Watchdog**
   - Use an independent watchdog so the controller resets on firmware lockup.

---

## Suggested Control Loop Structure

A simple first version:

```text
1 kHz timer interrupt or RTOS task:
  read encoder timer counts
  compute delta counts
  estimate wheel velocities
  read current sensors
  run velocity PID for each wheel
  apply acceleration/current limits
  update PWM outputs
  check command timeout
  check fault inputs

Main loop / communication task:
  receive commands from SBC
  publish wheel states
  publish diagnostics
  handle arming/disarming
  handle firmware update request
```

For differential drive, the SBC can send either:

```text
left_velocity_target
right_velocity_target
```

or:

```text
front_left_velocity_target
rear_left_velocity_target
front_right_velocity_target
rear_right_velocity_target
```

For a rigid 4-wheel differential-drive base, the two wheels on the same side will usually receive the same velocity target. Separate feedback per wheel is still useful because each motor/encoder/driver can behave slightly differently.

---

## SBC-to-MCU Protocol Sketch

Keep the low-level protocol simple. The MCU does not need to be a full ROS 2 computer.

Possible message types:

```text
HEARTBEAT
ARM
DISARM
SET_WHEEL_VELOCITIES
GET_STATE
STATE_REPORT
FAULT_REPORT
CLEAR_FAULTS
ENTER_BOOTLOADER
FIRMWARE_VERSION
PARAM_READ
PARAM_WRITE
```

A typical command/state pattern:

```text
SBC -> MCU:
  command_id
  timestamp
  target_front_left_velocity
  target_rear_left_velocity
  target_front_right_velocity
  target_rear_right_velocity
  max_accel
  enable_state

MCU -> SBC:
  firmware_version
  hardware_revision
  armed_state
  fault_state
  measured_wheel_positions
  measured_wheel_velocities
  motor_currents
  bus_voltage
  board_temperature
  missed_command_count
```

---

## Toolchain Support

The STM32G474 supports the development and deployment tools needed for this architecture.

Recommended tools:

| Tool | Use |
|---|---|
| STM32CubeMX | Pin assignment, clock tree setup, peripheral configuration. |
| STM32CubeIDE | Firmware development, debugging, building. |
| STM32CubeProgrammer | Flashing, verifying memory, setting option bytes, scripted programming. |
| ST-LINK / STLINK-V3 | SWD/JTAG flashing and debugging. |
| STM32CubeCLT | Command-line build workflows, useful for CI or repository scripts. |
| OpenOCD or pyOCD, optional | Alternative SWD/debug workflows depending on probe choice. |

STM32CubeProgrammer supports programming through SWD/JTAG and bootloader interfaces such as UART, USB DFU, I2C, SPI, and CAN, and supports command-line/scripting automation. This matches the no-manual-hookup flashing requirement if the board is wired correctly.

---

## Design Checklist Before Ordering a Custom PCB

Before selecting the exact package and ordering a board, create a CubeMX project and confirm:

- [ ] Four encoder timers are assigned without pin conflicts.
- [ ] All encoder A/B pins are routed to usable package pins.
- [ ] PWM outputs are assigned to timers appropriate for motor control.
- [ ] Current-sense ADC pins are available and not conflicting with other functions.
- [ ] CAN-FD RX/TX pins are available.
- [ ] USB D+/D- pins are available if using USB.
- [ ] SWDIO, SWCLK, and NRST are available on a permanent connector or internal probe path.
- [ ] BOOT0 or other bootloader-entry method is controllable if needed.
- [ ] Motor-driver enable/fault/brake pins are available.
- [ ] Emergency stop input has a clear hardware and firmware path.
- [ ] There are enough spare pins for revision ID, LEDs, debugging, or future sensors.
- [ ] Power domains and voltage levels are compatible with encoders and motor drivers.
- [ ] CAN transceiver is included if using CAN/CAN-FD.
- [ ] Current-sense scaling matches ADC input range.
- [ ] Motor-driver fault outputs are voltage-compatible with STM32 GPIO.
- [ ] External pull-ups/pull-downs place motor drivers in a safe disabled state on MCU reset.

---

## Development Plan

### Phase 1: Bench Prototype

Hardware:

- NUCLEO-G474RE.
- One motor driver.
- One motor with quadrature encoder.
- Current-sense signal if available.
- Bench power supply.
- Oscilloscope or logic analyzer if available.

Goals:

- Read one quadrature encoder using timer encoder mode.
- Generate PWM safely.
- Run one velocity PID loop.
- Read one current sensor.
- Implement command timeout.
- Report state over USB serial.

### Phase 2: Four-Motor Prototype

Goals:

- Use four hardware encoder timers.
- Control four motors.
- Send left/right velocity commands from SBC.
- Report wheel velocities and currents.
- Test command timeout and e-stop behavior.
- Add CAN/CAN-FD communication.

### Phase 3: Update/Recovery Workflow

Goals:

- Flash from SBC through ST-LINK/SWD.
- Add firmware version reporting.
- Add scripted flashing command.
- Test recovery from broken firmware.
- Test runtime bootloader path if desired.

### Phase 4: Custom PCB

Goals:

- Use 100-pin STM32G474 package unless a smaller package is proven sufficient.
- Include CAN transceiver.
- Include USB if useful.
- Include SWD connector or permanent internal SWD routing.
- Include boot/reset control.
- Include safe default pull-ups/pull-downs.
- Include motor-driver fault and enable routing.
- Include current-sense filtering and scaling.

---

## Final Recommendation

Use:

```text
Prototype:
  NUCLEO-G474RE

Custom PCB:
  STM32G474VET6 or similar 100-pin STM32G474 package
```

The STM32G474 is the best fit because it provides the practical combination needed for this robot:

- Four hardware encoder-capable timers.
- Strong motor PWM/timer resources.
- Fast ADC and rich analog support for current sensing.
- FDCAN for robust robot communication.
- USB for bring-up and optional update/debug workflows.
- SWD/JTAG recovery through ST-LINK.
- STM32CubeProgrammer automation support.
- A realistic path from Nucleo prototype to custom PCB.

The key design principle is: **normal updates can be convenient, but recovery must be reliable**. CAN/USB bootloading is useful, but permanent SWD access is what keeps the robot serviceable after firmware mistakes.

---

## References

- STMicroelectronics, **STM32G474 product page**: https://www.st.com/en/microcontrollers-microprocessors/stm32g474rc.html
- STMicroelectronics, **STM32G4 series overview**: https://www.st.com/en/microcontrollers-microprocessors/stm32g4-series.html
- STMicroelectronics, **STM32G4 series documentation**: https://www.st.com/en/microcontrollers-microprocessors/stm32g4-series/documentation.html
- STMicroelectronics, **NUCLEO-G474RE product page**: https://www.st.com/en/evaluation-tools/nucleo-g474re.html
- STMicroelectronics, **STM32G4 Nucleo-64 board user manual**: https://www.st.com/resource/en/user_manual/um2505-stm32g4-nucleo64-boards-mb1367-stmicroelectronics.pdf
- STMicroelectronics, **STM32CubeProgrammer product page**: https://www.st.com/en/development-tools/stm32cubeprog.html
- STMicroelectronics, **STM32CubeProgrammer user manual**: https://www.st.com/resource/en/user_manual/um2237-stm32cubeprogrammer-software-description-stmicroelectronics.pdf
- STMicroelectronics, **STM32Cube command-line toolset guide**: https://www.st.com/resource/en/user_manual/um3088-stm32cube-commandline-toolset-quick-start-guide-stmicroelectronics.pdf
