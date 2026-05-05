"""
main.py
=======
Entry point for the prop bench GUI node.

Usage (after building the workspace):
    ros2 run prop_bench_control prop_bench_gui

Or via launch file:
    ros2 launch prop_bench_control prop_bench.launch.py
"""

import sys
import os

import rclpy
from PyQt6 import QtWidgets  # PyQt6 enables HiDPI scaling automatically

from prop_bench_control.prop_bench_node import PropBenchNode, Ros2SpinThread
from prop_bench_control.throttle_profile import ThrottleProfile
from prop_bench_control.controller import PropBenchController
from prop_bench_control.gui.motor_stand_gui import Ui_Dialog

ROS_FREQ = 100  # Hz — must match PX4 offboard streaming rate (≥ 2 Hz)


def _find_throttle_profile_dir() -> str:
    """
    Resolve the throttle profile directory.

    Priority:
    1. PROP_BENCH_PROFILE_DIR environment variable — set by start_prop_bench.sh
       to point at the source tree, so new CSV files are visible immediately
       without rebuilding. Can also be overridden manually in any terminal.
    2. Installed share directory — fallback when the env var is not set and
       the package has been built with colcon.
    3. ~/throttle_profile — last-resort fallback, created if missing.
    """
    # Priority 1: environment variable (set by start_prop_bench.sh)
    env_dir = os.environ.get('PROP_BENCH_PROFILE_DIR', '').strip()
    if env_dir and os.path.isdir(env_dir):
        return env_dir

    # Priority 2: installed share directory
    try:
        from ament_index_python.packages import get_package_share_directory
        share_dir = get_package_share_directory('prop_bench_control')
        candidate = os.path.join(share_dir, 'throttle_profile')
        if os.path.isdir(candidate):
            return candidate
    except Exception:
        pass

    # Priority 3: last-resort fallback
    fallback = os.path.expanduser('~/throttle_profile')
    os.makedirs(fallback, exist_ok=True)
    return fallback


def main(args=None):
    # Initialize
    rclpy.init(args=args)
    node = PropBenchNode(freq=ROS_FREQ)

    # GUI Setup
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(dialog)

    # Load profiles and GUI/ROS node bridge
    csv_dir = _find_throttle_profile_dir()
    throttle_profile = ThrottleProfile(freq=ROS_FREQ)
    # bridge from GUI to ROS node
    controller = PropBenchController(ui, node, throttle_profile, csv_dir)  # noqa: F841

    # Background thread for ROS2 node
    spin_thread = Ros2SpinThread(node)
    spin_thread.start()

    # Show GUI
    dialog.show()
    exit_code = app.exec()

    # Shutdown
    node.disarm()
    spin_thread.stop()
    node.destroy_node()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
