import json
import os

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


def assign_id_for_routers(G: nx.Graph, CURRENT_LAB_PATH, vp_dafault_prefix="192.168.0.0/16", as_default_prefix="10.0.0.0/8"):
    """
    Assign loopback IP addresses to routers, and write them to individual files.
    Each file includes loopback IP, type, ASN (if available), and placeholder for port IPs.
    """
    node_type = nx.get_node_attributes(G, "type")

    for node in G.nodes():
        router_ip = None

        if node_type.get(node) == "as":
            if nx.get_node_attributes(G, node).get('ip_addr') is None:
                router_ip = ipv4_utils.generate_random_ipv4_with_save(
                    prefix=as_default_prefix,
                    count=1,
                    IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips')
                )

                log.info("Assigning IP: {} for router {}".format(router_ip, node))
                nx.set_node_attributes(G, {node: router_ip}, "ip_addr")

        elif node_type.get(node) == "VP":
            if nx.get_node_attributes(G, node).get('ip_addr') is None:
                router_ip = ipv4_utils.generate_random_ipv4_with_save(
                    prefix=vp_dafault_prefix,
                    count=1,
                    IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips')
                )
                log.info("Assigning IP: {} for router {}".format(router_ip, node))
                nx.set_node_attributes(G, {node: router_ip}, "ip_addr")

        if router_ip:
            ip_file_data = {
                "loopback": router_ip,
                "type": node_type.get(node),
                "asn": node,
                "interfaces": []  # 可在后续接口 IP 分配时 append
            }

            ip_file_path = os.path.join(CURRENT_LAB_PATH, "cache", f"{node}.ip")
            try:
                with open(ip_file_path, "w") as f:
                    json.dump(ip_file_data, f, indent=2)
                log.info(f"Wrote IP info to {ip_file_path}")
            except Exception as e:
                log.error(f"Error writing IP file for {node}: {e}")


def define_network_interfaces(G: nx.Graph, CURRENT_LAB_PATH):

    eth_table = assign_eth(G)

    for u_eth, v_eth in eth_table:
        # Assign p2p ip
        ip_lower, ip_higher = ipv4_utils.generate_p2p_ip_pairs(IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips'))
        #ip_lower, ip_higher = "111", "222"
        node_u = u_eth.strip().split(":")[0]
        node_v = v_eth.strip().split(":")[0]
        eth_u = u_eth.strip().split(":")[1]
        eth_v = v_eth.strip().split(":")[1]

        def update_node_ip_file(node_ip_file_path, eth, ip, endpoint):
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
                        "endpoint": endpoint
                    })

                # 写回文件
                with open(node_ip_file_path, "w") as f:
                    json.dump(ip_json, f, indent=2)

                return True

            except Exception as e:
                log.error(f"更新{node_ip_file_path}时发生错误: {str(e)}")
                return False

        # 使用示例
        node_u_ip_file_path = os.path.join(CURRENT_LAB_PATH, "cache", f"{node_u}.ip")
        node_v_ip_file_path = os.path.join(CURRENT_LAB_PATH, "cache", f"{node_v}.ip")

        # 更新node_u的IP配置
        update_node_ip_file(
            node_u_ip_file_path,
            eth_u,
            ip_lower,
            f"{node_v}:{eth_v}"
        )

        # 更新node_v的IP配置
        update_node_ip_file(
            node_v_ip_file_path,
            eth_v,
            ip_higher,
            f"{node_u}:{eth_u}"
        )

    return eth_table
