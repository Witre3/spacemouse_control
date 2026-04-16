import asyncio
import json
import threading

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
import websockets


class HaplyPosePublisher(Node):
    """Connects to a Haply websocket and publishes the cursor position as PoseStamped."""

    PUBLISH_PERIOD = 0.01
    RECONNECT_DELAY = 1.0

    def __init__(self):
        super().__init__('haply_pose_publisher')

        self.declare_parameter('haply_uri', 'ws://localhost:10001')
        self.declare_parameter('pose_topic', '/haply/pose')
        self.declare_parameter('frame_id', 'haply')

        self.haply_uri = self.get_parameter('haply_uri').get_parameter_value().string_value
        self.pose_topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self.publisher_ = self.create_publisher(PoseStamped, self.pose_topic, 10)
        self.timer = self.create_timer(self.PUBLISH_PERIOD, self.publish_pose)

        self._lock = threading.Lock()
        self._latest_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self._device_id = None
        self._connected = False

        self._thread = threading.Thread(target=self._run_websocket_loop, daemon=True)
        self._thread.start()

        self.get_logger().info(
            f'Publishing Haply pose on {self.pose_topic} from {self.haply_uri}'
        )

    def _run_websocket_loop(self):
        asyncio.run(self._websocket_loop())

    async def _websocket_loop(self):
        while rclpy.ok():
            try:
                async with websockets.connect(self.haply_uri) as ws:
                    self.get_logger().info(f'Connected to Haply device at {self.haply_uri}')
                    await self._consume_messages(ws)
            except Exception as exc:
                with self._lock:
                    self._connected = False
                    self._device_id = None
                self.get_logger().warn(
                    f'Failed to communicate with Haply device: {exc}. Retrying in {self.RECONNECT_DELAY:.1f}s'
                )
                await asyncio.sleep(self.RECONNECT_DELAY)

    async def _consume_messages(self, ws):
        first_state = json.loads(await ws.recv())
        inverse3_devices = first_state.get('inverse3', [])
        if not inverse3_devices:
            raise RuntimeError('No inverse3 device found in Haply handshake message')

        with self._lock:
            self._device_id = inverse3_devices[0]['device_id']
            self._connected = True

        await self._update_position_from_state(first_state, ws)

        while rclpy.ok():
            state = json.loads(await ws.recv())
            await self._update_position_from_state(state, ws)

    async def _update_position_from_state(self, state, ws):
        inverse3_devices = state.get('inverse3', [])
        if not inverse3_devices:
            return

        device_state = inverse3_devices[0].get('state', {})
        position = device_state.get('cursor_position')
        if position is not None:
            with self._lock:
                self._latest_position = {
                    'x': float(position.get('x', 0.0)),
                    'y': float(position.get('y', 0.0)),
                    'z': float(position.get('z', 0.0)),
                }

        await ws.send(json.dumps(self._create_keepalive()))

    def _create_keepalive(self):
        return {
            'inverse3': [{
                'device_id': self._device_id,
                'commands': {
                    'set_cursor_force': {
                        'vector': {'x': 0, 'y': 0, 'z': 0},
                    }
                },
            }]
        }

    def publish_pose(self):
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = self.frame_id

        with self._lock:
            position = dict(self._latest_position)
            connected = self._connected

        pose.pose.position.x = position['x']
        pose.pose.position.y = position['y']
        pose.pose.position.z = position['z']

        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 1.0

        if not connected:
            pose.pose.position.x = 0.0
            pose.pose.position.y = 0.0
            pose.pose.position.z = 0.0

        self.publisher_.publish(pose)


def main(args=None):
    rclpy.init(args=args)
    node = HaplyPosePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
