"""
Pydantic models for structured knowledge representation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime
import uuid

class MermaidDiagramType(str):
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "classDiagram"
    STATE = "stateDiagram"
    ER = "erDiagram"
    GANTT = "gantt"
    PIE = "pie"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"

class MermaidDiagram(BaseModel):
    """
    Base class for Mermaid diagrams.
    """
    type: str = Field(..., description="Type of diagram (e.g., flowchart, sequence)")
    title: Optional[str] = None
    script: str = Field(..., description="The raw Mermaid script content")

class Topic(BaseModel):
    """
    Represents a learning topic with structured knowledge.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Name of the topic")
    module_id: Optional[str] = None
    summary: str = Field(..., description="Brief summary of the topic")
    key_points: List[str] = Field(default_factory=list, description="Basic points to remember for exams")
    differences: List[str] = Field(default_factory=list, description="Key differences or contrasts")
    mnemonics: List[str] = Field(default_factory=list, description="Memory aids and mnemonics")
    questions: List[str] = Field(default_factory=list, description="Practice questions")
    subtopics: List[str] = Field(default_factory=list, description="All subtopics")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for this topic")
    importance_score: float = Field(default=0.0, description="Calculated importance based on question papers")
    mermaid_diagrams: List[MermaidDiagram] = Field(default_factory=list, description="List of mermaid diagram objects")
    created_at: datetime = Field(default_factory=datetime.now)


class Module(BaseModel):
    """
    Represents a module or unit within a subject.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    topics: List[Topic] = Field(default_factory=list)
    order: int = 0


class DifferenceTable(BaseModel):
    """
    Represents a comparison table between concepts.
    """
    concept_a: str
    concept_b: str
    differences: List[dict] = Field(default_factory=list, description="List of difference aspects")
    
    
class Mnemonic(BaseModel):
    """
    Represents a mnemonic device for memory retention.
    """
    topic: str
    technique: str = Field(..., description="Type of mnemonic (acronym, rhyme, story, etc.)")
    content: str = Field(..., description="The actual mnemonic")
    explanation: Optional[str] = None


class Question(BaseModel):
    """
    Represents a practice question with answer.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    question: str
    answer: str
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium", description="Difficulty level")
    type: Literal["multiple_choice", "open_ended"] = Field(default="multiple_choice", description="Question type")
    options: List[str] = Field(default_factory=list, description="Answer options for MCQ")
    source: Optional[str] = Field(None, description="Source (e.g., '2023 Exam Part B')")


class Syllabus(BaseModel):
    """
    Represents a complete syllabus with modules and topics.
    """
    title: str
    description: Optional[str] = None
    modules: List[Module] = Field(default_factory=list)
    # topics list kept for backward compatibility or flat view if needed, but primary structure is modules
    topics: List[Topic] = Field(default_factory=list) 
    question_bank_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Subject(BaseModel):
    """
    Represents a subject with its syllabus and resources.
    """
    name: str
    syllabus: Syllabus
    folder_path: str
    question_bank_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class AnimationCommandType(str):
    TEXT = "text"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    ARROW = "arrow"

class AnimationCommand(BaseModel):
    """
    A single drawing command for a frame.
    """
    type: str = Field(..., description="Type of shape: text, circle, rectangle, arrow")
    # Text
    text: Optional[str] = None
    position: Optional[List[int]] = Field(None, description="[x, y]")
    font_scale: float = 1.0
    # Circle
    center: Optional[List[int]] = Field(None, description="[x, y]")
    radius: Optional[int] = None
    # Rect / Arrow
    start_point: Optional[List[int]] = Field(None, description="[x, y] for rect top-left or arrow start")
    end_point: Optional[List[int]] = Field(None, description="[x, y] for rect bottom-right or arrow end")
    # Common
    color: List[int] = Field(default=[0, 0, 0], description="RGB color [r, g, b]") # OpenCV uses BGR but we'll ask Gemini for RGB and convert or just assume BGR? Let's assume RGB for ease of prompting.
    thickness: int = 2

class AnimationFrame(BaseModel):
    """
    A single frame in the animation.
    """
    commands: List[AnimationCommand] = Field(default_factory=list)
    duration_frames: int = Field(default=30, description="Number of frames to hold this static image")

class AnimationScript(BaseModel):
    """
    Represents an animation script for visual learning.
    """
    title: str
    topic: str
    fps: int = 30
    width: int = 800
    height: int = 600
    frames: List[AnimationFrame] = Field(default_factory=list, description="Sequence of frames")

class ExamSection(BaseModel):
    """
    Defines a section of an exam paper (e.g., Part A).
    """
    name: str = Field(..., description="Section name (e.g., 'Part A')")
    question_range: List[int] = Field(..., description="[Start, End] question numbers (inclusive)")
    marks_per_question: int
    has_choice: bool = False
    
class ExamPattern(BaseModel):
    """
    Defines the structure of an exam paper.
    """
    name: str
    sections: List[ExamSection] = Field(default_factory=list)
    # Mapping: "Module 1" -> [1, 2, 11], "Module 2" -> [3, 4, 12]
    module_mapping: Dict[str, List[int]] = Field(default_factory=dict, description="Map Module Name to Question Numbers")

class AnalyzedQuestion(BaseModel):
    """
    Represents a question extracted from a paper.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    number: int
    part: Optional[str] = None # 'a' or 'b' if multipart
    text: str
    marks: int
    module: Optional[str] = None
    topic: Optional[str] = None
    year: Optional[str] = None
    paper_name: Optional[str] = None
    
class QuestionBank(BaseModel):
    """
    Collection of analyzed questions.
    """
    questions: List[AnalyzedQuestion] = Field(default_factory=list)
