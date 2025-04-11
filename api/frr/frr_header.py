import os

from jinja2 import Environment, FileSystemLoader
from numpy.polynomial.hermite import hermder

from utils import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("FrrHeader")

# Fetch Jinja2 templates
env = Environment(loader=FileSystemLoader('templates/frr'))
template = env.get_template('frr_header.j2')

def frr_conf_header(frr_version, hostname):

    # Prepare topology information for Jinja2 template rendering
    header = {
        "frr_version": str(frr_version),
        "hostname": str(hostname),
    }

    # Render the template
    output = template.render(**header)
    return output


