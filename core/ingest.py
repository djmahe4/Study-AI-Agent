"""
Module for ingesting and processing syllabus data.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from .models import Topic, Syllabus, Question


class KnowledgeBase:
    """
    Manages storage and retrieval of knowledge data.
    """
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with required tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                summary TEXT,
                data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                topic TEXT,
                question TEXT,
                answer TEXT,
                data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_topic(self, topic: Topic) -> None:
        """Save a topic to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        topic_id = topic.id or str(uuid.uuid4())
        topic.id = topic_id
        
        cursor.execute("""
            INSERT OR REPLACE INTO topics (id, name, summary, data)
            VALUES (?, ?, ?, ?)
        """, (topic_id, topic.name, topic.summary, topic.model_dump_json()))
        
        conn.commit()
        conn.close()
    
    def save_question(self, question: Question) -> None:
        """Save a question to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        question_id = question.id or str(uuid.uuid4())
        question.id = question_id
        
        cursor.execute("""
            INSERT OR REPLACE INTO questions (id, topic, question, answer, data)
            VALUES (?, ?, ?, ?, ?)
        """, (question_id, question.topic, question.question, question.answer, question.model_dump_json()))
        
        conn.commit()
        conn.close()
    
    def get_topics(self) -> List[Topic]:
        """Retrieve all topics from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM topics")
        rows = cursor.fetchall()
        conn.close()
        
        return [Topic.model_validate_json(row[0]) for row in rows]
    
    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Retrieve a specific topic by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM topics WHERE id = ?", (topic_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Topic.model_validate_json(row[0])
        return None
    
    def get_questions(self, topic: Optional[str] = None) -> List[Question]:
        """Retrieve questions, optionally filtered by topic."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if topic:
            cursor.execute("SELECT data FROM questions WHERE topic = ?", (topic,))
        else:
            cursor.execute("SELECT data FROM questions")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Question.model_validate_json(row[0]) for row in rows]


def load_syllabus_from_json(file_path: str) -> Syllabus:
    """Load a syllabus from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return Syllabus(**data)


def save_syllabus_to_json(syllabus: Syllabus, file_path: str) -> None:
    """Save a syllabus to a JSON file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(syllabus.model_dump(), f, indent=2, default=str)
