import networkx as nx
from jinja2 import Template

def gen_clab_yaml_from_nx(g:nx.Graph):
    pass


# Define your NetworkX graph
G = nx.Graph()

# Add nodes with attributes
G.add_node("spine01", mgmt_ipv4="172.20.20.11", group="spine")
G.add_node("spine02", mgmt_ipv4="172.20.20.12", group="spine")
G.add_node("leaf01", mgmt_ipv4="172.20.20.21", group="leaf")
G.add_node("leaf02", mgmt_ipv4="172.20.20.22", group="leaf")

# Add edges (links)
G.add_edge("spine01", "leaf01")
G.add_edge("spine01", "leaf02")
G.add_edge("spine02", "leaf01")
G.add_edge("spine02", "leaf02")

# Convert NetworkX graph to Jinja-compatible dictionary
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

# Render the template
template = Template(template_str)
output = template.render(**topology)

# Save to file
output_file = "topology.clab.yaml"
with open(output_file, "w") as f:
    f.write(output)

print(f"Topology saved to {output_file}")
