"""Shared move_group launch, used by the demo, Gazebo and real-robot launches.

Everything that differs between backends is an argument, so the three entry
points stay identical:

* ``description_file``  - hardware-neutral URDF used only by move_group.  The
  Gazebo-specific URDF must NOT be used here: it contains the virtual base
  joints, which would clash with the SRDF virtual joint.
* ``controllers_file``  - MoveIt controller mapping (relative to this package
  or absolute).
* ``namespace``         - run move_group under the robot namespace.  Gazebo
  publishes its TF/joint states under ``/kmr_iiwa``, so move_group must live
  there too for relative ``tf``/``joint_states`` names to resolve correctly.
* ``joint_states_topic``- explicit joint state topic (relative names follow the
  node namespace).
* ``moveit_manage_controllers`` - each backend starts its own controllers, so
  MoveIt must not call ``switch_controller``.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def _as_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def _default_description():
    return os.path.join(
        get_package_share_directory("kmr_iiwa_urdf"),
        "urdf",
        "kmr_iiwa.urdf.xacro",
    )


def _launch_setup(context):
    cfg = context.launch_configurations
    robot_name = cfg["robot_name"]

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="kmr_iiwa_moveit_config")
        .robot_description(
            file_path=cfg["description_file"],
            mappings={"robot_name": robot_name},
        )
        .trajectory_execution(
            file_path=cfg["controllers_file"],
            moveit_manage_controllers=_as_bool(
                cfg["moveit_manage_controllers"]),
        )
        .to_moveit_configs()
    )

    publish_planning_scene = _as_bool(
        cfg["publish_monitored_planning_scene"])
    move_group_configuration = {
        "allow_trajectory_execution": _as_bool(
            cfg["allow_trajectory_execution"]),
        "publish_planning_scene": publish_planning_scene,
        "publish_geometry_updates": publish_planning_scene,
        "publish_state_updates": publish_planning_scene,
        "publish_transforms_updates": publish_planning_scene,
        "monitor_dynamics": False,
        "use_sim_time": _as_bool(cfg["use_sim_time"]),
    }

    node_kwargs = {}
    if cfg["namespace"]:
        node_kwargs["namespace"] = cfg["namespace"]

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict(), move_group_configuration],
        remappings=[("joint_states", cfg["joint_states_topic"])],
        **node_kwargs,
    )
    return [move_group]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="Namespace for move_group (e.g. kmr_iiwa in Gazebo)",
        ),
        DeclareLaunchArgument(
            "description_file",
            default_value=_default_description(),
            description=(
                "URDF/xacro used by move_group. Absolute path or path relative "
                "to kmr_iiwa_moveit_config."
            ),
        ),
        DeclareLaunchArgument(
            "controllers_file",
            default_value="config/moveit_controllers.yaml",
            description="MoveIt controller mapping file",
        ),
        DeclareLaunchArgument(
            "moveit_manage_controllers",
            default_value="false",
            description="Let MoveIt switch controller states via switch_controller",
        ),
        DeclareLaunchArgument(
            "joint_states_topic",
            default_value="joint_states",
            description="Topic move_group reads the current joint state from",
        ),
        DeclareLaunchArgument(
            "use_sim_time", default_value="false"),
        DeclareLaunchArgument(
            "allow_trajectory_execution", default_value="true"),
        DeclareLaunchArgument(
            "publish_monitored_planning_scene", default_value="true"),
        OpaqueFunction(function=_launch_setup),
    ])
