#!/usr/bin/env bash
# start_prop_bench.sh
# --------------------
# One-command startup: sources ROS2, then launches the XRCE-DDS agent
# and the prop bench GUI together.
#
# Usage:
#   ./scripts/start_prop_bench.sh                   # auto-detects ttyUSB* adapter
#   ./scripts/start_prop_bench.sh /dev/ttyUSB1      # explicit port override
#
# Port detection logic:
#   The Pixhawk USB cable always appears as /dev/ttyACM* (CDC-ACM device).
#   The USB-to-UART adapter always appears as /dev/ttyUSB* (USB serial device).
#   These are distinct device types so the adapter can be found automatically
#   regardless of plug-in order.
#
set -e

if [ -n "$1" ]; then
    PORT="$1"
else
    # Auto-detect the USB-UART adapter port (ttyUSB*, not ttyACM*)
    USB_PORTS=(/dev/ttyUSB*)
    if [ "${USB_PORTS[0]}" = "/dev/ttyUSB*" ]; then
        echo "[error] No USB-UART adapter found on any /dev/ttyUSB* port."
        echo "        Plug in the UART adapter (TELEM1) and retry."
        echo "        Or pass the port explicitly: $0 /dev/ttyUSBx"
        exit 1
    fi
    if [ "${#USB_PORTS[@]}" -gt 1 ]; then
        echo "[warn]  Multiple ttyUSB devices found: ${USB_PORTS[*]}"
        echo "[warn]  Using ${USB_PORTS[0]}. Pass a port explicitly to override."
    fi
    PORT="${USB_PORTS[0]}"
fi

# ── Source ROS2 and workspace ────────────────────────────────────────────────
source /opt/ros/humble/setup.bash

# Source the colcon install space if it exists relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_INSTALL="$SCRIPT_DIR/../install/setup.bash"
if [ -f "$WORKSPACE_INSTALL" ]; then
    source "$WORKSPACE_INSTALL"
else
    echo "[warn] Could not find install/setup.bash — run 'colcon build' first."
    echo "       Expected: $WORKSPACE_INSTALL"
fi

# ── Clean up stale agent processes ───────────────────────────────────────────
# If a previous session was killed, the agent may still hold the serial port
# open and the Pixhawk DDS client may be stuck in the old session state.
# Kill any lingering agent processes and wait for the Pixhawk client to detect
# the dropped session and re-initiate before the new agent starts.
if pkill -f MicroXRCEAgent 2>/dev/null || pkill -f micro-xrce-dds-agent 2>/dev/null; then
    echo "[info]  Stopped stale agent process — waiting 3 s for Pixhawk to reset DDS session..."
    sleep 3
fi

# ── Launch ───────────────────────────────────────────────────────────────────
# Detect which agent binary is available
if command -v MicroXRCEAgent &>/dev/null; then
    AGENT_BIN="MicroXRCEAgent"
elif command -v micro-xrce-dds-agent &>/dev/null; then
    AGENT_BIN="micro-xrce-dds-agent"
else
    echo "[error] Micro-XRCE-DDS Agent not found."
    echo "        Install via: sudo snap install micro-xrce-dds-agent --edge"
    exit 1
fi
export PROP_BENCH_PROFILE_DIR="$SCRIPT_DIR/../src/prop_bench_control/throttle_profile"
if [ ! -d "$PROP_BENCH_PROFILE_DIR" ]; then
    echo "WARNING: Profile directory not found at $PROP_BENCH_PROFILE_DIR"
    echo "GUI will fallback to internal share or home directory."
fi

echo "Agent binary  : $AGENT_BIN"
echo "Serial port   : $PORT"
echo "Profile dir   : $PROP_BENCH_PROFILE_DIR"

exec ros2 launch prop_bench_control prop_bench.launch.py \
    serial_port:="$PORT" \
    xrce_agent_bin:="$AGENT_BIN"
