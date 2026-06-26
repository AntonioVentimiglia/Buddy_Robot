cmake_minimum_required(VERSION 3.8)
project(buddy_firmware_interfaces)

find_package(ament_cmake REQUIRED)

install(DIRECTORY msg srv action schemas docs
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
