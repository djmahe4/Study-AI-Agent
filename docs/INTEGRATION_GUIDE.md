# 🔌 Integration Guide

## Where to Add Your Implementations

### 1. Gemini API Integration

**File:** `core/gemini_processor.py`

**What to do:**
```python
# Replace the __init__ method:
def __init__(self, api_key: Optional[str] = None):
    self.api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    # ADD THIS:
    import google.generativeai as genai
    genai.configure(api_key=self.api_key)
    self.model = genai.GenerativeModel('gemini-pro')
```

**Replace the placeholder method:**
```python
def process_syllabus_text(self, syllabus_text: str, subject_name: str) -> Syllabus:
    # ADD THIS:
    prompt = self._create_extraction_prompt(syllabus_text, subject_name)
    response = self.model.generate_content(prompt)
    syllabus_data = self._parse_gemini_response(response.text)
    
    # Parse the JSON response into Topic objects
    topics = [Topic(**topic_data) for topic_data in syllabus_data.get("topics", [])]
    
    return Syllabus(
        title=subject_name,
        description=f"Syllabus for {subject_name}",
        topics=topics
    )
```

**Environment Setup:**
```bash
# Add to .env file
GEMINI_API_KEY=your_api_key_here
```

**Install dependency:**
```bash
pip install google-generativeai
```

---

### 2. RAG Tool for Question Banks

**File:** `core/rag.py`

**What to do:**
```python
def __init__(self, knowledge_base=None):
    self.knowledge_base = knowledge_base
    
    # ADD THIS:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import PyPDFLoader
    
    self.embeddings = OpenAIEmbeddings()
    self.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    self.vector_store = None
```

**Add PDF loading method:**
```python
def load_question_bank(self, pdf_path: str):
    """Load and process question bank PDF."""
    from langchain.document_loaders import PyPDFLoader
    
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # Split into chunks
    texts = self.text_splitter.split_documents(documents)
    
    # Create vector store
    self.vector_store = FAISS.from_documents(texts, self.embeddings)
    
    return len(texts)
```

**Update query method:**
```python
def query(self, question: str, context: Optional[List[Topic]] = None) -> str:
    if not self.vector_store:
        return "No question bank loaded. Use load_question_bank() first."
    
    # ADD THIS:
    from langchain.chains import RetrievalQA
    from langchain.llms import OpenAI
    
    # Retrieve relevant context
    docs = self.vector_store.similarity_search(question, k=3)
    
    # Create QA chain
    llm = OpenAI(temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=self.vector_store.as_retriever(),
        return_source_documents=True
    )
    
    # Get answer
    result = qa_chain({"query": question})
    
    return result["result"]
```

**Install dependencies:**
```bash
pip install langchain openai faiss-cpu pypdf
```

**Environment setup:**
```bash
# Add to .env
OPENAI_API_KEY=your_api_key_here
```

---

### 3. Update create-subject Command

**File:** `cli.py`

**In the `create_subject` command, add RAG initialization:**
```python
# After creating subject, around line 120
if qbank_path:
    console.print("[cyan]Initializing RAG engine for question bank...[/cyan]")
    
    # ADD THIS:
    rag_engine = RAGEngine()
    num_chunks = rag_engine.load_question_bank(qbank_path)
    
    console.print(f"[green]Loaded {num_chunks} chunks from question bank[/green]")
    
    # Save RAG index
    rag_engine.vector_store.save_local(f"{subject_folder}/questions/rag_index")
```

---

### 4. Connect React CLI to Backend (Optional)

**Create a simple API:**

**File:** `api.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import KnowledgeBase
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb = KnowledgeBase()

@app.get("/api/subjects")
def get_subjects():
    with open("data/subjects/subjects.json") as f:
        return json.load(f)

@app.get("/api/topics")
def get_topics():
    return [t.dict() for t in kb.get_topics()]

# Add more endpoints as needed
```

**Run API:**
```bash
pip install fastapi uvicorn
uvicorn api:app --reload --port 8000
```

**Update React CLI:**

**File:** `frontend/src/Terminal.jsx`
```javascript
// Replace handleSubjects with API call
const handleSubjects = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/subjects');
    const subjects = await response.json();
    // Process and display subjects
  } catch (error) {
    addOutput(['Error fetching subjects:', error.message]);
  }
}
```

---

## Quick Start with Your API Keys

1. **Create `.env` file:**
```bash
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
```

2. **Install additional dependencies:**
```bash
pip install google-generativeai langchain openai faiss-cpu pypdf python-dotenv
```

3. **Update imports in files:**
```python
from dotenv import load_dotenv
load_dotenv()
```

4. **Test Gemini integration:**
```bash
python cli.py create-subject "Test" --syllabus-file data/sample_syllabus.txt
```

5. **Test RAG integration:**
```bash
python cli.py create-subject "Test RAG" \
  --syllabus-file data/sample_syllabus.txt \
  --question-bank @data/sample_questions.txt
```

---

## Testing Your Integration

**Test Gemini:**
```python
# test_gemini.py
from core.gemini_processor import GeminiProcessor

processor = GeminiProcessor()
syllabus = processor.process_syllabus_text("Machine Learning\n- Supervised\n- Unsupervised", "ML")
print(f"Extracted {len(syllabus.topics)} topics")
for topic in syllabus.topics:
    print(f"- {topic.name}: {len(topic.key_points)} key points")
```

**Test RAG:**
```python
# test_rag.py
from core.rag import RAGEngine

rag = RAGEngine()
rag.load_question_bank("data/sample_questions.txt")
answer = rag.query("What is supervised learning?")
print(answer)
```

---

## Troubleshooting

### Gemini API Issues
- Check API key is valid
- Verify API quota/limits
- Handle rate limiting (add retry logic)
- Parse JSON from markdown code blocks

### RAG Issues
- Ensure PDF is text-based (not scanned images)
- Adjust chunk_size for better results
- Try different embedding models
- Check OpenAI API quota

### Integration Tips
- Start with small test files
- Log intermediate outputs
- Add error handling for API failures
- Cache results to avoid repeated API calls
- Add progress indicators for long operations

---

## File Locations Summary

```
Study-AI-Agent/
├── core/
│   ├── gemini_processor.py    ← Add Gemini API here
│   └── rag.py                 ← Add RAG/LangChain here
├── cli.py                     ← Update commands to use RAG
├── api.py                     ← Create for backend API (optional)
├── .env                       ← Add API keys here (create this)
└── frontend/src/Terminal.jsx  ← Connect to API (optional)
```

---

## Next Steps

1. ✅ Get API keys (Gemini, OpenAI)
2. ✅ Create `.env` file
3. ✅ Install additional dependencies
4. ✅ Implement Gemini in `gemini_processor.py`
5. ✅ Implement RAG in `rag.py`
6. ✅ Test with sample data
7. ✅ Update CLI commands
8. ✅ Build more animations
9. ✅ Add your custom features!

**You have the foundation - now make it yours!** 🚀
