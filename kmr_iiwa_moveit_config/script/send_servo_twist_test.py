import sys
import time

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from rclpy.parameter import Parameter

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
ZERO_STAMP = len(sys.argv) > 2 and sys.argv[2] == "zero"
LINEAR_X = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05

rclpy.init()
node = Node(
    "servo_twist_test",
    parameter_overrides=[Parameter("use_sim_time", Parameter.Type.BOOL, True)],
)
pub = node.create_publisher(
    TwistStamped, "/kmr_iiwa/servo_node/delta_twist_cmds", 10
)


def tick():
    m = TwistStamped()
    if not ZERO_STAMP:
        m.header.stamp = node.get_clock().now().to_msg()
    m.header.frame_id = "odom"
    m.twist.linear.x = LINEAR_X
    pub.publish(m)


node.create_timer(0.02, tick)
end = time.time() + DURATION
while rclpy.ok() and time.time() < end:
    rclpy.spin_once(node, timeout_sec=0.05)
node.destroy_node()
rclpy.shutdown()
