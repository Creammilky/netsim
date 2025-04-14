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
template = env.get_template('frr_bgp_section.j2')

def frr_conf_peering(G: nx.Graph, CURRENT_LAB_PATH, hostname):
    peer_as_list = []
    appeared_as_list = []
    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
        ip_file_json = json.loads(f.read())
        if ip_file_json["type"] is "as":
        # Load this as all interfaces to make frr config for it
            try:
                interfaces = ip_file_json["interfaces"]
                loopback = ip_file_json["loopback"]
                asn = ip_file_json["asn"]
            except KeyError as e:
                log.error(e.__str__())

            f.close()

            for interface in interfaces:
                this_interface_ip = interface["ip"]
                peer_interface_ip = ipv4_utils.get_peer_ip(this_interface_ip + "/30")

                this_interface_endpoint = interface["endpoint"]
                peer_name = this_interface_endpoint.split(":")[0].strip()
                with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{peer_name}.ip"), mode="r") as f_peer:
                    peer_ip_file_json = json.loads(f_peer.read())
                    peer_asn = peer_ip_file_json["asn"]
                    peer_description = "router" + "-"  + peer_asn
                    peer_loopback_ip = peer_ip_file_json["loopback"]
                    f_peer.close()
                if peer_asn not in appeared_as_list:
                    as_info = {
                        "asn": peer_asn,
                        "interfaces": [],
                        "description": peer_description,
                    }
                    as_info["interfaces"].append(peer_loopback_ip)
                    peer_as_list.append(as_info)
                    appeared_as_list.append(peer_asn)

                elif peer_asn in appeared_as_list:
                    for as_info in peer_as_list:
                        if as_info["asn"] == peer_asn:
                            as_info["interfaces"].append(peer_loopback_ip)
                            break
                else:
                    log.error(f"Something went wrong when configuring bgp {asn}")

            # Render the template
            output = template.render(ASN=asn, router_id=loopback, peer_as_list=peer_as_list)
            return output

        elif ip_file_json["type"] is "host":
            try:

        # Load this host all interfaces to make frr config for it