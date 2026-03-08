# 🧠 Study-AI-Agent: AI Learning Engine

An AI-augmented intelligent learning system that teaches with mind maps, animations, structured knowledge, and interactive learning tools.

**Subject-Based Learning System** - Create subjects, process syllabi with Gemini AI, and integrate question banks with RAG.

## ✨ Features

- **📚 Structured Knowledge**: Pydantic-based data models for organizing learning content
- **🗺️ Mind Maps**: Mermaid.js concepts visualization embedded in Markdown
- **⚡ Persistent LLM Cache**: SQLite-based Gemini caching for instant repeated generations and quota saving
- **🎬 Animations**: AI-generated educational animations (GIF/Video) using OpenCV
- **❓ Quiz Mode**: Interactive Q&A with retrieval practice
- **📊 Difference Tables**: Learning through contrasts and comparisons
- **🧠 Mnemonics**: Memory aids and cognitive learning techniques
- **📝 Exam Analysis**: Automated parsing of PDF question papers and answer generation
- **💻 CLI Interface**: Rich interactive terminal interface
- **🌐 Streamlit UI**: Web-based learning dashboard with schema editing

## 🏗️ Architecture

```
Study-AI-Agent/
├─ data/                    # Data storage
│   ├─ subjects/           # Subject data (syllabus, notes, questions)
│   ├─ exam_patterns/      # Exam structure definitions
│   └─ memory.db           # SQLite knowledge base
├─ core/                    # Core Python modules
│   ├─ models.py           # Pydantic models (Topic, ExamPattern, etc.)
│   ├─ ingest.py           # Data ingestion
│   ├─ rag.py              # RAG engine (YouTube, Video Analysis)
│   ├─ exam_analysis.py    # PDF Question Paper Analysis
│   └─ mnemonics.py        # Mnemonic generation
├─ visual/                  # Visualization
│   ├─ mindmap_v2.py       # Mermaid mind map generation
│   └─ animate.py          # Animation rendering engine
├─ streamlit/               # Streamlit web UI
│   └─ app.py
└─ cli.py                   # Python CLI tool
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+ (for optional React frontend)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/djmahe4/Study-AI-Agent.git
   cd Study-AI-Agent
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### Interactive Mode

Run the CLI without arguments to enter interactive mode:
```bash
python cli.py
```

**Example interactive session:**
```
Enter command (or 'exit' to quit): help
Enter command (or 'exit' to quit): create-subject "Data Structures"
Enter command (or 'exit' to quit): ask-youtube "https://youtu.be/..." --topic "Stacks"
Enter command (or 'exit' to quit): exit
```

#### Key Workflows

**1. Create a Subject**
```bash
python cli.py create-subject "Machine Learning" --syllabus-file syllabus.txt
```

**2. Analyze Exam Papers (New!)**
```bash
# Define your exam pattern first
python cli.py configure-exam "UnivPattern2024"

# Ingest a PDF paper
python cli.py ingest-paper "Nov2023.pdf" --pattern "UnivPattern2024" --year "2023"

# Generate Solutions
python cli.py get-pyq-answers
```

**3. Visual Learning**
```bash
# Generate Mindmaps for all topics
python cli.py generate-mindmap-v2
```

#### Streamlit Web UI

Start the Streamlit interface:
```bash
streamlit run streamlit/app.py
```

Navigate to `http://localhost:8501` to:
- Browse structured topics and generated notes.
- **Generate Animations** dynamically for any topic.
- Edit subject schemas directly in the **Settings** page.
- Review **Previous Year Questions** and solutions alongside your notes.

## 📖 Core Concepts

### Pydantic Models

The system uses structured data models:

```python
from core import Topic, ExamPattern

topic = Topic(
    name="TCP/IP Protocol",
    summary="Reliable network communication protocol",
    key_points=["Connection-oriented", "Three-way handshake"],
    mermaid_diagrams=[{"type": "sequence", "script": "..."}]
)
```

### Animation Generation

Create educational animations from text descriptions:

```python
# In Streamlit UI: Click "Generate Animation"
# Backend: Gemini -> AnimationScript -> OpenCV -> GIF
```

## 📚 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[docs/FEATURES.md](docs/FEATURES.md)** - Complete feature list and examples
- **[docs/WORKFLOW_AND_DATA.md](docs/WORKFLOW_AND_DATA.md)** - Detailed data flow and formats
- **[docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** - Add Gemini/RAG integration

## 🔮 Recent Updates

**v2.0 - Major Feature Release**
- ✅ **Exam Analysis Pipeline**: Ingest PDF papers, map questions to modules, and auto-generate answers.
- ✅ **Dynamic Animations**: AI-driven generation of educational GIFs.
- ✅ **Schema Editing**: Direct JSON manipulation of syllabi via Streamlit.
- ✅ **Video Learning**: Deep integration of YouTube content into topic notes (Mindmaps + Summaries).

## 📄 License

MIT License
