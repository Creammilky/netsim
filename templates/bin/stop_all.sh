#!/bin/bash

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Stop all..."
bash "$SCRIPT_DIR/stop_daemon.sh"
sleep 1

sudo clab destroy

docker ps --filter "name=kafka" -q | xargs -r docker stop