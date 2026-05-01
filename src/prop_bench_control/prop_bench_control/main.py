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
from PyQt5 import QtWidgets

from prop_bench_control.prop_bench_node import PropBenchNode, Ros2SpinThread
from prop_bench_control.throttle_profile import ThrottleProfile
from prop_bench_control.controller import PropBenchController
from prop_bench_control.gui.motor_stand_gui import Ui_Dialog

ROS_FREQ = 100  # Hz — must match PX4 offboard streaming rate (≥ 2 Hz)


def _find_throttle_profile_dir() -> str:
    """
    Resolve the throttle profile directory.

    Priority:
    1. Installed share directory (colcon build / ros2 run)
    2. Sibling directory in the git repo (dev / source run)
    3. ~/throttle_profiles as a fallback
    """
    try:
        from ament_index_python.packages import get_package_share_directory
        share_dir = get_package_share_directory('prop_bench_control')
        candidate = os.path.join(share_dir, 'throttle_profiles')
        if os.path.isdir(candidate):
            return candidate
    except Exception:
        pass

    # Walk up from this file to find throttle_profile/ in the repo
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(here, 'throttle_profile')
        if os.path.isdir(candidate):
            return candidate
        here = os.path.dirname(here)

    fallback = os.path.expanduser('~/throttle_profiles')
    os.makedirs(fallback, exist_ok=True)
    return fallback


def main(args=None):
    rclpy.init(args=args)
    node = PropBenchNode(freq=ROS_FREQ)

    app = QtWidgets.QApplication(sys.argv)

    dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(dialog)

    csv_dir = _find_throttle_profile_dir()
    throttle_profile = ThrottleProfile(freq=ROS_FREQ)

    controller = PropBenchController(ui, node, throttle_profile, csv_dir)  # noqa: F841

    spin_thread = Ros2SpinThread(node)
    spin_thread.start()

    dialog.show()
    exit_code = app.exec_()

    node.disarm()
    spin_thread.stop()
    node.destroy_node()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
