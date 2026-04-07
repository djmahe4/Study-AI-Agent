#!/usr/bin/env python3
"""
explain_topic.py – Feynman-style topic explainer helper.

Lightweight CLI script for the concept-mastery skill.
No heavy dependencies: uses only stdlib + core.input_validator.

Usage:
    python skills/concept-mastery/scripts/explain_topic.py "recursion"
    python skills/concept-mastery/scripts/explain_topic.py "OSI model"
"""

import sys
import re
from pathlib import Path

# Add repo root so we can import core.input_validator
_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))

from core.input_validator import sanitize_text, classify_query_semantics


def feynman_template(topic: str) -> str:
    """Return a filled prompt template for Feynman-style explanation."""
    return f"""Explain "{topic}" using the Feynman Technique:
1. Simple explanation (ELI5, max 3 sentences)
2. One real-world analogy
3. Three key bullet points
4. One common misconception
5. One MCQ + one open-ended practice question with answers

Keep the total response under 400 words."""


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: explain_topic.py <topic>")
        sys.exit(1)

    raw_topic = " ".join(sys.argv[1:])
    clean_topic = sanitize_text(raw_topic, max_length=128)

    if not clean_topic.strip():
        print("Error: topic is empty after sanitization.")
        sys.exit(1)

    classification = classify_query_semantics(clean_topic)
    print(f"[concept-mastery] Topic: {clean_topic!r}")
    print(f"[concept-mastery] Detected type: {classification.query_type}  "
          f"confidence: {classification.confidence}")
    print(f"[concept-mastery] Aggregation strategy: {classification.aggregation_strategy}")
    print()
    print("--- Feynman Prompt ---")
    print(feynman_template(clean_topic))


if __name__ == "__main__":
    main()
