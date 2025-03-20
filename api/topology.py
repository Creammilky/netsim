import ast
import networkx as nx


def bgp_to_xml(bgp_update_file_path: str, existing_topology=None):
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
            try:
                line = ast.literal_eval(line.strip())  # 解析 BGP 数据
            except (SyntaxError, ValueError) as e:
                print(f"解析错误: {e}, 跳过 -> {line}")
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
                G.add_node(data["host"], type="VP", ip_addr=None)

            if not G.has_node(data["peer_asn"]):
                G.add_node(data["peer_asn"], type="as", ip_addr=data["peer"])

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
                        G.add_edge(as1, as2)
    return G
