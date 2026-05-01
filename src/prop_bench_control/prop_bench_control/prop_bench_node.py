"""
prop_bench_node.py
==================
ROS2 node for direct throttle control of a single motor via PX4 Pro v1.16
offboard mode over uXRCE-DDS.

Communication path:
  Laptop (this node) <--USB--> Pixhawk 6 (PX4)
  Micro-XRCE-DDS Agent bridges uORB topics to ROS2 DDS.

PX4 topics used
---------------
  Publish  /fmu/in/offboard_control_mode  -- heartbeat (100 Hz)
  Publish  /fmu/in/actuator_motors        -- normalized motor command [0,1]
  Publish  /fmu/in/vehicle_command        -- arm / mode commands
  Subscribe /fmu/out/vehicle_status       -- arming state & nav state

Result topic (for rosbag recording)
------------------------------------
  Publish  /prop_bench/result  (geometry_msgs/TwistStamped)
    linear.x  = throttle command (0-100 %)
    linear.y  = torque (Nm) -- future sensor hook
    linear.z  = thrust (N)  -- future sensor hook
    angular.x = ESC RPM     -- future sensor hook
    angular.y = optical RPM -- future sensor hook
    angular.z = voltage (V) -- future sensor hook
"""

import math

import rclpy
from rclpy.node import Node

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from px4_msgs.msg import (
    OffboardControlMode,
    ActuatorMotors,
    VehicleCommand,
    VehicleStatus,
)
from geometry_msgs.msg import TwistStamped

NAN = math.nan


# ── Qt signal bridge ─────────────────────────────────────────────────────────

class PropBenchSignals(QObject):
    """
    Thread-safe bridge between ROS2 callbacks (spin thread) and the Qt GUI
    (main thread).  All signals use Qt.QueuedConnection automatically when
    emitted from a different thread.
    """
    control_tick = pyqtSignal()
    vehicle_status_changed = pyqtSignal(bool, int)  # (is_armed, nav_state)


# ── ROS2 node ────────────────────────────────────────────────────────────────

class PropBenchNode(Node):
    """
    Manages all PX4 communication.  Runs inside Ros2SpinThread; GUI calls
    arm(), disarm(), set_throttle() from the main Qt thread (thread-safe via
    Python GIL for simple attribute writes).
    """

    # PX4 arming / nav state constants (from px4_msgs/msg/VehicleStatus.msg)
    ARMING_STATE_ARMED = 2
    NAV_STATE_OFFBOARD = 14

    # PX4 vehicle command IDs
    CMD_DO_SET_MODE = 176
    CMD_ARM_DISARM = 400

    def __init__(self, freq: int = 100):
        super().__init__('prop_bench')
        self.signals = PropBenchSignals()
        self._freq = freq

        # ── state (written from GUI thread, read from spin thread) ───────────
        self._throttle_normalized: float = 0.0  # 0.0 – 1.0
        self._vehicle_armed: bool = False
        self._nav_state: int = 0

        # ── publishers ────────────────────────────────────────────────────────
        self._offboard_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', 10)
        self._motors_pub = self.create_publisher(
            ActuatorMotors, '/fmu/in/actuator_motors', 10)
        self._cmd_pub = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', 10)
        self._result_pub = self.create_publisher(
            TwistStamped, '/prop_bench/result', 10)

        # ── subscriber ────────────────────────────────────────────────────────
        self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status',
            self._vehicle_status_cb,
            rclpy.qos.qos_profile_sensor_data,
        )

        # ── 100 Hz control loop timer ─────────────────────────────────────────
        self.create_timer(1.0 / freq, self._control_loop)

    # ── public API (called from GUI main thread) ──────────────────────────────

    def arm(self):
        """
        Switch to offboard mode then arm.
        PX4 requires OffboardControlMode to be streaming before the mode
        switch is accepted — our 100 Hz timer already ensures this.
        """
        self._send_vehicle_cmd(self.CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self._send_vehicle_cmd(self.CMD_ARM_DISARM, param1=1.0)

    def disarm(self):
        self._throttle_normalized = 0.0
        self._send_vehicle_cmd(self.CMD_ARM_DISARM, param1=0.0)

    def set_throttle(self, throttle_pct: float):
        """Accept 0–100 % and normalise to 0.0–1.0 for PX4."""
        self._throttle_normalized = max(0.0, min(1.0, throttle_pct / 100.0))

    def publish_result(self, throttle_pct: float,
                       torque: float = 0.0, thrust: float = 0.0,
                       esc_rpm: float = 0.0, optical_rpm: float = 0.0,
                       voltage: float = 0.0):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = throttle_pct
        msg.twist.linear.y = torque
        msg.twist.linear.z = thrust
        msg.twist.angular.x = esc_rpm
        msg.twist.angular.y = optical_rpm
        msg.twist.angular.z = voltage
        self._result_pub.publish(msg)

    # ── timer callback (spin thread, 100 Hz) ─────────────────────────────────

    def _control_loop(self):
        self._publish_offboard_mode()
        self._publish_motor_command()
        self.signals.control_tick.emit()

    # ── subscriber callback (spin thread) ────────────────────────────────────

    def _vehicle_status_cb(self, msg: VehicleStatus):
        self._vehicle_armed = (msg.arming_state == self.ARMING_STATE_ARMED)
        self._nav_state = msg.nav_state
        self.signals.vehicle_status_changed.emit(self._vehicle_armed,
                                                  self._nav_state)

    # ── internal helpers ──────────────────────────────────────────────────────

    def _publish_offboard_mode(self):
        msg = OffboardControlMode()
        msg.timestamp = self._timestamp_us()
        msg.direct_actuator = True
        msg.position = False
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.thrust_and_torque = False
        self._offboard_pub.publish(msg)

    def _publish_motor_command(self):
        msg = ActuatorMotors()
        msg.timestamp = self._timestamp_us()
        msg.timestamp_sample = msg.timestamp
        # NaN disables a motor slot; only slot 0 (motor 1 on PX4) is used.
        msg.control = [NAN] * 12
        msg.control[0] = self._throttle_normalized
        msg.reversible_flags = 0
        self._motors_pub.publish(msg)

    def _send_vehicle_cmd(self, command: int,
                          param1: float = 0.0, param2: float = 0.0):
        msg = VehicleCommand()
        msg.timestamp = self._timestamp_us()
        msg.command = command
        msg.param1 = param1
        msg.param2 = param2
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self._cmd_pub.publish(msg)

    def _timestamp_us(self) -> int:
        return int(self.get_clock().now().nanoseconds / 1000)


# ── ROS2 spin thread ──────────────────────────────────────────────────────────

class Ros2SpinThread(QThread):
    """
    Runs rclpy.spin(node) on a dedicated thread so the Qt event loop
    (main thread) is never blocked by ROS2 callbacks.
    """

    def __init__(self, node: PropBenchNode):
        super().__init__()
        self._node = node

    def run(self):
        try:
            rclpy.spin(self._node)
        except Exception as exc:
            print(f'[Ros2SpinThread] spin ended: {exc}')

    def stop(self):
        if rclpy.ok():
            rclpy.shutdown()
        self.wait(3000)
