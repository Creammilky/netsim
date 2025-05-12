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
template = env.get_template('frr_addtional_setting.j2')

def frr_conf_additional_setting(G: nx.Graph, CURRENT_LAB_PATH, hostname):

    # Render the template
    output = template.render()
    return output
