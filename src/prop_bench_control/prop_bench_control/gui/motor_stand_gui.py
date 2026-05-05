# Adapted from motor_stand_gui.ui template for ROS2 / PX4 prop bench controller.
# The plotWidget is left as a plain QWidget; the controller injects an MplCanvas.

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog:
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.resize(1018, 960)
        font = QtGui.QFont()
        font.setPointSize(31)
        Dialog.setFont(font)
        Dialog.setWindowTitle('FSC Propeller Bench Test Controller')

        # ── Left panel: arm button, manual checkbox, throttle slider ────────
        self.verticalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(20, 10, 191, 921))
        self.verticalLayoutWidget.setObjectName('verticalLayoutWidget')
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)

        self.arm_buttom = QtWidgets.QPushButton(self.verticalLayoutWidget)
        font_btn = QtGui.QFont()
        font_btn.setPointSize(19)
        self.arm_buttom.setFont(font_btn)
        self.arm_buttom.setText('Arm')
        self.arm_buttom.setObjectName('arm_buttom')
        self.verticalLayout_4.addWidget(self.arm_buttom)

        self.enable_manual = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        font_cb = QtGui.QFont()
        font_cb.setPointSize(16)
        self.enable_manual.setFont(font_cb)
        self.enable_manual.setText('Enable Manual')
        self.enable_manual.setObjectName('enable_manual')
        self.verticalLayout_4.addWidget(self.enable_manual)

        self.Throttle = QtWidgets.QSlider(self.verticalLayoutWidget)
        sp = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                   QtWidgets.QSizePolicy.Preferred)
        sp.setVerticalStretch(16)
        self.Throttle.setSizePolicy(sp)
        self.Throttle.setMinimumSize(QtCore.QSize(2, 2))
        self.Throttle.setPageStep(10)
        self.Throttle.setValue(0)
        self.Throttle.setMinimum(0)
        self.Throttle.setMaximum(100)
        self.Throttle.setOrientation(QtCore.Qt.Vertical)
        self.Throttle.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.Throttle.setTickInterval(10)
        self.Throttle.setObjectName('Throttle')
        self.verticalLayout_4.addWidget(self.Throttle)

        # ── Throttle cap group ────────────────────────────────────────────────
        f_cap = QtGui.QFont()
        f_cap.setPointSize(13)

        self.throttle_cap_group = QtWidgets.QGroupBox('Throttle Limit',
                                                       self.verticalLayoutWidget)
        self.throttle_cap_group.setFont(f_cap)
        cap_layout = QtWidgets.QVBoxLayout(self.throttle_cap_group)

        self.throttle_cap_checkbox = QtWidgets.QCheckBox('Cap Throttle')
        self.throttle_cap_checkbox.setFont(f_cap)
        self.throttle_cap_checkbox.setChecked(True)
        self.throttle_cap_checkbox.setObjectName('throttle_cap_checkbox')
        cap_layout.addWidget(self.throttle_cap_checkbox)

        self.throttle_cap_spinbox = QtWidgets.QDoubleSpinBox()
        self.throttle_cap_spinbox.setFont(f_cap)
        self.throttle_cap_spinbox.setRange(1.0, 100.0)
        self.throttle_cap_spinbox.setSingleStep(1.0)
        self.throttle_cap_spinbox.setValue(80.0)
        self.throttle_cap_spinbox.setSuffix(' %')
        self.throttle_cap_spinbox.setObjectName('throttle_cap_spinbox')
        cap_layout.addWidget(self.throttle_cap_spinbox)

        self.verticalLayout_4.addWidget(self.throttle_cap_group)

        # ── Top-right panel: live telemetry displays ─────────────────────────
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(220, 10, 751, 351))
        self.verticalLayoutWidget_3.setObjectName('verticalLayoutWidget_3')
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)

        # Row 1: column headers
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        for text, name in [('Throttle (%)', 'label'),
                            ('Torque (Nm)', 'label_5'),
                            ('Thrust (N)', 'label_2'),
                            ('Voltage (V)', 'label_7')]:
            lbl = QtWidgets.QLabel(self.verticalLayoutWidget_3)
            f = QtGui.QFont()
            f.setPointSize(25)
            lbl.setFont(f)
            lbl.setText(text)
            lbl.setObjectName(name)
            self.horizontalLayout_2.addWidget(lbl)
            setattr(self, name, lbl)
        self.verticalLayout_10.addLayout(self.horizontalLayout_2)

        # Row 2: LCD displays
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        for name in ['throttle_display', 'torque_display',
                     'thrust_display', 'voltage_display']:
            lcd = QtWidgets.QLCDNumber(self.verticalLayoutWidget_3)
            f = QtGui.QFont()
            f.setPointSize(29)
            lcd.setFont(f)
            lcd.setObjectName(name)
            self.horizontalLayout.addWidget(lcd)
            setattr(self, name, lcd)
        self.verticalLayout_10.addLayout(self.horizontalLayout)

        # Row 3: RPM column headers
        self.gridLayout_2 = QtWidgets.QGridLayout()
        for col, (text, name) in enumerate([('ESC RPM', 'label_3'),
                                            ('Optical RPM', 'label_4')]):
            lbl = QtWidgets.QLabel(self.verticalLayoutWidget_3)
            f = QtGui.QFont()
            f.setPointSize(18)
            lbl.setFont(f)
            lbl.setText(text)
            lbl.setObjectName(name)
            self.gridLayout_2.addWidget(lbl, 0, col)
            setattr(self, name, lbl)
        self.verticalLayout_10.addLayout(self.gridLayout_2)

        # Row 4: RPM LCD displays
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        for name in ['esc_rpm_display', 'optical_rpm_display']:
            lcd = QtWidgets.QLCDNumber(self.verticalLayoutWidget_3)
            f = QtGui.QFont()
            f.setPointSize(29)
            lcd.setFont(f)
            lcd.setObjectName(name)
            self.horizontalLayout_3.addWidget(lcd)
            setattr(self, name, lcd)
        self.verticalLayout_10.addLayout(self.horizontalLayout_3)

        # Row 5: mode / arm status labels
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.mode_status = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        f = QtGui.QFont()
        f.setPointSize(20)
        self.mode_status.setFont(f)
        self.mode_status.setText('---')
        self.mode_status.setObjectName('mode_status')
        self.horizontalLayout_5.addWidget(self.mode_status)

        self.arm_status = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.arm_status.setFont(f)
        self.arm_status.setText('Disarmed')
        self.arm_status.setObjectName('arm_status')
        self.horizontalLayout_5.addWidget(self.arm_status)
        self.verticalLayout_10.addLayout(self.horizontalLayout_5)

        # ── Middle-right panel: throttle profile controls ────────────────────
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(220, 370, 751, 425))
        self.verticalLayoutWidget_2.setObjectName('verticalLayoutWidget_2')
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)

        # ── Step Profile Generator group ──────────────────────────────────────
        f_step = QtGui.QFont()
        f_step.setPointSize(15)

        self.step_group = QtWidgets.QGroupBox('Step Profile Generator',
                                              self.verticalLayoutWidget_2)
        self.step_group.setFont(f_step)
        step_layout = QtWidgets.QHBoxLayout(self.step_group)
        step_layout.setSpacing(8)

        lbl_target = QtWidgets.QLabel('Target:')
        lbl_target.setFont(f_step)
        self.step_target_spinbox = QtWidgets.QDoubleSpinBox()
        self.step_target_spinbox.setFont(f_step)
        self.step_target_spinbox.setRange(0.0, 100.0)
        self.step_target_spinbox.setSingleStep(1.0)
        self.step_target_spinbox.setValue(20.0)
        self.step_target_spinbox.setSuffix(' %')
        self.step_target_spinbox.setObjectName('step_target_spinbox')

        lbl_hold = QtWidgets.QLabel('Hold:')
        lbl_hold.setFont(f_step)
        self.step_duration_spinbox = QtWidgets.QDoubleSpinBox()
        self.step_duration_spinbox.setFont(f_step)
        self.step_duration_spinbox.setRange(0.5, 300.0)
        self.step_duration_spinbox.setSingleStep(0.5)
        self.step_duration_spinbox.setValue(5.0)
        self.step_duration_spinbox.setSuffix(' s')
        self.step_duration_spinbox.setObjectName('step_duration_spinbox')

        self.step_generate_btn = QtWidgets.QPushButton('Generate && Load')
        self.step_generate_btn.setFont(f_step)
        self.step_generate_btn.setObjectName('step_generate_btn')

        step_layout.addWidget(lbl_target)
        step_layout.addWidget(self.step_target_spinbox)
        step_layout.addSpacing(16)
        step_layout.addWidget(lbl_hold)
        step_layout.addWidget(self.step_duration_spinbox)
        step_layout.addSpacing(16)
        step_layout.addWidget(self.step_generate_btn)
        self.verticalLayout_9.addWidget(self.step_group)

        # Scan / Load buttons
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.profile_load = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.profile_scan = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        f_btn2 = QtGui.QFont()
        f_btn2.setPointSize(18)
        for btn, text, name in [(self.profile_load, 'Load Throttle Profile', 'profile_load'),
                                 (self.profile_scan, 'Scan Throttle Profile', 'profile_scan')]:
            btn.setFont(f_btn2)
            btn.setText(text)
            btn.setObjectName(name)
            self.horizontalLayout_9.addWidget(btn)
        self.verticalLayout_9.addLayout(self.horizontalLayout_9)

        # Profile info label
        self.profile_info_display = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.profile_info_display.setFont(f_btn2)
        self.profile_info_display.setText('No File Loaded')
        self.profile_info_display.setObjectName('profile_info_display')
        self.verticalLayout_9.addWidget(self.profile_info_display)

        # CSV file list
        self.csv_view = QtWidgets.QListView(self.verticalLayoutWidget_2)
        f_list = QtGui.QFont()
        f_list.setPointSize(12)
        self.csv_view.setFont(f_list)
        self.csv_view.setObjectName('csv_view')
        self.verticalLayout_9.addWidget(self.csv_view)

        # Start / Stop buttons
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.profile_start = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.profile_stop = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        f_btn3 = QtGui.QFont()
        f_btn3.setPointSize(19)
        for btn, text, name in [(self.profile_start, 'Start', 'profile_start'),
                                 (self.profile_stop, 'Stop', 'profile_stop')]:
            btn.setFont(f_btn3)
            btn.setText(text)
            btn.setObjectName(name)
            self.horizontalLayout_6.addWidget(btn)
        self.verticalLayout_9.addLayout(self.horizontalLayout_6)

        # Profile status label
        self.profile_info = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.profile_info.setFont(f_btn3)
        self.profile_info.setText('Standby...')
        self.profile_info.setObjectName('profile_info')
        self.verticalLayout_9.addWidget(self.profile_info)

        # Progress bar
        self.motor_profile_progress = QtWidgets.QProgressBar(self.verticalLayoutWidget_2)
        self.motor_profile_progress.setValue(0)
        self.motor_profile_progress.setObjectName('motor_profile_progress')
        self.verticalLayout_9.addWidget(self.motor_profile_progress)

        # ── Bottom-right panel: plot widget (container for MplCanvas) ────────
        self.verticalLayoutWidget_4 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(220, 805, 751, 121))
        self.verticalLayoutWidget_4.setObjectName('verticalLayoutWidget_4')
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        # Plain container — MplCanvas is injected by PropBenchController
        self.plotWidget = QtWidgets.QWidget(self.verticalLayoutWidget_4)
        self.plotWidget.setObjectName('plotWidget')
        self.verticalLayout.addWidget(self.plotWidget)

        QtCore.QMetaObject.connectSlotsByName(Dialog)
