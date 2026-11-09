import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():

    pkg_project = get_package_share_directory('kmr_iiwa_urdf')
    joystick_config = os.path.join(
        pkg_project, 'config', 'controllers', 'joystick_ps3.yaml'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    joy_dev = LaunchConfiguration('joy_dev')
    topic_name = LaunchConfiguration('topic_name')

    teleop = GroupAction(actions=[
        PushRosNamespace(robot_name),
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[{
                'device_id': joy_dev,
                'deadzone': 0.3,
                'autorepeat_rate': 20.0,
                'use_sim_time': use_sim_time,
            }],
            output='screen',
        ),
        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_twist_joy_node',
            parameters=[
                joystick_config,
                {'use_sim_time': use_sim_time},
            ],
            remappings=[('cmd_vel', topic_name)],
            output='screen',
        ),
    ])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        DeclareLaunchArgument(
            "joy_dev", 
            default_value="0", 
            description=(
                "check with ls /dev/input/js* to find the correct joystick device"
            ),
        ),
        DeclareLaunchArgument(
            "topic_name",
            default_value="cmd_vel_teleop",
            description=(
                "Topic the joystick publishes to, relative to the robot "
                "namespace (resolves to /<robot_name>/cmd_vel_teleop)."
            ),
        ),
        teleop,
    ])
