"""
Module for RAG (Retrieval Augmented Generation) functionality.
Includes PDF text extraction (with OCR fallback) and YouTube search integration.
"""
import time
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from pathlib import Path
import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
from core.models import Topic, Question
from visual.cli_viz import single_line_viz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from DrissionPage import ChromiumPage
    HAS_DRISSION = True
except ImportError:
    HAS_DRISSION = False
    logger.warning("DrissionPage not found. YouTube search will be limited.")

# --- PDF Extraction Logic (from new_rag.py) ---

def ocr_page(page: fitz.Page):
    """
    Perform OCR on a PDF page using Tesseract.
    """
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # pytesseract.image_to_data returns detailed data including coordinates
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    ocr_lines = []
    high = []
    prob = ""

    # Basic logic to reconstruct lines/words
    for i, text in enumerate(data["text"]):
        if text.strip():
            try:
                # heuristic: if next two are empty, might be end of a block/line
                if (i + 2 < len(data["text"])) and data["text"][i+1]=="" and data["text"][i+2]=="":
                    for j in range(10): # look ahead a bit
                        if i+j < len(data["text"]) and data["text"][i+j] == ' ':
                            break
                        if i+j < len(data["text"]):
                             prob += data["text"][i+j] + " "
                
                if prob != "":
                    # Check if word number jumped (new line/block)
                    if i > 0 and data["word_num"][i] > data["word_num"][i-1] + 1:
                        pass # break logic in original, simplified here
                    high.append(prob.strip())
                
                prob = ""
            except Exception:
                pass
            
            ocr_lines.append({
                "text": text.strip(),
                "x": data["left"][i],
                "y": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i]
            })

    # Clean up 'high' list (reconstructed lines/headings)
    new_hight = [i for h in high for i in h.split()]
    no_dup = []
    for i in range(len(new_hight)):
        try:
            if i+1 < len(new_hight) and new_hight[i] == new_hight[i+1]:
                continue
            else:
                no_dup.append(new_hight[i])
        except Exception:
            pass
    
    return ocr_lines, [i for i in no_dup if len(i) > 1]


def looks_like_heading(text: str) -> bool:
    """Heuristic to check if text looks like a heading."""
    if len(text) < 3: return False
    if text.isdigit(): return False
    if text.istitle() or text.isupper():
        return True
    return False


def extract_topics_scanned(pdf_path: str) -> Dict[str, List[int]]:
    """
    Extract topics and their page ranges from a scanned PDF.
    Uses OCR if text layer is missing.
    """
    doc = fitz.open(pdf_path)
    topic_ranges = {}
    current_topic = None

    for page_num, page in enumerate(doc, start=1):
        # raw = page.get_text("dict")["blocks"]
        # In this implementation, we force OCR/checking or use the hybrid approach
        # For now, sticking to the provided new_rag.py logic which used OCR heavily
        
        try:
            lines, high = ocr_page(page)
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {e}")
            continue

        for line in high:
            txt = line
            if looks_like_heading(txt):
                current_topic = txt
                if current_topic not in topic_ranges:
                    topic_ranges[current_topic] = []
                topic_ranges[current_topic].append(page_num)
        
        if current_topic in topic_ranges:
            # Add next page as continuation (heuristic)
            topic_ranges[current_topic].append(page_num + 1)
            
    return topic_ranges

# --- YouTube Search Logic ---

class YouTubeSearcher:
    """
    Helper to search YouTube for educational content using DrissionPage.
    """
    def __init__(self):
        self.page = None
        if HAS_DRISSION:
            # Initialize lazily or on demand to avoid opening browser immediately
            pass

    def search_and_get_subtitles(self, course_name: str, topic: str, university: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search YouTube and attempt to get subtitles (mock/placeholder).
        """
        query = f"{course_name} {topic}"
        if university:
            query += f" {university}"

            
        logger.info(f"Searching YouTube for: {query}")
        encoded_query= quote(query)
        results = []
        
        if HAS_DRISSION:
            try:
                # Placeholder for DrissionPage logic
                self.page = ChromiumPage()
                self.page.get(f"https://www.youtube.com/results?search_query={encoded_query}")
                # ... extract video links and subtitles ...
                single_line_viz("Choose video!!...")
                time.sleep(10)
                # Since we can't fully run a browser in this headless/cli env often, 
                # this serves as the structural placeholder requested.
                
                # Mock result
                results.append({
                    "title": f"Lecture on {topic}",
                    "url": "https://youtube.com/watch?v=placeholder",
                    "subtitles": f"This is a placeholder subtitle transcript for {topic}..."
                })
            except Exception as e:
                logger.error(f"YouTube search failed: {e}")
        else:
            logger.warning("DrissionPage not installed. Returning empty results.")
            
        return results

# --- Main RAG Engine ---

class RAGEngine:
    """
    RAG engine to answer questions based on knowledge base.
    """
    def __init__(self, knowledge_base=None):
        self.knowledge_base = knowledge_base
        self.youtube_searcher = YouTubeSearcher()
    
    def ingest_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Ingest a PDF, extracting text/topics even if scanned.
        """
        logger.info(f"Ingesting PDF: {pdf_path}")
        try:
            topics_map = extract_topics_scanned(pdf_path)
            return {"status": "success", "topics_map": topics_map}
        except Exception as e:
            logger.error(f"Failed to ingest PDF: {e}")
            return {"status": "error", "message": str(e)}

    def search_multimedia(self, topic_name: str, course_context: str, university_context: str = ""):
        """
        Search for multimedia content (YouTube) for a topic.
        """
        return self.youtube_searcher.search_and_get_subtitles(course_context, topic_name, university_context)

    def query(self, question: str, context: Optional[List[Topic]] = None) -> str:
        """
        Query the knowledge base with a question.
        """
        if context:
            context_text = "\n".join([f"- {topic.name}: {topic.summary}" for topic in context])
            return f"Based on the available topics:\n{context_text}\n\nQuestion: {question}\n\n(Placeholder Answer)"
        
        return "RAG engine not configured."
    
    def generate_questions(self, topic: Topic, num_questions: int = 5) -> List[Question]:
        """
        Generate practice questions for a topic.
        """
        questions = []
        if topic.key_points:
            for i in range(min(num_questions, len(topic.key_points))):
                questions.append(Question(
                    topic=topic.name,
                    question=f"Explain {topic.key_points[i]}.",
                    answer=f"Detailed explanation of {topic.key_points[i]}.",
                    difficulty="medium",
                    type="open_ended"
                ))
        return questions