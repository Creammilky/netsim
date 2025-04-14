
# 🚧 Currently Working on this Project

This system is a BGP Digital twin. It aims to provide a full functional BGP simulating, experimenting, data collecting, and analysing system 
for someone wants to deploy their BGP lab fast, accurate and reality. The system is using no SDN technologies to provide the closest "twinning" to production environment.
We are using dockers with FRRouting instead.

## IP file

### What is an IP file

IP file (`.ip`) is the defined file format used for recording all the networking information of nodes in this system.
It usually contains these parameters: 
```json
{
  "loopback": "LO_IP",
  "type": "AS | VP | HOST",
  "asn": "AS_NUMBER",
  "interfaces": [
    {
      "name": "NAME_OF_THE_NETWORK_INTERFACE",
      "ip": "IP_ADDRESS",
      "endpoint": "NODE_ID:ENDPOINT_INTERFACE"
    }
  ]
}

```
 
### How I generate ip for types of nodes
If a node (AS, host, VP) with no given IP address, system will assign a random IP to it.

I use all of 3 private address prefixes.\
`10.0.0.0/8` is for ASs\
`172.16.0.0/12` is for whatever Hosts\
`192.168.0.0/24` is for Vantage Points (Because I think the number of VPs will not be too much)


## FRR module

### Generate frr.conf

For frr.conf

- **'eth0'** cannot use for peer-links in frr devices, because it is reserved for and used by container lab **'mgmt-ipv4'**



## Container lab module

### Generate clab.yml

- notice that we may not use **'eth0'** in links because *'eth0'* is reserved for container lab management ipv4 (mgmt-ipv4)


### How to refresh a lab or hot-modification

Maybe use docker command?

## Some developing notes

:smile:
consider Mininet, similar to container lab and have python api

also consider Container-net, can use container as a host, including frr

**BMP**
\
Fetch BGP updates... info from peer(A frr server or other router) but sending message to control/modify
\
TCP connection

## License

License: All Rights Reserved © 2025 Siyuan Tan
