"""
Pydantic models for structured knowledge representation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class Topic(BaseModel):
    """
    Represents a learning topic with structured knowledge.
    """
    id: Optional[str] = None
    name: str = Field(..., description="Name of the topic")
    summary: str = Field(..., description="Brief summary of the topic")
    key_points: List[str] = Field(default_factory=list, description="Key points to remember")
    differences: List[str] = Field(default_factory=list, description="Key differences or contrasts")
    mnemonics: List[str] = Field(default_factory=list, description="Memory aids and mnemonics")
    questions: List[str] = Field(default_factory=list, description="Practice questions")
    subtopics: List[str] = Field(default_factory=list, description="Related subtopics")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for this topic")
    created_at: datetime = Field(default_factory=datetime.now)


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
    id: Optional[str] = None
    topic: str
    question: str
    answer: str
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium", description="Difficulty level")
    type: Literal["multiple_choice", "open_ended"] = Field(default="multiple_choice", description="Question type")
    options: List[str] = Field(default_factory=list, description="Answer options for MCQ")


class Syllabus(BaseModel):
    """
    Represents a complete syllabus with topics.
    """
    title: str
    description: Optional[str] = None
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


class AnimationScript(BaseModel):
    """
    Represents an animation script for visual learning.
    """
    name: str
    description: str
    topic: str
    frames: List[dict] = Field(default_factory=list, description="Animation frames with instructions")
    duration: int = Field(default=5, description="Duration in seconds")
