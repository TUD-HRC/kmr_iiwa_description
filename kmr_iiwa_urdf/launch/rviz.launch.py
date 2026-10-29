import os
from ament_index_python.packages import (
    get_package_share_directory,
    get_package_prefix,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetLaunchConfiguration,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import xacro

def generate_launch_description():


    # Setup project paths
    pkg_project = get_package_share_directory('kmr_iiwa_urdf')

    robot_xacro = os.path.join(pkg_project, "urdf/", "kmr_iiwa.urdf.xacro")
    assert os.path.exists(robot_xacro), "The kmr_iiwa.urdf.xacro doesnt exist in " + str(robot_xacro)

    # Opaque function to use optional future launch arguments inside here
    def create_robot_description(context, *args, **kwargs):
        robot_description_config = xacro.process_file(
            robot_xacro,
        )

        return [SetLaunchConfiguration("robot_desc", robot_description_config.toxml())]

    create_robot_description_arg = OpaqueFunction(
        function=create_robot_description
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(pkg_project, "rviz", "kmr_iiwa.rviz"),
        ],
        parameters=[
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
            {"robot_description": ParameterValue(LaunchConfiguration("robot_desc"), value_type=str)},
        ],
        namespace=LaunchConfiguration("robot_name"),
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        condition=IfCondition(LaunchConfiguration("jsp")),
        namespace=LaunchConfiguration("robot_name"),
    )

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        condition=IfCondition(LaunchConfiguration("jsp_gui")),
        namespace=LaunchConfiguration("robot_name"),
    )

    return LaunchDescription([
        create_robot_description_arg,
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        #to not use with real robot that already send joint states
        DeclareLaunchArgument("jsp", default_value="false"),
        DeclareLaunchArgument("jsp_gui", default_value="false"),
        joint_state_publisher,
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz,
    ])