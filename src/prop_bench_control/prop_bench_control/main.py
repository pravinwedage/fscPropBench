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

    Expected repo layout (this file is at src/prop_bench_control/prop_bench_control/main.py):
        fscPropBench/
        ├── throttle_profile/   ← target
        └── src/
            └── prop_bench_control/
                └── prop_bench_control/
                    └── main.py  ← here

    Priority:
    1. Derived path from known repo structure (4 levels up from this file)
    2. Walk up from this file as a safety net
    3. ~/throttle_profile as a last-resort fallback (created if it does not exist)
    """
    # Priority 1: known repo structure — 4 levels up from this file is the repo root
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.join(here, '..', '..', '..', '..')
    candidate = os.path.normpath(os.path.join(repo_root, 'throttle_profile'))
    if os.path.isdir(candidate):
        return candidate

    # Priority 2: walk up in case the repo is nested differently
    for _ in range(6):
        candidate = os.path.join(here, 'throttle_profile')
        if os.path.isdir(candidate):
            return candidate
        here = os.path.dirname(here)

    # Priority 3: fallback
    fallback = os.path.expanduser('~/throttle_profile')
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
