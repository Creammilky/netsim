import os
import networkx as nx
import uuid
from jinja2 import Template
from utils import logger, ipv4_utils
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("clab")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")


def create_lab_dir(nodes: list):
    """
    Create directories for the lab setup.
    """
    os.makedirs(CURRENT_LAB_PATH, exist_ok=True)
    os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config'), exist_ok=True)
    for node in nodes:
        os.makedirs(os.path.join(CURRENT_LAB_PATH, 'config', str(node)), exist_ok=True)


def make_yaml_info_from_nx(G: nx.Graph):
    """
    Create YAML info from the NetworkX graph G.
    """
    # Todo: implement net interface in links/endpoints
    node_deg = G.degree()
    node_num = G.number_of_nodes()
    nodes = {}
    selected_keys = ["group", ]

    # Generate IP pool based on the number of nodes
    ip_pool = ipv4_utils.generate_random_ipv4(prefix="172.1.1.", count=node_num,
                                              IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH, 'used_ips'))
    index = 0

    for node, attr in G.nodes(data=True):
        attr_new = {
            "image": ROUTER_IMAGE,
            "binds": f"\n\t\t- config/{str(node)}:/etc/frr",
            "mgmt-ipv4": ip_pool[index],
        }
        attr_new.update({key: attr[key] for key in selected_keys})
        index += 1
        nodes[node] = attr_new

    return nodes


def gen_yaml_from_nx(G: nx.Graph):
    """
    Generate YAML from NetworkX graph and save to file.
    """
    # Create the lab directory structure
    create_lab_dir(list(G.nodes()))

    # Prepare node information for the YAML
    nodes = make_yaml_info_from_nx(G)

    # Prepare topology information for Jinja2 template rendering
    topology = {
        "name": "fdc",
        "topology": {
            "defaults": {
                "kind": "linux",
                "image": "wbitt/network-multitool:alpine-extra"
            },
            "nodes": {node: nodes[node] for node in nodes},
            "links": [{"endpoints": [u, v]} for u, v in G.edges]
        }
    }

    # Jinja2 template for generating the YAML configuration
    template_str = """\
# This is a data centre topology using FRRouting
name: {{ name }}

topology:
  defaults:
    kind: {{ topology.defaults.kind }}
    image: {{ topology.defaults.image }}

  nodes:{%- for node, attributes in topology.nodes.items() %}
    {{ node }}:{%- for key, value in attributes.items() %}
      {{ key }}: {{ value }}{%- endfor %}
    {%- endfor %}

  links:{%- for link in topology.links %}
    - endpoints: {{ link.endpoints | tojson }}{%- endfor %}
    """

    # Render the template
    template = Template(template_str)
    output = template.render(**topology)

    # Save the rendered YAML to a file
    output_file = "lab.clab.yml"
    with open(os.path.join(CURRENT_LAB_PATH, output_file), "w") as f:
        f.write(output)

    log.info(f"Topology saved to {output_file}")


# Generate CURRENT_LAB_PATH dynamically based on the lab
CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(uuid.uuid4()))
