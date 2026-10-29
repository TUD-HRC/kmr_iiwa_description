"""Gazebo + MoveIt.

Starts the existing Gazebo bringup (without its RViz), then move_group and the
MoveIt RViz under the ``/kmr_iiwa`` namespace.

Why the namespace matters: the Gazebo launch starts ``robot_state_publisher``
and the controller manager inside ``/kmr_iiwa``, so TF is published on
``/kmr_iiwa/tf`` and joint states on ``/kmr_iiwa/joint_states``.  Running
move_group in the same namespace makes its relative ``tf``, ``tf_static``,
``joint_states`` and ``arm_controller/follow_joint_trajectory`` names resolve to
the Gazebo ones without extra remappings.

MoveIt must not start robot_state_publisher or the static virtual joint TF:
Gazebo already provides both.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)


def generate_launch_description():
    moveit_pkg = get_package_share_directory("kmr_iiwa_moveit_config")
    gazebo_pkg = get_package_share_directory("kmr_iiwa_gazebo")

    robot_name = LaunchConfiguration("robot_name")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Launch configurations are global across includes, and the Gazebo bringup
    # declares its own ``rviz`` argument.  Passing ``rviz:=false`` to it would
    # therefore overwrite the top-level value and silently disable MoveIt's
    # RViz below.  A scoped GroupAction keeps the override local.
    gazebo = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_pkg, "launch", "kmr_iiwa.launch.py")
            ),
            launch_arguments={
                "robot_name": robot_name,
                "use_sim_time": use_sim_time,
                "world": LaunchConfiguration("world"),
                # MoveIt starts its own RViz (moveit.rviz).
                "rviz": "false",
            }.items(),
        ),
    ])

    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "move_group.launch.py")
        ),
        launch_arguments={
            "robot_name": robot_name,
            "namespace": robot_name,
            "use_sim_time": use_sim_time,
            "joint_states_topic": PythonExpression([
                "'/' + '", robot_name, "' + '/joint_states'",
            ]),
            "controllers_file": "config/moveit_controllers.yaml",
            # Each backend activates its own controllers.
            "moveit_manage_controllers": "false",
        }.items(),
    )

    moveit_rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "moveit_rviz.launch.py")
        ),
        launch_arguments={
            "robot_name": robot_name,
            "namespace": robot_name,
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    return LaunchDescription([
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument(
            "world",
            default_value=PathJoinSubstitution([
                gazebo_pkg, "world", "kmr_iiwa.world",
            ]),
        ),
        gazebo,
        move_group,
        moveit_rviz,
    ])
