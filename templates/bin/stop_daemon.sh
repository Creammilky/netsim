#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$SCRIPT_DIR/daemon.pid"

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    echo "Stopping daemon... PID: $PID"
    kill "$PID"
    rm -f "$PIDFILE"
else
    echo "No pidfile found. Daemon may not be running."
fi
