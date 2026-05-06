from typing import List, Dict, Any, Optional
from agents.ollama_client import OllamaClient
from agents.skill_loader import SkillLoader, SkillDefinition
import json

class ConversationMemory:
    def __init__(self, limit: int = 20):
        self.messages: List[Dict[str, str]] = []
        self.limit = limit

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.limit:
            self.messages = self.messages[-self.limit:]

    def get_context(self) -> List[Dict[str, str]]:
        return self.messages

class Orchestrator:
    def __init__(self, ollama: OllamaClient, loader: SkillLoader):
        self.ollama = ollama
        self.loader = loader

    async def route(self, message: str, memory: ConversationMemory) -> tuple[Optional[SkillDefinition], str]:
        """Detect intent and pick a skill or fallback."""
        skills = self.loader.list_skills()
        skill_descriptions = "\n".join([f"- {s.name}: {s.description}" for s in skills])
        
        prompt = f"""
        Analyze the user message and identify which study skill from the list below matches the user's intent.
        
        Skills:
        {skill_descriptions}
        - fallback: Use this if no specific study technique is requested.
        
        User Message: "{message}"
        
        Respond with ONLY the name of the skill in lowercase.
        """
        
        response = await self.ollama.chat(
            messages=[{"role": "system", "content": "You are an intent classifier."}, 
                     {"role": "user", "content": prompt}],
            model="llama3"
        )
        
        intent = response.get("message", {}).get("content", "").strip().lower()
        
        selected_skill = self.loader.get_skill(intent)
        if selected_skill:
            return selected_skill, f"Handling your request with the {selected_skill.name} skill..."
        
        return None, "Chatting with Study Buddy..."

    async def execute(self, message: str, memory: ConversationMemory, skill: Optional[SkillDefinition] = None, system_override: Optional[str] = None) -> Any:
        context = memory.get_context()
        
        if system_override:
            system_prompt = system_override
        elif skill:
            system_prompt = f"You are an AI assistant using the '{skill.name}' skill.\n\nInstructions:\n{skill.instructions}"
        else:
            system_prompt = "You are 'Study Buddy', a friendly AI tutor. Help the user with their learning goals."

        messages = [{"role": "system", "content": system_prompt}] + context
        messages.append({"role": "user", "content": message})
        
        # In a real multi-agent scenario, we might call multiple tools or agents here.
        # For this implementation, we use the skill instructions to guide the LLM.
        response = await self.ollama.chat(messages=messages, stream=True)
        return response
