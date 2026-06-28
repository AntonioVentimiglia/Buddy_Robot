"""Launch Buddy in Gazebo, spawned from the SAME URDF used by RViz.

There is no standalone model.sdf anymore: robot_state_publisher serves the
xacro on /robot_description, and ros_gz_sim spawns that. One geometry source.
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    xacro_file = PathJoinSubstitution([
        FindPackageShare('buddy_description'), 'urdf', 'buddy.urdf.xacro',
    ])
    world = PathJoinSubstitution([
        FindPackageShare('buddy_simulation'), 'worlds', 'empty_lab.sdf',
    ])

    robot_description = {
        'robot_description': Command([
            FindExecutable(name='xacro'), ' ', xacro_file, ' use_gazebo:=true',
        ]),
        'use_sim_time': True,
    }

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description],
        output='screen',
    )

    gz = ExecuteProcess(cmd=['gz', 'sim', '-r', world], output='screen')

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'buddy', '-topic', 'robot_description', '-z', '0.05'],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    return LaunchDescription([
        robot_state_publisher,
        gz,
        # Give the server a moment before spawning and bridging.
        TimerAction(period=3.0, actions=[spawn]),
        TimerAction(period=4.0, actions=[bridge]),
    ])
