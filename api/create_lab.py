import os
import networkx as nx
from api import generate_clab, topology
from utils import graph_utils

def create_lab_instance(G: nx.Graph, CURRENT_LAB_PATH):

    generate_clab.gen_yaml_from_nx(G, CURRENT_LAB_PATH=CURRENT_LAB_PATH)


    interactive_net = graph_utils.InteractiveNetwork(G)
    interactive_net.create_interactive_graph().show(os.path.join(CURRENT_LAB_PATH, 'network.html'), notebook=False)