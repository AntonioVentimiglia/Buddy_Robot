#include "buddy_base/base_hardware_interface(_IP).hpp"

namespace buddy_base {

bool BaseHardwareInterfaceIP::configure() { return false; }
bool BaseHardwareInterfaceIP::read() { return false; }
bool BaseHardwareInterfaceIP::write() { return false; }
bool BaseHardwareInterfaceIP::emergencyStopActive() const { return true; }

}  // namespace buddy_base
