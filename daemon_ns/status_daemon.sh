#!/bin/bash

PIDFILE="../test/daemon/mydaemon.pid"

if [ -f "$PIDFILE" ]; then
    PID=$(cat $PIDFILE)
    if ps -p $PID > /dev/null; then
        echo "Daemon is running. PID: $PID"
    else
        echo "Pidfile exists but no process found. Cleaning up..."
        rm -f "$PIDFILE"
    fi
else
    echo "Daemon is not running."
fi
