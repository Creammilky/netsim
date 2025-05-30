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

def frr_conf_peering(CURRENT_LAB_PATH, hostname):
    peer_as_list = []
    appeared_as_list = []
    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
        ip_file_json = json.loads(f.read())
        router_type = ip_file_json["type"].strip().lower()

        if router_type == "as" or router_type == "vp":
        # Load this host/as all interfaces to make frr config for it
            try:
                interfaces = ip_file_json["interfaces"]
                loopback = ip_file_json["loopback"]
                asn = ip_file_json["asn"]
            except KeyError as e:
                log.error(e.__str__())

            for interface in interfaces:
                this_interface_ip = interface["ip"]
                peer_type = interface["peer_type"].strip().lower()
                peer_interface_ip = ipv4_utils.get_peer_ip(this_interface_ip + "/30")

                this_interface_endpoint = interface["endpoint"]
                peer_name = this_interface_endpoint.split(":")[0].strip()
                with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{peer_name}.ip"), mode="r") as f_peer:
                    peer_ip_file_json = json.loads(f_peer.read())
                    peer_asn = peer_ip_file_json["asn"]
                    peer_description = peer_ip_file_json["name"]
                    peer_loopback_ip = peer_ip_file_json["loopback"]
                if peer_asn not in appeared_as_list:
                    as_info = {
                        "asn": peer_asn,
                        "interfaces":[],
                        "prefixes":[],
                        "description": peer_description,
                    }
                    # For handling host's prefix
                    if peer_type != "host":
                        as_info["interfaces"].append(peer_loopback_ip)
                        peer_as_list.append(as_info)
                        appeared_as_list.append(peer_asn)

                elif peer_asn in appeared_as_list:
                    for as_info in peer_as_list:
                        if as_info["asn"] == peer_asn:
                            if peer_type != "host":
                                as_info["interfaces"].append(peer_loopback_ip)
                                break
                else:
                    log.error(f"Something went wrong when configuring bgp {asn}")

            output = template.render(ASN=asn, router_id=loopback, peer_as_list=peer_as_list, ROUTER_TYPE=router_type)
            return output

