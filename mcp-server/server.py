from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
import asyncio

from config import settings
from agents.ollama_client import OllamaClient
from agents.skill_loader import SkillLoader
from agents.orchestrator import Orchestrator, ConversationMemory
from agents.free_llm_client import call_free_llm
from memory import MemoryDB

app = FastAPI(title="Study AI MCP Server")

# Global state
ollama = OllamaClient()
db = MemoryDB()
loader = SkillLoader()
loader.load_all()
orchestrator = Orchestrator(ollama, loader)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.on_event("startup")
async def startup():
    print(f"Loaded {len(loader.list_skills())} skills")
    await db.init_db()

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    return await handle_chat(req, use_external=False)

@app.post("/chat/external")
async def chat_external_endpoint(req: ChatRequest):
    return await handle_chat(req, use_external=True)

async def handle_chat(req: ChatRequest, use_external: bool = False):
    # Load history from DB
    history = await db.get_messages(req.session_id)
    memory = ConversationMemory()
    for msg in history:
        memory.add(msg["role"], msg["content"])
    
    # Route to skill
    skill, status_msg = await orchestrator.route(req.message, memory)
    
    async def event_generator():
        # Yield metadata first
        yield json.dumps({
            "type": "status",
            "skill": skill.name if skill else "fallback",
            "message": status_msg + (" (Using Frontier AI)" if use_external else "")
        }) + "\n"
        
        # Execute and stream
        full_response = ""
        
        if use_external:
            # Accurate call to the free-llm-apis MCP server (port 3000, --sse mode).
            # Produces structured educational output: Explanation + Python + Mermaid.
            enriched_query = (
                f"[Skill: {skill.name if skill else 'general'}]\n\n" + req.message
            ) if skill else req.message
            
            result = await call_free_llm(enriched_query, session_id=req.session_id)
            full_response = result
            yield json.dumps({"type": "content", "content": result}) + "\n"
        else:
            # Local fallback: agentic skills via Ollama.
            # Same structured educational output (Explanation + Python + Mermaid)
            # is requested so the toggle only changes *which* model answers, not the format.
            from .agents.free_llm_client import EDUCATIONAL_SYSTEM
            skill_context = skill.instructions if skill else ""
            local_system = f"{EDUCATIONAL_SYSTEM}\n\n---\nActive Skill: {skill.name if skill else 'Study Buddy'}\n{skill_context}"
            async for chunk in await orchestrator.execute(req.message, memory, skill, system_override=local_system):
                full_response += chunk
                yield json.dumps({"type": "content", "content": chunk}) + "\n"
                await asyncio.sleep(0.01)
            
        # Post-processing for learning insights (appends to the end)
        if use_external and "Mnemonic:" not in full_response:
             insight = "\n\n---\n**💡 Study Tip:** Try explaining this concept to someone else to solidify your understanding!"
             yield json.dumps({"type": "content", "content": insight}) + "\n"
             full_response += insight

        # Add to memory after completion
        await db.add_message(req.session_id, "user", req.message)
        await db.add_message(req.session_id, "assistant", full_response)
        
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/skills")
async def list_skills():
    return [s.dict() for s in loader.list_skills()]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
