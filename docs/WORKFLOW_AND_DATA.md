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

### 5. Content Prioritization & Syllabus Enrichment
**Command:** `ingest-paper <file> --pattern <PatternName> --year <Year>`
- **Input:** Past year question paper (PDF).
- **Processing:**
    - `PyMuPDF` extracts text.
    - `QuestionPaperAnalyzer` (Gemini Flash) extracts structured questions.
    - **Enrichment:** The system automatically maps questions back to the `syllabus.json`:
        - Updates `importance_score` based on question frequency and marks.
        - Appends question references to the `questions` array in the relevant Topic.
        - Extract and adds missing `subtopics` found in questions.
        - Creates **new Topics** if the question covers material not in the existing syllabus.
- **Output:**
    - `data/subjects/<name>/questions/question_bank.json`: Raw questions.
    - **Updated** `syllabus.json`: Enriched with importance and references.
    - **Updated** Markdown notes: Regenerated to include "Practice Questions" sections.

### 6. Study Phase (Output)
**Command:** `save-notes` / `get-pyq-answers` / `generate-mindmap-v2`
- `save-notes`: Generates a clean Markdown hierarchy. Notes now include question references.
- `generate-mindmap-v2`: Uses Gemini to generate conceptual diagrams and relationship maps.
- `get-pyq-answers`: Generates detailed solutions for specific, user-selected PYQs.

---

## 📄 Data Formats

### 1. Syllabus JSON (`syllabus.json`)
The core source of truth for a subject.

```json
{
  "title": "Computer Networks",
  "description": "...",
  "modules": [
    {
      "name": "Module 1",
      "topics": [
        {
          "name": "OSI Model",
          "summary": "7-layer architecture...",
          "importance_score": 0.85,
          "subtopics": ["Physical Layer", "Data Link Layer"],
          "questions": [
            { "text": "Define OSI Model.", "year": "2023", "marks": 2 }
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