"""Real KMR iiwa + MoveIt.

Starts the existing Sunrise bringup (the ``sunrise_communication`` launch, which
talks to the KMR controller over Sunrise/Ethernet) and MoveIt, both under
``/kmr_iiwa``.

What this launch deliberately does *not* do:

* no ``static_virtual_joint_tfs`` - the KMR/odometry node already publishes
  ``odom -> kmr_iiwa_base_link``;
* no ``controller_manager`` - the arm is driven through the Sunrise interface by
  ``lbr_commands_node``, which is already running in the namespace and offers
  ``/kmr_iiwa/follow_joint_trajectory_controller/follow_joint_trajectory``.

A ``robot_state_publisher`` is started here so the arm's link transforms are
published from ``/kmr_iiwa/joint_states``.

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
from launch_ros.actions import PushRosNamespace, SetRemap


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

    # Publish the base_link -> arm links transforms from the joint states.  The
    # generic rsp launch file does not handle namespaces or TF remaps, so scope
    # them here (tf2_ros treats /tf and /tf_static as absolute names).
    rsp = GroupAction([
        PushRosNamespace(namespace),
        SetRemap(src="/tf", dst="tf"),
        SetRemap(src="/tf_static", dst="tf_static"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(moveit_pkg, "launch", "rsp.launch.py")
            ),
        ),
    ])

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

    # Servo is opt-in.  On the real backend it publishes Float64MultiArray
    # joint positions, which lbr_commands_node forwards to the arm as
    # SetJointServoPosition commands.
    servo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "servo.launch.py")
        ),
        launch_arguments={
            "namespace": namespace,
            "use_sim_time": use_sim_time,
            "config_file": "config/servo_real.yaml",
            "command_type": "twist",
        }.items(),
        condition=IfCondition(LaunchConfiguration("servo")),
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
            "servo",
            default_value="false",
            description="Start MoveIt Servo (twist -> SetJointServoPosition)",
        ),
        DeclareLaunchArgument(
            "bringup",
            default_value="false",
            description=(
                "Start sunrise_communication.launch.py (set false if the "
                "Sunrise connection is already running)"
            ),
        ),
        bringup,
        rsp,
        move_group,
        moveit_rviz,
        servo,
    ])
