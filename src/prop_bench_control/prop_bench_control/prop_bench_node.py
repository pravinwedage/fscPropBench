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
  Subscribe /fmu/out/actuator_outputs     -- PX4 actual actuator outputs (feedback)

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

import csv
import math
import threading
from datetime import datetime, timezone

import rclpy
from rclpy.node import Node

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from px4_msgs.msg import (
    ActuatorOutputs,
    FailsafeFlags,
    OffboardControlMode,
    ActuatorMotors,
    VehicleCommand,
    VehicleCommandAck,
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
    failsafe_changed = pyqtSignal(bool, bool)        # (offboard_lost, gcs_lost)


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

    # CSV column headers for data recording
    _CSV_COLUMNS = [
        'timestamp_utc_iso8601',
        'timestamp_unix_ms',
        'throttle_cmd_pct',
        'arming_state',
        'latest_disarming_reason',
        'nav_state',
        'failsafe',
        'offboard_signal_lost',
        'gcs_connection_lost',
        'px4_actuator_output_0',
    ]

    def __init__(self, freq: int = 100):
        super().__init__('prop_bench')
        self.signals = PropBenchSignals()
        self._freq = freq

        # ── state (written from GUI thread, read from spin thread) ───────────
        self._throttle_normalized: float = 0.0  # 0.0 – 1.0
        self._vehicle_armed: bool = False
        self._nav_state: int = 0
        self._latest_vehicle_status: VehicleStatus | None = None
        self._latest_actuator_output_0: float = NAN
        self._offboard_signal_lost: bool = False
        self._gcs_connection_lost: bool = False
        self._latest_disarming_reason: int = 0

        # ── recording state ───────────────────────────────────────────────────
        self._recording: bool = False
        self._csv_file = None
        self._csv_writer = None

        # ── publishers ────────────────────────────────────────────────────────
        # offboard mode signal
        self._offboard_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', 10)
        # motor command signal
        self._motors_pub = self.create_publisher(
            ActuatorMotors, '/fmu/in/actuator_motors', 10)
        # arm, disarm or stop command signal
        self._cmd_pub = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', 10)
        # data logging
        self._result_pub = self.create_publisher(
            TwistStamped, '/prop_bench/result', 10)

        # ── subscribers ───────────────────────────────────────────────────────
        _best_effort = rclpy.qos.QoSProfile(
            reliability=rclpy.qos.ReliabilityPolicy.BEST_EFFORT,
            durability=rclpy.qos.DurabilityPolicy.VOLATILE,
            history=rclpy.qos.HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self._sub_vs   = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status',
            self._vehicle_status_cb, _best_effort)
        # Fallback: some PX4 v1.16 builds publish arming state on the v1 topic
        self._sub_vs1  = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status_v1',
            self._vehicle_status_cb, _best_effort)
        self._sub_fs   = self.create_subscription(
            FailsafeFlags, '/fmu/out/failsafe_flags',
            self._failsafe_flags_cb, _best_effort)
        self._sub_ack  = self.create_subscription(
            VehicleCommandAck, '/fmu/out/vehicle_command_ack',
            self._vehicle_command_ack_cb, _best_effort)
        # PX4 feedback: what was actually sent to the ESC
        self._sub_ao   = self.create_subscription(
            ActuatorOutputs, '/fmu/out/actuator_outputs',
            self._actuator_outputs_cb, _best_effort)

        # ── 100 Hz control loop timer ─────────────────────────────────────────
        self.create_timer(1.0 / freq, self._control_loop)

    # ── public API (called from GUI main thread) ──────────────────────────────

    def arm(self):
        """
        Switch to offboard mode then arm.
        PX4 requires OffboardControlMode to be streaming before the mode
        switch is accepted, ensured by the 100 Hz control loop timer.
        A 500 ms delay between SET_MODE and ARM prevents the temporary
        rejection that occurs when both commands are sent simultaneously.
        """
        self._send_vehicle_cmd(self.CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        threading.Timer(1.5, lambda: self._send_vehicle_cmd(
            self.CMD_ARM_DISARM, param1=1.0)).start()

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

    def start_recording(self, filepath: str) -> None:
        """Open a CSV file and begin writing one row per control-loop tick."""
        if self._recording:
            return
        self._csv_file = open(filepath, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow(self._CSV_COLUMNS)
        self._recording = True

    def stop_recording(self) -> None:
        """Flush and close the recording file."""
        self._recording = False
        fh = self._csv_file
        self._csv_writer = None
        self._csv_file = None
        if fh:
            try:
                fh.flush()
                fh.close()
            except Exception:
                pass

    # ── timer callback (spin thread, 100 Hz) ─────────────────────────────────

    def _control_loop(self):
        self._publish_offboard_mode()
        self._publish_motor_command()
        if self._recording:
            self._write_csv_row()
        self.signals.control_tick.emit()

    # ── subscriber callbacks (spin thread) ───────────────────────────────────

    def _vehicle_status_cb(self, msg: VehicleStatus):
        prev_armed = self._vehicle_armed
        self._latest_vehicle_status = msg
        self._vehicle_armed = (msg.arming_state == self.ARMING_STATE_ARMED)
        self._nav_state = msg.nav_state
        self._latest_disarming_reason = int(msg.latest_disarming_reason)
        if prev_armed and not self._vehicle_armed:
            print(f'[PX4] DISARMED — reason code {self._latest_disarming_reason}')
        self.signals.vehicle_status_changed.emit(self._vehicle_armed,
                                                  self._nav_state)

    def _failsafe_flags_cb(self, msg: FailsafeFlags):
        prev_offboard = self._offboard_signal_lost
        prev_gcs = self._gcs_connection_lost
        self._offboard_signal_lost = bool(msg.offboard_control_signal_lost)
        self._gcs_connection_lost = bool(msg.gcs_connection_lost)
        if self._offboard_signal_lost and not prev_offboard:
            print('[PX4] OFFBOARD SIGNAL LOST — COM_OF_LOSS_T countdown started')
        if not self._offboard_signal_lost and prev_offboard:
            print('[PX4] Offboard signal recovered')
        if self._gcs_connection_lost and not prev_gcs:
            print('[PX4] GCS CONNECTION LOST')
        self.signals.failsafe_changed.emit(self._offboard_signal_lost,
                                           self._gcs_connection_lost)

    def _vehicle_command_ack_cb(self, msg: VehicleCommandAck):
        # CMD_ARM_DISARM = 400; result 0 = ACCEPTED
        if msg.command == self.CMD_ARM_DISARM:
            print(f'[PX4] CMD_ARM_DISARM ack  result={msg.result}')

    def _actuator_outputs_cb(self, msg: ActuatorOutputs):
        if msg.noutputs > 0:
            self._latest_actuator_output_0 = float(msg.output[0])

    # ── internal helpers ──────────────────────────────────────────────────────

    def _write_csv_row(self):
        writer = self._csv_writer
        if writer is None:
            return
        now = datetime.now(timezone.utc)
        vs = self._latest_vehicle_status
        writer.writerow([
            now.isoformat(timespec='milliseconds'),
            int(now.timestamp() * 1000),
            f'{self._throttle_normalized * 100.0:.2f}',
            vs.arming_state if vs is not None else '',
            self._latest_disarming_reason,
            vs.nav_state if vs is not None else '',
            int(vs.failsafe) if vs is not None else '',
            int(self._offboard_signal_lost),
            int(self._gcs_connection_lost),
            f'{self._latest_actuator_output_0:.4f}',
        ])

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
        # All slots default to NaN (disabled). Slot 0 is only written when
        # throttle > 0 — sending NaN at zero prevents the ESC from idle-spinning
        # at the minimum armed PWM when the commanded throttle is zero.
        msg.control = [NAN] * 12
        if self._throttle_normalized > 0.0:
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
