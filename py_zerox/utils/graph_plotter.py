import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

def add_edges(graph, node, text_limit, parent=None):
    """Recursively add directed edges to the graph based on TreeOfContents structure."""
    
    # Mapping LaTeX section types to shorter names
    smol = {'document': 'doc', 'section': 'sec', 'subsection': 'ssec', 
            'subsubsection': 'sssec', 'paragraph': 'pg', 'subparagraph': 'spg'}
    
    # Create node name based on type and name, or string if it's a leaf
    node_label = ('Text:\n\n' + node) if isinstance(node, str) else (
        smol[node['type']] if node['type'] in smol else node['type']) + ':\n\n' + node['name']
    
    # Use the unique ID for graph connectivity
    node_id = str(node['id']) if not isinstance(node, str) else node
    
    # Limit label length for readability in the graph
    node_label = node_label[0:min(text_limit, len(node_label))]

    # Add the node with the label to the graph
    graph.add_node(node_id, label=node_label)
    
    # Add an edge from parent to this node if parent exists
    if parent:
        graph.add_edge(parent, node_id)
    
    # Recursively add edges for children if the node is a dictionary
    if isinstance(node, dict) and 'children' in node:
        for child in node['children']:
            add_edges(graph, child, text_limit = text_limit,parent =  node_id)

def draw_dict(dictt, text_limit):
    """Draw the TreeOfContents as a directed graph with improved layout and readability."""
    # Create a directed graph
    graph = nx.DiGraph()
    
    # Recursively add nodes and edges
    add_edges(graph, dictt, text_limit= text_limit)
 
    # Use a hierarchical layout for a clearer structure
    pos = graphviz_layout(graph, prog="dot")  
    
    plt.figure(figsize=(15, 10))  # Larger figure size for readability
    
    # Extract node labels for visualization
    labels = nx.get_node_attributes(graph, 'label')
    
    nx.draw(
        graph, pos, with_labels=True, labels=labels, node_size=200, node_color="skyblue",
        font_size=10, font_weight="bold", font_color="black", arrows=True, arrowstyle='->', arrowsize=15
    )
    
    plt.title("LaTeX Document Structure Tree (Directed)")
    plt.show()
