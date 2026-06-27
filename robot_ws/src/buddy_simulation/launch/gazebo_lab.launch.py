from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    world = PathJoinSubstitution([
        FindPackageShare('buddy_simulation'),
        'worlds',
        'empty_lab.sdf',
    ])
    model = PathJoinSubstitution([
        FindPackageShare('buddy_simulation'),
        'models',
        'buddy_v0_1',
        'model.sdf',
    ])

    return LaunchDescription([
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', world],
            output='screen',
        ),
        TimerAction(
            period=2.0,
            actions=[
                Node(
                    package='ros_gz_sim',
                    executable='create',
                    arguments=['-name', 'buddy', '-file', model, '-z', '0.02'],
                    output='screen',
                ),
            ],
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
                '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
                '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
                '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock',
            ],
            output='screen',
        ),
    ])
