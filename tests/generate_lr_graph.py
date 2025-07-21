#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :  generate_lr_graph.py
@Time    :  2025/07/13 12:05:37
@Author  :  XY 
@Version :  1.0
@Desc    :  为lightrag输出文件生成html图
'''

from ast import main
from os import name
import pipmaster as pm

if not pm.is_installed("pyvis"):
    pm.install("pyvis")
if not pm.is_installed("networkx"):
    pm.install("networkx")

import networkx as nx
from pyvis.network import Network
import random


def gen_lr_graph(graphml_path: str, save_path: str):
    """
    args:
        graphml_path: graphml图文件的路径
        save_path: 保存html文件的路径
    eg:
        graphml_path = "./inputs/sql_process_func/graph_chunk_entity_relation.graphml"
        save_path = "./output/sql_pf_knowledge_graph.html"
    """
    # Load the GraphML file
    G = nx.read_graphml(graphml_path)

    # Create a Pyvis network
    net = Network(height="100vh", notebook=True, )

    # Convert NetworkX graph to Pyvis network
    net.from_nx(G)

    # Add colors and title to nodes
    for node in net.nodes:
        node["color"] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        
        # 根据 entity_type 设置不同的节点大小
        entity_type = node.get("entity_type", "")
        
        # 根据实际的 entity_type 类型自定义大小
        if entity_type == "table":
            node["size"] = 50
            node["color"] = "#8B0000"  # 深红色
        elif entity_type == "field":
            node["size"] = 20
        else:
            node["size"] = 15  # 默认大小
        
        if "description" in node:
            node["title"] = node["description"]

    # Add title to edges
    for edge in net.edges:
        if "description" in edge:
            edge["title"] = edge["description"]

    # Save and display the network
    net.show(save_path)


# 测试
if __name__ == "__main__":
    graphml_path = "./inputs/sql_process_func/graph_chunk_entity_relation.graphml"
    save_path = "./inputs/sql_process_func/sql_pf_knowledge_graph.html"
    gen_lr_graph(graphml_path, save_path)