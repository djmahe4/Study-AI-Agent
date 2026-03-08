# ✨ System Features

## 🧠 Core Intelligence
- **AI Syllabus Processing**: Uses Google Gemini 2.0 to parse raw syllabus text into a structured `Subject -> Module -> Topic` hierarchy.
- **Contextual RAG**: Retrieves answers from local knowledge bases or YouTube videos using LangChain and FAISS.
- **Persistent LLM Cache (New!)**: A local SQLite cache (`data/cache.db`) intercepts duplicate Gemini API requests across diagram generation and syllabus parsing, drastically reducing API quota usage and dropping response times to near-zero.
- **Smart Mnemonics**: Automatically generates acronyms and memory aids for complex topics.

## 📚 Subject Management
- **Hierarchical Organization**: Subjects are organized into Modules and Topics.
- **Schema Editing (New!)**: Direct JSON editing of syllabi via the Streamlit Settings page allows for manual refinement of the AI-generated structure.
- **Markdown Notes**: Automatically generates a navigable Markdown structure (`Subject/Module/Topic.md`) for easy reading.
- **Persistence**: Data is saved as JSON and synced to a local SQLite Knowledge Base.

## 📺 YouTube Integration (New!)
- **`ask-youtube`**: Chat with any YouTube video. The system fetches captions and answers questions based *strictly* on the video content. Supports generating notes and mindmaps directly from videos.
- **`quiz-youtube`**: Generate multiple-choice quizzes from educational videos and save them to your question bank.

## 🎨 Visualization
- **Gemini-Powered Conceptual Diagrams (v2)**: Generates embedded `.md` files with complex relationship maps and mindmaps using AI-driven structural analysis.
- **Dynamic Animations**: 
    - **Topic Animations**: Generate custom educational animations (GIF/Video) for any topic using AI-generated scripts and OpenCV rendering.
    - **Integration**: Animations are automatically embedded into the Markdown notes.

## 💻 Interfaces
- **Interactive CLI**: Rich terminal interface with autocomplete, intelligent module filtering, and progress tracking.

## 📝 Assessment
- **Intelligent Syllabus Enrichment**: `ingest-paper` now automatically maps questions from PDFs to your syllabus, updating topic importance scores and practice questions. It even creates new syllabus topics if a paper contains material not previously covered.
- **Interactive PYQ Solutions**: `get-pyq-answers` allows you to preview questions in a rich table and selectively generate detailed answers for specific questions, saving time and API quota.
