"""
Module for processing syllabus text using Gemini AI.
"""
import json
from typing import Optional
from pathlib import Path
from .models import Syllabus, Topic


class GeminiProcessor:
    """
    Processes syllabus text using Gemini AI to extract structured data.
    
    TODO: Integrate with actual Gemini API
    TODO: Add API key management
    TODO: Add error handling and retries
    TODO: Support different prompts for various educational domains
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # TODO: Initialize Gemini client here
        # import google.generativeai as genai
        # genai.configure(api_key=api_key)
        # self.model = genai.GenerativeModel('gemini-pro')
    
    def process_syllabus_text(self, syllabus_text: str, subject_name: str) -> Syllabus:
        """
        Process syllabus text using Gemini to extract structured data.
        
        Args:
            syllabus_text: Raw syllabus text
            subject_name: Name of the subject
            
        Returns:
            Structured Syllabus object
        """
        # TODO: Replace with actual Gemini API call
        # prompt = self._create_extraction_prompt(syllabus_text, subject_name)
        # response = self.model.generate_content(prompt)
        # syllabus_data = self._parse_gemini_response(response.text)
        
        # Placeholder implementation - parses text manually
        topics = self._extract_topics_placeholder(syllabus_text)
        
        return Syllabus(
            title=subject_name,
            description=f"Syllabus for {subject_name}",
            topics=topics
        )
    
    def _create_extraction_prompt(self, syllabus_text: str, subject_name: str) -> str:
        """
        Create a prompt for Gemini to extract structured syllabus data.
        
        TODO: Refine prompt for better extraction
        TODO: Add few-shot examples
        """
        return f"""
Extract structured learning content from the following syllabus text for the subject "{subject_name}".

For each topic in the syllabus, extract:
- name: The topic name
- summary: A brief summary
- key_points: Important points to remember (list)
- differences: Key differences or contrasts (list)
- mnemonics: Memory aids if applicable (list)
- questions: Practice questions (list)
- subtopics: Related subtopics (list)
- prerequisites: Prerequisites for this topic (list)

Syllabus Text:
{syllabus_text}

Return the result as a JSON object with this structure:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "summary": "Brief summary",
      "key_points": ["Point 1", "Point 2"],
      "differences": ["Difference 1"],
      "mnemonics": ["Mnemonic 1"],
      "questions": ["Question 1?"],
      "subtopics": ["Subtopic 1"],
      "prerequisites": ["Prereq 1"]
    }}
  ]
}}
"""
    
    def _parse_gemini_response(self, response_text: str) -> dict:
        """
        Parse Gemini's JSON response.
        
        TODO: Add robust JSON extraction from markdown code blocks
        TODO: Handle malformed JSON gracefully
        """
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        return json.loads(response_text)
    
    def _extract_topics_placeholder(self, syllabus_text: str) -> list[Topic]:
        """
        Placeholder method to extract topics from text.
        This will be replaced by actual Gemini processing.
        """
        # Simple text parsing - split by lines and create topics
        lines = [line.strip() for line in syllabus_text.split('\n') if line.strip()]
        
        topics = []
        current_topic = None
        
        for line in lines:
            # Simple heuristic: Lines with less than 100 chars and not starting with '-' are topic names
            if len(line) < 100 and not line.startswith('-') and not line.startswith('•'):
                if current_topic:
                    topics.append(current_topic)
                current_topic = Topic(
                    name=line,
                    summary=f"Content about {line}",
                    key_points=[]
                )
            elif current_topic and (line.startswith('-') or line.startswith('•')):
                # This is a key point
                key_point = line.lstrip('-•').strip()
                current_topic.key_points.append(key_point)
        
        if current_topic:
            topics.append(current_topic)
        
        # If no topics found, create a single topic with all text
        if not topics:
            topics.append(Topic(
                name="Main Content",
                summary=syllabus_text[:200] + "..." if len(syllabus_text) > 200 else syllabus_text,
                key_points=lines[:5] if len(lines) >= 5 else lines
            ))
        
        return topics


def create_subject_folder(subject_name: str, base_path: str = "data/subjects") -> str:
    """
    Create a folder structure for a subject.
    
    Args:
        subject_name: Name of the subject
        base_path: Base directory for subjects
        
    Returns:
        Path to the created subject folder
    """
    # Sanitize subject name for folder
    safe_name = subject_name.lower().replace(" ", "_").replace("/", "_")
    subject_path = Path(base_path) / safe_name
    
    # Create folder structure
    subject_path.mkdir(parents=True, exist_ok=True)
    (subject_path / "syllabus").mkdir(exist_ok=True)
    (subject_path / "questions").mkdir(exist_ok=True)
    (subject_path / "notes").mkdir(exist_ok=True)
    (subject_path / "animations").mkdir(exist_ok=True)
    (subject_path / "mindmaps").mkdir(exist_ok=True)
    
    return str(subject_path)
