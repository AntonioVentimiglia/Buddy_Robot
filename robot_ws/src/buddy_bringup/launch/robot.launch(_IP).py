from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    start_nav = LaunchConfiguration('start_nav')
    start_perception = LaunchConfiguration('start_perception')
    start_arm = LaunchConfiguration('start_arm')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('start_nav', default_value='true'),
        DeclareLaunchArgument('start_perception', default_value='true'),
        DeclareLaunchArgument('start_arm', default_value='false'),
        # TODO: include robot_state_publisher, base, sensors, localization, nav, diagnostics.
    ])
