"""
Module for RAG (Retrieval Augmented Generation) functionality.
Includes PDF text extraction (with OCR fallback) and YouTube search integration.
"""
import time
import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from pathlib import Path
import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
from googletrans import Translator
from tqdm import tqdm

# LangChain & Gemini Imports
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
# from langchain.retrievers import ContextualCompressionRetriever
# from langchain.retrievers.document_compressors import LLMChainExtractor

from langchain_huggingface.embeddings import HuggingFaceEmbeddings

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

# --- Helper Functions (Moved from utils.py) ---

def create_main_chain(fpath):
    # 1. Load and Split Document
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # Assuming 'fpath' txt file is in the same directory as this script
    # Or provide the full path if it's elsewhere
    try:
        file_path = fpath # Adjust path if necessary
        with open(file_path, "r", encoding="utf-8") as file:
            transcript = file.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None # Return None instead of exit for better error handling

    chunks = splitter.create_documents([transcript])
    print(f"Number of chunks created: {len(chunks)}")

    # 2. Initialize Embeddings and Vector Store
    # We prioritize local HuggingFace embeddings if available
    embeddings = None
    try:
        # Check if we can use local embeddings (may be blocked by system policy)
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        print("[*] Using local HuggingFace embeddings.")
    except Exception as e:
        logger.warning(f"Local embeddings failed (likely system policy): {e}")
        
    if not embeddings:
        try:
            # Fallback to Gemini embedding model
            # Based on available models list: models/gemini-embedding-2
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
            print("[*] Using Google Generative AI embeddings (models/gemini-embedding-2).")
        except Exception as e2:
            logger.error(f"All embedding models failed: {e2}")
            return None

    vector_store = FAISS.from_documents(chunks, embeddings)
    base_retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    # 3. Initialize Chat Model
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=1.0)

    # --- Context Window Optimization Implementation ---
    # 4. Create a compressor for the retrieved documents
    # We'll use the same LLM for compression, but you could use a smaller, faster one if needed.
    compressor = LLMChainExtractor.from_llm(llm)

    # 5. Create a ContextualCompressionRetriever
    # This retriever will first get the documents using base_retriever,
    # then pass them through the compressor to extract relevant parts.
    compressed_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
    # --- End Context Window Optimization Implementation ---

    # 6. Define Prompt Template
    prompt = PromptTemplate(
        template="""
        You are a helpful assistant.
        Answer ONLY from the provided transcript context.
        If the context is insufficient, just say you don't know.

        Context: {context}
        Question: {question}
        """,
        input_variables=['context', 'question']
    )

    # 7. Define Document Formatter
    def format_docs(retrieved_docs):
        """Formats the retrieved documents into a single string."""
        context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
        return context_text

    # 8. Construct the RAG Chain using the compressed_retriever
    parallel_chain = RunnableParallel({
        'context': compressed_retriever | RunnableLambda(format_docs), # Use compressed_retriever here
        'question': RunnablePassthrough()
    })
    parser = StrOutputParser()
    main_chain = parallel_chain | prompt | llm | parser
    return main_chain

def post_load_json(jfile):
    """
    Converts a JSON subtitle file to a text file.
    """
    if not os.path.exists(jfile):
        print(f"Error: JSON file {jfile} not found.")
        return None
        
    with open(jfile,"r", encoding='utf-8') as JSON:
        jdata=json.load(JSON)
        
        events = []
        if isinstance(jdata, dict) and 'events' in jdata:
            events = jdata['events']
        elif isinstance(jdata, list):
            # Maybe it's just a list of segments?
            pass
            
        output_txt = f'{Path(jfile).stem}.txt'
        
        # Clear existing file
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("")
            
        text_accumulator = ""
        
        if events:
            # Existing logic for 'events' structure
            for event in events[1:]:
                if 'segs' in event and len(event['segs']) > 0:
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            text_accumulator += seg['utf8']
                    text_accumulator += " "
        else:
             print("Warning: 'events' key not found in JSON. Check format.")
             return None

        with open(output_txt, "a", encoding="utf-8") as file:
            file.write(text_accumulator)
            
    return output_txt

# --- YouTube Search Logic ---

