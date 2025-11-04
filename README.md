# 🧠 AI Learning Engine

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
learning-ai/
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

#### Python CLI

Initialize the knowledge base:
```bash
python cli.py init
```

Add a topic:
```bash
python cli.py add-topic "Machine Learning" --summary "Study of algorithms that learn from data" --key-points "Supervised learning, Unsupervised learning, Neural networks"
```

List all topics:
```bash
python cli.py list-topics
```

Generate a mind map:
```bash
python cli.py generate-mindmap --output-format json
```

Create an animation:
```bash
python cli.py create-animation tcp
```

Load a syllabus:
```bash
python cli.py load-syllabus data/syllabus/example.json
```

#### React Terminal CLI

Start the React-based terminal interface:
```bash
cd frontend
npm run dev
```

Open your browser to `http://localhost:3000` and use the terminal-style interface.

Available commands in React CLI:
- `help` - Show available commands
- `topics` - List all topics
- `add-topic <name>` - Add a new topic
- `questions [topic]` - List questions
- `quiz [topic]` - Start quiz mode
- `mindmap` - Generate mind map visualization
- `mnemonic <topic>` - Generate mnemonics
- `differences <example>` - Show comparison tables (tcp_vs_udp, stack_vs_queue)
- `animate <type>` - Create animations (tcp, stack)
- `clear` - Clear terminal
- `exit` - Exit application

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

## 🔮 Future Enhancements

- [ ] LLM integration (LangChain/Gemini) for RAG
- [ ] Advanced animation types (blockchain, neural networks)
- [ ] Spaced repetition algorithm
- [ ] Interactive simulations in Streamlit
- [ ] Voice-based learning mode
- [ ] Export to Anki/flashcard formats
- [ ] Collaborative learning features

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