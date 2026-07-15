# Launch the drive-base bridge (buddy_base) against the real MCU or the mock.
#
#   ros2 launch buddy_bringup base.launch.py                 # real MCU (udev name)
#   ros2 launch buddy_bringup base.launch.py port:=/dev/pts/3 auto_arm:=true
#
# For the mock: run `python3 robot_ws/src/buddy_firmware_interfaces/python/mock_mcu.py`
# first and pass the pty path it prints as port:=.
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("port", default_value="/dev/buddy_drive_mcu",
                              description="Serial device: udev name for the real "
                                          "MCU (falls back: /dev/ttyACM0) or mock pty"),
        DeclareLaunchArgument("auto_arm", default_value="false",
                              description="Request ARM automatically (bench only)"),
        Node(
            package="buddy_base",
            executable="bridge_node",
            name="buddy_base_bridge",
            output="screen",
            parameters=[{
                "port": LaunchConfiguration("port"),
                "auto_arm": LaunchConfiguration("auto_arm"),
            }],
        ),
    ])
