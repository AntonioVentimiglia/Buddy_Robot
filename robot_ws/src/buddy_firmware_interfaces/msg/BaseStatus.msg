# In progress custom message. Rename to BaseStatus.msg and add to CMakeLists when finalized.
std_msgs/Header header
bool estop_active
bool armed
bool command_watchdog_ok
float32 battery_voltage
float32 left_velocity_mps
float32 right_velocity_mps
uint32 fault_code
string fault_text
