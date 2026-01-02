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

### 3. Content Prioritization (Input)
**Command:** `ingest-paper <file> --year <year>`
- **Input:** Past year question paper (PDF/Image).
- **Processing (Stub):**
    - (Planned) OCR + RAG to map questions to specific Topics.
    - Updates `importance_score` in the Topic model.
- **Goal:** Identify high-yield topics for focused study.

### 4. Study Phase (Output)
**Command:** `save-notes`
- Generates a clean Markdown hierarchy for reading.
- **Structure:**
    ```text
    notes/
    ├── README.md              # Subject Overview & Module Index
    ├── Module 1 - Name/
    │   ├── README.md          # Module Overview & Topic Index
    │   ├── 1. Topic A.md      # Detailed Notes, Mnemonics, Diagrams
    │   └── 2. Topic B.md
    ```

### 5. Deepening Knowledge (RAG & Interactive)
**Command:** `ask-youtube <url> "<question>"` / `quiz-youtube <url>`
- **Input:** YouTube URL.
- **Processing:**
    - `DrissionPage` fetches subtitles.
    - RAG Engine (LangChain + Gemini) indexes the transcript.
- **Output:**
    - Answers to specific questions based *only* on the video.
    - Generated MCQs saved to the Question Bank.

### 6. Visualization
**Command:** `generate-mindmap-v2` / `create-animation`
- **Mind Map:**
    - Reads Topics from Knowledge Base.
    - Generates `mindmap.mmd` (Mermaid.js format).
- **Animations:**
    - Generates procedural animations (e.g., TCP Handshake) using OpenCV.

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

### 2. Topic Model (Internal/DB)
Used for RAG context and individual processing.

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Topic title |
| `module_id` | UUID | Parent module reference |
| `summary` | String | AI-generated summary |
| `key_points` | List[Str] | Bullet points for quick review |
| `mnemonics` | List[Str] | Memory aids (e.g., "All People Seem To Need Data Processing") |
| `questions` | List[Str] | Practice questions associated with this topic |
| `importance` | Float | 0.0-1.0 score based on exam frequency |

### 3. Question Bank (SQLite)
Stores generated or manual questions.

| Field | Type | Description |
|-------|------|-------------|
| `topic` | String | Associated topic or "YouTube: <URL>" |
| `question` | String | The question text |
| `answer` | String | Correct answer/explanation |
| `type` | String | `multiple_choice` or `open_ended` |
| `options` | List[Str] | Choices for MCQs |
