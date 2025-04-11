"""
    Import examples, look below "#"
"""
# Builtins
import json
import os
import uuid

# Packages(site)
from dotenv import load_dotenv

# Internal Files
from api import topology, create_lab
from utils import logger, xml_parser


# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("main")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
FRR_VERSION = os.getenv("FRR_VERSION")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Usage example
if __name__ == "__main__":
    # Generate CURRENT_LAB_PATH dynamically based on the lab
    CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(uuid.uuid4()))

    parser = xml_parser.GraphParser("test/route-xmls/route_2.xml")
    parser.parse()

    G_xml = parser.get_networkx()
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

    G_updates = topology.bgp_to_networkx('test/ripe_output.txt')

    create_lab.create_lab_instance(G=G_updates, CURRENT_LAB_PATH=CURRENT_LAB_PATH, frr_version=FRR_VERSION)
