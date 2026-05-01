# fscPropBench — ROS2 Prop Bench Controller

ROS2 offboard throttle controller for a **Pixhawk 6** running **PX4 Pro v1.16**,
connected via USB.  Provides a PyQt5 GUI for manual slider control and
automated throttle sweep profiles.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│  Laptop (Ubuntu 22.04 / ROS2 Humble)                  │
│                                                        │
│  ┌────────────────┐   Qt signals    ┌───────────────┐ │
│  │  PyQt5 GUI     │◄───────────────►│  Controller   │ │
│  │  (main thread) │                 │               │ │
│  └────────────────┘                 └──────┬────────┘ │
│                                            │calls     │
│  ┌────────────────────────────────────────▼────────┐  │
│  │  PropBenchNode (rclpy.Node)  ← Ros2SpinThread  │  │
│  │                                                 │  │
│  │  Pub: /fmu/in/offboard_control_mode  (100 Hz)  │  │
│  │  Pub: /fmu/in/actuator_motors        (100 Hz)  │  │
│  │  Pub: /fmu/in/vehicle_command        (on event)│  │
│  │  Sub: /fmu/out/vehicle_status                  │  │
│  │  Pub: /prop_bench/result (TwistStamped)        │  │
│  └─────────────────────────────────────────────────┘  │
│                        │ DDS (uXRCE-DDS)               │
│                        │ USB serial                    │
└────────────────────────┼──────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Micro-XRCE-DDS     │
              │  Agent (laptop)     │
              └──────────┬──────────┘
                         │ UART/USB
              ┌──────────▼──────────┐
              │  Pixhawk 6          │
              │  PX4 Pro v1.16      │
              │  uXRCE-DDS client   │
              └─────────────────────┘
```

### Key Source Files

| File | Purpose |
|------|---------|
| `prop_bench_control/main.py` | Entry point: initialises ROS2, Qt, wires everything together |
| `prop_bench_control/prop_bench_node.py` | ROS2 node — all PX4 pub/sub, 100 Hz timer, Qt signal bridge |
| `prop_bench_control/controller.py` | GUI↔node logic: arm/disarm, throttle routing, profile state |
| `prop_bench_control/throttle_profile.py` | Throttle profile state machine (WAIT→SPEED_UP→PROFILE) |
| `prop_bench_control/gui/motor_stand_gui.py` | PyQt5 widget layout (`Ui_Dialog`) |
| `prop_bench_control/gui/mplcanvas.py` | Embedded Matplotlib canvas for profile preview |
| `launch/prop_bench.launch.py` | ROS2 launch file (starts XRCE agent + GUI together) |
| `scripts/start_prop_bench.sh` | One-command startup script |

---

## Installation

Built for Ubuntu 22.04 and ROS2 Humble. The following steps are required. 

### 1. ROS2 Humble

```bash
sudo apt install ros-humble-desktop python3-colcon-common-extensions
```

If ROS2 is not yet installed at all, follow the full guide at
https://docs.ros.org/en/humble/Installation.html first.

Add the base ROS2 source to `~/.bashrc` so it is available in every terminal:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 2. Workspace + px4_msgs

This git repo is the ROS2 workspace root. `px4_msgs` is a required package and must sit alongside `prop_bench_control` inside `src/`:

```
fscPropBench/              ← workspace root  (run colcon build here)
└── src/
    ├── px4_msgs/          ← clone this in
    └── prop_bench_control/
