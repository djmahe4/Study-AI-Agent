# 🚀 Quick Start Guide

## Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies (for React Terminal CLI)
```bash
cd frontend
npm install
cd ..
```

## Basic Usage

### Step 1: Initialize the System
```bash
python cli.py init
```

### Step 2: Create Your First Subject

**Option A: From a text file**
```bash
python cli.py create-subject "Machine Learning" --syllabus-file data/sample_syllabus.txt
```

**Option B: Interactive mode**
```bash
python cli.py create-subject "Data Structures"
# Paste your syllabus text, then press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows)
```

**Option C: With question bank (for RAG)**
```bash
python cli.py create-subject "Algorithms" \
  --syllabus-file syllabus.txt \
  --question-bank @questions.pdf
```

### Step 3: Explore Your Subject

**List all subjects:**
```bash
python cli.py list-subjects
```

**Select a subject:**
```bash
python cli.py select-subject "Machine Learning"
```

**List topics in current subject:**
```bash
python cli.py list-topics
```

### Step 4: Generate Learning Materials

**Create a mind map:**
```bash
python cli.py generate-mindmap --output-format json
```

**Generate animations:**
```bash
python cli.py create-animation --animation-type tcp
python cli.py create-animation --animation-type stack
```

**View difference tables:**
```bash
python cli.py show-difference --example tcp_vs_udp
python cli.py show-difference --example stack_vs_queue
```

**Create mnemonics:**
```bash
python cli.py create-mnemonic "TCP Handshake" "Synchronize,Your,Network"
```

### Step 5: Add Questions

```bash
python cli.py add-question "Machine Learning" \
  "What is supervised learning?" \
  "Learning from labeled data" \
  --difficulty medium
```

**List questions:**
```bash
python cli.py list-questions "Machine Learning"
```

### Step 6: Use the React Terminal CLI

```bash
cd frontend
npm run dev
```

Then open http://localhost:3000 in your browser and use terminal commands:
- `help` - See all commands
- `subjects` - List subjects
- `select Machine Learning` - Select a subject
- `topics` - List topics
- `quiz` - Start quiz mode
- `mindmap` - View mind map
- `differences tcp_vs_udp` - Compare concepts

### Step 7: Use Streamlit Web Interface

```bash
streamlit run streamlit/app.py
```

Open http://localhost:8501 to access the web interface.

## Example Workflow

```bash
# 1. Initialize
python cli.py init

# 2. Create subject
python cli.py create-subject "Computer Networks" \
  --syllabus-file data/sample_syllabus.txt

# 3. List subjects
python cli.py list-subjects

# 4. Generate mind map
python cli.py generate-mindmap

# 5. Create animations
python cli.py create-animation --animation-type tcp

# 6. View differences
python cli.py show-difference --example tcp_vs_udp

# 7. Add questions
python cli.py add-question "Computer Networks" \
  "What is TCP?" \
  "Transmission Control Protocol" \
  --difficulty easy

# 8. Start learning with React CLI
cd frontend && npm run dev
```

## Folder Structure After Creating a Subject

```
data/subjects/machine_learning/
├── animations/         # Generated animations
├── mindmaps/          # Mind map visualizations
├── notes/             # User notes
├── questions/         # Question banks
└── syllabus/          # Syllabus JSON
    └── machine_learning.json
```

## Tips

1. **Syllabus Format**: Use clear topic headers and bullet points for best results
2. **Question Banks**: Use `@` prefix to specify question bank file path
3. **Current Subject**: The system remembers your selected subject
4. **Animations**: Videos are saved in `data/subjects/<subject>/animations/`
5. **Mind Maps**: Export to JSON for use in visualizations

## Next Steps

- See [TODO.md](TODO.md) for planned features
- Check [README.md](README.md) for detailed documentation
- Explore the code to customize for your needs

## Need Help?

Run any command with `--help` for more information:
```bash
python cli.py create-subject --help
python cli.py --help
```
