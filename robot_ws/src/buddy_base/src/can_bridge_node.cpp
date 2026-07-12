// In progress: CAN/CAN-FD bridge skeleton.
// Responsibilities:
// - Subscribe to /cmd_vel or receive wheel setpoints from ros2_control.
// - Send commands to drive MCU.
// - Publish wheel states, odom inputs, fault codes, E-stop state, and diagnostics.
// - Never bypass MCU watchdog/safety logic.

int main(int argc, char** argv) {
  (void)argc;
  (void)argv;
  return 0;
}
