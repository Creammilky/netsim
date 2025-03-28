import os
import networkx as nx
from utils import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("EthManager")

# Fetch environment variables
LABS_PATH = os.getenv("LABS_PATH")
if not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

def eth_naming(G: nx.Graph, CURRENT_LAB_PATH):
    # Reconstruct edges
    edges = []
    eth_count = [(node_id, 0) for node_id, _ in G.degree()]
    log.debug(eth_count)
    for u, v in G.edges(data=False):
        if u == v:
            log.warning(f"Edge [{u},{v}] are Loopback in network topology")
            # Todo: How to deal with loopback

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