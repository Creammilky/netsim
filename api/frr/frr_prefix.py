import os
import json

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("FrrBgpPeering")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))
template = env.get_template('announcements.j2')


'''
We don't need config frr for a host, but we need to config for router who has hosts.
'''
def frr_conf_bgp_prefix(CURRENT_LAB_PATH, hostname):
    network_prefixes = []
    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
        ip_file_json = json.loads(f.read())
        if ip_file_json["type"] == "as" or ip_file_json["type"] == "VP":
            # Load this host/as all interfaces to make frr config for it
            try:
                interfaces = ip_file_json["interfaces"]
                loopback = ip_file_json["loopback"]
                asn = ip_file_json["asn"]
            except KeyError as e:
                log.error(e.__str__())

            for interface in interfaces:
                if interface["peer_type"] == "host":
                    this_interface_endpoint = interface["endpoint"]
                    peer_name = this_interface_endpoint.split(":")[0].strip()
                    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{peer_name}.ip"), mode="r") as f_peer:
                        peer_ip_file_json = json.loads(f_peer.read())
                        # Todo: temporarily keep this branch until this system support multi prefix on one host
                        if isinstance(peer_ip_file_json["prefixes"], str):
                            network_prefixes.append(peer_ip_file_json["prefixes"])
                        elif isinstance(peer_ip_file_json["prefixes"], list):
                            for prefix in peer_ip_file_json["prefixes"]: # Read prefix from peer(host)? I'm not sure.
                                network_prefixes.append(prefix)
                        f_peer.close()

    output = template.render(network_prefixes=network_prefixes)
    return output
