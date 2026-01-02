import argparse
import os
import json
import time
from pathlib import Path
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
# New imports for context window optimization
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from googletrans import Translator
import asyncio
from tqdm import tqdm

try:
    from DrissionPage import ChromiumPage
    HAS_DRISSION = True
except ImportError:
    HAS_DRISSION = False

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
        print(f"Please ensure '{fpath}' is in the correct directory.")
        return None # Return None instead of exit for better error handling

    chunks = splitter.create_documents([transcript])
    print(f"Number of chunks created: {len(chunks)}")

    # 2. Initialize Embeddings and Vector Store with Google Generative AI
    # Note: Requires google-generativeai to be installed or compatible shim
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_documents(chunks, embeddings)
    base_retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    # 3. Initialize Chat Model with Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1.0)

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

async def new_translate_text_file(input_filepath, output_filepath="", dest_lang='en', src_lang='auto', chunk_size=4000):
    """
    Translates the content of a text file line by line using googletrans asynchronously.

    Args:
        input_filepath (str): The path to the input text file.
        output_filepath (str): The path to save the translated text file.
        dest_lang (str): The target language code (e.g., 'es' for Spanish, 'fr' for French).
        src_lang (str): The source language code (e.g., 'en' for English).
                        'auto' detects the source language automatically.
    """
    output_filepath=f"trans_{{Path(input_filepath).stem}}.txt"
    translator = Translator()
    #translated_lines = []

    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            content=infile.read()

        print(f"Translating '{input_filepath}' from {src_lang.upper()} to {dest_lang.upper()}...")

        try:
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            translated_chunks = []

            print(f"Translating: {os.path.basename(input_filepath)}")
            for chunk in tqdm(chunks, desc="  Chunks", leave=False):
                result = await translator.translate(chunk, src=src_lang, dest=dest_lang)
                translated_chunks.append(result.text)

            translated_content = ' '.join(translated_chunks)
        except Exception as e:
            with open("error_log.txt", "a", encoding="utf-8") as log:
                log.write(f"{input_filepath}: {e}\n")
            translated_content = content

        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            #for translated_line in translated_lines:
                #outfile.write(translated_line + '\n')
            outfile.write(translated_content)

        print(f"\nTranslation complete! Translated text saved to '{output_filepath}'")
        return output_filepath

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'")
        return None
    except Exception as e:
        print(f"An unexpected error during translation occurred: {e}")
        return None

def postLoad(jfile="LearningtoHackA.json"):
    if not os.path.exists(jfile):
        print(f"Error: JSON file {jfile} not found.")
        return None
        
    with open(jfile,"r", encoding='utf-8') as JSON:
        jdata=json.load(JSON)
        # Handle YouTube's json structure if it differs, or standard one
        # The existing code assumed a specific structure: jdata['events']
        
        # If structure matches standard YouTube transcript format (list of dicts)
        # or the 'events' structure from DrissionPage interception (depends on exact API response)
        # Let's try to be robust
        
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
            # Fallback or alternative structure parsing could go here
            # For now, just dumping the raw text if events not found
             print("Warning: 'events' key not found in JSON. Check format.")
             return None

        with open(output_txt, "a", encoding="utf-8") as file:
            file.write(text_accumulator)
            
    return output_txt

def loader(page):
    """
    Loads subtitles from a YouTube video using DrissionPage.
    Expects 'page' to be an instance of ChromiumPage.
    """
    if not HAS_DRISSION:
        print("DrissionPage not installed.")
        return None

    # page.get(url) should be called before this if needed, or passed in
    
    # Start listening to network logs
    page.listen.start()
    
    print("Waiting for network requests...")
    time.sleep(10) # Wait for video to load and subs to fetch
    found=False
    
    # Filter and display subtitle API responses
    # Limited retries to avoid infinite loop in automation
    max_retries = 3
    retries = 0
    
    while not found and retries < max_retries:
        print("!! Click 'CC' button manually to extract subtitles (if running interactively)")
        for step in page.listen.steps():
            if hasattr(step, 'response') and step.response:
                url = step.response.url
                try:
                    content_type = step.response.headers.get('Content-Type', '')
                except:
                    continue
                    
                if 'api' in url.lower() and 'timedtext' in url.lower() and 'json' in content_type:
                    print(f"API URL: {url}")
                    try:
                        body = step.response.body
                        # Check if body is bytes or str
                        if isinstance(body, bytes):
                             # Often connection is compressed, DrissionPage usually handles it but be safe
                             pass
                        
                        json_string = json.dumps(body, indent=2, ensure_ascii=False)
                        tit = page.title.replace(" ","_")
                        filename = f"{tit}.json"
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(json_string)

                        print(f"✅ JSON saved to {filename}")
                        page.stop_loading()
                        return filename
                    except Exception as e:
                        print("❌ Failed to save JSON:", e)
                    
                    found = True
                    break
        
        if not found:
            print("No subtitle API response found yet, retrying...")
            time.sleep(5)
            # page.refresh() # careful with refresh, it might reset the network log
            retries += 1
            
    return None

def youtube_rag_engine(url=None, json_path=None, query=None):
    """
    Orchestrates the YouTube RAG workflow.
    
    Args:
        url (str): YouTube video URL (requires DrissionPage interaction).
        json_path (str): Path to existing subtitle JSON file.
        query (str): Question to ask the RAG chain.
        
    Returns:
        The answer string or the chain object.
    """
    
    if not json_path:
        if url and HAS_DRISSION:
            print(f"Launching browser for {url}...")
            # Note: This part requires a GUI environment or headless setup that works with DrissionPage
            try:
                page = ChromiumPage()
                page.get(f"{url}&cc_load_policy=1") 
                json_path = loader(page)
                page.quit()
            except Exception as e:
                print(f"Browser automation failed: {e}")
                return None
        else:
            print("No JSON path provided and cannot fetch from URL (DrissionPage missing or no URL).")
            return None

    if not json_path or not os.path.exists(json_path):
        print(f"Invalid JSON path: {json_path}")
        return None

    # Process JSON to Text
    print(f"Processing subtitle JSON: {json_path}")
    txt_path = postLoad(json_path)
    
    if not txt_path:
        print("Failed to convert JSON to text.")
        return None
        
    print(f"Subtitle text saved to: {txt_path}")
    
    # Create RAG Chain
    print("Initializing RAG chain...")
    chain = create_main_chain(txt_path)
    
    if not chain:
        print("Failed to create RAG chain.")
        return None
        
    if query:
        print(f"Querying: {query}")
        result = chain.invoke(query)
        return result
    
    return chain
