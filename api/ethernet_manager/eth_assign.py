import json
import os
from sys import prefix

import networkx as nx
from dotenv import load_dotenv

from utils import ipv4_utils
from utils import logger


# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("EthManager")

# Fetch environment variables
LABS_PATH = os.getenv("LABS_PATH")
if not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")


def assign_eth(G: nx.Graph):
    edges = []
    eth_count = [(node_id, 0) for node_id, _ in G.degree()]
    log.debug(eth_count)
    for u, v in G.edges(data=False):
        if u == v:
            log.warning(f"Edge [{u},{v}] are Loopback in network topology")
            # Todo: How to deal with loopback

        # I think it is not necessary but just let it here
        elif not G.has_edge(u, v):
            log.error(f"Edge [{u},{v}] not found network topology")
            raise Exception("Unexpected edge found in network topology")

        else:
            for idx, (node_id, count) in enumerate(eth_count):
                if node_id == u and count < nx.degree(G, u):
                    u_eth = str(u) + ":eth" + str(count + 1)
                    eth_count[idx] = (node_id, count + 1)  # Update the tuple in the list
                elif node_id == v and count < nx.degree(G, v):
                    v_eth = str(v) + ":eth" + str(count + 1)
                    eth_count[idx] = (node_id, count + 1)  # Update the tuple in the list
                else:
                    # log.debug(f"{node_id}, {u}, {v}, {count}")
                    continue
            edges.append((u_eth, v_eth))
    return edges

def assign_id_for_router(G: nx.Graph, CURRENT_LAB_PATH,
                         vp_default_prefix="192.168.0.0/16",
                         as_default_prefix="10.0.0.0/8",
                         host_default_prefix="172.16.0.0/12"):
    """
    Assign loopback IP addresses to routers, and write them to individual files.
    Each file includes loopback IP, type, ASN (if available), and placeholder for port IPs.
    """
    node_type = nx.get_node_attributes(G, "type")
    node_name = nx.get_node_attributes(G, "name")

    for node in G.nodes():
        router_ip = G.nodes[node].get('ip_addr')
        node_t = node_type.get(node, "as")  # 默认为 as 类型
        node_n = node_name.get(node, f"{node_t}:{node}")

        if router_ip is None:
            if node_t.strip().lower() == "as":
                prefix = as_default_prefix
            elif node_t.strip().lower() == "vp":
                prefix = vp_default_prefix
            elif node_t.strip().lower() == "host":
                prefix = host_default_prefix
            else:
                log.error(f"Unknown node type '{node_t}' for node {node}")
                continue

            router_ip = ipv4_utils.generate_random_ipv4_with_save(
                prefix=prefix,
                count=1,
                IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips')
            )
            G.nodes[node]['ip_addr'] = router_ip
            log.info(f"Assigning IP: {router_ip} for router {node_t.upper()} {node}")
        else:
            log.info(f"Router {node} ({node_t}) already has IP {router_ip}, skip assigning")

        own_prefix = None
        if node_type.get(node).strip().lower() == "host":
            node_network_prefixes = nx.get_node_attributes(G, "prefix", None)
            own_prefix = node_network_prefixes.get(node, None)

        ip_file_data = {
            "name": node_n,
            "loopback": router_ip,
            "type": node_t,
            "asn": node,
            "prefixes": own_prefix if own_prefix is not None else None, # Todo: One host has and can only has one prefix by now, I might improve this later.
            "interfaces": [],
        }
        new_ip_file(CURRENT_LAB_PATH, node, ip_file_data)


def new_ip_file(CURRENT_LAB_PATH, node, ip_file_data):
    ip_file_path = os.path.join(CURRENT_LAB_PATH, "cache", f"{node}.ip")
    try:
        with open(ip_file_path, "w") as f:
            json.dump(ip_file_data, f, indent=2)
        log.info(f"Wrote IP info to {ip_file_path}")
    except Exception as e:
        log.error(f"Error writing IP file for {node}: {e}")


def define_network_interfaces_ip(G: nx.Graph, CURRENT_LAB_PATH):

    eth_table = assign_eth(G)

    for u_eth, v_eth in eth_table:
        # Assign p2p ip
        node_u = u_eth.strip().split(":")[0]
        node_v = v_eth.strip().split(":")[0]
        eth_u = u_eth.strip().split(":")[1]
        eth_v = v_eth.strip().split(":")[1]
        node_type = nx.get_node_attributes(G, "type")

        if node_type.get(node_v).strip().lower() != "host" and node_type.get(node_u).strip().lower() != "host":
            log.debug(f"Assigning interface for as/vp {node_u} and {node_v}")
            host_prefix = None
            ip_lower, ip_higher , _ = ipv4_utils.generate_p2p_ip_pairs(IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips'))
        else:
            # prefix is decide by the one who owns the prefix. Router's ip just need to satisfy connection requirements.
            if node_type.get(node_u).strip().lower() == "host":
                log.debug(f"Assigning interface for host {node_u}")
                hostname = node_u
            else:
                log.debug(f"Assigning interface for host {node_v}")
                hostname = node_v
            with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
                ip_file_json = json.loads(f.read())
            host_prefix = ip_file_json["prefixes"]
            ip_lower, ip_higher, _ = ipv4_utils.generate_p2p_ip_pairs(IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips'),
                                                                   prefix=host_prefix)

        node_u_ip_file_path = os.path.join(CURRENT_LAB_PATH, "cache", f"{node_u}.ip")
        node_v_ip_file_path = os.path.join(CURRENT_LAB_PATH, "cache", f"{node_v}.ip")

        # 更新node_u的IP配置
        update_node_ip_file(
            node_ip_file_path=node_u_ip_file_path,
            eth=eth_u,
            ip=ip_lower,
            endpoint=f"{node_v}:{eth_v}",
            endpoint_ip=ip_higher,
            peer_type=node_type.get(node_v),
            host_prefix=host_prefix,
        )

        # 更新node_v的IP配置
        update_node_ip_file(
            node_ip_file_path=node_v_ip_file_path,
            eth=eth_v,
            ip=ip_higher,
            endpoint=f"{node_u}:{eth_u}",
            endpoint_ip=ip_lower,
            peer_type=node_type.get(node_u),
            host_prefix=host_prefix,
        )

    return eth_table


def update_node_ip_file(node_ip_file_path, eth, ip, endpoint, endpoint_ip ,peer_type, host_prefix = None):
        try:
            # 尝试读取现有配置
            try:
                with open(node_ip_file_path, "r") as f:
                    ip_json = json.loads(f.read())
            except FileNotFoundError:
                # 文件不存在时创建新的配置
                ip_json = {"interfaces": []}
            except json.JSONDecodeError:
                log.error(f"{node_ip_file_path} 不是有效的JSON")
                return False

            # 检查接口是否已经存在
            interface_exists = False
            for interface in ip_json["interfaces"]:
                if eth in interface:
                    # 接口已存在，更新信息
                    interface[eth] = ip
                    interface["endpoint"] = endpoint
                    interface_exists = True
                    break

            # 如果接口不存在，添加新接口
            if not interface_exists:
                ip_json["interfaces"].append({
                    "name" : eth,
                    "ip": ip,
                    "endpoint": endpoint,
                    "endpoint_ip": endpoint_ip,
                    "peer_type": peer_type,
                    "host_prefix": host_prefix if host_prefix is not None else None,
                })

            # 写回文件
            with open(node_ip_file_path, "w") as f:
                json.dump(ip_json, f, indent=2)

            return True

        except Exception as e:
            log.error(f"更新{node_ip_file_path}时发生错误: {str(e)}")
            return False