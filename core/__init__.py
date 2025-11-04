"""
Core module for the AI Learning Engine.
"""
from .models import Topic, Syllabus, Question, Mnemonic, DifferenceTable, AnimationScript, Subject
from .ingest import KnowledgeBase, load_syllabus_from_json, save_syllabus_to_json
from .mnemonics import create_acronym_mnemonic, create_difference_table, get_example_difference
from .rag import RAGEngine

__all__ = [
    'Topic',
    'Syllabus',
    'Subject',
    'Question',
    'Mnemonic',
    'DifferenceTable',
    'AnimationScript',
    'KnowledgeBase',
    'load_syllabus_from_json',
    'save_syllabus_to_json',
    'create_acronym_mnemonic',
    'create_difference_table',
    'get_example_difference',
    'RAGEngine',
]
