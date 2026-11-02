import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    control_launch = os.path.join(
        get_package_share_directory('diffdrive_bot'), 'launch', 'control.launch.py')
    side_length = ParameterValue(LaunchConfiguration('side_length'), value_type=float)

    return LaunchDescription([
        DeclareLaunchArgument('side_length', default_value='0.5',
                              description='Side of the square in m'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(control_launch)),
        Node(
            package='my_robot_nodes',
            executable='rotate_server',
            parameters=[{'use_sim_time': True}],
            output='screen',
        ),
        Node(
            package='my_robot_nodes',
            executable='square_driver',
            parameters=[{'side_length': side_length, 'use_sim_time': True}],
            output='screen',
        ),
    ])
