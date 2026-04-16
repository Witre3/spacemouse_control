import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import socket
import struct
import threading

class SpaceMouseServer(Node):
    def __init__(self):
        super().__init__('spacemouse_tcp_server')
        self.publisher = self.create_publisher(Joy, '/spacemouse_joy', 10)

    def publish_from_data(self, data: bytes):
    # 6 floats (4 bytes each) + 2 unsigned bytes = 26 bytes total
        if len(data) != 26:
            self.get_logger().warn(f"Invalid data length: {len(data)}")
            return

        axes_and_buttons = struct.unpack('6f2B', data)  # 8 values
        joy = Joy()
        joy.axes = list(axes_and_buttons[:6])
        joy.buttons = [int(axes_and_buttons[6]), int(axes_and_buttons[7])]
        self.publisher.publish(joy)



def tcp_server(node, ip='0.0.0.0', port=8584):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen(1)

    conn, addr = server.accept()
    node.get_logger().info(f"TCP connection from {addr}")

    buffer = b""
    FRAME_SIZE = 26  # 6 floats (4B) + 2 bytes

    try:
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                node.get_logger().info("TCP client disconnected")
                break

            buffer += chunk

            # process all complete frames in the buffer
            while len(buffer) >= FRAME_SIZE:
                frame = buffer[:FRAME_SIZE]
                buffer = buffer[FRAME_SIZE:]
                node.publish_from_data(frame)

    except Exception as e:
        node.get_logger().error(f"TCP server error: {e}")
    finally:
        conn.close()
        server.close()

def main(args=None):
    rclpy.init(args=args)
    node = SpaceMouseServer()
    thread = threading.Thread(target=tcp_server, args=(node,), daemon=True)
    thread.start()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
