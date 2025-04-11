import os
import json

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from utils import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("FrrInterfaces")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))
template = env.get_template('frr_interfaces.j2')

def frr_conf_interfaces(G: nx.Graph, CURRENT_LAB_PATH, hostname):
    interfaces = []
    node_degrees = nx.degree(G)
    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
        ip_file_json = json.loads(f.read())

    loopback = ip_file_json["loopback"]
    interfaces_json = ip_file_json["interfaces"]


    node_degree = node_degrees[hostname]
    has_selfloop = (hostname, hostname) in nx.selfloop_edges(G=G)

    expected_interfaces = node_degree - 2 if has_selfloop else node_degree

    if len(interfaces_json) == 0:
        log.error(f"No interfaces in {hostname}.ip")
        raise Exception(f"No interfaces in {hostname}.ip")
    elif len(interfaces_json) != expected_interfaces:
        log.error(
            f"NetworkX({node_degree}) and .ip files({len(interfaces_json)}) do not match in {hostname}.ip"
        )
        raise Exception(f"NetworkX and .ip files do not match in {hostname}.ip")
    else:
        if has_selfloop:
            log.warning(f"{hostname} has self-loop edges, maybe BGP prepending")

        for interface_dict in interfaces_json:
            interface = {
                "name": interface_dict["name"],
                "ip": interface_dict["ip"],
            }
            interfaces.append(interface)

    # Render the template
    output = template.render(loopback=loopback, interfaces=interfaces)
    return output
