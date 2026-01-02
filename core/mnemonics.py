"""
Module for generating and managing mnemonics and memory aids.
"""
from typing import List
from .models import Mnemonic, DifferenceTable


def create_acronym_mnemonic(topic: str, key_points: List[str]) -> Mnemonic:
    """
    Create an acronym-based mnemonic from key points.
    
    Args:
        topic: The topic name
        key_points: List of key points to remember
        
    Returns:
        A Mnemonic object with the acronym
    """
    if not key_points:
        return Mnemonic(
            topic=topic,
            technique="acronym",
            content="",
            explanation="No key points provided"
        )
    
    # Extract first letters
    acronym = "".join([point[0].upper() for point in key_points if point])
    
    return Mnemonic(
        topic=topic,
        technique="acronym",
        content=acronym,
        explanation=f"Each letter represents: {', '.join(key_points)}"
    )


def create_difference_table(concept_a: str, concept_b: str, aspects: List[dict]) -> DifferenceTable:
    """
    Create a comparison table between two concepts.
    
    Args:
        concept_a: First concept name
        concept_b: Second concept name
        aspects: List of difference aspects with keys 'aspect', 'concept_a_value', 'concept_b_value'
        
    Returns:
        A DifferenceTable object
    """
    return DifferenceTable(
        concept_a=concept_a,
        concept_b=concept_b,
        differences=aspects
    )


# Example difference templates
EXAMPLE_DIFFERENCES = {
    "tcp_vs_udp": {
        "concept_a": "TCP",
        "concept_b": "UDP",
        "differences": [
            {"aspect": "Connection", "concept_a_value": "Connection-oriented", "concept_b_value": "Connectionless"},
            {"aspect": "Reliability", "concept_a_value": "Reliable", "concept_b_value": "Unreliable"},
            {"aspect": "Speed", "concept_a_value": "Slower", "concept_b_value": "Faster"},
            {"aspect": "Use Case", "concept_a_value": "File transfer, Email", "concept_b_value": "Streaming, Gaming"}
        ]
    },
    "stack_vs_queue": {
        "concept_a": "Stack",
        "concept_b": "Queue",
        "differences": [
            {"aspect": "Order", "concept_a_value": "LIFO (Last In First Out)", "concept_b_value": "FIFO (First In First Out)"},
            {"aspect": "Operations", "concept_a_value": "Push, Pop", "concept_b_value": "Enqueue, Dequeue"},
            {"aspect": "Use Case", "concept_a_value": "Function calls, Undo", "concept_b_value": "Task scheduling, BFS"}
        ]
    }
}


def get_example_difference(key: str) -> DifferenceTable:
    """Get an example difference table by key."""
    if key in EXAMPLE_DIFFERENCES:
        data = EXAMPLE_DIFFERENCES[key]
        return DifferenceTable(**data)
    return None
