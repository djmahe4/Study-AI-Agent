import frontmatter
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from config import settings

class SkillDefinition(BaseModel):
    name: str
    description: str
    version: str = "1.0"
    tags: List[str] = []
    category: str = "general"
    instructions: str
    path: Path

class SkillLoader:
    def __init__(self, skills_dir: Path = settings.SKILLS_DIR):
        self.skills_dir = skills_dir
        self.skills: Dict[str, SkillDefinition] = {}

    def load_all(self):
        self.skills = {}
        if not self.skills_dir.exists():
            return
        
        for skill_folder in self.skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / "SKILL.md"
                if skill_file.exists():
                    self._load_skill(skill_file)

    def _load_skill(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                
            skill = SkillDefinition(
                name=post.get("name", file_path.parent.name),
                description=post.get("description", ""),
                version=str(post.get("version", "1.0")),
                tags=post.get("tags", []),
                category=post.get("category", "general"),
                instructions=post.content,
                path=file_path
            )
            self.skills[skill.name] = skill
        except Exception as e:
            print(f"Error loading skill {file_path}: {e}")

    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        return self.skills.get(name)

    def list_skills(self) -> List[SkillDefinition]:
        return list(self.skills.values())
