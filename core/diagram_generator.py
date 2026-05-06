"""
Module for generating conceptual Mermaid diagrams using Gemini AI via LangChain.
Focuses on educational/conceptual understanding of topics.
"""
import json
import logging
import os
import time
from typing import List, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted
from tenacity import (
    retry, retry_if_exception_type, stop_after_attempt,
    wait_exponential, before_sleep_log
)

from .models import MermaidDiagram, ConceptDiagramSet
from .gemini_processor import SimpleGeminiCache

logger = logging.getLogger(__name__)


DIAGRAM_PROMPT_TEMPLATE = """You are an expert educator creating visual study aids for a university student.

Given the following topic notes, generate conceptual Mermaid diagrams that help the student **understand** the topic deeply — not just memorize it.

**Topic:** {topic_name}
**Module:** {module_name}
**Subject:** {subject_name}

**Notes Content:**
{markdown_content}

Generate 2-3 Mermaid diagrams that best explain this topic conceptually. Choose the most appropriate diagram types from:
- `flowchart` — for processes, algorithms, decision flows, compilation phases
- `graph` — for concept relationships and dependencies
- `stateDiagram-v2` — for state transitions (e.g., parser states, automata)
- `sequenceDiagram` — for step-by-step interactions between components
- `mindmap` — for topic hierarchies and sub-concept breakdowns
- `classDiagram` — for showing structure/relationships between entities

Rules:
1. Each diagram must be **syntactically valid Mermaid** — test it mentally before outputting.
2. Focus on **conceptual clarity** — show HOW things work, WHY they relate, WHAT the flow is.
3. Use descriptive labels on edges/arrows to explain relationships.
4. Keep diagrams readable — no more than 15 nodes per diagram.
5. Do NOT wrap the scripts in markdown code fences.

Also identify the key conceptual relationships between concepts in this topic.

Return your response as a valid JSON object with this exact structure:
{{
  "topic_name": "{topic_name}",
  "summary": "One-line conceptual summary",
  "diagrams": [
    {{
      "type": "flowchart",
      "title": "Descriptive Title",
      "script": "flowchart TD\\n    A[Start] --> B[Step]"
    }}
  ],
  "relationships": [
    {{
      "from_concept": "Concept A",
      "to_concept": "Concept B",
      "relationship": "produces"
    }}
  ]
}}
"""


class MermaidDiagramGenerator:
    """
    Generates conceptual Mermaid diagrams for topics using Gemini AI.
    Uses the same retry/rate-limiting pattern as QuestionPaperAnalyzer.
    """

    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Set it via env or pass directly.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,  # Slightly creative for diagram generation
            google_api_key=api_key
        )
        self.cache = SimpleGeminiCache()

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=15, min=30, max=120),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def generate_diagrams(
        self,
        topic_name: str,
        markdown_content: str,
        module_name: str = "",
        subject_name: str = ""
    ) -> ConceptDiagramSet:
        """
        Generate conceptual diagrams for a topic from its markdown notes.

        Args:
            topic_name: Name of the topic
            markdown_content: The topic's markdown notes content
            module_name: Name of the parent module
            subject_name: Name of the subject

        Returns:
            ConceptDiagramSet with diagrams and relationships
        """
        prompt = DIAGRAM_PROMPT_TEMPLATE.format(
            topic_name=topic_name,
            module_name=module_name,
            subject_name=subject_name,
            markdown_content=markdown_content
        )

        # Check cache first
        cache_key_model = "gemini-2.5-flash-diagrams"
        cached = self.cache.get(prompt, cache_key_model)

        if cached:
            response_text = cached
        else:
            try:
                response = self.llm.invoke(prompt)
                response_text = response.content
                self.cache.set(prompt, cache_key_model, response_text)
            except ResourceExhausted:
                raise  # Let tenacity handle retry
            except Exception as e:
                logger.error(f"Error generating diagrams for '{topic_name}': {e}")
                # Return a fallback empty set
                return ConceptDiagramSet(
                    topic_name=topic_name,
                    summary=f"Failed to generate diagrams: {e}",
                    diagrams=[],
                    relationships=[]
                )

        # Parse the response
        return self._parse_response(response_text, topic_name)

    def _parse_response(self, response_text: str, topic_name: str) -> ConceptDiagramSet:
        """Parse Gemini's JSON response into a ConceptDiagramSet."""
        try:
            # Clean up potential markdown fences
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            result = ConceptDiagramSet.model_validate_json(cleaned)
            return result

        except Exception as e:
            logger.error(f"Failed to parse diagram response for '{topic_name}': {e}")
            # Try a best-effort fallback: extract any mermaid-looking content
            return ConceptDiagramSet(
                topic_name=topic_name,
                summary=f"Parse error — raw response saved",
                diagrams=[MermaidDiagram(
                    type="mindmap",
                    title=f"{topic_name} (raw)",
                    script=f"mindmap\n  root(({topic_name}))\n    Parse error"
                )],
                relationships=[]
            )
