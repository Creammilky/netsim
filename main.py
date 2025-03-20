from utils import xml_parser, graph_utils
from api import generate_clab
# Usage example
if __name__ == "__main__":
    parser = xml_parser.GraphParser("test/route-xmls/route_complex_1.xml")
    parser.parse()

    # Print all nodes and their weights
    print("Nodes:")
    for node_id, node in parser.nodes.items():
        print(f"ID: {node_id}, Label: {node.group}, Weight: {node.weight}")

    # Print all edges
    print("\nEdges:")
    for edge in parser.edges:
        print(f"{edge.source} -> {edge.target} (Weight: {edge.weight}, Type: {edge.type})")

    G = parser.get_networkx()
    # graph_utils.draw_networkx_graph(G)
    # graph_utils.draw_networkx_graph_complex(G)
    for g_node, g_attr in G.nodes.items():
        print(f"{g_node}: {g_attr}")

    # ASN = nx.get_node_attributes(G, "ASN")
    # print(ASN)
    #
    # print("--------------------------------\n")
    # print({node: G.nodes[node] for node in G.nodes})
    # print("--------------------------------\n")
    #
    # print(nx.degree(G))
    # print("--------------------------------\n")
    # print(G.edges())

    generate_clab.gen_yaml_from_nx(G)


    interactive_net = graph_utils.InteractiveNetwork(G)
    interactive_net.create_interactive_graph().show('../network.html', notebook=False)