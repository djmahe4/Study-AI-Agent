"""
Core module for the AI Learning Engine.
"""
from .models import (
    Topic, Syllabus, Question, Mnemonic, DifferenceTable, AnimationScript, Subject, Module,
    UserProgress, Achievement, PomodoroSession, TodoItem, FlashcardDeck, Flashcard, CustomNote
)
from .ingest import KnowledgeBase, load_syllabus_from_json, save_syllabus_to_json, save_syllabus_to_markdown
from .mnemonics import create_acronym_mnemonic, create_difference_table, get_example_difference
from .rag import RAGEngine
from .utils import normalize_subject_name, get_subject_dir
from .persistence import DataPersistenceManager, get_persistence_manager
from .gamification import GamificationManager
from .pomodoro import PomodoroTimer
from .todo_manager import TodoManager
from .flashcards import FlashcardManager
from .cheatsheet import CheatsheetGenerator
from .practice import PracticeGenerator
from .notes_manager import NotesManager
from .input_validator import (
    sanitize_text,
    sanitize_syllabus_text,
    sanitize_question_text,
    validate_subject_name,
)

__all__ = [
    'Topic',
    'Syllabus',
    'Subject',
    'Module',
    'Question',
    'Mnemonic',
    'DifferenceTable',
    'AnimationScript',
    'KnowledgeBase',
    'load_syllabus_from_json',
    'save_syllabus_to_json',
    'save_syllabus_to_markdown',
    'create_acronym_mnemonic',
    'create_difference_table',
    'get_example_difference',
    'RAGEngine',
    'normalize_subject_name',
    'get_subject_dir',
    # Input validation helpers
    'sanitize_text',
    'sanitize_syllabus_text',
    'sanitize_question_text',
    'validate_subject_name',
]
