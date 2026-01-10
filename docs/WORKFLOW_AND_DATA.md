# Workflow & Data Formats

This document outlines the standard workflow for the AI Learning Engine and the data formats used for inputs, processing, and outputs.

## 🔄 Core Workflow

The system is designed to transform raw educational content into structured, interactive learning materials.

### 1. Setup
**Command:** `init` -> `set-api-key`
- Initializes the local knowledge base (`data/memory.db`) and directory structure.
- Configures the Google Gemini API key for AI processing.

### 2. Subject Creation (Input & Processing)
**Command:** `create-subject <name> --syllabus-file <file>`
- **Input:** Raw text syllabus (e.g., from a `.txt` file or pasted input).
- **Processing (AI):**
    - The `GeminiProcessor` sends the syllabus to Gemini 2.0 Flash.
    - AI extracts a structured hierarchy: **Subject -> Modules -> Topics**.
- **Output:**
    - `data/subjects/<name>/syllabus/syllabus.json`: Structured data.
    - `data/subjects/<name>/notes/`: Directory structure with Markdown notes.
    - **Knowledge Base:** Topics are saved to SQLite for querying.

### 3. Refinement
**Interface:** Streamlit Web UI -> Settings Page
- **Action:** Select a subject and directly edit the `syllabus.json` schema.
- **Goal:** Correct AI hallucinations, add missing topics, or reorder modules manually.

### 4. Exam Pattern Configuration (New!)
**Command:** `configure-exam <PatternName>`
- **Input:** Interactive wizard.
    - Define Sections (e.g., "Part A", "Part B") with mark weightage.
    - Define Module Mapping (e.g., "Module 1 covers Questions 1, 2, 11").
- **Output:** `data/exam_patterns/<PatternName>.json`
- **Goal:** Define the structure of question papers for accurate analysis.

### 5. Content Prioritization & Question Bank (Input)
**Command:** `ingest-paper <file> --pattern <PatternName> --year <Year>`
- **Input:** Past year question paper (PDF).
- **Processing:**
    - `PyMuPDF` extracts text.
    - `QuestionPaperAnalyzer` (Gemini Flash) extracts structured questions (Part A/B, Marks, etc.).
    - Maps questions to Modules based on the defined Pattern.
- **Output:** `data/subjects/<name>/questions/question_bank.json`

### 6. Study Phase (Output)
**Command:** `save-notes` / `get-pyq-answers`
- `save-notes`: Generates a clean Markdown hierarchy for reading.
- `get-pyq-answers`: Generates detailed solutions for ingested PYQs and appends them to module notes.
- **Structure:**
    ```text
    notes/
    ├── README.md              # Subject Overview & Module Index
    ├── Module 1 - Name/
    │   ├── README.md          # Module Overview & Topic Index
    │   ├── 1. Topic A.md      # Detailed Notes, Mnemonics, Diagrams
    │   ├── 1. Topic A_mermaid.md # Embedded Mindmap
    │   ├── 1. Topic A_anim.gif   # Embedded Animation
    │   └── PYQ_Solutions.md   # Generated Exam Solutions
    ```

### 7. Deepening Knowledge (RAG & Interactive)
**Command:** `ask-youtube <url> --topic <topic>`
- **Input:** YouTube URL.
- **Processing:**
    - `DrissionPage` fetches subtitles.
    - RAG Engine indexes the transcript and generates structured notes.
- **Output:**
    - Appends video summary and insights to the topic's Markdown note.
    - Generates a Mermaid mindmap for the video content.

## 4. Visualizing & Learning (Web UI)
Run `python cli.py run-web` to launch the dashboard.

### **Features**
1.  **Topics Page**: View content hierarchically (**Subject -> Module -> Topic**). Expand modules to see topics.
2.  **Question Bank**: Analyze exam trends.
    -   **Subject Overview**: Charts for Questions per Module and Marks Distribution.
    -   **Module Drill-down**: Filter questions by module.
    -   **Repeated Questions**: Identifies similar questions across years to help prioritize high-yield topics.
3.  **Mind Maps**: Interactive view of topic relationships.
4.  **Animations**: Generate and view concept animations.
5.  **Quiz Mode**: Practice questions filtered by Subject/Module.

---

## 📄 Data Formats

### 1. Syllabus JSON (`syllabus.json`)
The core source of truth for a subject.

```json
{
  "title": "Computer Networks",
  "description": "Study of network protocols...",
  "modules": [
    {
      "id": "uuid...",
      "name": "Module 1: Introduction",
      "order": 1,
      "topics": [
        {
          "id": "uuid...",
          "name": "OSI Model",
          "summary": "7-layer architecture...",
          "key_points": ["Layer 1: Physical", "Layer 7: Application"],
          "module_id": "uuid...",
          "importance_score": 0.0,
          "mermaid_diagrams": [
             { "type": "flowchart", "script": "graph TD; A-->B;" }
          ]
        }
      ]
    }
  ]
}
```

### 2. Exam Pattern JSON (`exam_patterns/University2024.json`)
Defines the structure for parsing papers.

```json
{
  "name": "University2024",
  "sections": [
    { "name": "Part A", "question_range": [1, 10], "marks_per_question": 2, "has_choice": false },
    { "name": "Part B", "question_range": [11, 15], "marks_per_question": 13, "has_choice": true }
  ],
  "module_mapping": {
    "Module 1": [1, 2, 11],
    "Module 2": [3, 4, 12]
  }
}
```

### 3. Analyzed Question (`questions/question_bank.json`)
Extracted question data.

```json
[
  {
    "id": "uuid...",
    "number": 1,
    "part": "a",
    "text": "Define OSI Model.",
    "marks": 2,
    "module": "Module 1",
    "year": "2023",
    "paper_name": "Nov_2023.pdf"
  }
]
```

### 4. Animation Script (Internal)
Used for generating procedural animations.

```json
{
  "title": "TCP Handshake",
  "topic": "Transmission Control Protocol",
  "fps": 30,
  "frames": [
    {
      "duration_frames": 30,
      "commands": [
         { "type": "circle", "center": [100, 100], "radius": 50, "color": [255, 0, 0] },
         { "type": "text", "text": "SYN", "position": [120, 120] }
      ]
    }
  ]
}
```