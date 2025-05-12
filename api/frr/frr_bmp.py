import os
import json

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("FrrBmp")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))
template = env.get_template('frr_bgp_bmp.j2')
BMP_IP = os.getenv("BMP_IP")
BMP_PORT = os.getenv("BMP_PORT")

'''
We don't need config frr for a host, but we need to config for router who has hosts.
'''
def frr_conf_bgp_bmp(CURRENT_LAB_PATH, hostname):
    with open(file=os.path.join(CURRENT_LAB_PATH, "cache", f"{hostname}.ip"), mode="r") as f:
        ip_file_json = json.loads(f.read())
    if ip_file_json["type"].lower() == "vp":
        output = template.render(bmp_ip=BMP_IP, bmp_port=BMP_PORT)
        return output
    else:
        return ""

