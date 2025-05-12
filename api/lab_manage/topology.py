import ast
import os
from xml.dom import minidom

import networkx as nx
import xml.etree.ElementTree as ET

from utils import logger, xml_parser

# Initialize logger
log = logger.Logger("Topology")


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


'''
Make user have ability to mitigate whole network topology via export to XML
'''
# # I don't know why new function has problem with graph comparing, so keep this
# def networkx_to_xml(G: nx.Graph, save_path: str):
#     # 创建根元素
#     root = ET.Element('Graph')
#
#     # 创建 Nodes 节点
#     nodes_elem = ET.SubElement(root, 'Nodes')
#
#     # 分离字符串类型的节点ID和数字类型的节点ID
#     str_nodes = [(node_id, attrs) for node_id, attrs in G.nodes(data=True) if isinstance(node_id, str)]
#     num_nodes = [(node_id, attrs) for node_id, attrs in G.nodes(data=True) if isinstance(node_id, (int, float))]
#
#     # 按字典顺序排序字符串类型的节点ID
#     str_nodes.sort(key=lambda x: x[0])
#
#     # 按数字顺序排序数字类型的节点ID
#     num_nodes.sort(key=lambda x: x[0])
#
#     # 将排序后的节点合并
#     sorted_nodes = str_nodes + num_nodes
#
#     # 为每个节点创建 XML 元素
#     for node_id, attrs in sorted_nodes:
#         node_elem = ET.SubElement(nodes_elem, 'Node', id=str(node_id))
#
#         # 添加 ASN 标签，值等于 node_id
#         asn_elem = ET.SubElement(node_elem, 'ASN')
#         asn_elem.text = str(node_id)
#
#         # 添加节点的其他属性
#         for key, value in attrs.items():
#             sub_elem = ET.SubElement(node_elem, key)
#             sub_elem.text = str(value)
#
#     # 创建并保存 XML 文件
#     tree = ET.ElementTree(root)
#     tree.write(save_path, encoding='utf-8', xml_declaration=True)

def networkx_to_xml(G: nx.Graph, save_path: str):
    # 创建根元素
    root = ET.Element('Graph')

    # 创建 Nodes 节点
    nodes_elem = ET.SubElement(root, 'Nodes')

    # 分离纯数字字符串和混合字符串类型的节点ID
    def sort_key(node_id):
        # 判断是否是纯数字字符串，如果是则转换为整数，否则按字典序排序
        if node_id.isdigit():
            return (0, int(node_id))  # 纯数字字符串按数值排序
        else:
            return (1, node_id)  # 混合字符串按字典序排序

    # 将节点按排序规则排序
    sorted_nodes = sorted(G.nodes(data=True), key=lambda x: sort_key(x[0]))

    # 为每个节点创建 XML 元素
    for node_id, attrs in sorted_nodes:
        node_elem = ET.SubElement(nodes_elem, 'Node', id=str(node_id))

        # 添加 ASN 标签，值等于 node_id
        asn_elem = ET.SubElement(node_elem, 'ASN')
        asn_elem.text = str(node_id)

        # 添加节点的其他属性
        for key, value in attrs.items():
            sub_elem = ET.SubElement(node_elem, key)
            sub_elem.text = str(value)

    # 创建 Edges 节点
    edges_elem = ET.SubElement(root, 'Edges')
    for source, target, attrs in G.edges(data=True):
        edge_elem = ET.SubElement(edges_elem, 'Edge', source=str(source), target=str(target))
        for key, value in attrs.items():
            sub_elem = ET.SubElement(edge_elem, key)
            sub_elem.text = str(value)

    # 格式化为字符串
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed_str = minidom.parseString(xml_str)
    pretty_xml_as_bytes = parsed_str.toprettyxml(indent="    ", encoding="UTF-8")
    pretty_xml_as_string = pretty_xml_as_bytes.decode("utf-8")

    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 写入文件
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_as_string)

    log.info(f"XML saved to: {save_path}")

def xml_to_networkx(xml_path: str):
    parser = xml_parser.GraphParser(xml_path)
    parser.parse()
    G_xml = parser.get_networkx()
    return G_xml

if __name__ == "__main__":
    G = nx.Graph()
    G.add_node("1", Label="Router A", ASN=64512, type="as")
    G.add_node("2", Label="Router B", ASN=64513, type="as")
    G.add_node("h1", Label="Router C", ASN=64514, Type="host", Prefix="100.1.1.0/24")
    G.add_node("4", Label="Router D", ASN=64515, type="as")
    G.add_node("5", Label="Router E", ASN=64516, Weight=0.80, type="as")
    G.add_node("6", Label="Router F", ASN=64517, type="as")
    G.add_node("h2", Label="Router C", ASN=64512, Type="host", Prefix="100.3.3.0/24")

    G.add_edge("2", "4")
    G.add_edge("4", "5")
    G.add_edge("5", "6")
    G.add_edge("h1", "6")
    G.add_edge("1", "4")
    G.add_edge("1", "h2", Weight=0.80, Status="active")

    xml_output = networkx_to_xml(G, "./test.xml")
    print(xml_output)
