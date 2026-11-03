"""MoveIt Servo teleoperation for the kmr_iiwa arm.

Servo converts Cartesian twist commands into a stream of joint commands.  The
output format is selected by ``config_file``:

* ``config/servo.yaml`` (demo/Gazebo) publishes ``trajectory_msgs/JointTrajectory``
  on the arm ``joint_trajectory_controller``;
* ``config/servo_real.yaml`` (real robot) publishes ``std_msgs/Float64MultiArray``
  on ``servo_joint_cmd``, which ``lbr_commands_node`` forwards to the arm as
  ``SetJointServoPosition``.

Servo is not the primary planning scene monitor: move_group keeps publishing
the planning scene and Servo reads it for collision and singularity checks.
Start this launch after (or together with) the backend that runs move_group.

Topics with ``namespace:=kmr_iiwa``:

* input   ``/kmr_iiwa/servo_node/delta_twist_cmds``  geometry_msgs/TwistStamped
* status  ``/kmr_iiwa/servo_node/status``            moveit_msgs/ServoStatus
* pause   ``/kmr_iiwa/servo_node/pause_servo``       std_srvs/SetBool
* output  ``/kmr_iiwa/follow_joint_trajectory_controller/joint_trajectory``
          (``config/servo.yaml``) or ``/kmr_iiwa/servo_joint_cmd``
          (``config/servo_real.yaml``)

Publish a **stamped** TwistStamped yourself (frame ``odom``)::

    ros2 topic pub -r 20 /kmr_iiwa/servo_node/delta_twist_cmds \\
      geometry_msgs/msg/TwistStamped \\
      "{header: {frame_id: odom}, twist: {linear: {x: 0.05}}}"

A zero stamp is treated as stale and the command is dropped.

Servo 2.12.x leaves its command type uninitialized, so it rejects every command
until ``~/switch_command_type`` is called.  ``set_servo_command_type.py`` does
that automatically on every start.

Servo streams commands only while they keep arriving (``incoming_command_timeout``
in ``config/servo.yaml``).  A zero twist is still a valid command and holds the
current pose.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch_param_builder import ParameterBuilder
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
    namespace = cfg["namespace"].strip("/")

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="kmr_iiwa_moveit_config")
        .robot_description(
            file_path=cfg["description_file"],
            mappings={"robot_name": robot_name},
        )
        .to_moveit_configs()
    )

    # Servo's generated parameter listener uses the ``moveit_servo`` prefix, so
    # the flat YAML must be nested under that key.  Without it the node dies
    # with "parameter 'moveit_servo.move_group_name' is not initialized".
    servo_params = ParameterBuilder("kmr_iiwa_moveit_config").yaml(
        cfg["config_file"]
    ).to_dict()

    node_kwargs = {}
    if namespace:
        node_kwargs["namespace"] = namespace

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node",
        name="servo_node",
        output="screen",
        parameters=[
            {"moveit_servo": servo_params},
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            {"use_sim_time": _as_bool(cfg["use_sim_time"])},
        ],
        # /tf and /tf_static are absolute names in tf2_ros, so the namespace
        # alone does not move them; these remaps keep Servo on /kmr_iiwa/tf.
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
        **node_kwargs,
    )

    # Servo's expected_command_type_ is uninitialized in 2.12.x, so it rejects
    # all input until the service is called.  This one-shot node waits for the
    # service, sets the type and exits.
    set_command_type = Node(
        package="kmr_iiwa_moveit_config",
        executable="set_servo_command_type.py",
        name="set_servo_command_type",
        output="screen",
        parameters=[{"command_type": cfg["command_type"]}],
        **node_kwargs,
    )

    return [servo_node, set_command_type]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("robot_name", default_value="kmr_iiwa"),
        DeclareLaunchArgument(
            "namespace",
            default_value="kmr_iiwa",
            description="Namespace shared with move_group (e.g. kmr_iiwa)",
        ),
        DeclareLaunchArgument(
            "description_file",
            default_value=_default_description(),
            description="Hardware-neutral URDF/xacro used by Servo",
        ),
        DeclareLaunchArgument(
            "config_file",
            default_value="config/servo.yaml",
            description=(
                "Servo parameters, relative to this package: config/servo.yaml "
                "(JointTrajectory) or config/servo_real.yaml (Float64MultiArray)"
            ),
        ),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument(
            "command_type",
            default_value="twist",
            description="Servo input mode: twist, joint_jog or pose",
        ),
        OpaqueFunction(function=_launch_setup),
    ])
