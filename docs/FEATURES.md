# ✨ System Features

## 🧠 Core Intelligence
- **AI Syllabus Processing**: Uses Google Gemini 2.0 to parse raw syllabus text into a structured `Subject -> Module -> Topic` hierarchy.
- **Contextual RAG**: Retrieves answers from local knowledge bases or YouTube videos using LangChain and FAISS.
- **Smart Mnemonics**: Automatically generates acronyms and memory aids for complex topics.

## 📚 Subject Management
- **Hierarchical Organization**: Subjects are organized into Modules and Topics.
- **Markdown Notes**: Automatically generates a navigable Markdown structure (`Subject/Module/Topic.md`) for easy reading.
- **Persistence**: Data is saved as JSON and synced to a local SQLite Knowledge Base.

## 📺 YouTube Integration (New!)
- **`ask-youtube`**: Chat with any YouTube video. The system fetches captions and answers questions based *strictly* on the video content.
- **`quiz-youtube`**: Generate multiple-choice quizzes from educational videos and save them to your question bank.

## 🎨 Visualization
- **Mermaid.js Mind Maps**: Generates `.mmd` files to visualize the relationships between topics and modules.
- **Procedural Animations**: Python-based generation of educational animations (e.g., TCP Handshake, Stack Operations) using OpenCV.
- **Difference Tables**: AI-generated comparison tables (e.g., TCP vs UDP).

## 💻 Interfaces
- **Interactive CLI**: Rich, color-coded terminal interface with autocomplete and workflow guidance.
- **Streamlit Dashboard**: Web-based explorer for topics, quizzes, and visualizations.
- **React Terminal**: (Experimental) Browser-based command line interface.

## 📝 Assessment
- **Question Bank**: Stores generated questions.
- **Quiz Mode**: Interactive CLI or Web-based quizzes.
- **Paper Ingestion** (Beta): Infrastructure to ingest PDF question papers for topic prioritization.