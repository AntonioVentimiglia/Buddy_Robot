#pragma once

// In progress: ros2_control hardware interface for Buddy's four-wheel differential base.
// Promote this file after the motor driver, MCU, and bus protocol are selected.

namespace buddy_base {

class BaseHardwareInterfaceIP {
 public:
  bool configure();
  bool read();
  bool write();
  bool emergencyStopActive() const;
};

}  // namespace buddy_base
