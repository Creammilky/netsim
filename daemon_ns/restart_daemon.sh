#!/bin/bash

echo "Restarting daemon..."
bash /home/carl/Projects/netsim/daemon_ns/stop_daemon.sh
sleep 1
bash /home/carl/Projects/netsim/daemon_ns/start_daemon.sh
