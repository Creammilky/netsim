
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

## 📖 BGP 仿真环境 Lab 创建进度记录

本仓库用于记录基于 NetworkX 图形描述生成 BGP 仿真 Lab 的各个步骤完成情况。节点类型分为：
- **AS**（自治系统路由器）
- **VP**（Vantage Point）
- **Host**（终端主机）

---

### 📊 实验环境创建进度表

| 序号 | 功能点                                            | AS | VP | Host  |
|:--:|:-----------------------------------------------|:---|:---|:------|
| 1  | 创建目录 `create_lab_dir`                          | ✅  | ✅  | ✅     |
| 2  | 网卡编号与接口名分配 `assign_id_for_router`              | ✅  | ✅  | ✅     |
| 3  | IP 分配 `define_network_interfaces_ip`           | ✅  | ✅  | ✅     |
| 4  | FRR 配置 `gen_frr_config / daemons / vtysh.conf` | ✅  | ❌  | ⬜     |
| 5  | 生成 containerlab 拓扑 YAML `gen_yaml_from_nx`     | ✅  | ✅  | ❌     |
| 6  | 生成交互式拓扑图 `create_interactive_graph`            |  ❌  | ❌   | ❌      |

### 📈 进度记录说明

- 每个功能点根据节点类型，记录完成状态：
  - ✅ 表示已完成
  - ❌ 表示未完成
  - ⬜ 表示不需要
- 随开发实时更新本表格，便于查看开发进度

---

### 📌 使用说明

#### 功能简介
本工具通过 NetworkX 图结构定义网络拓扑，依据节点类型自动完成配置生成、IP 分配、YAML 拓扑文件创建以及交互式拓扑图绘制。

#### 节点类型定义：
- `AS`：自治系统核心路由器，负责 BGP 配置
- `VP`：用于观测路由状态的观测点 (Vantage Point)
- `Host`：终端主机，模拟客户或边缘设备

#### 环境依赖
- Python 3.9+
- containerlab
- frr (Docker 镜像)
- 必要 Python 包详见 `requirements.txt`

---

## License

License: All Rights Reserved © 2025 Siyuan Tan
