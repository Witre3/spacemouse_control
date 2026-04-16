import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped

class SpaceMouseToTwist(Node):
    def __init__(self):
        super().__init__('spacemouse_to_twist')

        # Parameters
        self.declare_parameter('deadman_button', 0)         # index in Joy.buttons
        self.declare_parameter('scale_linear', 70.7)      # m/s per raw unit
        self.declare_parameter('scale_angular', 0.8)     # rad/s per raw unit
        #self.declare_parameter('deadzone_linear', 0.02)
        #self.declare_parameter('deadzone_angular', 0.1)

        self.deadman_button = self.get_parameter('deadman_button').get_parameter_value().integer_value
        self.scale_linear = self.get_parameter('scale_linear').get_parameter_value().double_value
        self.scale_angular = self.get_parameter('scale_angular').get_parameter_value().double_value

        self.sub = self.create_subscription(Joy, '/spacemouse_joy',
                                            self.joy_cb, 10)
        self.pub = self.create_publisher(TwistStamped,
                                         '/arm_command_node/twist_cmd/mux/joy',
                                         10)

        self.get_logger().info('SpaceMouse → Twist bridge started')

    def joy_cb(self, msg: Joy):
        # Deadman: if button not pressed, send zero twist
        deadman_pressed = False
        if 0 <= self.deadman_button < len(msg.buttons):
            deadman_pressed = bool(msg.buttons[self.deadman_button])

        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()
        twist.header.frame_id = 'base_link'  # adjust if your stack expects a specific frame

        if deadman_pressed:
            # SpaceMouse axes: [y, x, z, roll, pitch, yaw] in your client code
            # Map to Kinova twist: linear x,y,z and angular x,y,z
            axes = msg.axes
            if len(axes) >= 6:
                # Tweak signs/mapping to taste
                twist.twist.linear.x  =  self.scale_linear  * axes[0]   # x
                twist.twist.linear.y  =  self.scale_linear  * axes[1]   # y
                twist.twist.linear.z  =  self.scale_linear  * axes[2]   # z

                twist.twist.angular.x =  self.scale_angular * axes[3]   # roll
                twist.twist.angular.y =  self.scale_angular * axes[4]   # pitch
                twist.twist.angular.z =  self.scale_angular * axes[5]   # yaw
        else:
            # All zeros (stop)
            #pass
            axes = msg.axes
            #WITH Tool Reference Frame
            #twist.twist.linear.x  =  self.scale_linear  * -axes[1]   # x
            #twist.twist.linear.y  =  self.scale_linear  * axes[2]   # y
            #twist.twist.linear.z  =  self.scale_linear  * axes[0]   # z

            #twist.twist.angular.x =  self.scale_angular * axes[4]   # roll
            #twist.twist.angular.y =  self.scale_angular * -axes[5]   # pitch
            #twist.twist.angular.z =  self.scale_angular * axes[3]   # yaw

            #With Base Reference Frame
            twist.twist.linear.x  =  self.scale_linear  * axes[0]   # x
            twist.twist.linear.y  =  self.scale_linear  * -axes[1]   # y
            twist.twist.linear.z  =  self.scale_linear  * axes[2]   # z

            twist.twist.angular.x =  self.scale_angular * axes[3]   # roll
            twist.twist.angular.y =  self.scale_angular * axes[4]   # pitch
            twist.twist.angular.z =  self.scale_angular * -axes[5]   # yaw
            

        self.pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = SpaceMouseToTwist()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()