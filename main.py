"""
    Import examples, look below "#"
"""
# Builtins
import os
import uuid

# Packages(site)
from dotenv import load_dotenv

# Internal Files
from api.lab_manage import topology, create_lab
from utils import logger, xml_parser


# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("main")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
FRR_VERSION = os.getenv("FRR_VERSION")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Usage example
if __name__ == "__main__":
    # Generate CURRENT_LAB_PATH dynamically based on the lab
    CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(uuid.uuid4()))

    parser = xml_parser.GraphParser("test/route-xmls/route_2.xml")
    parser.parse()

    G_xml = parser.get_networkx()

    G_updates = topology.bgp_to_networkx('test/ripe_output.txt')

    create_lab.create_lab_instance(G=G_xml, CURRENT_LAB_PATH=CURRENT_LAB_PATH, frr_version=FRR_VERSION)
