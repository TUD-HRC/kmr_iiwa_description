"""One-file Nav2 example: Gazebo simulation + Nav2 + slam_toolbox.

Starts the simulated KMR iiwa (kmr_iiwa_gazebo) and the existing Nav2
bringup (kmr_iiwa_nav2/nav2_launch.py) with the simulated clock enabled.

Usage:
    ros2 launch kmr_iiwa_nav2 gazebo.launch.py
    ros2 launch kmr_iiwa_nav2 gazebo.launch.py rviz:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    pkg_nav2 = get_package_share_directory('kmr_iiwa_nav2')
    pkg_gazebo = get_package_share_directory('kmr_iiwa_gazebo')

    world_path = os.path.join(pkg_gazebo, 'world', 'sandbox.world')
    rviz_conf_path = os.path.join(pkg_nav2, 'rviz', 'kmr_iiwa.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    rviz = LaunchConfiguration('rviz', default='true')
    rviz_conf = LaunchConfiguration('rviz_conf', default=rviz_conf_path)
    world = LaunchConfiguration('world', default=world_path)

    # Gazebo world, robot spawn, controllers, robot_state_publisher and the
    # gz -> ROS bridges (/clock, /kmr_iiwa/scan_front_right, scan_back_left).
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'kmr_iiwa.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'rviz': rviz,
            'rviz_conf': rviz_conf,
            'world': world,
        }.items(),
    )

    # Scan merger + slam_toolbox + Nav2, all in the /kmr_iiwa namespace.
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'nav2_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use the Gazebo clock (keep true in simulation)',
        ),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Start RViz from the Gazebo launch file',
        ),
        DeclareLaunchArgument(
            'rviz_conf', default_value=rviz_conf_path,
            description='RViz config file',
        ),
        DeclareLaunchArgument(
            'world', default_value=world_path,
            description='Gazebo world file to load',
        ),
        gazebo,
        nav2,
    ])
