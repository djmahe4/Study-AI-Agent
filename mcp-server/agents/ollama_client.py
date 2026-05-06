import httpx
import json
from typing import List, Dict, Any, Optional, AsyncIterable
from config import settings

class OllamaClient:
    def __init__(self, host: str = settings.OLLAMA_HOST):
        self.host = host
        self.client = httpx.AsyncClient(base_url=host, timeout=120.0)

    async def chat(self, 
                   messages: List[Dict[str, str]], 
                   model: str = settings.OLLAMA_CHAT_MODEL,
                   stream: bool = False) -> Any:
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7
            }
        }
        
        if stream:
            return self._stream_chat(payload)
        else:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()

    async def _stream_chat(self, payload: Dict[str, Any]) -> AsyncIterable[str]:
        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        yield chunk["message"].get("content", "")
                    if chunk.get("done"):
                        break

    async def embed(self, text: str, model: str = settings.OLLAMA_EMBED_MODEL) -> List[float]:
        payload = {
            "model": model,
            "prompt": text
        }
        response = await self.client.post("/api/embeddings", json=payload)
        response.raise_for_status()
        return response.json()["embedding"]

    async def close(self):
        await self.client.aclose()
