
# 🚧 Currently Working on this Project 
:smile:
consider Mininet, similar to container lab and have python api

also consider Container-net, can use container as a host, including frr

### Generate clab.yml

- notice that we may not use **'eth0'** in links because *'eth0'* is reserved for container lab management ipv4 (mgmt-ipv4)

### Generate frr.conf

For frr.conf

- **'eth0'** cannot use for peer-links in frr devices, because it is reserved for and used by container lab **'mgmt-ipv4'**
- God, I haven't really know how to write a frr.conf yet...