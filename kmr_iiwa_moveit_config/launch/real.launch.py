"""Real KMR iiwa + MoveIt.

Starts the existing Sunrise bringup (the ``sunrise_communication`` launch, which
talks to the KMR controller over Sunrise/Ethernet) and MoveIt, both under
``/kmr_iiwa``.

What this launch deliberately does *not* do:

* no ``robot_state_publisher`` - the real robot publishes its TF (including the
  arm's joint transforms) and the KMR/odometry node publishes
  ``odom -> kmr_iiwa_base_link``;
* no ``static_virtual_joint_tfs`` - same reason, the world/base transform is
  already provided;
* no ``controller_manager`` - the arm is driven through the Sunrise interface by
  ``lbr_commands_node``, which is already running in the namespace and offers
  ``/kmr_iiwa/arm_controller/follow_joint_trajectory``.

MoveIt therefore only needs the hardware-neutral URDF (as a parameter, not as a
published topic), the controller mapping and the namespaced joint states.
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
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    moveit_pkg = get_package_share_directory("kmr_iiwa_moveit_config")
    ros2_pkg = get_package_share_directory("kmr_iiwa_ros2")

    robot_name = LaunchConfiguration("robot_name")
    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # The bringup can be skipped when the Sunrise connection is already running
    # (e.g. started by hand while testing).  The scoped GroupAction keeps the
    # namespace override local: launch configurations are global across
    # includes, so leaking ``namespace`` would also affect the includes below.
    bringup = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(ros2_pkg, "launch",
                                 "sunrise_communication.launch.py")
                ),
                launch_arguments={"namespace": namespace}.items(),
            ),
        ],
        condition=IfCondition(LaunchConfiguration("bringup")),
    )

    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "move_group.launch.py")
        ),
        launch_arguments={
            "robot_name": robot_name,
            "namespace": namespace,
            "use_sim_time": use_sim_time,
            "joint_states_topic": PythonExpression([
                "'/' + '", namespace, "' + '/joint_states'",
            ]),
            "controllers_file": "config/moveit_controllers.yaml",
            # The arm controller is managed by the Sunrise bringup.
            "moveit_manage_controllers": "false",
        }.items(),
    )

    moveit_rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "moveit_rviz.launch.py")
        ),
        launch_arguments={
            "robot_name": robot_name,
            "namespace": namespace,
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    return LaunchDescription([
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        DeclareLaunchArgument(
            "namespace",
            default_value="kmr_iiwa",
            description="Namespace shared by the bringup, move_group and RViz",
        ),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument(
            "bringup",
            default_value="false",
            description=(
                "Start sunrise_communication.launch.py (set false if the "
                "Sunrise connection is already running)"
            ),
        ),
        bringup,
        move_group,
        moveit_rviz,
    ])
