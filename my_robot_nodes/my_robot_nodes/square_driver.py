import math

import rclpy
from action_msgs.msg import GoalStatus
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):

    def __init__(self):
        super().__init__('square_driver')
        self.declare_parameter('side_length', 0.5)
        self.has_odom = False

        self.create_subscription(Odometry, 'odom', self.on_odom, 10)
        self.drive_client = ActionClient(self, DriveDistance, 'drive_distance')
        self.rotate_client = ActionClient(self, Rotate, 'rotate')

    def on_odom(self, msg):
        self.has_odom = True

    def run_goal(self, client, goal):
        client.wait_for_server()
        send_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return result_future.result().status == GoalStatus.STATUS_SUCCEEDED

    def drive_square(self):
        # both servers reject goals until odometry has arrived
        self.get_logger().info('Waiting for odometry')
        while rclpy.ok() and not self.has_odom:
            rclpy.spin_once(self, timeout_sec=0.5)

        side_length = self.get_parameter('side_length').value
        for side in range(1, 5):
            self.get_logger().info(f'Side {side}: driving {side_length:.2f} m')
            if not self.run_goal(self.drive_client, DriveDistance.Goal(distance=side_length)):
                self.get_logger().error(f'Drive failed on side {side}, stopping')
                return

            self.get_logger().info(f'Side {side}: turning left')
            if not self.run_goal(self.rotate_client, Rotate.Goal(angle=math.pi / 2)):
                self.get_logger().error(f'Turn failed on side {side}, stopping')
                return

        self.get_logger().info('Square done')


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        node.drive_square()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
