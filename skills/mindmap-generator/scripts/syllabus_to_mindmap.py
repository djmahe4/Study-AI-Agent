#!/usr/bin/env python3
"""
syllabus_to_mindmap.py – Convert a plain-text syllabus to a Mermaid mindmap.

Lightweight helper for the mindmap-generator skill.
Outputs a .mmd file that can be rendered with mermaid.js or pasted into
any Markdown editor that supports Mermaid diagrams.

Usage:
    python skills/mindmap-generator/scripts/syllabus_to_mindmap.py syllabus.txt
    python skills/mindmap-generator/scripts/syllabus_to_mindmap.py syllabus.txt -o output.mmd
"""

import sys
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))

from core.input_validator import sanitize_syllabus_text, sanitize_mermaid_label


def _safe_node_label(label: str) -> str:
    """Delegate to the canonical sanitize_mermaid_label helper."""
    return sanitize_mermaid_label(label)


def text_to_mermaid(subject_name: str, text: str) -> str:
    """
    Parse plain-text syllabus and build a Mermaid mindmap string.

    Uses simple heuristics:
    - Lines matching "Module/Unit N" → Level 1 node
    - Indented or sub-lines → Level 2 (topics)
    - Deeper indentation → Level 3 (subtopics)
    """
    root = _safe_node_label(subject_name)
    lines_out = ["mindmap", f"  root(({root}))"]

    current_module: str = ""
    current_topic: str = ""

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        indent = len(line) - len(line.lstrip())
        label = _safe_node_label(stripped)

        if re.match(r"^(module|unit)\s*\d+", stripped, re.IGNORECASE):
            current_module = label
            current_topic = ""
            lines_out.append(f"    {label}")
        elif indent == 0 and current_module:
            # Top-level topic under current module
            current_topic = label
            lines_out.append(f"      {label}")
        elif indent > 0 and current_topic:
            # Subtopic
            lines_out.append(f"        {label}")
        elif indent == 0 and not current_module:
            # No modules detected – treat as a flat topic list
            current_topic = label
            lines_out.append(f"    {label}")

    return "\n".join(lines_out)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: syllabus_to_mindmap.py <syllabus.txt> [-o output.mmd]")
        sys.exit(1)

    input_file = args[0]
    output_file = None
    if "-o" in args:
        idx = args.index("-o")
        try:
            output_file = args[idx + 1]
        except IndexError:
            pass

    raw = Path(input_file).read_text(encoding="utf-8")
    clean = sanitize_syllabus_text(raw)
    subject = Path(input_file).stem.replace("_", " ").title()
    mermaid = text_to_mermaid(subject, clean)

    if output_file:
        Path(output_file).write_text(mermaid, encoding="utf-8")
        print(f"Mindmap written to {output_file}")
    else:
        print(mermaid)


if __name__ == "__main__":
    main()
