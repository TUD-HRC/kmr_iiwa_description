"""MoveIt RViz, optionally in the robot namespace.

In Gazebo both move_group and RViz run under ``/kmr_iiwa`` so that the relative
topics used by the MotionPlanning plugin (``monitored_planning_scene``,
``display_planned_path``, ``tf``, ``robot_description``) resolve to the
namespaced ones.
"""

import os
import tempfile

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def _as_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def _rviz_config_with_namespace(source, namespace):
    """Return a copy of ``source`` with the MotionPlanning display namespace set.

    The MotionPlanning display cannot inherit the ROS namespace it happens to
    run in.  It builds every move_group name with MoveIt's own helper

        rclcpp::names::append(move_group_namespace, "move_action")
        // -> clean(move_group_namespace + "/" + "move_action")

    so an empty ``Move Group Namespace`` yields the *absolute* name
    ``/move_action``.  With RViz in ``/kmr_iiwa`` that silently talks to a
    non-existent root action server: Plan does nothing, scene edits are
    published to the wrong topics, and the plugin idles for 2 x 30 s in
    ``wait_for_action_server`` before it becomes usable.
    """
    with open(source) as handle:
        config = yaml.safe_load(handle)

    for display in config.get("Visualization Manager", {}).get("Displays", []):
        if str(display.get("Class", "")).endswith("MotionPlanning"):
            display["Move Group Namespace"] = namespace

    fd, path = tempfile.mkstemp(prefix="kmr_iiwa_moveit_", suffix=".rviz")
    with os.fdopen(fd, "w") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
    return path


def _default_description():
    return os.path.join(
        get_package_share_directory("kmr_iiwa_urdf"),
        "urdf",
        "kmr_iiwa.urdf.xacro",
    )


def _launch_setup(context):
    cfg = context.launch_configurations

    moveit_config = MoveItConfigsBuilder(
        cfg["robot_name"], package_name="kmr_iiwa_moveit_config"
    ).robot_description(
        file_path=cfg["description_file"],
        mappings={"robot_name": cfg["robot_name"]},
    ).to_moveit_configs()

    parameters = [
        moveit_config.robot_description,
        # move_group is configured with publish_robot_description_semantic=false
        # (we must not publish a second, hardware-neutral robot_description next
        # to robot_state_publisher's), so RViz needs the SRDF as a parameter.
        moveit_config.robot_description_semantic,
        moveit_config.planning_pipelines,
        moveit_config.robot_description_kinematics,
        moveit_config.joint_limits,
        {"use_sim_time": _as_bool(cfg["use_sim_time"])},
    ]

    node_kwargs = {}
    namespace = cfg["namespace"].strip("/")
    rviz_config = cfg["rviz_config"]
    if namespace:
        # move_group runs in this namespace; see _rviz_config_with_namespace.
        node_kwargs["namespace"] = cfg["namespace"]
        rviz_config = _rviz_config_with_namespace(rviz_config, "/" + namespace)

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        respawn=False,
        arguments=["-d", rviz_config],
        parameters=parameters,
        **node_kwargs,
    )
    return [rviz]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="Namespace for RViz (same as move_group)",
        ),
        DeclareLaunchArgument(
            "description_file",
            default_value=_default_description(),
            description="URDF/xacro used by the MoveIt RViz plugin",
        ),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=os.path.join(
                get_package_share_directory("kmr_iiwa_moveit_config"),
                "config",
                "moveit.rviz",
            ),
        ),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        OpaqueFunction(function=_launch_setup),
    ])
