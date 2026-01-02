# 🧠 Study-AI-Agent: AI Learning Engine

An AI-augmented intelligent learning system that teaches with mind maps, animations, structured knowledge, and interactive learning tools.

**Subject-Based Learning System** - Create subjects, process syllabi with Gemini AI, and integrate question banks with RAG.

## ✨ Features

- **📚 Structured Knowledge**: Pydantic-based data models for organizing learning content
- **🗺️ Mind Maps**: NetworkX-powered concept visualization
- **🎬 Animations**: OpenCV-based educational animations
- **❓ Quiz Mode**: Interactive Q&A with retrieval practice
- **📊 Difference Tables**: Learning through contrasts and comparisons
- **🧠 Mnemonics**: Memory aids and cognitive learning techniques
- **💻 CLI Interface**: Both Python and React-based terminal interfaces
- **🌐 Streamlit UI**: Web-based learning dashboard

## 🏗️ Architecture

```
Study-AI-Agent/
├─ data/                    # Data storage
│   ├─ syllabus/           # Syllabus JSON files
│   ├─ qbank/              # Question banks
│   └─ memory.db           # SQLite knowledge base
├─ core/                    # Core Python modules
│   ├─ models.py           # Pydantic models
│   ├─ ingest.py           # Data ingestion
│   ├─ rag.py              # RAG engine (placeholder)
│   └─ mnemonics.py        # Mnemonic generation
├─ visual/                  # Visualization
│   ├─ mindmap.py          # Mind map generation
│   └─ animate.py          # Animation creation
├─ streamlit/               # Streamlit web UI
│   └─ app.py
├─ frontend/                # React CLI interface
│   └─ src/
│       ├─ Terminal.jsx    # CLI component
│       └─ App.jsx
└─ cli.py                   # Python CLI tool
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

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

3. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

### Usage

#### Interactive Mode (New!)

Run the CLI without arguments to enter interactive mode:
```bash
python cli.py
```

In interactive mode, you can:
- Type any command without the `python cli.py` prefix
- Get immediate help with `help` command
- Use quoted strings for arguments with spaces
- Exit anytime with `exit` command

**Example interactive session:**
```
Enter command (or 'exit' to quit): help
Enter command (or 'exit' to quit): list-subjects
Enter command (or 'exit' to quit): add-topic "Python Basics" --summary "Introduction to Python"
Enter command (or 'exit' to quit): exit
```

#### Creating a Subject

**Create a subject from a syllabus file:**
```bash
python cli.py create-subject "Machine Learning" --syllabus-file syllabus.txt
```

**With question bank (uses RAG):**
```bash
python cli.py create-subject "Machine Learning" \
  --syllabus-file syllabus.txt \
  --question-bank @questions.pdf
```

**Interactive mode:**
```bash
python cli.py create-subject "Machine Learning"
# Then paste syllabus text and press Ctrl+D
```

**Managing subjects:**
```bash
# List all subjects
python cli.py list-subjects

# Select a subject to work with
python cli.py select-subject "Machine Learning"
```

#### Python CLI Commands

**Available commands (run directly or in interactive mode):**

```bash
# System initialization
python cli.py init                    # Initialize knowledge base

# Subject management
python cli.py list-subjects           # List all subjects
python cli.py select-subject "ML"     # Select active subject
python cli.py delete-subject "ML"     # Delete a subject

# Topic management  
python cli.py add-topic "Topic Name" --summary "..." --key-points "A,B,C"
python cli.py list-topics             # List topics

# Question management
python cli.py add-question "Topic" "Question?" "Answer" --difficulty easy
python cli.py list-questions          # List all questions

# Learning aids
python cli.py generate-mindmap        # Generate mind map
python cli.py create-animation tcp    # Create animation (tcp/stack)
python cli.py show-difference --example tcp_vs_udp
python cli.py create-mnemonic "Topic" "Key,Points"

# Syllabus operations
python cli.py load-syllabus file.json # Import syllabus
python cli.py export-syllabus         # Export current syllabus

# Configuration
python cli.py set-api-key YOUR_KEY    # Set Gemini API key
```

**Pro tip:** Use `python cli.py COMMAND --help` for detailed help on any command.

#### React Terminal CLI (Optional)

For a browser-based terminal experience:
```bash
cd frontend
npm run dev
# Open http://localhost:3000
```

See [FEATURES.md](FEATURES.md) for available React CLI commands.

#### Streamlit Web UI

Start the Streamlit interface:
```bash
streamlit run streamlit/app.py
```

Navigate to `http://localhost:8501` to access the web interface.

## 📖 Core Concepts

### Pydantic Models

The system uses structured data models:

```python
from core import Topic, Question, Syllabus

topic = Topic(
    name="TCP/IP Protocol",
    summary="Reliable network communication protocol",
    key_points=["Connection-oriented", "Three-way handshake"],
    mnemonics=["SYN-ACK-ACK"]
)
```

### Mind Map Generation

Create visual concept maps:

```python
from visual import MindMapGenerator

generator = MindMapGenerator()
generator.add_topics_from_syllabus(topics)
generator.export_to_json("mindmap.json")
```

### Animations

Generate educational animations:

```python
from visual import create_tcp_handshake_animation

create_tcp_handshake_animation("output.mp4")
```

## 🎯 Learning Techniques

1. **Spaced Repetition**: Built-in quiz system for retrieval practice
2. **Visual Learning**: Mind maps and animations
3. **Mnemonic Devices**: Acronyms and memory aids
4. **Comparative Learning**: Difference tables for contrasting concepts
5. **Structured Knowledge**: Organized hierarchical content

## 📚 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[docs/FEATURES.md](docs/FEATURES.md)** - Complete feature list and examples
- **[docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** - Add Gemini/RAG integration
- **[docs/TODO.md](docs/TODO.md)** - Planned enhancements and roadmap

## 🔮 Recent Updates

**v1.1 - CLI Fixes (Latest)**
- ✅ Fixed interactive mode command execution
- ✅ Added proper error handling for invalid commands
- ✅ Improved command parsing with quoted string support
- ✅ Fixed global variable initialization issues
- ✅ Enhanced user experience with better prompts

## 🛠️ Technologies

**Backend:**
- Python 3.8+
- Pydantic (data validation)
- NetworkX (graph visualization)
- OpenCV (animations)
- SQLite (storage)
- Typer (CLI)
- Streamlit (web UI)

**Frontend:**
- React 18
- Vite (build tool)
- Custom terminal component

## 📝 Example Syllabus Format

```json
{
  "title": "My Course",
  "description": "Course description",
  "topics": [
    {
      "name": "Topic Name",
      "summary": "Brief summary",
      "key_points": ["Point 1", "Point 2"],
      "mnemonics": ["Memory aid"],
      "questions": ["Question 1?"],
      "subtopics": ["Subtopic 1"],
      "prerequisites": ["Prereq 1"]
    }
  ]
}
```

## 🤝 Contributing

Contributions are welcome! This is a foundational implementation designed to leave room for innovation.

## 📄 License

MIT License

## 🙏 Acknowledgments

Built with cognitive science principles and modern AI techniques to enhance learning effectiveness.