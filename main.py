from api import topology, create_lab
import os

import uuid
from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("main")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Usage example
if __name__ == "__main__":
    # Generate CURRENT_LAB_PATH dynamically based on the lab
    CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(uuid.uuid4()))

    # parser = xml_parser.GraphParser("test/route-xmls/route_complex_1.xml")
    # parser.parse()
    #
    # # Print all nodes and their weights
    # print("Nodes:")
    # for node_id, node in parser.nodes.items():
    #     print(f"ID: {node_id}, Label: {node.group}, Weight: {node.weight}")
    #
    # # Print all edges
    # print("\nEdges:")
    # for edge in parser.edges:
    #     print(f"{edge.source} -> {edge.target} (Weight: {edge.weight}, Type: {edge.type})")
    #
    # G = parser.get_networkx()
    # # graph_utils.draw_networkx_graph(G)
    # # graph_utils.draw_networkx_graph_complex(G)
    # for g_node, g_attr in G.nodes.items():
    #     print(f"{g_node}: {g_attr}")
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

    G = topology.bgp_to_networkx('test/ripe_output_bak.txt')
    create_lab.create_lab_instance(G, CURRENT_LAB_PATH)
