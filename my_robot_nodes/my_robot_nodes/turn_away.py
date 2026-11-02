import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.msg import ObstacleInfo

FORWARD_SPEED = 0.2
TURN_SPEED = 0.5


class TurnAway(Node):

    def __init__(self):
        super().__init__('turn_away')
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(ObstacleInfo, 'obstacle', self.on_obstacle, 10)

    def on_obstacle(self, msg):
        twist = Twist()
        if msg.too_close:
            # angle > 0 means the obstacle is on the left, so turn right
            twist.angular.z = -TURN_SPEED if msg.angle > 0.0 else TURN_SPEED
        else:
            twist.linear.x = FORWARD_SPEED
        self.cmd_vel_pub.publish(twist)


def main():
    rclpy.init()
    node = TurnAway()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
