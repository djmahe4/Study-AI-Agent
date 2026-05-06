# 🚀 Quick Start Guide

Get started with the AI Learning Engine in 5 minutes!

```mermaid
flowchart LR
    A[1. Install & Setup] --> B[2. create-subject]
    B --> C[3. generate-mindmap-v2]
    C --> D[4. ingest-paper]
    D --> E[5. get-pyq-answers]
    
    style A fill:#4a148c,stroke:#ab47bc,color:#fff
    style B fill:#004d40,stroke:#26a69a,color:#fff
    style C fill:#0d47a1,stroke:#42a5f5,color:#fff
    style D fill:#e65100,stroke:#ffa726,color:#fff
    style E fill:#b71c1c,stroke:#ef5350,color:#fff
```

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
Generate a visual map of your curriculum. You can target a single module to save time:

```bash
python cli.py generate-mindmap-v2 --module 1
```
*This uses Gemini to generate conceptual relationship maps saved as `<topic>_mermaid.md`.*

### 3. Solve Previous Papers
Ingest a question paper to prioritize your study:

```bash
python cli.py ingest-paper "path/to/2024_ktv.pdf" ktu
```
*The system maps questions to your syllabus and enriches your notes.*

Now, solve specific questions interactively:

```bash
python cli.py get-pyq-answers --module 3
```
*You will see a table of questions; select the ones you want to solve by index.*

## Useful Commands

| Command | Description |
|---------|-------------|
| `python cli.py` | Enter interactive mode (type `help` to see options) |
| `python cli.py ingest-paper` | Map PDF questions to syllabus & notes |
| `python cli.py get-pyq-answers` | Generate AI solutions for paper questions |
| `python cli.py generate-mindmap-v2` | Create Gemini-powered conceptual diagrams |

## Next Steps
- Read [WORKFLOW_AND_DATA.md](WORKFLOW_AND_DATA.md) for detailed data flow.
- Check [FEATURES.md](FEATURES.md) for full capabilities.