import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_difference(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


class RotateServer(Node):

    def __init__(self):
        super().__init__('rotate_server')
        self.declare_parameter('turn_speed', 0.5)
        self.yaw = None

        # execute() loops until the turn is done, so odom needs its own thread to keep updating
        group = ReentrantCallbackGroup()
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10, callback_group=group)
        self.action_server = ActionServer(
            self, Rotate, 'rotate',
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=lambda goal_handle: CancelResponse.ACCEPT,
            callback_group=group,
        )

    def on_odom(self, msg):
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def on_goal(self, goal):
        if goal.angle == 0.0 or self.yaw is None:
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def execute(self, goal_handle):
        goal = goal_handle.request.angle
        self.get_logger().info(f'Rotating {goal:.2f} rad')

        twist = Twist()
        twist.angular.z = math.copysign(self.get_parameter('turn_speed').value, goal)
        feedback = Rotate.Feedback()
        result = Rotate.Result()
        turned = 0.0
        last_yaw = self.yaw

        while rclpy.ok() and abs(turned) < abs(goal):
            if goal_handle.is_cancel_requested:
                self.cmd_vel_pub.publish(Twist())
                goal_handle.canceled()
                result.turned = turned
                self.get_logger().info(f'Canceled after {turned:.2f} rad')
                return result

            self.cmd_vel_pub.publish(twist)
            time.sleep(0.05)

            # add up small steps instead of yaw - start_yaw, which jumps at +-pi
            yaw = self.yaw
            turned += angle_difference(yaw, last_yaw)
            last_yaw = yaw
            feedback.turned = turned
            goal_handle.publish_feedback(feedback)

        self.cmd_vel_pub.publish(Twist())
        goal_handle.succeed()
        result.turned = turned
        self.get_logger().info(f'Done, turned {turned:.2f} rad')
        return result


def main():
    rclpy.init()
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
