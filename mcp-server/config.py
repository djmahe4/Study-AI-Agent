from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "llama3"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    
    # free-llm-apis MCP server (run with: node dist/src/server.js --sse)
    FREE_LLM_HOST: str = "http://localhost:3000"
    
    SKILLS_DIR: Path = Path(__file__).parent.parent / "skills"
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    DB_PATH: Path = DATA_DIR / "chat_memory.db"
    
    PORT: int = 8765
    DEBUG: bool = True

    class Config:
        env_prefix = "MCP_"

settings = Settings()
