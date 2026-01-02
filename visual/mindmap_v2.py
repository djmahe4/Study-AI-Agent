from mermaid.graph import Graph
from core.models import Topic
from typing import List

class MindMapGenerator2:
    def __init__(self, topics: List[Topic]):
        self.topics = topics

    def generate_script(self) -> str:
        # Use mindmap syntax
        script = "mindmap\n"
        script += "  root((Syllabus))\n"
        for topic in self.topics:
            # Basic sanitization for mermaid text
            safe_name = self._sanitize(topic.name)
            script += f"    {safe_name}\n"
            if topic.key_points:
                for kp in topic.key_points:
                    safe_kp = self._sanitize(kp)
                    # Truncate if too long to keep diagram readable
                    if len(safe_kp) > 50:
                        safe_kp = safe_kp[:47] + "..."
                    script += f"      {safe_kp}\n"
        return script

    def _sanitize(self, text: str) -> str:
        # Replace characters that might break mermaid syntax
        # Also remove newlines
        return text.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('"', "'").replace('\n', ' ')

    def save(self, filepath: str):
        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        script = self.generate_script()
        graph = Graph("MindMap", script)
        # mermaid-py saves with .mmd extension by default if not specified or just writes the file
        graph.save(filepath)
        return filepath
