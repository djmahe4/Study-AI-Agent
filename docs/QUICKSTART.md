# 🚀 Quick Start Guide

Get started with the AI Learning Engine v2.0 in 5 minutes!

## Prerequisites
- Python 3.10+
- Google Gemini API Key

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/djmahe4/Study-AI-Agent.git
cd Study-AI-Agent

# 2. Install dependencies
pip install -r requirements.txt
```

## First-Time Setup

1. **Initialize the System**:
   ```bash
   python cli.py init
   ```

2. **Set your API Key**:
   ```bash
   python cli.py set-api-key YOUR_GOOGLE_API_KEY
   ```

## Recommended Workflow

### 1. Create a Subject
Paste your syllabus into a text file (e.g., `syllabus.txt`) or pass it directly.

```bash
python cli.py create-subject "Computer Networks" --syllabus-file syllabus.txt
```
*The AI will generate a structured `Module -> Topic` hierarchy and create Markdown notes in `data/subjects/computer_networks/notes`.*

### 2. Study & Visualize
Generate a visual map of your curriculum:

```bash
python cli.py generate-mindmap-v2
```
*Open the generated `.mmd` file in [Mermaid Live Editor](https://mermaid.live).*

### 3. Deepen Understanding with YouTube
Found a good lecture? Quiz yourself on it immediately.

```bash
python cli.py quiz-youtube "https://www.youtube.com/watch?v=..." --num 5 --save
```

### 4. Interactive Exploration
Launch the web dashboard to explore notes and take quizzes graphically.

```bash
python cli.py run-web
```

## Useful Commands

| Command | Description |
|---------|-------------|
| `python cli.py` | Enter interactive mode (type `help` to see options) |
| `python cli.py list-subjects` | View all your subjects |
| `python cli.py save-notes` | Regenerate Markdown notes for the active subject |
| `python cli.py ask-youtube` | Ask a specific question to a video |

## Next Steps
- Read [WORKFLOW_AND_DATA.md](WORKFLOW_AND_DATA.md) for detailed data flow.
- Check [FEATURES.md](FEATURES.md) for full capabilities.