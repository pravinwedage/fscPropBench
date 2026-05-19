"""
prop_bench.launch.py
====================
Starts the Micro-XRCE-DDS agent (Pixhawk bridge) and the prop bench GUI
with a single command:

    ros2 launch prop_bench_control prop_bench.launch.py

Optional overrides:
    serial_port:=/dev/ttyACM0   (default: /dev/ttyUSB0)
    baud:=921600                 (default: 921600)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, Shutdown
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for Pixhawk USB connection (e.g. /dev/ttyUSB0 or /dev/ttyACM0)',
    )
    baud_arg = DeclareLaunchArgument(
        'baud',
        default_value='921600',
        description='Serial baud rate',
    )
    agent_bin_arg = DeclareLaunchArgument(
        'xrce_agent_bin',
        default_value='MicroXRCEAgent',
        description='Micro-XRCE-DDS agent binary name (MicroXRCEAgent or micro-xrce-dds-agent)',
    )
    record_bag_arg = DeclareLaunchArgument(
        'record_bag',
        default_value='false',
        description='Set to "true" to record a rosbag alongside the GUI (all prop_bench topics)',
    )

    xrce_agent = ExecuteProcess(
        cmd=[
            LaunchConfiguration('xrce_agent_bin'), 'serial',
            '--dev', LaunchConfiguration('serial_port'),
            '-b',   LaunchConfiguration('baud'),
        ],
        output='screen',
        name='micro_xrce_dds_agent',
    )

    gui_node = Node(
        package='prop_bench_control',
        executable='prop_bench_gui',
        name='prop_bench_gui',
        output='screen',
        on_exit=Shutdown(),
    )

    bag_record = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '/prop_bench/result',
            '/fmu/out/vehicle_status',
            '/fmu/out/actuator_outputs',
        ],
        output='screen',
        name='rosbag_record',
        condition=IfCondition(LaunchConfiguration('record_bag')),
    )

    return LaunchDescription([
        serial_port_arg,
        baud_arg,
        agent_bin_arg,
        record_bag_arg,
        xrce_agent,
        gui_node,
        bag_record,
    ])
