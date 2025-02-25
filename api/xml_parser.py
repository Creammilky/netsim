import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional
import networkx as nx
from utils import graph_utils
from api import clab_yaml_gen


@dataclass
class Property:
    name: str
    value: str


@dataclass
class Node:
    id: str
    label: str
    weight: float
    ASN: int
    properties: List[Property]

    def get_attr(self) -> dict:
        return {"id": self.id,
                "label": self.label,
                "weight": self.weight,
                "ASN": self.ASN,
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

    def _parse_nodes(self):
        for node_elem in self.root.findall('./Nodes/Node'):
            node_id = node_elem.get('id')
            label = node_elem.find('Label').text
            weight = float(node_elem.find('Weight').text) if node_elem.find('Weight') is not None else None
            ASN = node_elem.find('ASN').text
            properties = []
            for prop in node_elem.findall('./Properties/Property'):
                properties.append(Property(
                    name=prop.get('name'),
                    value=prop.text if prop.text else ''
                ))

            self.nodes[node_id] = Node(
                id=node_id,
                label=label,
                weight=weight,
                ASN = ASN,
                properties=properties
            )

    def _parse_edges(self):
        for edge_elem in self.root.findall('./Edges/Edge'):
            source = edge_elem.get('source')
            target = edge_elem.get('target')
            weight = float(edge_elem.find('Weight').text) if edge_elem.find('Weight') is not None else None
            edge_type = edge_elem.find('Type').text

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
        print(f"ID: {node_id}, Label: {node.label}, Weight: {node.weight}")

    # Print all edges
    print("\nEdges:")
    for edge in parser.edges:
        print(f"{edge.source} -> {edge.target} (Weight: {edge.weight}, Type: {edge.type})")

    G = parser.get_networkx()
    # graph_utils.draw_networkx_graph(G)
    # graph_utils.draw_networkx_graph_complex(G)
    for g_node, g_attr in G.nodes.items():
        print(f"{g_node}: {g_attr}")
    for g_deg in G.degree():
        print(f"{g_deg}")
    # ASN = nx.get_node_attributes(G, "ASN")
    # print(ASN)
    clab_yaml_gen.gen_clab_yaml_from_nx(G)
    #interactive_net = graph_utils.InteractiveNetwork(G)
    #interactive_net.create_interactive_graph().show('../network.html', notebook=False)