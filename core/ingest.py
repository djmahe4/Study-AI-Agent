"""
Module for ingesting and processing syllabus data.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from .models import Topic, Syllabus, Question
import uuid


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
    
    def save_analyzed_questions(self, questions: List['AnalyzedQuestion'], subject_name: str) -> None:
        """Save analyzed exam questions to a subject-specific JSON file using QuestionBank model."""
        from .models import QuestionBank, AnalyzedQuestion
        
        path = Path(f"data/subjects/{subject_name}/questions/question_bank.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        
        current_bank = QuestionBank(questions=[])
        
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Migration: Convert old list format to QuestionBank
                        # Ensure we validate/convert dicts to AnalyzedQuestion
                        validated_qs = [AnalyzedQuestion(**q) for q in data]
                        current_bank.questions = validated_qs
                    elif isinstance(data, dict):
                        current_bank = QuestionBank(**data)
                except Exception as e:
                    print(f"Error loading existing question bank: {e}")
        
        # Merge new questions
        # Simple append. De-duplication could be added here based on ID or content.
        current_bank.questions.extend(questions)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(current_bank.model_dump(), f, indent=2, default=str)

    def get_analyzed_questions(self, subject_name: str) -> List[dict]:
        """Retrieve analyzed questions for a subject."""
        path = Path(f"data/subjects/{subject_name}/questions/question_bank.json")
        if not path.exists():
            return []
            
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # It's likely a QuestionBank
                    return data.get("questions", [])
            except Exception:
                return []


def load_syllabus_from_json(file_path: str) -> Syllabus:
    """Load a syllabus from a JSON file."""
    with open(file_path, 'r',encoding='utf-8') as f:
        data = json.load(f)
    return Syllabus(**data)


def save_syllabus_to_json(syllabus: Syllabus, file_path: str) -> None:
    """Save a syllabus to a JSON file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w',encoding='utf-8') as f:
        json.dump(syllabus.model_dump(), f, indent=2, default=str)


def save_syllabus_to_markdown(syllabus: Syllabus, output_dir: str) -> None:
    """
    Save a syllabus to a Markdown file structure (Subject/Module/Topic.md).
    """
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Subject Index (Readme)
    with open(base_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(f"# {syllabus.title}\n\n")
        if syllabus.description:
            f.write(f"{syllabus.description}\n\n")
        f.write("## Modules\n")
        for m in syllabus.modules:
            f.write(f"- [{m.name}]({m.name}/README.md)\n")

    for i, module in enumerate(syllabus.modules, 1):
        # Create Module Folder
        safe_mod_name = module.name.replace(":", " -").replace("/", "-").strip()
        mod_dir = base_dir / safe_mod_name
        mod_dir.mkdir(parents=True, exist_ok=True)
        
        # Module Index
        with open(mod_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(f"# {module.name}\n\n")
            if module.description:
                f.write(f"{module.description}\n\n")
            f.write("## Topics\n")
            for t in module.topics:
                safe_t_name = t.name.replace("/", "-").strip()
                f.write(f"- [{t.name}]({i}.{safe_t_name}.md)\n")

        # Topic Files
        for j, topic in enumerate(module.topics, 1):
            safe_topic_name = topic.name.replace("/", "-").strip()
            # Ensure filename is valid
            safe_topic_name = "".join([c for c in safe_topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
            topic_file = mod_dir / f"{j}. {safe_topic_name}.md"
            
            with open(topic_file, 'w', encoding='utf-8') as f:
                f.write(f"# {topic.name}\n\n")
                f.write(f"**Module:** {module.name}\n\n")
                f.write(f"**Summary:** {topic.summary}\n\n")
                
                if topic.key_points:
                    f.write("## Key Points\n")
                    for kp in topic.key_points:
                        f.write(f"- {kp}\n")
                    f.write("\n")
                
                if topic.mnemonics:
                    f.write("## Mnemonics\n")
                    for m in topic.mnemonics:
                        f.write(f"- **{m}**\n")
                    f.write("\n")
                
                if topic.mermaid_diagrams:
                    f.write("## Visualizations\n")
                    for diag in topic.mermaid_diagrams:
                        # Handle both dictionary (legacy) and MermaidDiagram object
                        if isinstance(diag, dict):
                            title = diag.get('title') or diag.get('type', 'Diagram').capitalize()
                            script = diag.get('script')
                        else:
                            title = diag.title or diag.type.capitalize()
                            script = diag.script
                            
                        f.write(f"### {title}\n")
                        f.write(f"```mermaid\n{script}\n```\n\n")
                
                if topic.questions:
                    f.write("## Practice Questions\n")
                    for q in topic.questions:
                        f.write(f"- {q}\n")
                    f.write("\n")
