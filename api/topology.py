import ast
import networkx as nx
from utils import logger

# Initialize logger
log = logger.Logger("Topology")

def bgp_to_xml(bgp_update_file_path: str):
    # Todo: Unfinished.
    with open(bgp_update_file_path) as file:
        for line in file:
            print(line.strip())  # strip() 去除换行符
    pass


def bgp_to_networkx(bgp_update_file_path: str, existing_topology=None):
    if existing_topology is None:
        G = nx.Graph()
    else:
        G = existing_topology

    with open(bgp_update_file_path) as file:
        for line in file:
            log.debug(line.strip())
            try:
                line = ast.literal_eval(line.strip())  # 解析 BGP 数据
            except (SyntaxError, ValueError) as e:
                log.warning("解析错误: {e}, 跳过 -> {line}")
                continue

            # 确保 "path" 不是 None
            path = line.get("path") or []  # 如果 path 为 None，改为空列表

            # 解析数据
            data = {
                "peer": line.get("peer"),
                "peer_asn": str(line.get("peer_asn")),
                "host": line.get("host"),
                "type": line.get("type"),
                "path": list(map(str, path)),  # 确保 path 可迭代
                "origin": line.get("origin"),
                "announcements": line.get("announcements", []),
                "withdrawals": line.get("withdrawals", []),
            }

            # 处理 BGP 拓扑
            if not G.has_node(data["host"]):
                G.add_node(data["host"], type="VP", ip_addr=None, prefix = [])

            if not G.has_node(data["peer_asn"]):
                G.add_node(data["peer_asn"], type="as", ip_addr=data["peer"], prefix = [])

            if not G.has_edge(data["host"], data["peer_asn"]):
                G.add_edge(data["host"], data["peer_asn"])

            # 处理 AS Path
            if len(data["path"]) > 1:
                for i in range(len(data["path"]) - 1):
                    as1, as2 = data["path"][i], data["path"][i + 1]

                    if not G.has_node(as1):
                        G.add_node(as1, type="as")
                    if not G.has_node(as2):
                        G.add_node(as2, type="as")

                    if not G.has_edge(as1, as2):
                        if as1 == as2:
                            # Todo: how to deal with this
                            log.info(f"{as1} acclaimed a prepending ")
                            G.add_edge(as1, as2)
                        else:
                            G.add_edge(as1, as2)

            if not data["path"]:  # 确保 path 不是空列表
                log.debug(f"Empty path found in data: {data}")
                prefix_asn = data["peer_asn"]  # 取最后一个 ASN
            else:
                prefix_asn = data["path"][-1]

            prefixs = nx.get_node_attributes(G, "prefix").get(prefix_asn,[])

            log.debug(f"{prefix_asn} prefix: {prefixs}")

            # Announcement
            if data.get("announcements") and len(data["announcements"]) > 0:
                first_announcement = data["announcements"][0]

                if "prefixes" in first_announcement and first_announcement["prefixes"]:
                    prefixs.append(first_announcement["prefixes"])
                    nx.set_node_attributes(G, {prefix_asn: prefixs}, "prefix")
                else:
                    log.debug(f"No prefixes found in announcement: {first_announcement}")
            else:
                log.debug("data['announcements'] is empty or missing")

            # Withdraw
            # Todo: withdraw?




    return G