```

Clone `px4_msgs` and check out the branch matching PX4 v1.16.
Message definitions must match exactly or DDS topic types will not align.

```bash
cd src/
git clone https://github.com/PX4/px4_msgs.git
cd px4_msgs
git checkout release/1.16    # branch for PX4 v1.16
cd ../..                     # back to workspace root
```

### 3. Python dependencies

```bash
pip3 install pyqt5 matplotlib numpy
```

`ament_index_python` ships with ROS2 Humble and does not need a separate install.

### 4. Micro-XRCE-DDS Agent

This is a required standalone binary that bridges the Pixhawk's internal uORB bus to ROS2 DDS over the USB serial link. It is **not** a ROS2 package.

**Option A — snap (recommended):**
```bash
sudo snap install micro-xrce-dds-agent --edge
```

**Option B — build from source:**
```bash
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install
```

> `scripts/start_prop_bench.sh` auto-detects which binary name is present
> (`micro-xrce-dds-agent` or `MicroXRCEAgent`), so either option works.

### 5. Serial port permissions

Serial port access is required to connect to the Pixhawk. Without this the agent will fail with "permission denied" on `/dev/ttyUSB0`.

```bash
sudo usermod -a -G dialout $USER
```

**Log out and back in** for the group change to take effect.
Verify with: `groups | grep dialout`

### 6. Fetch remaining ROS dependencies

```bash
# From workspace root (fscPropBench/)
rosdep install --from-paths src --ignore-src -r -y
```

### 7. Build

```bash
# From workspace root (fscPropBench/)
colcon build
```

colcon resolves dependency order automatically (`px4_msgs` before
`prop_bench_control`). If the build fails, try building them separately:

```bash
colcon build --packages-select px4_msgs
colcon build --packages-select prop_bench_control
```

### 8. Set up the workspace alias

An alias can be setup instead of manually sourcing the `setup.bash` file in each terminal or putting it in `~/.bashrc` and potentially having conflicts. Add this alias instead to `~/.bashrc`:

```bash
echo "alias fscPropBench='source /home/pravin/workspaces/fscPropBench/fscPropBench/install/setup.bash'" >> ~/.bashrc
source ~/.bashrc
```

After this, activate the workspace in any terminal with:

```bash
fscPropBench
```

---

### 9. PX4 Configuration (one-time, via QGroundControl)

Additional setup on the Pixhawk is required. Connect the motor ESC cable to **I/O PWM OUT [MAIN] 1**. Pixhawk should be powered by the ground station laptop, and the ESC powered directly by a sufficient battery. 

#### Parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| `COM_RCREQ` | `0` | Allow offboard control without RC receiver |
| `COM_PREARM_MODE` | `0` | Disable pre-arm checks for bench use |
| `CBRK_SUPPLY_CHK` | `894281` | Skip supply voltage check |
| `CBRK_IO_SAFETY` | `22027` | Skip IO safety switch |
| `SYS_CTRL_ALLOC` | `1` | Enable dynamic control allocation |
| `PWM_MAIN_FUNC1` | `101` | Route Motor 1 → **MAIN OUT 1** |

> **Why `PWM_MAIN_FUNC1 = 101`?**
> The ROS2 node commands `ActuatorMotors.control[0]`, which PX4 calls "Motor 1"
> (function code 101). Setting `PWM_MAIN_FUNC1 = 101` maps that motor command
> to the physical **MAIN OUT 1** pin. All other `PWM_MAIN_FUNC*` should remain
> at `0` (disabled) to prevent unintended outputs on the bench.

#### Actuator mapping in QGroundControl (alternative to parameter above)

1. Open **Vehicle Setup → Actuators**.
2. Under **PWM MAIN**, set Output 1 to function **Motor 1**.
3. Leave all other outputs as **Disabled**.
4. Click **Save** and reboot the Pixhawk.

#### Additional Settings

Your setup may require additional parameter configuration in Pixhawk in order to ensure the system can be armed. This may vary depending on your actual hardware. A sample configuration file is located in `src/px4_configs`. 

## Usage

Follow these steps after every system startup.

### 1. Activate the workspace

```bash
fscPropBench
```

This sources `install/setup.bash` for this project without affecting any other
ROS2 workspaces you may have on the same machine.

### 2. Connect the Pixhawk

Plug the Pixhawk 6 into the laptop via USB. Confirm the port:

```bash
ls /dev/ttyUSB*   # typically /dev/ttyUSB0
# or
ls /dev/ttyACM*   # some Pixhawk configurations appear here
```

### 3. Launch everything

```bash
# From the repo root (fscPropBench/)
./scripts/start_prop_bench.sh                # default port /dev/ttyUSB0
./scripts/start_prop_bench.sh /dev/ttyACM0   # explicit port
```

This single command starts the **Micro-XRCE-DDS agent** and the **GUI** together in the same terminal. Both will print their output to the same window.

### Manual two-terminal alternative

If you prefer to keep the agent and GUI in separate terminals:

```bash
# Terminal 1 — XRCE agent
prop_bench
MicroXRCEAgent serial --dev /dev/ttyUSB0 -b 921600

