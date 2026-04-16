import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import pyspacemouse
from easyhid.easyhid import HIDException
import socket
import struct

class SpaceMouseJoy(Node):
    """Publishes SpaceMouse input over TCP as serialized Joy messages."""

    TIMER_FREQUENCY = 0.01  # 100 Hz
    RECONNECT_FREQUENCY = 1.0  # Reconnect attempt frequency for SpaceMouse
    TCP_IP = 'rove-hotspot.local' #hostname of rove router
    TCP_PORT = 8584

    def __init__(self):
        super().__init__('spacemouse_tcp_client')
        self.timer = self.create_timer(self.TIMER_FREQUENCY, self.publish_joy_data)
        self.reconnect_timer = None
        self.sock = None

        self.connect_tcp()

        failed = True
        while failed:
            try:
                pyspacemouse.open()
                failed = False
            except Exception as e:
                self.get_logger().error(f'Failed to connect SpaceMouse: {e}')

    def connect_tcp(self):
        """Attempts to connect to the Jetson TCP server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.0)
            self.sock.connect((self.TCP_IP, self.TCP_PORT))
            self.get_logger().info(f"Connected to TCP server at {self.TCP_IP}:{self.TCP_PORT}")
        except Exception as e:
            self.get_logger().error(f"Could not connect to TCP server: {e}")
            self.sock = None

    def start_reconnect_timer(self):
        if self.reconnect_timer is None:
            self.reconnect_timer = self.create_timer(self.RECONNECT_FREQUENCY, self.attempt_reconnect)
            self.get_logger().info('Started reconnect timer.')

    def stop_reconnect_timer(self):
        if self.reconnect_timer is not None:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
            self.get_logger().info('Stopped reconnect timer.')

    def attempt_reconnect(self):
        try:
            if pyspacemouse.open():
                self.get_logger().info('Reconnected to SpaceMouse.')
                self.stop_reconnect_timer()
            else:
                self.get_logger().warn('Failed to reconnect SpaceMouse.')
        except Exception as e:
            self.get_logger().error(f'Reconnect error: {e}')

    def publish_joy_data(self):
        try:
            state = pyspacemouse.read()
            if state is None:
                self.get_logger().warn('No SpaceMouse data. Sending zero values.')
                state = self.create_zero_state()

            joy_msg = self.create_joy_message(state)

            if self.sock:
                packed = struct.pack('6f2B', *joy_msg.axes, *joy_msg.buttons)
                self.sock.sendall(packed)
            else:
                self.get_logger().warn('TCP socket not connected.')

        except HIDException as e:
            self.get_logger().warn(f'SpaceMouse read error: {e}. Sending zero values.')
            joy_msg = self.create_joy_message(self.create_zero_state())
            if self.sock:
                packed = struct.pack('6f2B', *joy_msg.axes, *joy_msg.buttons)
                self.sock.sendall(packed)
            self.start_reconnect_timer()
        except Exception as e:
            self.get_logger().error(f'Unexpected error: {e}')

    def create_joy_message(self, state):
        joy_msg = Joy()
        joy_msg.axes = [
            float(state.y) if state.y is not None else 0.0,
            float(state.x) if state.x is not None else 0.0,
            float(state.z) if state.z is not None else 0.0,
            float(state.roll) if state.roll is not None else 0.0,
            float(state.pitch) if state.pitch is not None else 0.0,
            float(state.yaw) if state.yaw is not None else 0.0,
        ]
        joy_msg.buttons = [
            int(state.buttons[0]) if state.buttons and state.buttons[0] is not None else 0,
            int(state.buttons[1]) if state.buttons and state.buttons[1] is not None else 0,
        ]
        return joy_msg

    def create_zero_state(self):
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
