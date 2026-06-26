cmake_minimum_required(VERSION 3.8)
project(buddy_manipulation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch urdf meshes rviz worlds models behavior_trees maps docs
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
