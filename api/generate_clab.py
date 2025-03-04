import os
import networkx as nx
import uuid
from jinja2 import Template, Environment, FileSystemLoader
from sympy.codegen.ast import Raise

from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("clab.yml")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/clab'))
template = env.get_template('clab.yaml.jinja2')

def create_lab_dir(nodes: list):
    """
    Create directories for the lab setup.
    """
    os.makedirs(CURRENT_LAB_PATH, exist_ok=True)
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config'), exist_ok=True)
    for node in nodes:
        os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config', str(node)), exist_ok=True)


def make_yaml_info_from_nodes(G: nx.Graph):
    """
    Create YAML info from the NetworkX graph G.
    """
    # Todo: implement net interface in links/endpoints
    node_deg = G.degree()
    node_num = G.number_of_nodes()
    nodes = {}
    selected_keys = ["group", ]

    # Generate IP pool based on the number of nodes
    # Remember
    ip_pool = ipv4_utils.generate_random_ipv4(prefix="172.20.20.", count=node_num,
                                              IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'used_ips'))
    index = 0

    # Reconstruct nodes
    for node, attr in G.nodes(data=True):
        attr_new = {
            "image": ROUTER_IMAGE,
            "binds": f"\n        - config/{str(node)}:/etc/frr", # Caution for 8 spaces here...
            "mgmt-ipv4": ip_pool[index],
        }
        attr_new.update({key: attr[key] for key in selected_keys})
        index += 1
        nodes[node] = attr_new

    return nodes

def make_yaml_info_from_edges(G: nx.Graph):
    # Reconstruct edges
    edges = []
    eth_count = [(node_id, 0) for node_id, _ in G.degree()]
    print(eth_count)
    for u, v in G.edges(data=False):
        if u == v:
            log.error(f"Edge [{u},{v}] are Loopback in network topology")
            raise Exception("Loopback found in network topology")
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
                    print(node_id, u, v, count)
                    continue
            edges.append((u_eth, v_eth))
    return edges

def gen_yaml_from_nx(G: nx.Graph):
    """
    Generate YAML from NetworkX graph and save to file.
    """
    # Create the lab directory structure
    create_lab_dir(list(G.nodes()))

    # Prepare node information for the YAML
    nodes = make_yaml_info_from_nodes(G)
    edges = make_yaml_info_from_edges(G)

    # Prepare topology information for Jinja2 template rendering
    topology = {
        "name": "fdc",
        "topology": {
            "defaults": {
                "kind": "linux",
                "image": "wbitt/network-multitool:alpine-extra"
            },
            "nodes": {node: nodes[node] for node in nodes},
            "links": [{"endpoints": [u, v]} for u, v in edges]
        }
    }

    # Render the template
    output = template.render(**topology)

    # Save the rendered YAML to a file
    output_file = "lab.clab.yaml"
    with open(os.path.join(CURRENT_LAB_PATH, output_file), "w") as f:
        f.write(output)

    log.info(f"Topology saved to {output_file}")


# Generate CURRENT_LAB_PATH dynamically based on the lab
CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(uuid.uuid4()))
