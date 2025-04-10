import os

import networkx as nx

from utils import logger
from dotenv import load_dotenv
from api.frr import frr_header, frr_interfaces

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("clab.yml")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

def gen_frr_config_for_routers(G:nx.Graph ,CURRENT_LAB_PATH, frr_version, hostname):

    header_info = frr_header.frr_conf_header(frr_version=frr_version, hostname=hostname)
    interfaces_info = frr_interfaces.frr_conf_interfaces(G=G, CURRENT_LAB_PATH=CURRENT_LAB_PATH ,hostname=hostname)

    with open(os.path.join(CURRENT_LAB_PATH, "config", f"{hostname}","frr.config"), mode="w+") as f:
        frr_config = header_info + "\n" + interfaces_info + "\n"
        f.write(frr_config)

if __name__ == '__main__':
    print("Generating FRR config for routers")


