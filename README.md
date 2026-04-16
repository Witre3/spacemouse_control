# Capra SpaceMouse Package

This ROS 2 package provides a node that publishes input from a SpaceMouse as a `sensor_msgs/msg/Joy` message. It handles live updates from the device and will recover even if the device is temporarily disconnected.

## Overview

The main node is `spacemouse_joy.py`. It:
- Connects to a 3Dconnexion SpaceMouse using `pyspacemouse`.
- Reads 6-DOF motion and 2-button states.
- Publishes them at 100 Hz as `Joy` messages on the `joy` topic.
- Handles disconnections and attempts to reconnect every second, publishing zeros until the device is restored.

## Node: `spacemouse_joy.py`

### Purpose

Publishes 3D SpaceMouse data to the `/spacemouse_joy` topic as a standard `sensor_msgs/msg/Joy` message.

### Published

- **Topic**: `/spacemouse_joy`  
  **Type**: `sensor_msgs/msg/Joy`  
  **Frequency**: ~100 Hz  
  **Content**:
  - `axes[0]` — Translation Y (forward/backward)
  - `axes[1]` — Translation X (left/right)
  - `axes[2]` — Translation Z (up/down)
  - `axes[3]` — Rotation Roll (left/right)
  - `axes[4]` — Rotation Pitch (forward/backward)
  - `axes[5]` — Rotation Yaw (twist)
  - `buttons[0]` — Button 1 (left)
  - `buttons[1]` — Button 2 (right)
  
  The axes order have been adjusted to fit the order expected from twist.

| Index | Field         | Type    | Description                    |
|-------|---------------|---------|--------------------------------|
| 0     | axes[0]       | `float` | Translate forward/backward     |
| 1     | axes[1]       | `float` | Translate left/right           |
| 2     | axes[2]       | `float` | Translate up/down              |
| 3     | axes[3]       | `float` | Rotate roll (tilt left/right)  |
| 4     | axes[4]       | `float` | Rotate pitch (tilt fore/aft)   |
| 5     | axes[5]       | `float` | Rotate yaw (twist)             |
| 0     | buttons[0]    | `int`   | Button 1 (left)                |
| 1     | buttons[1]    | `int`   | Button 2 (right)               |

### Behavior

- On startup: attempts to connect to the SpaceMouse.
- On each timer tick (10 ms): reads and publishes motion/button data.
- On error: publishes zeros and starts a 1 Hz reconnect timer.
- On successful reconnection: resumes normal publishing.


## Setup

This setup is simplified for Ubuntu 22.04. See the original documentation for a complete setup.

### Part 1: Installing PySpaceMouse

Source: [PySpaceMouse GitHub](https://github.com/JakubAndrysek/PySpaceMouse)

1. Install the package:
    ```sh
    pip install pyspacemouse
    ```

2. Install dependencies:
    1. The library uses `hidapi` as a low-level interface to the device and `easyhid` as a Python abstraction for easier use.
        ```sh
        sudo apt-get install libhidapi-dev
        ```

    2. Add rules for permissions:
        ```sh
        sudo echo 'KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"' > /etc/udev/rules.d/99-hidraw-permissions.rules
        sudo usermod -aG plugdev $USER
        newgrp plugdev
        ```

    3. `easyhid` is a `hidapi` interface for Python - required on all platforms:
        ```sh
        pip install git+https://github.com/bglopez/python-easyhid.git
        ```

### Part 2: Give Permission to Access HID Devices
Source (Chinese): [CSDN Blog](https://blog.csdn.net/qq_40081208/article/details/144306644) [Wayback Machine Mirror](https://web.archive.org/web/20250405190521/https://blog.csdn.net/qq_40081208/article/details/144306644)

By default, ordinary users may not have permission to access HID devices.

1. Run the following command to add the `idVendor` and `idProduct` of the 3D SpaceMouse in udev rules:
    ```sh
    sudo tee /etc/udev/rules.d/99-spacemouse.rules > /dev/null <<EOF
    SUBSYSTEM=="input", GROUP="input", MODE="0660"
    KERNEL=="hidraw*", ATTRS{idVendor}=="256f", ATTRS{idProduct}=="c635", MODE="0666"
    EOF
    ```
    *These IDs are for CAPRA's SpaceMouse. See the original setup for other devices.*

2. Reload udev rules:
    ```sh
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    ```

3. Disconnect and reconnect the SpaceMouse.

4. Make sure the current user belongs to the input group (expect no output):
    ```sh
    sudo usermod -a -G input $USER
    ```

5. Log out and log back in to Ubuntu.


## Launch

All nodes can be launched using:

```bash
ros2 run your_package_name spacemouse_joy.py
