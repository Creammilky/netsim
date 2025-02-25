#!/bin/sh

# Test host-leaf connectivity
docker exec clab-fdc-leaf01 ping 192.168.11.2 -c 3
docker exec clab-fdc-leaf01 ping 192.168.12.2 -c 3
docker exec clab-fdc-leaf02 ping 192.168.21.2 -c 3
docker exec clab-fdc-leaf02 ping 192.168.22.2 -c 3
docker exec clab-fdc-leaf03 ping 192.168.31.2 -c 3
docker exec clab-fdc-leaf03 ping 192.168.32.2 -c 3
