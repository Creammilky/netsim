from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from utils.xml_parser import GraphParser
from utils.graph_utils import InteractiveNetwork

app = Flask(__name__)
parser = GraphParser('../../test/route_3.xml')
parser.parse()
G = parser.get_networkx()
interactive_net = InteractiveNetwork(G)  # G 是你的原始NetworkX图

# 启用跨域访问
CORS(app)


@app.route('/update_graph', methods=['POST'])
def update_graph():
    data = request.json
    action = data['action']
    interactive_net.update_graph(action, data)
    return jsonify({"status": "success"})


@app.route('/show_graph')
def show_graph():
    return interactive_net.create_interactive_graph().show('network.html', notebook=False)


@app.route('/')
def root():
    interactive_net.create_interactive_graph().save_graph('./templates/network.html')
    return render_template('network.html')


if __name__ == '__main__':
    app.run(debug=True)