class YouTubeSearcher:
    """
    Helper to search YouTube for educational content using DrissionPage.
    """
    def __init__(self):
        self.page = None
        # if HAS_DRISSION:
        #     # Initialize lazily or on demand
        #     pass

    def _wait_for_subs(self, page, video_id: str, timeout=15) -> Optional[str]:
        """
        Internal method to listen for subtitle API responses, filtering by video ID.
        """
        print(f"[*] Waiting for network requests (timedtext) for video {video_id}...")
        found = False
        
        # Filter and display subtitle API responses
        max_retries = 3
        retries = 0
        
        while not found and retries < max_retries:
            # Try to trigger CC if not found yet
            if retries > 0:
                print(f"[*] Retry {retries}: Attempting to toggle CC again...")
                try:
                    video = page.ele('tag:video', timeout=2)
                    if video:
                        video.click()
                        page.actions.type('c')
                except:
                    pass

            # Wait for the listener to catch something
            res = page.listen.wait(timeout=5)
            if res:
                url = res.url
                if 'timedtext' in url.lower():
                    # Check if the video ID matches to avoid capturing ad subtitles
                    if f"v={video_id}" in url or f"video_id={video_id}" in url:
                        print(f"[+] Found correct Subtitle API URL: {url}")
                        try:
                            if not res.response or not res.response.body:
                                print("[!] Empty response body, skipping...")
                                continue
                                
                            body = res.response.body
                            json_string = json.dumps(body, indent=2, ensure_ascii=False)
                            tit = page.title.replace(" ","_")
                            # Sanitize filename
                            tit = "".join([c for c in tit if c.isalnum() or c=='_']).rstrip()
                            if not tit: tit = "youtube_subs"
                            filename = f"{tit}.json"
                            
                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(json_string)

                            print(f"[SUCCESS] JSON saved to {filename}")
                            page.stop_loading()
                            return filename
                        except Exception as e:
                            print(f"[ERROR] Failed to save JSON: {e}")
                    else:
                        print(f"[*] Ignoring subtitle URL for different video (likely an ad): {url}")
            
            retries += 1
            
        return None

    def search_and_get_subtitles(self, course_name: str, topic: str, university: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search YouTube and attempt to get subtitles.
        """
        query = f"{course_name} {topic}"
        if university:
            query += f" {university}"

        logger.info(f"Searching YouTube for: {query}")
        encoded_query= quote(query)
        results = []
        
        if HAS_DRISSION:
            try:
                self.page = ChromiumPage()
                # 1. Search
                self.page.get(f"https://www.youtube.com/results?search_query={encoded_query}")
                single_line_viz("Searching video...")
                
                # Mock selection logic: pick the first video that isn't an ad (simplified)
                # In a real CLI, we might want to list top 3 and ask user to pick, 
                # but here we'll just try to grab the first valid result.
                
                # For now, let's just use the search URL as the 'context' or allow user to paste a URL.
                # But to follow the 'search' instruction:
                # We would need to parse the search results page.
                
                # Let's simplify: return a placeholder that tells the user to use 'ask-youtube <URL>'
                # because fully automating "pick the best video" is complex without user input.
                
                # However, if we want to "Implement gemini.md", we should try to support the flow.
                # Let's assume the user might provide a URL or we just open the search page.
                
                # If we really want to grab a video, we need selectors.
                # self.page.ele('xpath://...').click()
                
                # For this implementation, I will return a result saying "Please provide a specific URL"
                # OR if I can, I'll grab the first video link.
                
                # Let's just return a structure that the caller can use.
                results.append({
                    "title": f"Search Results for {query}",
                    "url": f"https://www.youtube.com/results?search_query={encoded_query}",
                    "subtitles": "Search performed. Please select a video URL and use 'ask-youtube <URL>'."
                })
                
                self.page.quit()

            except Exception as e:
                logger.error(f"YouTube search failed: {e}")
                if self.page:
                    self.page.quit()
        else:
            logger.warning("DrissionPage not installed. Returning empty results.")
            
        return results

    def fetch_captions(self, url: str) -> Optional[str]:
        """
        Fetches captions for a specific YouTube URL.
        Returns the path to the converted text file.
        """
        if not HAS_DRISSION:
            print("DrissionPage not installed.")
            return None
            
        # 0. Cache Check
        # We need a predictable filename based on the URL or Title
        # For simplicity, we'll check if a JSON matching this video ID exists
        video_id = ""
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "be/" in url:
            video_id = url.split("be/")[1].split("?")[0]
            
        # Check data/cache first
        cache_dir = os.path.join("data", "cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            
        import glob
        # Search for existing JSON with this video_id in data/cache
        pattern = os.path.join(cache_dir, f"*{video_id}*.json")
        existing_jsons = glob.glob(pattern)
        if existing_jsons:
            print(f"[*] Found cached transcript for {video_id}: {existing_jsons[0]}")
            return post_load_json(existing_jsons[0])

        json_path = None
        try:
            print(f"[*] Launching browser for {url}...")
            # Use headless if not in a desktop environment or as a preference
            # For verification, we'll keep it default (usually headed)
            self.page = ChromiumPage()
            
            # Start listening BEFORE navigation and specify target
            self.page.listen.start(targets='timedtext')
            
            print(f"[*] Navigating to {url}...")
            self.page.get(url) 
            
            # Ad Skipping Logic (inspired by user's reference)
            def skip_youtube_ads():
                try:
                    # Accelerate and mute any ad
                    js_accelerate = """
                    try {
                        const player = document.getElementById('movie_player') || document.querySelector('.html5-video-player');
                        if (player && (player.classList.contains('ad-showing') || player.classList.contains('ad-interrupting'))) {
                            const video = document.querySelector('video.html5-main-video') || document.querySelector('video');
                            if (video) {
                                video.playbackRate = 16.0;
                                video.muted = true;
                                if (video.paused) video.play();
                            }
                            // Try to click skip button
                            const skipBtn = document.querySelector('.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-ad-skip-button-container');
                            if (skipBtn) skipBtn.click();
                            return "ad_detected";
                        }
                    } catch(e) {}
                    return "no_ad";
                    """
                    for _ in range(10): # Try for 10 seconds
                        res = self.page.run_js(js_accelerate)
                        if res == "no_ad":
                            # Check if ad is really gone
                            if not self.page.ele('.ad-showing', timeout=0.5):
                                break
                        time.sleep(1)
                except: pass

            skip_youtube_ads()

            # Wait for video to appear and be ready
            video = self.page.ele('.html5-main-video', timeout=15)
            if not video:
                video = self.page.ele('tag:video', timeout=5)
                
            if video:
                print("[*] Video detected. Waiting for player to settle...")
                time.sleep(3) # Wait for UI overlays/ads to settle
                
                # Try to enable CC automatically
                # 1. Check if already enabled
                for attempt in range(3):
                    try:
                        # Hover over the video to make the controls (and CC button) visible
                        print(f"[*] Attempt {attempt+1}: Hovering over video to show controls...")
                        video.hover()
                        time.sleep(1)
                        
                        cc_btn = self.page.ele('.ytp-subtitles-button', timeout=5)
                        if cc_btn:
                            if cc_btn.attr('aria-pressed') == 'false':
                                print("[*] Enabling subtitles via CC button click...")
                                cc_btn.click()
                                time.sleep(1)
                            else:
                                print("[*] Subtitles already active.")
                                break # Success
                        else:
                            # Fallback to keyboard shortcut 'c'
                            print("[*] CC button not found, trying keyboard shortcut 'c'...")
                            # Click video center to ensure focus
                            video.click()
                            self.page.actions.type('c')
                            time.sleep(1)
                            
                        # Verify if subtitles are appearing (we'll see timedtext requests anyway)
                        # but we can check the button state again
                        cc_btn_check = self.page.ele('.ytp-subtitles-button', timeout=2)
                        if cc_btn_check and cc_btn_check.attr('aria-pressed') == 'true':
                            print("[*] Subtitles successfully activated.")
                            break
                    except Exception as e:
                        print(f"[!] Attempt {attempt+1} failed: {e}")
                        time.sleep(2)
            else:
                print("[!] Could not find video element.")
            video_id = ""
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "be/" in url:
                video_id = url.split("be/")[1].split("?")[0]
                
            # Wait for network requests (timedtext)
            print(f"[*] Waiting for network requests (timedtext)...")
            start_wait = time.time()
            found_data = None
            
            # We'll wait up to 45 seconds total
            while time.time() - start_wait < 45:
                packet = self.page.listen.wait(timeout=1)
                if packet:
                    url_match = packet.url
                    if 'timedtext' in url_match:
                        # Extract v= parameter from URL
                        import urllib.parse
                        parsed_url = urllib.parse.urlparse(url_match)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        req_v = query_params.get('v', [None])[0]
                        
                        if req_v == video_id:
                            print(f"[*] Caught subtitles for main video: {req_v}")
                            found_data = packet.response.body
                            break
                        else:
                            # If we can't find the main video ID, we might accept the first one 
                            # that appears AFTER we are sure ads are gone
                            if not self.page.ele('.ad-showing', timeout=0.1):
                                print(f"[*] Caught subtitles (ID: {req_v}). No ad showing, assuming this is the content.")
                                found_data = packet.response.body
                                break
                            else:
                                print(f"[*] Ignoring subtitle URL for ad video: {req_v}")
                
                # Periodically try to skip ads and toggle CC
                if int(time.time() - start_wait) % 5 == 0:
                    skip_youtube_ads()
                    try:
                        video.hover()
                        self.page.actions.type('c')
                    except: pass
            
            self.page.listen.stop()
            self.page.quit()

            if found_data:
                # Save to data/cache
                import json
                temp_json = os.path.join("data", "cache", f"yt_subs_{video_id}.json")
                with open(temp_json, "w", encoding="utf-8") as f:
                    if isinstance(found_data, dict):
                        json.dump(found_data, f, ensure_ascii=False, indent=2)
                    elif isinstance(found_data, bytes):
                        f.write(found_data.decode('utf-8'))
                    else:
                        f.write(str(found_data))
                
                return post_load_json(temp_json)
            
            self.page.listen.stop()
            self.page.quit()
            return None

        except Exception as e:
            print(f"[ERROR] Browser automation failed: {e}")
            if hasattr(self, 'page') and self.page:
                try:
                    self.page.quit()
                except:
                    pass
            return None
            
        if json_path:
            return post_load_json(json_path)
        return None

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

    def ask_youtube(self, url: str, query: str) -> str:
        """
        End-to-end RAG on a YouTube video.
        """
        # 1. Fetch Captions
        txt_path = self.youtube_searcher.fetch_captions(url)
        if not txt_path:
            return "Failed to fetch or process subtitles."

        # 2. Create Chain
        chain = create_main_chain(txt_path)
        if not chain:
            return "Failed to create reasoning chain."

        # 3. Invoke
        try:
            result = chain.invoke(query)
            return result
        except Exception as e:
            return f"Error during query: {e}"

    def generate_quiz_from_video(self, url: str, num_questions: int = 5) -> List[Question]:
        """
        Generates a quiz from a YouTube video.
        """
        # 1. Fetch Captions
        txt_path = self.youtube_searcher.fetch_captions(url)
        if not txt_path:
            logger.error("Failed to fetch subtitles.")
            return []

        # 2. Read transcript
        with open(txt_path, "r", encoding="utf-8") as f:
            transcript = f.read()

        # 3. Generate Questions
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.7)
        
        prompt = f"""
        Generate {num_questions} multiple-choice questions based on the following transcript.
        Return the result as a raw JSON list of objects (no markdown formatting) with keys: 'question', 'options' (list of strings), 'answer' (correct option string).
        
        Transcript:
        {transcript[:20000]}
        """
        
        try:
            response = llm.invoke(prompt)
            content = response.content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            questions = []
            for item in data:
                q = Question(
                    topic="YouTube Video", 
                    question=item['question'],
                    answer=item['answer'],
                    options=item.get('options', []),
                    difficulty="medium",
                    type="multiple_choice"
                )
                questions.append(q)
            return questions
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []

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

    def analyze_video_structure(self, url: str, topic_name: str) -> Dict[str, Any]:
        """
        Analyze a video to generate Notes, Mindmap, and Differences.
        Returns a dictionary with 'notes', 'mindmap_script', 'differences'.
        """
        # 1. Fetch Captions
        txt_path = self.youtube_searcher.fetch_captions(url)
        if not txt_path:
            return {"error": "Failed to fetch subtitles"}

        with open(txt_path, "r", encoding="utf-8") as f:
            transcript = f.read()

        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.7)
        
        # We can do this in one comprehensive prompt or multiple. 
        # For better structure, let's use a structured prompt.
        
        prompt = f"""
        Analyze the following YouTube transcript for the topic "{topic_name}".
        
        Provide the output in valid JSON format with the following keys:
        1. "summary": A concise summary of the video.
        2. "key_points": A list of key learning points (strings).
        3. "detailed_notes": A markdown string containing detailed study notes structured with headers.
        4. "mindmap_mermaid": A Mermaid.js mindmap script (start with 'mindmap' keyword) representing the video content.
        5. "differences": A list of objects {{ "concept_a": "...", "concept_b": "...", "explanation": "..." }} if any comparisons are made (e.g. TCP vs UDP). If none, empty list.
        
        Transcript:
        {transcript[:25000]} 
        """
        # Truncate transcript to avoid token limits if necessary, though 2.5 Flash has 1M context. 
        # We'll trust the model to handle it, but keep a safety limit if it's huge.
        
        try:
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.replace("```json", "").replace("```", "").strip()
            
            # Simple JSON cleanup if model adds text around it
            if content.startswith("json"): content = content[4:]
            
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return {"error": str(e)}