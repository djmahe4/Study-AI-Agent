"""
Module for parsing and analyzing question papers (PYQs).
"""
import fitz  # PyMuPDF
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from google.genai import types
from icecream import ic
ic.disable()
from core.models import ExamPattern, AnalyzedQuestion, QuestionBank

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionPaperAnalyzer:
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,  # Deterministic for extraction
            google_api_key=api_key
        )

    def extract_text(self, pdf_path: str) -> str:
        """Extracts text from a PDF file."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def _extract_year_sections(self, text: str, default_year: str) -> List[Tuple[str, str]]:
        """
        Splits the text into sections based on detected year headers using regex.
        Each section is a tuple of (inferred_year, section_text).
        """
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = list(re.finditer(year_pattern, text))

        if not matches:
            return [(default_year, text)]

        sections = []
        positions = [m.start() for m in matches]

        for i in range(len(positions) + 1):
            start = positions[i - 1] if i > 0 else 0
            end = positions[i] if i < len(positions) else len(text)
            section_text = text[start:end].strip()

            if not section_text:
                continue

            # Infer year for this section: use the year at the start of the section
            year_match = re.search(year_pattern, section_text[:500])  # Check first 500 chars for header
            year = year_match.group(1) if year_match else default_year
            sections.append((year, section_text))

        return sections

    def parse_questions_from_text(self, text: str, year: str, paper_name: str) -> List[AnalyzedQuestion]:
        """
        Uses Gemini to extract structured questions from raw text.
        """
        # Chunking strategy: If text is too long, we might need to split.
        # But Flash context is huge, so we try sending whole text first.
        # If it fails, we fall back to year-wise splitting.

        base_prompt = """
        Extract all examination questions from the following text, which may contain multiple consecutive question papers from different years.

        For each question, identify:
        - Year: Infer from the nearest header, section title, or context (e.g., '2020' if the question appears under a '2020' paper section). If unclear, use 'Unknown'.
        - Question Number (integer)
        - Part/Sub-question (e.g., 'a', 'b', or null)
        - The exact Text of the question
        - Marks allocated (integer, infer from context if possible, else 0)

        Ignore instructions like "Answer all questions" or extraneous header information.
        Focus on the numbered questions. Group questions by their inferred year where possible.

        Text:
        {}
        """

        structured_llm = self.llm.with_structured_output(QuestionBank)

        try:
            prompt = base_prompt.format(text)
            ic("Invoking LLM for full text parsing...")
            result = structured_llm.invoke(prompt)
            questions = result.questions
            ic(f"LLM returned {len(questions)} questions from full text.")
            # Post-process to add metadata, with fallback for year
            for q in questions:
                if not q.year or q.year == 'Unknown':
                    q.year = year
                q.paper_name = paper_name

            return questions
        except Exception as e:
            logger.warning(f"LLM Extraction on full text failed: {e}. Falling back to year-wise splitting.")

            # Fallback: Split into year sections and parse each
            sections = self._extract_year_sections(text, year)
            all_questions = []

            fallback_prompt_template = """
            Extract all examination questions from the following text section.

            Use the year: {} for all questions in this section.

            For each question, identify:
            - Question Number (integer)
            - Part/Sub-question (e.g., 'a', 'b', or null)
            - The exact Text of the question
            - Marks allocated (integer, infer from context if possible, else 0)

            Ignore instructions like "Answer all questions" or extraneous header information.
            Focus on the numbered questions.

            Text:
            {}
            """

            for sec_year, sec_text in sections:
                if not sec_text.strip():
                    continue
                try:
                    sub_prompt = fallback_prompt_template.format(sec_year, sec_text)
                    sub_result = structured_llm.invoke(sub_prompt)
                    ic("Invoked LLM for year section:", sec_year)
                    sub_questions = sub_result.questions

                    for q in sub_questions:
                        q.year = sec_year
                        q.paper_name = paper_name
                        all_questions.append(q)

                    logger.info(f"Successfully parsed section for year {sec_year} with {len(sub_questions)} questions.")
                except Exception as sub_e:
                    logger.error(f"Failed to parse section for year {sec_year}: {sub_e}")
                    continue

            logger.info(f"Fallback parsing completed. Total questions extracted: {len(all_questions)}")
            return all_questions

    def map_questions_to_modules(self, questions: List[AnalyzedQuestion], pattern: ExamPattern) -> List[
        AnalyzedQuestion]:
        """
        Maps extracted questions to modules based on the provided ExamPattern.
        """
        # Create a reverse mapping for O(1) lookup: Question Number -> Module Name
        # Logic: If pattern says Module 1 has [1, 2, 11], and we have Q1, assign Mod 1.

        q_to_mod = {}
        for mod_name, q_nums in pattern.module_mapping.items():
            ic(f"Mapping questions {q_nums} to module {mod_name}")
            for q_num in q_nums:
                q_to_mod[q_num] = mod_name

        for q in questions:
            if q.number in q_to_mod:
                q.module = q_to_mod[q.number]
            else:
                # Fallback: maybe use Part mapping if strict number mapping fails?
                # For now, strict mapping is requested.
                q.module = "Unknown"
        ic(questions[:2])  # Show first 2 for inspection after mapping
        return questions

    def analyze_paper(self, pdf_path: str, pattern: ExamPattern, year: str = "Unknown") -> List[AnalyzedQuestion]:
        """
        Full pipeline: Extract -> Parse -> Map.
        Supports handling of large PDFs containing multiple consecutive years' question papers by inferring years during parsing,
        with fallback to year-wise splitting if full-text parsing fails.
        """
        text = self.extract_text(pdf_path)
        if not text:
            return []

        raw_qs = self.parse_questions_from_text(text, year, Path(pdf_path).name)
        ic(f"Extracted {len(raw_qs)} questions from paper.")
        ic(raw_qs[:2])  # Show first 2 for inspection
        mapped_qs = self.map_questions_to_modules(raw_qs, pattern)
        ic("After mapping to modules:", mapped_qs[:2])

        return mapped_qs

    def generate_answer(self, question: AnalyzedQuestion, context: str = "") -> str:
        """
        Generates an answer for a specific question, optionally using context.
        """
        # Simple generation for now. RAG context would be passed in if available.
        prompt = f"""
        Answer the following university examination question.
        Question: {question.text}
        Marks: {question.marks}

        Context (Notes):
        {context}

        Provide a concise, point-wise answer suitable for an exam.
        """
        try:
            response = self.llm.invoke(prompt, tools=[types.Tool(google_search=types.GoogleSearch())]
                                       )
            return response.content
        except Exception:
            return "Failed to generate answer."