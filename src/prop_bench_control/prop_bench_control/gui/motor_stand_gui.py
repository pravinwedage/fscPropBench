# GUI layout for FSC Propeller Bench Test Controller.
# Uses Qt layout managers (no absolute geometry) so the window is fully
# resizable. A minimum size prevents content from being cut off.
# The plotWidget is a plain QWidget; MplCanvas is injected by the controller.

from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog:
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setWindowTitle('FSC Propeller Bench Test Controller')
        Dialog.setMinimumSize(QtCore.QSize(960, 750))

        # ── Root: left panel | right panel ───────────────────────────────────
        root = QtWidgets.QHBoxLayout(Dialog)
        root.setSpacing(10)
        root.setContentsMargins(10, 10, 10, 10)

        # ════════════════════════════════════════════════════════════════════
        # LEFT PANEL  (fixed width, fills height)
        # ════════════════════════════════════════════════════════════════════
        left = QtWidgets.QWidget()
        left.setFixedWidth(280)
        lv = QtWidgets.QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(6)

        self.arm_buttom = QtWidgets.QPushButton('Arm')
        self.arm_buttom.setFont(self._f(16))
        self.arm_buttom.setObjectName('arm_buttom')
        lv.addWidget(self.arm_buttom)

        self.enable_manual = QtWidgets.QCheckBox('Enable Manual')
        self.enable_manual.setFont(self._f(13))
        self.enable_manual.setObjectName('enable_manual')
        lv.addWidget(self.enable_manual)

        self.Throttle = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        self.Throttle.setObjectName('Throttle')
        self.Throttle.setMinimum(0)
        self.Throttle.setMaximum(100)
        self.Throttle.setValue(0)
        self.Throttle.setPageStep(10)
        self.Throttle.setTickPosition(QtWidgets.QSlider.TickPosition.TicksRight)
        self.Throttle.setTickInterval(10)
        self.Throttle.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.Throttle.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        lv.addWidget(self.Throttle, stretch=1)

        # Throttle limit group
        self.throttle_cap_group = QtWidgets.QGroupBox('Throttle Limit')
        self.throttle_cap_group.setFont(self._f(13))
        self.throttle_cap_group.setObjectName('throttle_cap_group')
        cg = QtWidgets.QVBoxLayout(self.throttle_cap_group)
        cg.setSpacing(4)

        self.throttle_cap_checkbox = QtWidgets.QCheckBox('Cap Throttle')
        self.throttle_cap_checkbox.setFont(self._f(13))
        self.throttle_cap_checkbox.setChecked(True)
        self.throttle_cap_checkbox.setObjectName('throttle_cap_checkbox')
        cg.addWidget(self.throttle_cap_checkbox)

        self.throttle_cap_spinbox = QtWidgets.QDoubleSpinBox()
        self.throttle_cap_spinbox.setFont(self._f(13))
        self.throttle_cap_spinbox.setRange(1.0, 100.0)
        self.throttle_cap_spinbox.setSingleStep(1.0)
        self.throttle_cap_spinbox.setValue(80.0)
        self.throttle_cap_spinbox.setSuffix(' %')
        self.throttle_cap_spinbox.setObjectName('throttle_cap_spinbox')
        cg.addWidget(self.throttle_cap_spinbox)

        lv.addWidget(self.throttle_cap_group)
        root.addWidget(left)

        # ════════════════════════════════════════════════════════════════════
        # RIGHT PANEL  (stretches to fill remaining space)
        # ════════════════════════════════════════════════════════════════════
        right = QtWidgets.QWidget()
        rv = QtWidgets.QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)

        # ── Live telemetry ───────────────────────────────────────────────────
        telem = QtWidgets.QGroupBox('Live Telemetry')
        telem.setFont(self._f(11))
        tl = QtWidgets.QVBoxLayout(telem)
        tl.setSpacing(4)

        # Column headers: Throttle / Torque / Thrust / Voltage
        h_labels = QtWidgets.QHBoxLayout()
        for text, name in [('Throttle (%)', 'label'), ('Torque (Nm)', 'label_5'),
                            ('Thrust (N)',  'label_2'), ('Voltage (V)', 'label_7')]:
            lbl = QtWidgets.QLabel(text)
            lbl.setFont(self._f(15))
            lbl.setObjectName(name)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            h_labels.addWidget(lbl)
            setattr(self, name, lbl)
        tl.addLayout(h_labels)

        # LCD row: throttle / torque / thrust / voltage
        h_lcds = QtWidgets.QHBoxLayout()
        for name in ['throttle_display', 'torque_display',
                     'thrust_display', 'voltage_display']:
            lcd = QtWidgets.QLCDNumber()
            lcd.setFont(self._f(20))
            lcd.setMinimumHeight(65)
            lcd.setObjectName(name)
            h_lcds.addWidget(lcd)
            setattr(self, name, lcd)
        tl.addLayout(h_lcds)

        # Column headers: ESC RPM / Optical RPM
        h_rpm_labels = QtWidgets.QHBoxLayout()
        for text, name in [('ESC RPM', 'label_3'), ('Optical RPM', 'label_4')]:
            lbl = QtWidgets.QLabel(text)
            lbl.setFont(self._f(14))
            lbl.setObjectName(name)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            h_rpm_labels.addWidget(lbl)
            setattr(self, name, lbl)
        tl.addLayout(h_rpm_labels)

        # LCD row: ESC RPM / Optical RPM
        h_rpm = QtWidgets.QHBoxLayout()
        for name in ['esc_rpm_display', 'optical_rpm_display']:
            lcd = QtWidgets.QLCDNumber()
            lcd.setFont(self._f(20))
            lcd.setMinimumHeight(65)
            lcd.setObjectName(name)
            h_rpm.addWidget(lcd)
            setattr(self, name, lcd)
        tl.addLayout(h_rpm)

        # Status row: mode / arm state
        h_status = QtWidgets.QHBoxLayout()
        self.mode_status = QtWidgets.QLabel('---')
        self.mode_status.setFont(self._f(15))
        self.mode_status.setObjectName('mode_status')
        h_status.addWidget(self.mode_status)

        self.arm_status = QtWidgets.QLabel('Disarmed')
        self.arm_status.setFont(self._f(15))
        self.arm_status.setObjectName('arm_status')
        h_status.addWidget(self.arm_status)
        tl.addLayout(h_status)

        rv.addWidget(telem, stretch=0)

        # ── Step profile generator ───────────────────────────────────────────
        self.step_group = QtWidgets.QGroupBox('Step Profile Generator')
        self.step_group.setFont(self._f(12))
        self.step_group.setObjectName('step_group')
        sg = QtWidgets.QHBoxLayout(self.step_group)
        sg.setSpacing(8)

        sg.addWidget(self._lbl('Target:', 13))
        self.step_target_spinbox = QtWidgets.QDoubleSpinBox()
        self.step_target_spinbox.setFont(self._f(13))
        self.step_target_spinbox.setRange(0.0, 100.0)
        self.step_target_spinbox.setSingleStep(1.0)
        self.step_target_spinbox.setValue(20.0)
        self.step_target_spinbox.setSuffix(' %')
        self.step_target_spinbox.setObjectName('step_target_spinbox')
        sg.addWidget(self.step_target_spinbox)

        sg.addSpacing(12)
        sg.addWidget(self._lbl('Hold:', 13))
        self.step_duration_spinbox = QtWidgets.QDoubleSpinBox()
        self.step_duration_spinbox.setFont(self._f(13))
        self.step_duration_spinbox.setRange(0.5, 300.0)
        self.step_duration_spinbox.setSingleStep(0.5)
        self.step_duration_spinbox.setValue(5.0)
        self.step_duration_spinbox.setSuffix(' s')
        self.step_duration_spinbox.setObjectName('step_duration_spinbox')
        sg.addWidget(self.step_duration_spinbox)

        sg.addSpacing(12)
        self.step_generate_btn = QtWidgets.QPushButton('Generate && Load')
        self.step_generate_btn.setFont(self._f(13))
        self.step_generate_btn.setObjectName('step_generate_btn')
        sg.addWidget(self.step_generate_btn)

        rv.addWidget(self.step_group, stretch=0)

        # ── CSV throttle profile (stretches vertically) ──────────────────────
        csv_box = QtWidgets.QGroupBox('CSV Throttle Profile')
        csv_box.setFont(self._f(11))
        cl = QtWidgets.QVBoxLayout(csv_box)
        cl.setSpacing(6)

        # Scan / Load buttons
        sl_row = QtWidgets.QHBoxLayout()
        self.profile_load = QtWidgets.QPushButton('Load Throttle Profile')
        self.profile_load.setFont(self._f(14))
        self.profile_load.setObjectName('profile_load')
        sl_row.addWidget(self.profile_load)

        self.profile_scan = QtWidgets.QPushButton('Scan Throttle Profile')
        self.profile_scan.setFont(self._f(14))
        self.profile_scan.setObjectName('profile_scan')
        sl_row.addWidget(self.profile_scan)
        cl.addLayout(sl_row)

        self.profile_info_display = QtWidgets.QLabel('No File Loaded')
        self.profile_info_display.setFont(self._f(13))
        self.profile_info_display.setObjectName('profile_info_display')
        cl.addWidget(self.profile_info_display)

        self.csv_view = QtWidgets.QListView()
        self.csv_view.setFont(self._f(11))
        self.csv_view.setObjectName('csv_view')
        cl.addWidget(self.csv_view, stretch=1)

        # Start / Stop buttons
        ss_row = QtWidgets.QHBoxLayout()
        self.profile_start = QtWidgets.QPushButton('Start')
        self.profile_start.setFont(self._f(15))
        self.profile_start.setObjectName('profile_start')
        ss_row.addWidget(self.profile_start)

        self.profile_stop = QtWidgets.QPushButton('Stop')
        self.profile_stop.setFont(self._f(15))
        self.profile_stop.setObjectName('profile_stop')
        ss_row.addWidget(self.profile_stop)
        cl.addLayout(ss_row)

        self.profile_info = QtWidgets.QLabel('Standby...')
        self.profile_info.setFont(self._f(14))
        self.profile_info.setObjectName('profile_info')
        cl.addWidget(self.profile_info)

        self.motor_profile_progress = QtWidgets.QProgressBar()
        self.motor_profile_progress.setValue(0)
        self.motor_profile_progress.setObjectName('motor_profile_progress')
        cl.addWidget(self.motor_profile_progress)

        rv.addWidget(csv_box, stretch=1)

        # ── Plot (MplCanvas injected by controller) ──────────────────────────
        self.plotWidget = QtWidgets.QWidget()
        self.plotWidget.setObjectName('plotWidget')
        self.plotWidget.setMinimumHeight(120)
        self.plotWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred)
        rv.addWidget(self.plotWidget, stretch=0)

        root.addWidget(right, stretch=1)
        Dialog.setLayout(root)

        QtCore.QMetaObject.connectSlotsByName(Dialog)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _f(self, size: int) -> QtGui.QFont:
        f = QtGui.QFont()
        f.setPointSize(size)
        return f

    def _lbl(self, text: str, size: int) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text)
        lbl.setFont(self._f(size))
        return lbl