# Terminal 2 — GUI
prop_bench
ros2 run prop_bench_control prop_bench_gui
```

---

## GUI Reference

### Arm / Disarm
1. Click **Arm** — sends `SET_MODE → OFFBOARD` then `ARM` to PX4.
2. Button changes to **Disarm**. Click again to disarm and zero the throttle.
3. If PX4 rejects arming (pre-arm check failure), the button reverts automatically.

### Manual Mode
1. Check **Enable Manual** to activate the throttle slider.
2. Use the vertical slider (0 – 100 %) to command the motor.
3. The slider is only active when **armed AND manual is checked**.

### Step Profile (steady-state testing)

The **Step Profile Generator** panel is the quickest way to run a fixed-throttle
steady-state hold:

1. Uncheck **Enable Manual** to enter profile mode.
2. Set **Target** (0 – 100 %) and **Hold** duration (seconds).
3. Click **Generate & Load** — previews the step in the plot.
4. **Arm**, then click **Start**.

Sequence that runs:
```
0 %  ──── 2 s safety wait ────►  target %  ──── hold duration ────►  0 %
     (ThrottleProfile WAIT phase)  (immediate step, no ramp)      (auto stop)
```

The 2-second wait is enforced regardless of the profile loaded.
Throttle returns to zero automatically when the hold ends.

### CSV Throttle Profile Mode (arbitrary waveforms)

1. Uncheck **Enable Manual**.
2. Click **Scan Throttle Profile** — lists `.csv` files from `throttle_profile/`.
3. Select a file and click **Load Throttle Profile** — previews the waveform.
4. **Arm**, then click **Start**.
   - **Wait phase**: 2 s at zero throttle.
   - **Speed-up phase**: ramps smoothly to `profile_data[0]`.
   - **Profile phase**: plays CSV values at 100 Hz.
5. Click **Stop** at any time to abort and zero the throttle.

### Recording Data

```bash
ros2 bag record /prop_bench/result
```

Result topic layout (`geometry_msgs/TwistStamped`):

| Field | Data |
|-------|------|
| `twist.linear.x` | Throttle command (0 – 100 %) |
| `twist.linear.y` | Torque (Nm) — sensor hook |
| `twist.linear.z` | Thrust (N) — sensor hook |
| `twist.angular.x` | ESC RPM — sensor hook |
| `twist.angular.y` | Optical RPM — sensor hook |
| `twist.angular.z` | Voltage (V) — sensor hook |

---

## Throttle Profile CSV Format

- Single-column `.csv`, one value per row.
- Values in range **0 – 100** (percent throttle).
- Update rate assumed **100 Hz** (one row per 10 ms).

Example — 5-second ramp to 50 %:
```
0
5
10
15
20
25
30
35
40
45
50
```

---

## Adding Sensor Feedback

The four grey LCD displays (Torque, Thrust, ESC RPM, Voltage) are placeholders.
To wire in real sensors:
1. Add a ROS2 subscriber in `PropBenchNode` for your sensor topic.
2. Emit a new `pyqtSignal` from the subscriber callback.
3. Connect the signal in `PropBenchController` and update the relevant LCD widget.
