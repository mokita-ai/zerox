import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
 
def add_edges(graph, node, parent=None):
    """Recursively add directed edges to the graph based on TreeOfContents structure."""
    # Set the node name based on whether the node is a string or dictionary
 
    smol = {'document' : 'doc', 'section':'sec', 'subsection':'ssec', 'subsubsection':'sssec', 'paragraph' : 'pg', 'subparagraph':'spg'}
    
 
    node_name = ('Text:\n\n' + node[0:min(10, len(node))] )if isinstance(node, str) else ( smol[node['type']] if node['type']  in smol else  node['type']) + ':\n\n' + node['name'] + str (node['id'])
    
    if parent:
        parent_name = parent
        graph.add_edge(parent_name, node_name)
 
    if isinstance(node, str):
        return
 
    for child in node['children']:
        add_edges(graph, child, node_name)
 
 
def draw_dict(dictt):
    """Draw the TreeOfContents as a directed graph with improved layout and readability."""
    # Create a directed graph
    graph = nx.DiGraph()
    
    # Recursively add nodes and edges
    add_edges(graph, dictt)
 
    # Use a hierarchical layout for a clearer structure
    pos = graphviz_layout(graph, prog="dot")  
    
    plt.figure(figsize=(15, 10))  # Larger figure size for readability
    nx.draw(
        graph, pos, with_labels=True, node_size=200, node_color="skyblue",
        font_size=10, font_weight="bold", font_color="black", arrows=True, arrowstyle='->', arrowsize=15
    )
    plt.title("LaTeX Document Structure Tree (Directed)")
    plt.show()