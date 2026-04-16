from setuptools import find_packages, setup

package_name = 'spacemouse_joy'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'websockets'],
    zip_safe=True,
    maintainer='Club Capra ETS',
    maintainer_email='capra@ens.etsmtl.ca',
    description='''This ROS 2 package provides a node to publish a 3DSpaceMouse's input as constant `Joy` messages and another to listen to and print `Joy` messages for easy validation. It supports disconnects.''',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'spacemouse_joy_publisher = spacemouse_joy.spacemouse_joy_publisher:main',
            'spacemouse_tcp_client = spacemouse_joy.spacemouse_tcp_client:main',
            'spacemouse_tcp_server = spacemouse_joy.spacemouse_tcp_server:main',
            'spacemouse_to_twist = spacemouse_joy.spacemouse_to_twist:main',
            'haply_pose_publisher = spacemouse_joy.haply_ros:main',
        ],
    },
)
