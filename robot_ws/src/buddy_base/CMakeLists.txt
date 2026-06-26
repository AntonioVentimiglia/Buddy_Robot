cmake_minimum_required(VERSION 3.8)
project(buddy_base)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface QUIET)
find_package(pluginlib QUIET)

install(DIRECTORY config docs launch include src
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
