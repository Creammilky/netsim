import json
import os
import networkx as nx

from api import generate_clab, generate_frr_config
from utils import graph_utils, ipv4_utils
from utils import logger
from api.ethernet_manager import eth_assign

# Initialize logger
log = logger.Logger("CreateLab")

def create_lab_instance(G: nx.Graph, CURRENT_LAB_PATH, frr_version):

    create_lab_dir(list(G.nodes()), CURRENT_LAB_PATH)
    node_num = G.number_of_nodes()
    # assign router ethernet and IP
    eth_assign.assign_id_for_routers(G, CURRENT_LAB_PATH)

    # generate config file according to IP and AS
    eth_table = eth_assign.define_network_interfaces(G, CURRENT_LAB_PATH)

    # Todo: CRITICAL generate config files according to cache/*.ip
    for host in G.nodes():
        generate_frr_config.gen_frr_config_for_routers(G=G, CURRENT_LAB_PATH=CURRENT_LAB_PATH, frr_version=frr_version, hostname=host)

    # assign mgmt-ipv4 for container lab and gen yaml
    # Todo:think about ip prefix setting and container lab
    mgmt_ips = ipv4_utils.generate_random_ipv4(prefix="", count=node_num,
                                              IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips'))

    generate_clab.gen_yaml_from_nx(G, CURRENT_LAB_PATH=CURRENT_LAB_PATH, eth_table=eth_table, mgmt_ips=mgmt_ips)


    interactive_net = graph_utils.InteractiveNetwork(G)
    interactive_net.create_interactive_graph().show(os.path.join(CURRENT_LAB_PATH, 'network.html'), notebook=False)


def create_lab_dir(nodes: list, CURRENT_LAB_PATH):
    """
    Create directories for the lab setup.
    """
    os.makedirs(CURRENT_LAB_PATH, exist_ok=True)
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config'), exist_ok=True)

    # Todo: I want this should be a hidden folder in future
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'cache'), exist_ok=True)
    for node in nodes:
        os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config', str(node)), exist_ok=True)