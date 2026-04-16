import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import pyspacemouse
from easyhid.easyhid import HIDException  # Handle HID errors (disconnection issues)

class SpaceMouseJoy(Node):
    """Publishes SpaceMouse input as a Joy message."""

    TIMER_FREQUENCY = 0.01  # Timer frequency for publishing Joy messages
    RECONNECT_FREQUENCY = 1.0  # Timer frequency for attempting reconnection

    def __init__(self):
        super().__init__('spacemouse_joy_publisher')
        self.publisher_ = self.create_publisher(Joy, '/spacemouse_joy', 10)
        self.timer = self.create_timer(self.TIMER_FREQUENCY, self.publish_joy_data)  # Timer for publishing Joy messages
        self.reconnect_timer = None

        failed = True

        while failed:
            try:
                pyspacemouse.open()
                failed = False
            except Exception as e:
                self.get_logger().error(f'Failed to connect SpaceMouse: {e}')


    def start_reconnect_timer(self):
        """Starts a timer to attempt reconnection to the SpaceMouse."""
        if self.reconnect_timer is None:
            self.reconnect_timer = self.create_timer(self.RECONNECT_FREQUENCY, self.attempt_reconnect)
            self.get_logger().info('Started reconnect timer.')

    def stop_reconnect_timer(self):
        """Stops the reconnection timer."""
        if self.reconnect_timer is not None:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
            self.get_logger().info('Stopped reconnect timer.')

    def attempt_reconnect(self):
        """Attempts to reconnect to the SpaceMouse."""
        try:
            if pyspacemouse.open():
                self.get_logger().info('Reconnected to SpaceMouse.')
                self.stop_reconnect_timer()
            else:
                self.get_logger().error('Failed to reconnect SpaceMouse. Publishing zero values.')
        except Exception as e:
            self.get_logger().error(f'Error while attempting to reconnect SpaceMouse: {e}')

    def publish_joy_data(self):
        """Reads SpaceMouse state and publishes a Joy message."""
        try:
            state = pyspacemouse.read()
            if state is None:
                self.get_logger().warn('SpaceMouse returned no data! Publishing zero values.')
                state = self.create_zero_state()

            joy_msg = self.create_joy_message(state)
            self.publisher_.publish(joy_msg)

            # Print the Joy message axes and buttons for debugging

            # Full float data:
            #self.get_logger().info(f'Published: axes={joy_msg.axes}, buttons={joy_msg.buttons}')
            
            # Abbreviated float data for better readability:
            printable_axes = [f"{x:6.2f}" for x in joy_msg.axes]
            printable_buttons = " ".join(str(b) for b in joy_msg.buttons)
            self.get_logger().info(f"Axes: {' '.join(printable_axes)}   Buttons: {printable_buttons}")

        except HIDException as e:
            self.get_logger().warn(f'SpaceMouse read error: {e}. Publishing zero values.')
            joy_msg = self.create_joy_message(self.create_zero_state())
            self.publisher_.publish(joy_msg)
            self.start_reconnect_timer()

        except Exception as e:
            self.get_logger().error(f'Unexpected error while reading SpaceMouse: {e}')
            joy_msg = self.create_joy_message(self.create_zero_state())
            self.publisher_.publish(joy_msg)

    def create_joy_message(self, state):
        """Converts SpaceMouse state into a Joy message."""
        joy_msg = Joy()

        # Matching axes to twist msg axes
        
        joy_msg.axes = [
            # Publishing as epxected by twist
            float(state.y) if state.y is not None else 0.0,  # Translation Y (forward/backward)
            float(state.x) if state.x is not None else 0.0,  # Translation X (left/right)
            float(state.z) if state.z is not None else 0.0,  # Translation Z (up/down)

            # Publishing as expected for conversion in quaternion
            float(state.roll) if state.roll is not None else 0.0,  # Rotation Y (roll)
            float(state.pitch) if state.pitch is not None else 0.0,  # Rotation X (pitch)
            float(state.yaw) if state.yaw is not None else 0.0,  # Rotation Z (yaw/twist)
        ]
        joy_msg.buttons = [
            int(state.buttons[0]) if state.buttons and state.buttons[0] is not None else 0,  # Button 1 (left)
            int(state.buttons[1]) if state.buttons and state.buttons[1] is not None else 0,  # Button 2 (right)
        ]

        return joy_msg

    def create_zero_state(self):
        """Creates a state with zero values for all axes."""
        class ZeroState:
            x = y = z = pitch = yaw = roll = 0.0
            buttons = [0, 0]

        return ZeroState()


def main(args=None):
    rclpy.init(args=args)
    node = SpaceMouseJoy()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()