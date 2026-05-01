#!/usr/bin/env bash
# start_prop_bench.sh
# --------------------
# One-command startup: sources ROS2, then launches the XRCE-DDS agent
# and the prop bench GUI together.
#
# Usage:
#   ./scripts/start_prop_bench.sh                   # uses /dev/ttyUSB0
#   ./scripts/start_prop_bench.sh /dev/ttyACM0      # explicit port
#
set -e

PORT="${1:-/dev/ttyUSB0}"

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
