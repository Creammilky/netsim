import os
import networkx as nx
import uuid
import json
from jinja2 import Template, Environment, FileSystemLoader
from utils import logger, ipv4_utils
from dotenv import load_dotenv
import ipaddress

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("frr-config")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# # Fetch Jinja2 templates
# env = Environment(loader=FileSystemLoader('templates/frr'))
# template = env.get_template('frr.conf.jinja2')


# Define the Jinja2 template for FRR configuration
FRR_TEMPLATE = """frr version 8.1_git
frr defaults traditional
hostname {{ hostname }}
no ipv6 forwarding
!
{% for interface in interfaces %}
interface {{ interface.name }}
{% if interface.ip %}
 ip address {{ interface.ip }}
{% endif %}
exit
!
{% endfor %}
router bgp {{ asn }}
 bgp router-id {{ router_id }}
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 timers bgp {{ keepalive }} {{ holdtime }}
{% for peer_group in peer_groups %}
 neighbor {{ peer_group.name }} peer-group
 neighbor {{ peer_group.name }} remote-as {{ peer_group.remote_as }}
 neighbor {{ peer_group.name }} advertisement-interval 0
{% for neighbor in peer_group.neighbors %}
 neighbor {{ neighbor }} interface peer-group {{ peer_group.name }}
{% endfor %}
{% endfor %}
 !
 address-family ipv4 unicast
{% for network in networks %}
  network {{ network }}
{% endfor %}
 exit-address-family
exit
!
"""


class NetworkTopology:
    def __init__(self, topology_file):
        """Initialize with a topology file in JSON format."""
        with open(topology_file, 'r') as f:
            self.topology = json.load(f)

        # Validate the topology structure
        self._validate_topology()

        # Generate IP subnets for networks
        self._generate_ip_subnets()

    def _validate_topology(self):
        """Validate the structure of the topology file."""
        required_keys = ['nodes', 'links', 'autonomous_systems']
        for key in required_keys:
            if key not in self.topology:
                raise ValueError(f"Topology is missing required key: {key}")

    def _generate_ip_subnets(self):
        """Generate IP subnets for the networks."""
        # Start with a base subnet
        base_net = ipaddress.IPv4Network('192.168.0.0/16')
        subnets = list(base_net.subnets(prefixlen_diff=8))  # Break into /24 subnets

        self.subnet_map = {}
        subnet_index = 0

        # Assign subnets to links
        for link in self.topology['links']:
            if 'subnet' not in link:
                if subnet_index >= len(subnets):
                    raise ValueError("Not enough subnets available")
                link['subnet'] = str(subnets[subnet_index])
                subnet_index += 1

    def generate_frr_configs(self, output_dir):
        """Generate FRR config files for all nodes."""
        os.makedirs(output_dir, exist_ok=True)

        # Create a template
        template = Template(FRR_TEMPLATE)

        for node in self.topology['nodes']:
            node_config = self._create_node_config(node)

            # Render the template
            config_content = template.render(**node_config)

            # Write to file
            filename = os.path.join(output_dir, f"{node['name']}_frr.conf")
            with open(filename, 'w') as f:
                f.write(config_content)

            print(f"Generated configuration for {node['name']}")

    def _create_node_config(self, node):
        """Create a configuration dictionary for a node."""
        # Find the AS for this node
        node_as = None
        for asys in self.topology['autonomous_systems']:
            if node['name'] in asys['nodes']:
                node_as = asys
                break

        if not node_as:
            raise ValueError(f"Node {node['name']} is not assigned to any AS")

        # Get all links for this node
        node_links = []
        for link in self.topology['links']:
            if node['name'] in [link['source'], link['target']]:
                node_links.append(link)

        # Create interfaces
        interfaces = []
        networks = []

        # Add loopback interface
        loopback_ip = f"10.10.10.{node.get('id', 1)}/32"
        interfaces.append({
            'name': 'lo',
            'ip': loopback_ip
        })

        # Process other interfaces
        for i, link in enumerate(node_links):
            # Determine if this is eth1, eth2, etc.
            if node['name'] == link['source']:
                interface_name = f"eth{i + 1}"
                peer_name = link['target']
            else:
                interface_name = f"eth{i + 1}"
                peer_name = link['source']

            # If subnet is specified, calculate IP
            if 'subnet' in link:
                subnet = ipaddress.IPv4Network(link['subnet'])
                # First usable IP for source, second for target
                if node['name'] == link['source']:
                    ip = f"{next(subnet.hosts())}/{subnet.prefixlen}"
                else:
                    hosts = list(subnet.hosts())
                    if len(hosts) > 1:
                        ip = f"{hosts[1]}/{subnet.prefixlen}"
                    else:
                        ip = f"{hosts[0]}/{subnet.prefixlen}"

                # Add to networks if this is an edge node (connected to hosts)
                if node.get('type') == 'leaf' and ('host' in peer_name):
                    networks.append(str(subnet))
            else:
                ip = None

            interfaces.append({
                'name': interface_name,
                'ip': ip
            })

        # Create peer groups based on connections to other ASes
        peer_groups = []
        peer_group_map = {}

        for link in node_links:
            # Skip links to hosts
            if 'host' in link['source'] or 'host' in link['target']:
                continue

            peer = link['target'] if node['name'] == link['source'] else link['source']

            # Find peer's AS
            peer_as = None
            for asys in self.topology['autonomous_systems']:
                if peer in asys['nodes']:
                    peer_as = asys
                    break

            if not peer_as:
                continue

            # If peer is in a different AS, add a peer group
            if peer_as['asn'] != node_as['asn']:
                pg_name = f"AS{peer_as['asn']}"

                if pg_name not in peer_group_map:
                    peer_group_map[pg_name] = {
                        'name': pg_name,
                        'remote_as': peer_as['asn'],
                        'neighbors': []
                    }

                # Find the interface name for this link
                for i, l in enumerate(node_links):
                    if (l['source'] == link['source'] and l['target'] == link['target']) or \
                            (l['source'] == link['target'] and l['target'] == link['source']):
                        interface_name = f"eth{i + 1}"
                        break

                peer_group_map[pg_name]['neighbors'].append(interface_name)

        peer_groups = list(peer_group_map.values())

        # If there are no external peers, create a SPINE peer group for spine-leaf connections
        if not peer_groups and node.get('type') == 'leaf':
            spine_peers = []
            for i, link in enumerate(node_links):
                peer = link['target'] if node['name'] == link['source'] else link['source']
                if 'spine' in peer:
                    spine_peers.append(f"eth{i + 1}")

            if spine_peers:
                peer_groups.append({
                    'name': 'SPINE',
                    'remote_as': node_as['asn'] - 1,  # Assuming spine is usually one AS below
                    'neighbors': spine_peers
                })

        return {
            'hostname': node['name'],
            'asn': node_as['asn'],
            'router_id': loopback_ip.split('/')[0],
            'interfaces': interfaces,
            'networks': networks,
            'peer_groups': peer_groups,
            'keepalive': 3,
            'holdtime': 9
        }


