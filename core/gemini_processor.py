"""
Module for processing syllabus text using Gemini AI.
"""
import json
from typing import Optional
from pathlib import Path
import logging
from .models import Syllabus, Topic#,InitialSyllabus
import google.generativeai as genai
from pydantic import BaseModel as PydanticModel
import json


class GeminiProcessor:
    """
    Processes syllabus text using Gemini AI to extract structured data.
    
    TODO: Integrate with actual Gemini API
    TODO: Add API key management
    TODO: Add error handling and retries
    TODO: Support different prompts for various educational domains
    """
    
    #def __init__(self, api_key: Optional[str] = None):
        #self.api_key = api_key
    def __init__(self, model: genai.GenerativeModel):
        """
        Initialize GeminiProcessor with a Gemini model.
        """
        # import google.generativeai as genai
        # genai.configure(api_key=api_key)
        self.model = model#genai.GenerativeModel('gemini-pro')
    
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
        prompt_res = self._create_extraction_prompt(syllabus_text, subject_name)
        # response = self.model.generate_content(prompt)
        # syllabus_data = self._parse_gemini_response(prompt_res)
        return prompt_res
        # Placeholder implementation - parses text manually
        # topics = self._extract_topics_placeholder(syllabus_text)
        #
        # return Syllabus(
        #     title=subject_name,
        #     description=f"Syllabus for {subject_name}",
        #     topics=topics
        # )
    
    def _create_extraction_prompt(self, syllabus_text: str, subject_name: str) -> str:
        """
        Create a prompt for Gemini to extract structured syllabus data.
        
        TODO: Refine prompt for better extraction
        TODO: Add few-shot examples
        """
        prompt_text=f"""
Extract structured learning content from the following syllabus text for the subject "{subject_name}".

Syllabus Text:
{syllabus_text}

Return the result as a JSON object with this structure:
```json
{Syllabus.schema_json(indent=2)}
```
"""
        return call_gemini(self.model, prompt_text,Syllabus.schema_json(indent=2))
    
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
    
    # def _extract_topics_placeholder(self, syllabus: Syllabus) -> list[Topic]:
    #     """
    #     Placeholder method to extract topics from text.
    #     This will be replaced by actual Gemini processing.
    #     """
    #
    #
    #     if current_topic:
    #         topics.append(current_topic)
    #
    #     # If no topics found, create a single topic with all text
    #     if not topics:
    #         topics.append(Topic(
    #             name="Main Content",
    #             summary=syllabus_text[:200] + "..." if len(syllabus_text) > 200 else syllabus_text,
    #             key_points=lines[:5] if len(lines) >= 5 else lines
    #         ))
    #
    #     return topics


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


def call_gemini(model: genai.GenerativeModel, prompt: str,schema: PydanticModel) -> str:
    """
    Call Gemini model with a prompt and return the response text.

    Args:
        model: Gemini GenerativeModel instance
        prompt: Prompt string
        schema: Pydantic model schema for response formatting

    Returns:
        Response as parsed Pydantic model
    """
    #final_prompt = prompt.format(schema=schema)
    response = model.generate_content(prompt)
    raw_text = response.text
    json_string = raw_text.strip().lstrip('```json').rstrip('```').strip()
    parsed_json = PydanticModel.parse_raw(schema,json_string)
    try:
        with open(f"{schema.__class__.__name__}.json", "w",encoding="utf-8") as f:
            json.dump(parsed_json.dict(), f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        logging.error(f"Error saving JSON file: {e}")
    return parsed_json