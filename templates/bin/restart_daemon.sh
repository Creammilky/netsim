#!/bin/bash

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Restarting daemon..."
bash "$SCRIPT_DIR/stop_daemon.sh"
sleep 1
bash "$SCRIPT_DIR/start_daemon.sh"