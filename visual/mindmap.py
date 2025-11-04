"""
Module for generating mind maps using NetworkX.
"""
import networkx as nx
from typing import List, Dict, Optional
from pathlib import Path


class MindMapGenerator:
    """
    Generates mind maps from topics using NetworkX.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_topic(self, topic_name: str, parent: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Add a topic to the mind map.
        
        Args:
            topic_name: Name of the topic
            parent: Parent topic name (if any)
            metadata: Additional metadata for the node
        """
        self.graph.add_node(topic_name, **(metadata or {}))
        if parent:
            self.graph.add_edge(parent, topic_name)
    
    def add_topics_from_syllabus(self, topics: List, root_name: str = "Syllabus"):
        """
        Build a mind map from a list of topics.
        
        Args:
            topics: List of Topic objects
            root_name: Name of the root node
        """
        self.graph.add_node(root_name, level=0)
        
        for topic in topics:
            # Add main topic
            self.graph.add_node(topic.name, 
                              summary=topic.summary,
                              level=1)
            self.graph.add_edge(root_name, topic.name)
            
            # Add subtopics if any
            for subtopic in topic.subtopics:
                self.graph.add_node(subtopic, level=2)
                self.graph.add_edge(topic.name, subtopic)
    
    def export_to_json(self, output_path: str) -> None:
        """
        Export the mind map to JSON format.
        
        Args:
            output_path: Path to save the JSON file
        """
        import json
        from networkx.readwrite import json_graph
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        data = json_graph.node_link_data(self.graph)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_to_graphviz(self, output_path: str) -> None:
        """
        Export the mind map to Graphviz DOT format.
        
        Args:
            output_path: Path to save the DOT file
        """
        from networkx.drawing.nx_pydot import write_dot
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        write_dot(self.graph, output_path)
    
    def get_graph_data(self) -> Dict:
        """
        Get the graph data in a format suitable for visualization.
        
        Returns:
            Dictionary with nodes and edges
        """
        nodes = []
        edges = []
        
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                'id': node,
                'label': node,
                **data
            })
        
        for source, target in self.graph.edges():
            edges.append({
                'source': source,
                'target': target
            })
        
        return {'nodes': nodes, 'edges': edges}
    
    def clear(self):
        """Clear the graph."""
        self.graph.clear()


def create_simple_mindmap(topics: List, output_format: str = "json") -> str:
    """
    Helper function to create a simple mind map from topics.
    
    Args:
        topics: List of Topic objects
        output_format: Format to export (json, dot)
        
    Returns:
        Path to the exported file
    """
    generator = MindMapGenerator()
    generator.add_topics_from_syllabus(topics)
    
    output_path = f"data/mindmap.{output_format}"
    
    if output_format == "json":
        generator.export_to_json(output_path)
    elif output_format == "dot":
        generator.export_to_graphviz(output_path)
    
    return output_path
