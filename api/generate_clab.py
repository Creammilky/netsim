import os

import networkx as nx
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from utils import logger, ipv4_utils


# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("GenClab")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/clab'))
template = env.get_template('clab.yaml.j2')

def make_yaml_info_from_nodes(G: nx.Graph, mgmt_ips: (list|str) = "auto"):
    """
    Create YAML info from the NetworkX graph G.
    """
    # Todo: implement net interface in links/endpoints ??
    number_of_nodes = G.number_of_nodes()
    nodes = {}
    selected_keys = []
    index = 0

    if isinstance(mgmt_ips, str) and mgmt_ips == "auto":
        for node, attr in G.nodes(data=True):
            attr_new = {
                "image": ROUTER_IMAGE,
                "binds": f"\n        - config/{str(node)}:/etc/frr",  # Caution for 8 spaces here...
            }
            attr_new.update({key: attr[key] for key in selected_keys})
            index += 1
            nodes[node] = attr_new

    elif isinstance(mgmt_ips, list) and mgmt_ips is not None:
        if len(mgmt_ips) != number_of_nodes:
            log.error("Cannot make clab.yaml due to not enough mgmt-ips provided.")
            raise Exception("Cannot make clab.yaml due to not enough mgmt-ips.")
        for node, attr in G.nodes(data=True):
            attr_new = {
                "image": ROUTER_IMAGE,
                "binds": f"\n        - config/{str(node)}:/etc/frr", # Caution for 8 spaces here...
                "mgmt-ipv4": mgmt_ips[index],
            }
            attr_new.update({key: attr[key] for key in selected_keys})
            index += 1
            nodes[node] = attr_new

    else:
        log.error("Error type of given mgmt-ipv4")
        raise Exception("Error type of given mgmt-ipv4")
    return nodes

def make_yaml_info_from_edges(G: nx.Graph):
    # Reconstruct edges
    edges = []
    eth_count = [(node_id, 0) for node_id, _ in G.degree()]
    log.debug(eth_count)
    for u, v in G.edges(data=False):
        if u == v:
            log.warning(f"Edge [{u},{v}] are Loopback in network topology")
            # Todo: How to deal with loopback

            # raise Exception("Loopback found in network topology")
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

def gen_yaml_from_nx(G: nx.Graph, CURRENT_LAB_PATH, eth_table, mgmt_prefix, mgmt_ips:(list|str) ="auto",):
    """
    Generate YAML from NetworkX graph and save to file.
    """
    # Prepare node information for the YAML
    nodes = make_yaml_info_from_nodes(G,mgmt_ips)
    edges = eth_table

    # Prepare topology information for Jinja2 template rendering
    topology = {
        "name": f"{CURRENT_LAB_PATH.split('/')[-1]}",
        "mgmt": "auto" if mgmt_ips == "auto" else str(mgmt_prefix),
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