# Example usage
if __name__ == "__main__":
    # Example topology file structure (this would be loaded from a JSON file)
    topology = {
        "nodes": [
            {"name": "spine01", "type": "spine", "id": 1},
            {"name": "spine02", "type": "spine", "id": 2},
            {"name": "leaf01", "type": "leaf", "id": 21},
            {"name": "leaf02", "type": "leaf", "id": 22},
            {"name": "host11", "type": "host", "id": 111},
            {"name": "host12", "type": "host", "id": 112}
        ],
        "links": [
            {"source": "spine01", "target": "leaf01", "subnet": "10.1.1.0/30"},
            {"source": "spine01", "target": "leaf02", "subnet": "10.1.1.4/30"},
            {"source": "spine02", "target": "leaf01", "subnet": "10.1.1.8/30"},
            {"source": "spine02", "target": "leaf02", "subnet": "10.1.1.12/30"},
            {"source": "leaf01", "target": "host11", "subnet": "192.168.11.0/24"},
            {"source": "leaf01", "target": "host12", "subnet": "192.168.12.0/24"}
        ],
        "autonomous_systems": [
            {"asn": 65000, "nodes": ["spine01", "spine02"]},
            {"asn": 65001, "nodes": ["leaf01"]},
            {"asn": 65002, "nodes": ["leaf02"]}
        ]
    }

    # Save the example topology to a file
    with open('example_topology.json', 'w') as f:
        json.dump(topology, f, indent=2)

    # Create an instance of the topology
    net_topo = NetworkTopology('example_topology.json')

    # Generate the FRR configurations
    net_topo.generate_frr_configs('frr_configs')

    print("All configurations generated successfully.")