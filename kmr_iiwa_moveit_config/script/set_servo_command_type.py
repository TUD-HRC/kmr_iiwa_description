#!/usr/bin/env python3

"""Set MoveIt Servo's command type once the service is available.

Servo 2.12.x leaves ``expected_command_type_`` uninitialized, so every incoming
twist/joint-jog/pose command is rejected with

    Command type has not been set, cannot accept input

until ``~/switch_command_type`` is called.  The service must be called again
every time Servo restarts.  This node waits for the service, sets the requested
type (TWIST by default) and exits.
"""

import sys

import rclpy
from moveit_msgs.srv import ServoCommandType
from rclpy.node import Node

# 0 = JOINT_JOG, 1 = TWIST, 2 = POSE
COMMAND_TYPES = {
    "joint_jog": ServoCommandType.Request.JOINT_JOG,
    "twist": ServoCommandType.Request.TWIST,
    "pose": ServoCommandType.Request.POSE,
}


class SetServoCommandType(Node):
    def __init__(self):
        super().__init__("set_servo_command_type")

        self.declare_parameter("servo_node", "servo_node")
        self.declare_parameter("command_type", "twist")

        servo_node = self.get_parameter("servo_node").value
        command_type = str(self.get_parameter("command_type").value).lower()

        if command_type not in COMMAND_TYPES:
            self.get_logger().error(
                f"Unknown command_type '{command_type}', "
                f"expected one of {list(COMMAND_TYPES)}")
            raise SystemExit(1)

        # Relative name: resolves against this node's namespace, so it follows
        # the robot namespace used by the launch file.
        self.service_name = f"{servo_node}/switch_command_type"
        self.command_type = COMMAND_TYPES[command_type]

    def run(self):
        client = self.create_client(ServoCommandType, self.service_name)
        while rclpy.ok() and not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                f"Waiting for service {self.service_name} ...")

        if not rclpy.ok():
            return 1

        request = ServoCommandType.Request()
        request.command_type = self.command_type
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)

        if future.result() is None:
            self.get_logger().error(
                f"Call to {self.service_name} failed or timed out")
            return 1

        self.get_logger().info(
            f"Servo command type set to {request.command_type} "
            f"(success={future.result().success})")
        return 0 if future.result().success else 1


def main(args=None):
    rclpy.init(args=args)
    node = SetServoCommandType()
    try:
        return node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
