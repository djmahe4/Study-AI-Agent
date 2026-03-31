#!/usr/bin/env python3
"""
inspect_retrieval.py – Print semantic classification + strategy for a query.

Lightweight helper for the rag-optimizer skill.

Usage:
    python skills/rag-optimizer/scripts/inspect_retrieval.py "What is TCP?"
    python skills/rag-optimizer/scripts/inspect_retrieval.py "How to implement quicksort?"
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))

from core.input_validator import sanitize_question_text, classify_query_semantics

_STRATEGY_DESCRIPTIONS = {
    "summarize-first": (
        "Retrieve broadly (top-10 chunks), ask the LLM to summarise, "
        "then extract the specific answer. Best for short factual queries."
    ),
    "detailed-chunk-merge": (
        "Retrieve top-5 chunks per source, interleave by relevance score, "
        "concatenate into one context. Best for conceptual/procedural queries."
    ),
    "source-priority": (
        "Rank sources: textbook > PDF notes > YouTube > web. Take top-3 "
        "chunks per tier. Best for comparative queries where authority matters."
    ),
    "gap-analysis": (
        "Diff retrieved chunks against syllabus key_points. Flag uncovered "
        "points. Best for generative tasks (quiz/mindmap/flashcard creation)."
    ),
}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: inspect_retrieval.py <query>")
        sys.exit(1)

    raw_query = " ".join(sys.argv[1:])
    clean_query = sanitize_question_text(raw_query)

    if not clean_query.strip():
        print("Error: query is empty after sanitization.")
        sys.exit(1)

    result = classify_query_semantics(clean_query)

    print(f"\n{'='*60}")
    print(f"RAG Optimizer – Retrieval Inspection")
    print(f"{'='*60}")
    print(f"Query          : {clean_query!r}")
    print(f"Primary Type   : {result.query_type}")
    print(f"Confidence     : {result.confidence:.2f}")
    print(f"Strategy       : {result.aggregation_strategy}")
    print()
    print("All Label Scores:")
    for label, score in result.labels:
        bar = "█" * int(score * 20)
        print(f"  {label:<14} {score:.3f}  {bar}")
    print()
    print(f"Strategy Detail:\n  {_STRATEGY_DESCRIPTIONS.get(result.aggregation_strategy, '')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
