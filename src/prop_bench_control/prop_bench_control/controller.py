"""
controller.py
=============
PropBenchController connects the PyQt5 GUI to the PropBenchNode and the
ThrottleProfile state machine.

All GUI interaction happens here; the node and profile objects stay
free of Qt dependencies.
"""

import os
import csv

import numpy as np
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtWidgets import QVBoxLayout, QMessageBox

from prop_bench_control.prop_bench_node import PropBenchNode
from prop_bench_control.throttle_profile import (
    ThrottleProfile,
    THROTTLE_DISABLED, THROTTLE_WAIT, THROTTLE_SPEED_UP,
)
from prop_bench_control.gui.mplcanvas import MplCanvas


class PropBenchController:
    """
    Wires the GUI widgets to the ROS2 node and throttle-profile logic.

    Lifecycle
    ---------
    1. Instantiate after setupUi() and before app.exec_().
    2. The ROS2 node runs in Ros2SpinThread; its signals arrive in the Qt
       main thread via Qt.QueuedConnection (automatic for cross-thread emits).
    3. GUI button/slider callbacks call node methods directly — these are
       thread-safe (simple Python attribute writes, publisher.publish is
       also thread-safe in rclpy).
    """

    def __init__(self, ui, node: PropBenchNode,
                 throttle_profile: ThrottleProfile,
                 csv_dir: str):
        self._ui = ui
        self._node = node
        self._profile = throttle_profile
        self._csv_dir = csv_dir

        # ── local state ───────────────────────────────────────────────────────
        self._armed = False        # mirrors user intent (toggled by Arm button)
        self._manual_enabled = False
        self._throttle_pct = 0.0  # 0.0 – 100.0

        # ── CSV list model ────────────────────────────────────────────────────
        self._csv_model = QStringListModel()
        ui.csv_view.setModel(self._csv_model)

        # ── matplotlib canvas ─────────────────────────────────────────────────
        self._canvas = MplCanvas(width=7, height=3, dpi=60)
        layout = QVBoxLayout(ui.plotWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        # ── connect ROS2 signals → GUI slots ─────────────────────────────────
        node.signals.control_tick.connect(self._on_control_tick)
        node.signals.vehicle_status_changed.connect(self._on_vehicle_status_changed)

        # ── connect GUI widgets → controller slots ────────────────────────────
        self._setup_gui_connections()

    # ── GUI setup ─────────────────────────────────────────────────────────────

    def _setup_gui_connections(self):
        ui = self._ui
        ui.Throttle.setEnabled(False)
        ui.Throttle.valueChanged.connect(self._on_slider_moved)
        ui.arm_buttom.clicked.connect(self._on_arm_clicked)
        ui.enable_manual.stateChanged.connect(self._on_manual_toggled)
        ui.profile_start.clicked.connect(self._profile.activate)
        ui.profile_stop.clicked.connect(self._profile.reset)
        ui.profile_scan.clicked.connect(self._scan_csv_files)
        ui.profile_load.clicked.connect(self._load_csv_file)
        ui.step_generate_btn.clicked.connect(self._generate_step_profile)

    # ── slots connected to ROS2 signals ───────────────────────────────────────

    def _on_control_tick(self):
        """Called 100 Hz from the ROS2 spin thread via Qt queued signal."""
        self._update_throttle_from_source()
        self._send_throttle()
        self._update_telemetry_labels()
        self._update_slider_enable()
        self._update_profile_controls()
        self._update_profile_status_label()
        self._node.publish_result(self._throttle_pct)

    def _on_vehicle_status_changed(self, px4_armed: bool, nav_state: int):
        """Handle unexpected PX4 disarm (e.g. failsafe, pre-arm check fail)."""
        if not px4_armed and self._armed:
            self._armed = False
            self._throttle_pct = 0.0
            self._ui.arm_buttom.setText('Arm')
            self._ui.arm_status.setText('Disarmed (PX4)')

    # ── GUI callback slots ────────────────────────────────────────────────────

    def _on_arm_clicked(self):
        self._throttle_pct = 0.0
        if self._armed:
            self._armed = False
            self._ui.arm_buttom.setText('Arm')
            self._node.disarm()
        else:
            self._armed = True
            self._ui.arm_buttom.setText('Disarm')
            self._node.arm()

    def _on_manual_toggled(self, state: int):
        self._manual_enabled = (state == Qt.Checked)
        if not self._manual_enabled:
            self._throttle_pct = 0.0
            self._ui.Throttle.setValue(0)

    def _on_slider_moved(self):
        if self._manual_enabled and self._armed:
            self._throttle_pct = float(self._ui.Throttle.value())

    # ── throttle source logic ─────────────────────────────────────────────────

    def _update_throttle_from_source(self):
        if self._armed and not self._manual_enabled:
            self._profile.update_and_get_throttle()
            self._throttle_pct = self._profile.throttle
        elif not self._armed:
            if not self._manual_enabled:
                self._profile.reset()
            self._throttle_pct = 0.0

    def _send_throttle(self):
        if not self._armed:
            self._throttle_pct = 0.0
        self._node.set_throttle(self._throttle_pct)

    # ── GUI update helpers ────────────────────────────────────────────────────

    def _update_telemetry_labels(self):
        self._ui.throttle_display.display(f'{self._throttle_pct:.0f}')
        self._ui.arm_status.setText('Armed' if self._armed else 'Disarmed')
        if self._manual_enabled:
            self._ui.mode_status.setText('Manual')
            self._ui.motor_profile_progress.setValue(0)
        else:
            self._ui.mode_status.setText('Profile')
            self._ui.motor_profile_progress.setValue(self._profile.get_progress())

    def _update_slider_enable(self):
        if self._armed and self._manual_enabled:
            self._ui.Throttle.setEnabled(True)
        else:
            self._ui.Throttle.setEnabled(False)
            if not self._manual_enabled:
                self._ui.Throttle.setValue(0)

    def _update_profile_controls(self):
        if self._manual_enabled:
            self._ui.profile_start.setEnabled(False)
            self._ui.profile_stop.setEnabled(False)
        else:
            self._ui.profile_start.setEnabled(
                self._profile.phase == THROTTLE_DISABLED and self._armed)
            self._ui.profile_stop.setEnabled(True)

    def _update_profile_status_label(self):
        phase = self._profile.phase
        if phase == THROTTLE_DISABLED:
            self._ui.profile_info.setText('Standby...')
        elif phase == THROTTLE_WAIT:
            self._ui.profile_info.setText(
                f'Countdown {self._profile.get_count_down_time()} s...')
        elif phase == THROTTLE_SPEED_UP:
            self._ui.profile_info.setText('Ramping to start throttle...')
        else:
            self._ui.profile_info.setText('Running throttle profile...')

    # ── Step profile generator ────────────────────────────────────────────────

    def _generate_step_profile(self):
        """
        Build a step-input profile in memory and load it into the profile object.

        Sequence (all at 100 Hz):
          1. 2 s at 0 %  — handled by ThrottleProfile's WAIT phase
          2. Single 0.0 sample so SPEED_UP phase completes instantly
             (SPEED_UP ramps to profile_data[0]; if that is 0 the ramp is skipped)
          3. hold_duration seconds at target %
          4. Profile ends → throttle returns to 0 automatically

        The result is a true step input with no ramp.
        """
        target = self._ui.step_target_spinbox.value()
        hold_dur = self._ui.step_duration_spinbox.value()
        freq = self._profile.frequency

        hold_steps = max(1, int(round(hold_dur * freq)))
        # One leading 0 so the SPEED_UP phase skips immediately, then the step.
        data = [0.0] + [target] * hold_steps

        self._profile.load_throttle_profile(data)

        total_s = len(data) / freq
        t = np.linspace(0, total_s, len(data)).tolist()
        self._canvas.update_plot(t, data)
        self._ui.profile_info_display.setText(
            f'Step  {target:.1f} %  for  {hold_dur:.1f} s  '
            f'(+ 2 s safety wait)'
        )

    # ── CSV file management ───────────────────────────────────────────────────

    def _scan_csv_files(self):
        if not os.path.isdir(self._csv_dir):
            QMessageBox.warning(None, 'Directory Not Found',
                                f'Cannot find: {self._csv_dir}')
            return
        files = [f for f in os.listdir(self._csv_dir) if f.endswith('.csv')]
        if files:
            self._csv_model.setStringList(sorted(files))
        else:
            QMessageBox.information(None, 'No Files',
                                    f'No .csv files in:\n{self._csv_dir}')

    def _load_csv_file(self):
        selected = self._ui.csv_view.selectedIndexes()
        if not selected:
            QMessageBox.warning(None, 'No Selection',
                                'Select a file from the list first.')
            return

        filename = selected[0].data()
        filepath = os.path.join(self._csv_dir, filename)

        try:
            data = []
            with open(filepath, 'r') as fh:
                for row in csv.reader(fh):
                    if len(row) != 1:
                        QMessageBox.critical(None, 'Format Error',
                                             'File must have exactly one value per row.')
                        return
                    data.append(float(row[0]))

            if not data:
                QMessageBox.critical(None, 'Empty File', 'The file contains no data.')
                return

            duration = len(data) / self._profile.frequency
            t = np.linspace(0, duration, len(data)).tolist()
            self._canvas.update_plot(t, data)
            self._ui.profile_info_display.setText(
                f'{filename}  |  {duration:.1f} s  |  '
                f'max {max(data):.1f} %  min {min(data):.1f} %'
            )
            self._profile.load_throttle_profile(data)

        except (ValueError, OSError) as exc:
            QMessageBox.critical(None, 'Load Error', f'Failed to load file:\n{exc}')
