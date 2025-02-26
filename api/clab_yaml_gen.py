import os
import networkx as nx
import uuid
from jinja2 import Template
from utils import logger, ipv4_utils
from dotenv import load_dotenv

load_dotenv()
log = logger.Logger("clab")

ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(uuid.uuid4()))

def create_lab_dir():
    os.makedirs(CURRENT_LAB_PATH, exist_ok=True)



def make_yaml_info_from_nx(G: nx.Graph):
    node_deg = G.degree()
    node_num = G.number_of_nodes()

    # Todo: see how can we make this mechanism more elegant
    selected_keys = ["group",]

    ip_pool = ipv4_utils.generate_random_ipv4(prefix=None, count=node_num, IP_STORAGE_FILE=os.path.join(CURRENT_LAB_PATH,'used_ips'))
    index = 0

    for node, attr in G.nodes(data=True):
        attr_new = {
            "image": ROUTER_IMAGE,
            "mgmt-ipv4": ip_pool[index],
        }
        attr_new.update({key: attr[key] for key in selected_keys})

        index += 1
        pass
    # {node: G.nodes[node] for node in G.nodes}

def gen_clab_yaml_from_nx(G: nx.Graph):
    topology = {
        "name": "fdc",
        "topology": {
            "defaults": {
                "kind": "linux",
                "image": "wbitt/network-multitool:alpine-extra"
            },
            "nodes": {node: G.nodes[node] for node in G.nodes},
            "links": [{"endpoints": [u, v]} for u, v in G.edges]
        }
    }

    # Load the Jinja2 template with reduced blank lines
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

    # Render the template5
    template = Template(template_str)
    output = template.render(**topology)

    # Save to file
    output_file = "topology.clab.yaml"
    with open(output_file, "w") as f:
        f.write(output)

    log.info(f"Topology saved to {output_file}")
