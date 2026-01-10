"""
Module for processing syllabus text using Gemini AI (google-genai SDK).
"""
import json
import os
import hashlib
import logging
logging.basicConfig(filename='gemini_processor.log', level=logging.INFO)
from typing import Optional, Dict, Any, Union
from pathlib import Path
from .models import Syllabus, Topic
from .utils import normalize_subject_name, get_subject_dir
from google import genai
from google.genai import types
import google.genai
from pydantic import BaseModel as PydanticModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/cache/gemini")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class SimpleGeminiCache:
    """
    A simple file-based cache for Gemini responses to save costs.
    Mimics the intent of prompt-cache for local development.
    """
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir

    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate a unique hash for the prompt and model."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[str]:
        """Retrieve cached response if it exists."""
        key = self._get_cache_key(prompt, model)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Cache hit for prompt hash: {key}")
                    return data.get("response")
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        return None

    def set(self, prompt: str, model: str, response: str):
        """Save response to cache."""
        key = self._get_cache_key(prompt, model)
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"prompt": prompt, "model": model, "response": response}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

class GeminiProcessor:
    """
    Processes syllabus text using Gemini AI to extract structured data.
    Uses the new google-genai SDK.
    """
    
    def __init__(self, client: Optional[genai.Client] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize GeminiProcessor with a Gemini client.
        
        Args:
            client: An initialized google.genai.Client. If None, one will be created.
            model_name: The model to use (default: gemini-2.5-flash).
        """
        if client:
            self.client = client
        else:
            # Assumes GEMINI_API_KEY or GOOGLE_API_KEY is set in environment
            self.client = genai.Client()
            
        self.model_name = model_name
        self.cache = SimpleGeminiCache()
    
    def process_syllabus_text(self, syllabus_text: str, subject_name: str) -> Syllabus:
        """
        Process syllabus text using Gemini to extract structured data.
        
        Args:
            syllabus_text: Raw syllabus text
            subject_name: Name of the subject
            
        Returns:
            Structured Syllabus object
        """
        prompt = self._create_extraction_prompt(syllabus_text, subject_name)
        return self._call_gemini_with_schema(prompt, Syllabus)
    
    def _create_extraction_prompt(self, syllabus_text: str, subject_name: str) -> str:
        """
        Create a prompt for Gemini to extract structured syllabus data with modules.
        """
        return f"""
Extract structured learning content from the following syllabus text for the subject "{subject_name}".
Organize the content into logically defined Modules (or Units) as they appear in the syllabus.

Syllabus Text:
{syllabus_text}

Return the result as a valid JSON object matching the following structure:
{{
  "title": "{subject_name}",
  "description": "Subject Description",
  "modules": [
    {{
      "name": "Module 1: Name",
      "description": "Module overview",
      "order": 1,
      "topics": [
        {{
          "name": "Topic Name",
          "summary": "Brief summary",
          "key_points": ["Point 1", "Point 2"],
          "subtopics": ["Subtopic 1", "Subtopic 2"]
        }}
      ]
    }}
  ]
}}
"""

    def _call_gemini_with_schema(self, prompt: str, schema_cls: Any) -> Any:
        """
        Call Gemini model and parse the response into a Pydantic model.
        Uses local caching to reduce calls.
        """
        # 1. Check Cache
        cached_text = self.cache.get(prompt, self.model_name)
        if cached_text:
             response_text = cached_text
        else:
            # 2. Call API
            try:
                # Using the new SDK's generate_content method
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        #tools=[types.Tool(google_search=types.GoogleSearch())],
                        )
                )
                response_text = response.text
                # 3. Save to Cache
                self.cache.set(prompt, self.model_name, response_text)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}")
                # Fallback or re-raise. For now, re-raise to be handled by caller
                raise e

        # 4. Parse Response
        try:
            # Clean up potential markdown blocks if the model ignored JSON mode (less likely with config)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Using Pydantic's model_validate_json or parse_raw (older pydantic)
            # Checking pydantic version in requirements was 2.5.3, so model_validate_json is preferred
            try:
                parsed_obj = schema_cls.model_validate_json(cleaned_text)
            except AttributeError:
                # Fallback for older Pydantic V1 if environment differs
                parsed_obj = schema_cls.parse_raw(cleaned_text)
                
            # Save debug dump
            try:
                with open(f"{schema_cls.__name__}.json", "w", encoding="utf-8") as f:
                    json.dump(parsed_obj.model_dump(), f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"Could not save debug JSON: {e}")
                print(parsed_obj)
            return parsed_obj
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}\nResponse text: {response_text}")
            raise e

def create_subject_folder(subject_name: str, base_path: str = "data/subjects") -> str:
    """
    Create a folder structure for a subject.
    
    Args:
        subject_name: Name of the subject
        base_path: Base directory for subjects
        
    Returns:
        Path to the created subject folder
    """
    subject_path = get_subject_dir(subject_name, base_path)
    
    # Create folder structure
    subject_path.mkdir(parents=True, exist_ok=True)
    (subject_path / "syllabus").mkdir(exist_ok=True)
    (subject_path / "questions").mkdir(exist_ok=True)
    (subject_path / "notes").mkdir(exist_ok=True)
    (subject_path / "animations").mkdir(exist_ok=True)
    (subject_path / "mindmaps").mkdir(exist_ok=True)
    
    return str(subject_path)
