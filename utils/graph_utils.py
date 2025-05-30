import matplotlib.pyplot as plt
import numpy as np
from pyvis.network import Network
import networkx as nx
from utils import logger
import json

# Initialize logger
log = logger.Logger("GraphUtils")


def make_hashable(data):
    """递归地将列表或字典转换为不可变类型（元组）"""
    if isinstance(data, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in data.items()))
    elif isinstance(data, list):
        return tuple(make_hashable(item) for item in data)
    else:
        return data


def is_graphs_equal(G1, G2):
    # 比较节点 ID 和属性（使用递归转换为不可变类型）
    nodes_1 = {(node, make_hashable(attrs)) for node, attrs in G1.nodes(data=True)}
    nodes_2 = {(node, make_hashable(attrs)) for node, attrs in G2.nodes(data=True)}

    if nodes_1 != nodes_2:
        return False
    # 比较边及其属性（递归转换）
    edges_1 = {(source, target, make_hashable(attrs)) for source, target, attrs in G1.edges(data=True)}
    edges_2 = {(source, target, make_hashable(attrs)) for source, target, attrs in G2.edges(data=True)}

    if edges_1 != edges_2:
        return False
    return True


class InteractiveNetwork:
    def __init__(self, G=None):
        self.G = G if G else nx.Graph()
        self.net = None

    def create_interactive_graph(self):
        # 创建pyvis网络对象
        self.net = Network(height='750px', width='100%', bgcolor='#ffffff', cdn_resources='remote')

        # 处理现有的图数据
        H = nx.Graph()

        # 处理节点
        # 计算度的最大最小值，用于归一化
        degrees = dict(self.G.degree())
        max_degree = max(degrees.values()) if degrees else 1
        min_degree = min(degrees.values()) if degrees else 0
        node_type = nx.get_node_attributes(self.G, "type")

        for node, attrs in self.G.nodes(data=True):
            # 计算节点度
            node_degree = degrees.get(node, 0)

            # 归一化计算 size，避免过小或过大
            min_size = 10
            max_size = 80
            size = min_size + (max_size - min_size) * (
                (node_degree - min_degree) / (max_degree - min_degree) if max_degree != min_degree else 0)

            # 构造 title 信息
            title_html = f"Node {node}\n"
            for key, value in attrs.items():
                if isinstance(value, list):
                    # log.debug(f"list: {key}: {value}")
                    title_html += f"\n{key}:\n"
                    for prop in value:
                        # Todo: to satisfy different type of attrs of nodes
                        title_html += f"{key}: {prop}\n"
                else:
                    title_html += f"{key}: {value}\n"

            # 添加节点，并设置大小
            if node_type.get(node, "").lower() == "vp":
                H.add_node(node, title=title_html, label=f"Node {node}", color="#8B0012", size=size)
            elif node_type.get(node, "").lower() == "as":
                H.add_node(node, title=title_html, label=f"Node {node}", color="#20B2AA", size=size)
            elif node_type.get(node, "").lower() == "host":
                H.add_node(node, title=title_html, label=f"Node {node}", color="#7FFFAA", size=size)
            else:
                H.add_node(node, title=title_html, label=f"Node {node}", size=size)

        for u, v, attrs in self.G.edges(data=True):
            title_html = f"Edge {u}-{v}"
            for key, value in attrs.items():
                if isinstance(value, list):
                    title_html += f"\n{key}:\n"
                    for prop in value:
                        title_html += f"{prop.name}: {prop.value}\n"
                else:
                    title_html += f"{key}: {value}\n"

            H.add_edge(u, v, title=title_html)

        self.net.from_nx(H)

        # 添加交互控制选项
        self.net.set_options("""
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08
                },
                "solver": "forceAtlas2Based"
            },
            "nodes": {
                "font": {"size": 16},
                "size": 30
            },
            "edges": {
                "smooth": {"type": "dynamic"},
                "width": 2
            },
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": true,
                "tooltipDelay": 200
            },
            "manipulation": {
                "enabled": true,
                "initiallyActive": true
            }
        }
        """)

        # 添加自定义HTML控件
        self.net.html += """
        <div style="position: absolute; top: 10px; left: 10px; z-index: 999;">
            <button onclick="addNode()">Add Node</button>
            <button onclick="removeNode()">Remove Node</button>
            <button onclick="addEdge()">Add Edge</button>
            <button onclick="removeEdge()">Remove Edge</button>
        </div>
        <script>
        function addNode() {
            var nodeId = prompt("Enter node ID:");
            if (nodeId) {
                var data = {action: 'add_node', id: nodeId};
                updateGraph(data);
            }
        }

        function removeNode() {
            var nodeId = prompt("Enter node ID to remove:");
            if (nodeId) {
                var data = {action: 'remove_node', id: nodeId};
                updateGraph(data);
            }
        }

        function addEdge() {
        
            var from = prompt("Enter source node ID:");
            var to = prompt("Enter target node ID:");
            if (from && to) {
                var data = {action: 'add_edge', from: from, to: to};
                updateGraph(data);
            }
        }

        function removeEdge() {
            var from = prompt("Enter source node ID:");
            var to = prompt("Enter target node ID:");
            if (from && to) {
                var data = {action: 'remove_edge', from: from, to: to};
                updateGraph(data);
            }
        }

        function updateGraph(data) {
            // 发送更新到后端
            fetch('/update_graph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                // 刷新图
                location.reload();
            });
        }
        </script>
        """

        return self.net

    def update_graph(self, action, data):
        """更新图的数据结构"""
        if action == 'add_node':
            self.G.add_node(data['id'])
        elif action == 'remove_node':
            self.G.remove_node(data['id'])
        elif action == 'add_edge':
            self.G.add_edge(data['from'], data['to'])
        elif action == 'remove_edge':
            self.G.remove_edge(data['from'], data['to'])

