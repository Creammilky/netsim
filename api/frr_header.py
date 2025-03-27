import os
import networkx as nx
from jinja2 import Environment, FileSystemLoader

from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("clab.yml")

# Fetch environment variables
LABS_PATH = os.getenv("LABS_PATH")
if not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))
template = env.get_template('frr_header.j2')

def frr_conf_header(frr_version, hostname):

    # Prepare topology information for Jinja2 template rendering
    topology = {
        "frr_version": str(frr_version),
        "hostname": str(hostname),
    }

    # Render the template
    output = template.render(**topology)
    return output


