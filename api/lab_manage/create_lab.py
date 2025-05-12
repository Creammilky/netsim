import os

import networkx as nx

from api.lab_manage import frr_configurator, generate_clab
from utils import graph_utils, ipv4_utils
from utils import logger
from api.ethernet_manager import eth_assign
from api.lab_manage.topology import networkx_to_xml

# Initialize logger
log = logger.Logger("CreateLab")

mgmt_prefix = "172.20.0.0/16"

def create_lab_instance(G: nx.Graph, CURRENT_LAB_PATH, frr_version):
    create_lab_dir(list(G.nodes()), CURRENT_LAB_PATH)
    node_num = G.number_of_nodes()
    # assign router ethernet and IP
    eth_assign.assign_id_for_router(G, CURRENT_LAB_PATH)

    # generate config file according to IP and AS
    eth_table = eth_assign.define_network_interfaces_ip(G, CURRENT_LAB_PATH)

    for host in G.nodes():
        if nx.get_node_attributes(G, "type")[host] == "host":
            continue
        else:
            # no frr configration for host
            frr_configurator.gen_frr_config(G=G, CURRENT_LAB_PATH=CURRENT_LAB_PATH, frr_version=frr_version,
                                            hostname=host)
            frr_configurator.gen_frr_daemon(CURRENT_LAB_PATH=CURRENT_LAB_PATH, hostname=host)
            frr_configurator.gen_vtysh_config(CURRENT_LAB_PATH=CURRENT_LAB_PATH, hostname=host)
    # assign mgmt-ipv4 for container lab and gen yaml
    mgmt_ips = ipv4_utils.generate_random_ipv4_with_save(prefix=mgmt_prefix, count=node_num,
                                              IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'cache', 'used_ips'))

    generate_clab.gen_yaml_from_nx(G, CURRENT_LAB_PATH=CURRENT_LAB_PATH, eth_table=eth_table, mgmt_ips=mgmt_ips, mgmt_prefix=mgmt_prefix)

    # create the first version xml of this lab
    networkx_to_xml(G, os.path.join(CURRENT_LAB_PATH, 'versions', 'topology_0.xml'))
    interactive_net = graph_utils.InteractiveNetwork(G)
    interactive_net.create_interactive_graph().show(os.path.join(CURRENT_LAB_PATH, 'network.html'), notebook=False)


def create_lab_dir(nodes: list, CURRENT_LAB_PATH):
    """
    Create directories for the lab setup.
    """
    os.makedirs(CURRENT_LAB_PATH, exist_ok=True)
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config'), exist_ok=True)
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'versions'), exist_ok=True)

    # Todo: I want this should be a hidden folder in future
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'cache'), exist_ok=True)
    for node in nodes:
        os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config', str(node)), exist_ok=True)