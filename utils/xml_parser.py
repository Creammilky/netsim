import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional
import networkx as nx
from api.lab_manage import generate_clab


@dataclass
class Property:
    name: str
    value: str

'''
I decide to put other attr into properties, like commercial relationships...
'''
@dataclass
class Node:
    id: str
    ip_addr: str
    prefix: list
    group: str
    weight: float
    ASN: int
    type: str
    properties: List[Property]

    def get_attr(self) -> dict:
        return {"id": self.id,
                "ip_addr": self.ip_addr,
                "group": self.group,
                "prefix": self.prefix,
                "weight": self.weight,
                "ASN": self.ASN,
                "type": self.type,
                "properties": self.properties}



@dataclass
class Edge:
    source: str
    target: str
    weight: float
    type: str
    properties: List[Property]

    def get_attr(self) -> dict:
        return {"weight": self.weight,
                "type": self.type,
                "properties": self.properties}


class GraphParser:
    def __init__(self, xml_file: str):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def parse(self):
        self._parse_nodes()
        self._parse_edges()

    @staticmethod
    def find_text_case_insensitive(parent, tag_name):
        for elem in parent:
            if elem.tag.lower() == tag_name.lower():
                return elem.text
        return None

    def _parse_nodes(self):

        for node_elem in self.root.findall('./Nodes/Node'):
            # 属性字典，统一小写
            attribs = {k.lower(): v for k, v in node_elem.attrib.items()}
            _node_id = attribs.get('id')

            _group = self.find_text_case_insensitive(node_elem, 'Label')

            _weight_text = self.find_text_case_insensitive(node_elem, 'Weight')
            _weight = float(_weight_text) if _weight_text is not None else None

            _ASN = self.find_text_case_insensitive(node_elem, 'ASN')
            _type = self.find_text_case_insensitive(node_elem, 'Type')

            _ip_addr = self.find_text_case_insensitive(node_elem, 'Ip_addr')
            _prefix = self.find_text_case_insensitive(node_elem, 'Prefix') or []
            # 读取 Properties
            properties = []
            for prop in node_elem.findall('./Properties/Property'):
                prop_name = None
                # 同样处理属性字典，大小写无关
                prop_attribs = {k.lower(): v for k, v in prop.attrib.items()}
                prop_name = prop_attribs.get('name')

                prop_value = prop.text or ''
                properties.append(Property(name=prop_name, value=prop_value))

            self.nodes[_node_id] = Node(
                id=_node_id,
                ip_addr=_ip_addr,
                prefix=_prefix,
                group=_group,
                weight=_weight,
                ASN = _ASN,
                type=_type,
                properties=properties
            )

    def _parse_edges(self):
        for edge_elem in self.root.findall('./Edges/Edge'):
            source = edge_elem.get('source')
            target = edge_elem.get('target')
            weight = float(edge_elem.find('Weight').text) if edge_elem.find('Weight') is not None else None
            edge_type = self.find_text_case_insensitive(edge_elem, 'Type')
            properties = []
            for prop in edge_elem.findall('./Properties/Property'):
                properties.append(Property(
                    name=prop.get('name'),
                    value=prop.text if prop.text else ''
                ))

            self.edges.append(Edge(
                source=source,
                target=target,
                weight=weight,
                type=edge_type,
                properties=properties
            ))

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_connected_nodes(self, node_id: str) -> List[str]:
        connected = []
        for edge in self.edges:
            if edge.source == node_id:
                connected.append(edge.target)
            elif edge.type == 'undirected' and edge.target == node_id:
                connected.append(edge.source)
        return connected

    def __str__(self) -> str:
        self.parse()
        output = []
        output.append("Nodes:")
        for node_id, node in self.nodes.items():
            output.append(f"ID: {node_id}, Label: {node.label}, Weight: {node.weight}")

        # Print all edges
        output.append("\nEdges:")
        for edge in self.edges:
            output.append(f"{edge.source} -> {edge.target} (Weight: {edge.weight}, Type: {edge.type})")

        return output.__str__()

    def get_networkx(self):
        G = nx.Graph()
        for node_id, node in self.nodes.items():
            G.add_nodes_from([(node_id, node.get_attr())])
        for edge in self.edges:
            G.add_edges_from([(edge.source, edge.target, edge.get_attr())])
        return G


# Usage example
if __name__ == "__main__":
    parser = GraphParser("../test/route_2.xml")
    parser.parse()

    # Print all nodes and their weights
    print("Nodes:")
    for node_id, node in parser.nodes.items():
        print(f"ID: {node_id}, Label: {node.group}, Weight: {node.weight}")

    # Print all edges
    print("\nEdges:")
    for edge in parser.edges:
        print(f"{edge.source} -> {edge.target} (Weight: {edge.weight}, Type: {edge.type})")

    G = parser.get_networkx()
    # graph_utils.draw_networkx_graph(G)
    # graph_utils.draw_networkx_graph_complex(G)
    for g_node, g_attr in G.nodes.items():
        print(f"{g_node}: {g_attr}")

    # ASN = nx.get_node_attributes(G, "ASN")
    # print(ASN)
    #
    # print("--------------------------------\n")
    # print({node: G.nodes[node] for node in G.nodes})
    # print("--------------------------------\n")
    #
    # print(nx.degree(G))
    # print("--------------------------------\n")
    # print(G.edges())

    generate_clab.gen_yaml_from_nx(G)


    #interactive_net = graph_utils.InteractiveNetwork(G)
    #interactive_net.create_interactive_graph().show('../network.html', notebook=False)