def draw_pyvis_network(G):
    # 创建一个新的NetworkX图来存储处理后的数据
    H = nx.Graph()

    # 处理节点及其属性
    for node, attrs in G.nodes(data=True):
        # 将属性转换为可序列化的格式
        clean_attrs = {}
        title = ""
        for key, value in attrs.items():
            if isinstance(value, list):  # 处理属性列表
                clean_attrs[key] = [str(prop.name) + ': ' + str(prop.value)
                                    for prop in value]
                title += f"{key}:\n" + "\n".join(
                    [str(prop.name) + ': ' + str(prop.value) for prop in value]) + "\n\n"
            else:
                clean_attrs[key] = str(value)
                title += f"{key}: {str(value)}\n\n"

        # 将title属性添加到节点中
        H.add_node(node, **clean_attrs, title=title)

    # 处理边及其属性
    for u, v, attrs in G.edges(data=True):
        # 将边属性转换为可序列化的格式
        clean_attrs = {}
        title = ""
        for key, value in attrs.items():
            if isinstance(value, list):  # 处理属性列表
                clean_attrs[key] = [str(prop.name) + ': ' + str(prop.value)
                                    for prop in value]
                title += f"{key}:\n" + "\n".join(
                    [str(prop.name) + ': ' + str(prop.value) for prop in value]) + "\n\n"
            else:
                clean_attrs[key] = str(value)
                title += f"{key}: {str(value)}\n\n"

        # 将title属性添加到边中
        H.add_edge(u, v, **clean_attrs, title=title)

    # 创建pyvis网络对象
    net = Network(height='750px', width='100%', bgcolor='#ffffff', cdn_resources='remote')

    # 使用处理后的图
    net.from_nx(H)

    # 设置显示选项
    net.set_options("""
    {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
        },
        "nodes": {
            "font": {"size": 20},
            "size": 20
        },
        "edges": {
            "color": {"inherit": true},
            "smooth": {"type": "dynamic"},
            "width": 2
        }
    }
    """)

    # 保存为HTML文件
    net.show('network.html', notebook=False)


def draw_networkx_graph(G):
    plt.figure(figsize=(12, 8))

    # 使用最简单的圆形布局
    pos = nx.circular_layout(G)

    nx.draw(G,
            pos=pos,
            with_labels=True,
            node_color='lightblue',
            node_size=500)

    plt.axis('off')
    plt.show()


def draw_networkx_graph_complex(G):
    plt.figure(figsize=(12, 8))

    # 尝试不同的布局算法和参数
    try:
        # 方法1: spring_layout 增加迭代次数和调整参数
        pos = nx.spring_layout(G, k=0.5, iterations=100, scale=1.0, seed=42)
    except:
        try:
            # 方法2: 如果spring_layout失败，尝试kamada_kawai_layout
            pos = nx.kamada_kawai_layout(G)
        except:
            # 方法3: 最后使用最简单的随机布局
            pos = nx.random_layout(G)

    # 检查位置坐标的有效性
    for node, (x, y) in pos.items():
        if not (np.isfinite(x) and np.isfinite(y)):
            # 如果发现无效坐标，替换为随机有效位置
            pos[node] = (np.random.uniform(0, 1), np.random.uniform(0, 1))

    # 绘制图形
    nx.draw(G,
            pos=pos,
            with_labels=True,
            node_color='lightblue',
            node_size=500,
            font_weight='bold',
            edge_color='gray')

    plt.axis('off')
    plt.show()

