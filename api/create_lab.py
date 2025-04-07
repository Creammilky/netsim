import os
import networkx as nx
from api import generate_clab, topology
from utils import graph_utils, ipv4_utils
from utils import logger

# Initialize logger
log = logger.Logger("CreateLab")

def create_lab_instance(G: nx.Graph, CURRENT_LAB_PATH):

    create_lab_dir(list(G.nodes()), CURRENT_LAB_PATH)
    node_num = G.number_of_nodes()
    # assign router ethernet and IP
    assign_ip_for_routers(G, CURRENT_LAB_PATH)
    # generate config file according to IP and AS

    # assign mgmt-ipv4 for container lab and gen yaml

    # Todo:think about ip prefix setting and container lab
    mgmt_ips = ipv4_utils.generate_random_ipv4(prefix="", count=node_num,
                                              IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips'))

    generate_clab.gen_yaml_from_nx(G,  CURRENT_LAB_PATH=CURRENT_LAB_PATH, mgmt_ips=mgmt_ips)


    interactive_net = graph_utils.InteractiveNetwork(G)
    interactive_net.create_interactive_graph().show(os.path.join(CURRENT_LAB_PATH, 'network.html'), notebook=False)


def assign_ip_for_routers(G: nx.Graph, CURRENT_LAB_PATH, vp_dafault_prefix = "192.168." , as_default_prefix = "10."):
    """
    Assign IP addresses to routers if not given.
    """
    node_type = nx.get_node_attributes(G, "type")
    for node in G.nodes():
        if node_type[node] == "as":
            if nx.get_node_attributes(G, node).get('ip_addr') is None:
                router_ip = ipv4_utils.generate_random_ipv4(prefix=as_default_prefix, count=1,
                                                            IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache','used_ips'))
                log.info("Assigning IP: {} for router {}".format(router_ip, node))
                nx.set_node_attributes(G, {node: router_ip}, "ip_addr")
        if node_type[node] == "VP":
            if nx.get_node_attributes(G, node).get('ip_addr') is None:
                router_ip = ipv4_utils.generate_random_ipv4(prefix=vp_dafault_prefix, count=1,
                                                            IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache','used_ips'))
                log.info("Assigning IP: {} for VP {}".format(router_ip, node))
                nx.set_node_attributes(G, {node: router_ip}, "ip_addr")




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