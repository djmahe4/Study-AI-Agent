"""
Skill Generator: Transforms study notes and PYQ solutions into Agent Skills.
"""
import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

from core.gemini_processor import GeminiProcessor
from core.persistence import get_persistence_manager
from core.utils import get_subject_dir

# Define schema for LLM structured output
class SkillMetadata(BaseModel):
    name: str = Field(..., description="topic-kebab-case name")
    description: str = Field(..., description="One sentence description of the capability.")
    tags: List[str] = Field(default_factory=list)
    category: str = "study"
    priority: str = "medium"
    type: Literal["practical", "theoretical"] = "theoretical"
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    instructions: str = Field(..., description="Detailed instructions for the agent.")

logger = logging.getLogger(__name__)

class SkillGenerator:
    """
    Automates the creation of Agent Skills from static study notes.
    """

    def __init__(self, gemini_processor: Optional[GeminiProcessor] = None):
        self.processor = gemini_processor or GeminiProcessor()
        self.persistence = get_persistence_manager()

    def generate_skill_from_markdown(
        self, 
        md_file: Path, 
        subject: str, 
        module_name: str,
        skill_root: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Processes a markdown file and creates a corresponding skill directory.
        """
        if not md_file.exists():
            return None

        # 1. Read content
        content = md_file.read_text(encoding="utf-8")
        if not content.strip():
            return None

        # 2. Ask Gemini to generate the SKILL metadata
        prompt = f"""
        You are an Expert Pedagogy Designer. Transform the following study notes into an 'Agent Skill'.
        
        SUBJECT: {subject}
        MODULE: {module_name}
        CONTENT:
        {content[:4000]}  # Truncate if too long
        
        TASK:
        Generate a YAML frontmatter for an AI Agent Skill.
        Categorize as 'practical' if it involves code, mathematical problem solving, or simulations.
        Categorize as 'theoretical' if it is purely conceptual explanation.
        
        OUTPUT FORMAT (JSON):
        {{
            "name": "topic-kebab-case",
            "description": "One sentence description of the capability.",
            "tags": ["tag1", "tag2"],
            "category": "study",
            "priority": "medium",
            "type": "practical | theoretical",
            "level": "beginner | intermediate | advanced",
            "instructions": "Detailed instructions for the agent on how to use this knowledge to help the user."
        }}
        """

        try:
            # We reuse the GeminiProcessor's generic ability to return JSON
            metadata_obj = self.processor._call_gemini_with_schema(prompt, SkillMetadata)
            metadata = metadata_obj.model_dump()
            
            # 3. Create directory structure
            # Root skills folder at project root / skills / [subject] / [module] / [topic]_skill
            skill_base = skill_root or (Path(__file__).resolve().parent.parent / "skills")
            skill_name = metadata.get("name", md_file.stem.lower().replace(" ", "-"))
            if not skill_name.endswith("-skill"):
                skill_name += "-skill"
            
            target_dir = skill_base / subject.lower() / module_name.replace(" ", "_").lower() / skill_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 4. Write SKILL.md
            skill_md_path = target_dir / "SKILL.md"
            
            frontmatter = "---\n"
            for key in ["name", "description", "category", "priority"]:
                frontmatter += f"{key}: {metadata.get(key)}\n"
            
            # Tags list
            tags = metadata.get("tags", [])
            frontmatter += f"tags: {tags}\n"
            frontmatter += f"type: {metadata.get('type', 'theoretical')}\n"
            frontmatter += f"level: {metadata.get('level', 'intermediate')}\n"
            frontmatter += "version: 1.0\n"
            frontmatter += "allowed_tools: []\n"
            frontmatter += "---\n\n"
            
            body = f"# {metadata.get('name', skill_name)}\n\n"
            body += f"## Instructions\n{metadata.get('instructions', 'No specific instructions.')}\n\n"
            body += "## Knowledge Content\n"
            body += content
            
            self.persistence.safe_markdown_write(skill_md_path, frontmatter + body)
            
            # 5. If practical, create scripts placeholder
            if metadata.get("type") == "practical":
                (target_dir / "scripts").mkdir(exist_ok=True)
                (target_dir / "scripts" / "README.md").write_text("Place utility scripts for this skill here.")

            logger.info(f"Generated skill: {skill_md_path}")
            return target_dir

        except Exception as e:
            logger.error(f"Failed to generate skill for {md_file}: {e}")
            return None

    def auto_scaffold_subject(self, subject: str, module_name: Optional[str] = None):
        """
        Scans notes for a subject and generates skills. Optional module_name for targeting.
        """
        subject_dir = get_subject_dir(subject)
        notes_dir = subject_dir / "notes"
        
        if not notes_dir.exists():
            logger.warning(f"No notes found for {subject}")
            return
            
        directories = [notes_dir / module_name] if module_name else sorted(notes_dir.iterdir())
        
        for module_dir in directories:
            if not module_dir.is_dir():
                continue
            
            curr_module = module_dir.name
            # Look for PYQ_Solutions.md as high priority
            pyq_file = module_dir / "PYQ_Solutions.md"
            if pyq_file.exists():
                self.generate_skill_from_markdown(pyq_file, subject, curr_module)
                time.sleep(12) # Strict 5 RPM throttling
            
            # Also process other topic files
            for topic_file in module_dir.glob("*.md"):
                if topic_file.name == "PYQ_Solutions.md" or topic_file.name == "README.md":
                    continue
                self.generate_skill_from_markdown(topic_file, subject, curr_module)
                time.sleep(12) # Strict 5 RPM throttling

def generate_skills_for_subject(subject_name: str, module_name: Optional[str] = None):
    """Entry point for CLI."""
    from core.gemini_processor import GeminiProcessor
    processor = GeminiProcessor()
    generator = SkillGenerator(processor)
    generator.auto_scaffold_subject(subject_name, module_name)
