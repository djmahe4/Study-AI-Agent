# YouTube RAG Integration

## Overview
The YouTube RAG (Retrieval Augmented Generation) feature allows users to ask questions about the content of a YouTube video. It uses the video's subtitles/captions as the knowledge base.

## Architecture
- **YouTubeSearcher (`core/rag.py`)**: Handles searching YouTube and fetching subtitles using `DrissionPage`.
- **RAGEngine (`core/rag.py`)**: Orchestrates the RAG process.
    - `ask_youtube(url, query)`: Main entry point.
- **RAG Chain**: Uses LangChain and Google Gemini.
    - **Retriever**: `FAISS` vector store with `ContextualCompressionRetriever`.
    - **LLM**: `gemini-2.5-flash`.
    - **Prompt**: Standard Q&A prompt.

## Usage
### CLI Command
```bash
python cli.py ask-youtube <VIDEO_URL> "<QUESTION>"
```

### Example
```bash
python cli.py ask-youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "What is the song about?"
```

## Dependencies
- `DrissionPage`: For browser automation to fetch subtitles (requires Chrome/Chromium).
- `langchain`, `langchain-google-genai`: For RAG logic.
- `faiss-cpu`: For vector storage.

## Notes
- The tool requires a GUI environment (or configured headless) for `DrissionPage` to launch the browser and fetch subtitles.
- Subtitles are cached as `.json` and converted to `.txt` files.
