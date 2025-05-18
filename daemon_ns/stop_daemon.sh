#!/bin/bash

PIDFILE="../test/daemon/mydaemon.pid"

if [ -f "$PIDFILE" ]; then
    PID=$(cat $PIDFILE)
    echo "Stopping daemon process $PID..."
    kill -SIGTERM $PID
    sleep 1
    echo "Done."
else
    echo "No pidfile found."
fi
