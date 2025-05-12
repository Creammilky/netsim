import os

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from utils import logger
from dotenv import load_dotenv
from api.frr import frr_header, frr_interfaces, frr_staticroute, frr_peering, frr_additional, frr_prefix, frr_bmp

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("FRRConfigurator")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))


def gen_frr_config(G:nx.Graph ,CURRENT_LAB_PATH, frr_version, hostname):
    header_info = frr_header.frr_conf_header(frr_version=frr_version, hostname=hostname)
    interfaces_info = frr_interfaces.frr_conf_interfaces(G=G, CURRENT_LAB_PATH=CURRENT_LAB_PATH ,hostname=hostname)
    static_routes_info = frr_staticroute.frr_conf_static_routes(CURRENT_LAB_PATH=CURRENT_LAB_PATH, hostname=hostname)
    bgp_peering_info = frr_peering.frr_conf_peering(CURRENT_LAB_PATH=CURRENT_LAB_PATH, hostname=hostname)
    prefix = frr_prefix.frr_conf_bgp_prefix(CURRENT_LAB_PATH=CURRENT_LAB_PATH, hostname=hostname)
    bmp_setting = frr_bmp.frr_conf_bgp_bmp(CURRENT_LAB_PATH=CURRENT_LAB_PATH, hostname=hostname)
    additional_setting = frr_additional.frr_conf_additional_setting(G, CURRENT_LAB_PATH, hostname)

    with open(os.path.join(CURRENT_LAB_PATH, "config", f"{hostname}","frr.conf"), mode="w+") as f:
        print(hostname)
        frr_config = header_info + "\n" +interfaces_info + "\n" + static_routes_info + "\n" + bgp_peering_info + prefix + bmp_setting +"\n" + additional_setting
        f.write(frr_config)


def gen_frr_daemon(CURRENT_LAB_PATH, hostname ,**kwargs):
    kwargs = kwargs.copy()
    daemon_keyword_list = ["bgpd", "ospfd", "isisd", ]
    template = env.get_template('daemons.j2')
    # make sure kwargs can specify daemons, but in future

    with open(os.path.join(CURRENT_LAB_PATH, "config", f"{hostname}","daemons"), mode="w+") as f:
        output = template.render()
        f.write(output)


def gen_vtysh_config(CURRENT_LAB_PATH, hostname ,**kwargs):
    kwargs = kwargs.copy()
    daemon_keyword_list = ["bgpd", "ospfd", "isisd", ]
    template = env.get_template('vtysh.j2')

    # make sure kwargs can specify vtysh.j2, but in future

    with open(os.path.join(CURRENT_LAB_PATH, "config", f"{hostname}","vtysh.conf"), mode="w+") as f:
        output = template.render()
        f.write(output)


if __name__ == '__main__':
    print("Generating FRR config for routers")


