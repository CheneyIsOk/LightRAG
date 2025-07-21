import os
import networkx as nx

# 配置
WORKING_DIR = "./inputs/book"
GRAPHML_PATH = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
HTML_PATH = os.path.join(WORKING_DIR, "book_knowledge_graph.html")

# 工具函数：加载和保存graphml
def load_graph():
    if os.path.exists(GRAPHML_PATH):
        return nx.read_graphml(GRAPHML_PATH)
    else:
        return nx.Graph()

g = load_graph()

data = g.nodes(data=True)
entity_list = list(data)
print(entity_list[0])
