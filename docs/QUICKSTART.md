# 🚀 Quick Start Guide

Get started with the AI Learning Engine in 5 minutes!

## Prerequisites

- Python 3.8+
- (Optional) Node.js 18+ for React Terminal CLI

## Installation

```bash
# Clone the repository
git clone https://github.com/djmahe4/Study-AI-Agent.git
cd Study-AI-Agent

# Install Python dependencies
pip install -r requirements.txt
```

## Basic Usage

### Step 1: Initialize the System
```bash
python cli.py init
```

### Step 2: Use Interactive Mode (Recommended for Beginners)

```bash
python cli.py
```

You'll see a prompt where you can type commands directly:
```
Enter command (or 'exit' to quit): help
Enter command (or 'exit' to quit): create-subject "My Subject" --syllabus-file syllabus.txt
Enter command (or 'exit' to quit): list-subjects
```

### Step 3: Create Your First Subject

**From a text file:**
```bash
python cli.py create-subject "Machine Learning" --syllabus-file data/sample_syllabus.txt
```

**With question bank:**
```bash
python cli.py create-subject "Algorithms" \
  --syllabus-file syllabus.txt \
  --question-bank questions.pdf
```

### Step 4: Explore Your Subject

```bash
# List all subjects
python cli.py list-subjects

# Select a subject
python cli.py select-subject "Machine Learning"

# List topics
python cli.py list-topics
```

### Step 5: Generate Learning Materials

**Mind map:**
```bash
python cli.py generate-mindmap
```

**Animations:**
```bash
python cli.py create-animation tcp
python cli.py create-animation stack
```

**Difference tables:**
```bash
python cli.py show-difference --example tcp_vs_udp
```

**Mnemonics:**
```bash
python cli.py create-mnemonic "TCP Handshake" "Synchronize,Acknowledge,Connect"
```

### Step 6: Add Custom Content

```bash
# Add a topic
python cli.py add-topic "Python Basics" --summary "Introduction to Python" --key-points "Variables,Functions,Loops"

# Add a question
python cli.py add-question "Python Basics" \
  "What is a variable?" \
  "A variable stores data" \
  --difficulty easy
```

## Optional: Web Interfaces

### Streamlit Web UI
```bash
streamlit run streamlit/app.py
# Open http://localhost:8501
```

### React Terminal CLI
```bash
cd frontend
npm install  # First time only
npm run dev
# Open http://localhost:3000
```

## Example Workflow

```bash
# 1. Initialize
python cli.py init

# 2. Create subject
python cli.py create-subject "Computer Networks" \
  --syllabus-file data/sample_syllabus.txt

# 3. Generate learning aids
python cli.py generate-mindmap
python cli.py create-animation tcp
python cli.py show-difference --example tcp_vs_udp

# 4. Add custom questions
python cli.py add-question "Computer Networks" \
  "What is TCP?" \
  "Transmission Control Protocol" \
  --difficulty easy
```

## Tips for Success

1. **Use Interactive Mode**: Great for exploring commands without typing `python cli.py` repeatedly
2. **Start Small**: Begin with one subject and a simple syllabus
3. **Explore Commands**: Run `python cli.py COMMAND --help` for detailed options
4. **Current Subject**: The system remembers your selected subject across commands
5. **Quoted Arguments**: Use quotes for multi-word arguments: `"Machine Learning"`

## Common Commands Reference

```bash
# Getting help
python cli.py --help              # List all commands
python cli.py COMMAND --help      # Help for specific command
python cli.py                     # Interactive mode with help

# Subject management
python cli.py list-subjects       # View all subjects
python cli.py select-subject "ML" # Switch active subject
python cli.py delete-subject "ML" # Remove a subject

# Content management
python cli.py list-topics         # View topics
python cli.py list-questions      # View questions
python cli.py export-syllabus     # Export to JSON
```

## Next Steps

- Read [FEATURES.md](FEATURES.md) for comprehensive feature documentation
- Check [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) to add Gemini/RAG APIs
- See [TODO.md](TODO.md) for planned enhancements
- Explore [../README.md](../README.md) for architecture details

## Troubleshooting

**Command not found?**
- Ensure you're in the project directory
- Check Python is installed: `python --version`

**Module not found?**
- Install dependencies: `pip install -r requirements.txt`

**API key errors?**
- Set your key: `python cli.py set-api-key YOUR_KEY`
- Or create `.env` file with `GOOGLE_API_KEY=your_key`

## Need More Help?

Run any command with `--help`:
```bash
python cli.py create-subject --help
python cli.py --help
```

Or start interactive mode and type `help`!
