import os
import json

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("FrrStaticRoute")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))
template = env.get_template('frr_static_route.j2')

def frr_conf_static_routes(G: nx.Graph, CURRENT_LAB_PATH, hostname):
    static_routes = []
    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
        ip_file_json = json.loads(f.read())
    interfaces = ip_file_json["interfaces"]

    for interface in interfaces:
        peer_type = interface["peer_type"]
        if peer_type != "host":
            this_interface_ip = interface["ip"]
            peer_interface_ip = ipv4_utils.get_peer_ip(this_interface_ip + "/30")

            this_interface_endpoint = interface["endpoint"]
            peer_name = this_interface_endpoint.split(":")[0].strip()
            with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{peer_name}.ip"), mode="r") as f_peer:
                peer_ip_file_json = json.loads(f_peer.read())
                peer_loopback_ip = peer_ip_file_json["loopback"]
                f_peer.close()

            static_routes.append({
                "peer_lo" : peer_loopback_ip,
                "peer_interface_ip" : peer_interface_ip
            })
        else:
            # No static route for host (I don't know why but LZS did like that)
            continue

    # Render the template
    output = template.render(static_routes=static_routes)
    return output
