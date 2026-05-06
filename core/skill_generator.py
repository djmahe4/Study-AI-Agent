"""
Skill Generator: Transforms study notes and PYQ solutions into Agent Skills.
"""
import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

import hashlib
import json
from core.gemini_processor import GeminiProcessor
from core.persistence import get_persistence_manager
from core.utils import get_subject_dir, normalize_subject_name

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
        # Use flash-lite for bulk skill generation: 1500 req/day vs 20 req/day for flash
        self.processor = gemini_processor or GeminiProcessor(model_name="gemini-3.1-flash-lite-preview") #"gemini-2.5-flash-lite")
        self.persistence = get_persistence_manager()
        self.cache_path = Path("data/cache/skill_factory.json")
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_cache()

    def _load_cache(self):
        """Loads the skill factory cache from disk."""
        if self.cache_path.exists():
            try:
                self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load skill factory cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self):
        """Saves the skill factory cache to disk."""
        try:
            self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save skill factory cache: {e}")

    def _calculate_hash(self, content: str) -> str:
        """Calculates a SHA-256 hash of the content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

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

        # 1. Read content and check cache
        content = md_file.read_text(encoding="utf-8")
        if not content.strip():
            return None
        
        content_hash = self._calculate_hash(content)
        cache_key = f"{subject}:{module_name}:{md_file.name}"
        
        if cache_key in self.cache and self.cache[cache_key].get("hash") == content_hash:
            existing_dir = Path(self.cache[cache_key]["path"])
            if existing_dir.exists():
                logger.info(f"Cache hit (high-level) for {md_file.name}")
                return existing_dir

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
            # Always derive the directory name from the source filename (strip leading "N. " prefix).
            # This guarantees uniqueness even when Gemini returns the same name for multiple files.
            file_stem = re.sub(r"^\d+\.\s*", "", md_file.stem).strip().lower().replace(" ", "-")
            skill_name = file_stem if file_stem else metadata.get("name", md_file.stem.lower().replace(" ", "-"))
            if not skill_name.endswith("-skill"):
                skill_name += "-skill"
            
            target_dir = skill_base / normalize_subject_name(subject) / module_name.replace(" ", "_").lower() / skill_name
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

            # 6. Update cache
            self.cache[cache_key] = {
                "hash": content_hash,
                "path": str(target_dir),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self._save_cache()

            logger.info(f"Generated skill: {skill_md_path}")
            return target_dir

        except Exception as e:
            logger.error(f"Failed to generate skill for {md_file}: {e}")
            return None

    def auto_scaffold_subject(self, subject: str, module_name: Optional[str] = None) -> Dict[str, int]:
        """
        Scans notes for a subject and generates skills. Optional module_name for targeting.
        Returns a summary of stats.
        """
        stats = {"total": 0, "created": 0, "cache_hits": 0, "failed": 0}
        subject_dir = get_subject_dir(subject)
        notes_dir = subject_dir / "notes"
        
        if not notes_dir.exists():
            logger.warning(f"No notes found for {subject}")
            return stats
            
        directories = [notes_dir / module_name] if module_name else sorted(notes_dir.iterdir())
        
        for module_dir in directories:
            if not module_dir.is_dir():
                continue
            
            curr_module = module_dir.name
            # Gather files to process
            files_to_process = []
            
            pyq_file = module_dir / "PYQ_Solutions.md"
            if pyq_file.exists():
                files_to_process.append(pyq_file)
            
            for topic_file in module_dir.glob("*.md"):
                if topic_file.name == "PYQ_Solutions.md" or topic_file.name == "README.md":
                    continue
                files_to_process.append(topic_file)

            for md_file in files_to_process:
                stats["total"] += 1
                # Initialize before try so it's always defined in the except block
                is_cache_hit = False
                try:
                    if "mermaid" in md_file.name:
                        continue
                    # Check cache before calling generate (which also checks cache but we want to track it for stats)
                    content = md_file.read_text(encoding="utf-8")
                    content_hash = self._calculate_hash(content)
                    cache_key = f"{subject}:{curr_module}:{md_file.name}"
                    
                    is_cache_hit = cache_key in self.cache and self.cache[cache_key].get("hash") == content_hash
                    
                    result = self.generate_skill_from_markdown(md_file, subject, curr_module)
                    
                    if result:
                        if is_cache_hit:
                            stats["cache_hits"] += 1
                        else:
                            stats["created"] += 1
                    else:
                        stats["failed"] += 1
                        
                    # Sleep between API calls to respect flash-lite's RPM limits
                    if not is_cache_hit:
                        time.sleep(6)  # 6s = 10 RPM, safe for both 2.5 and 3.1 flash-lite
                except Exception as e:
                    logger.error(f"Error processing {md_file}: {e}")
                    stats["failed"] += 1
                    # Ensure we sleep on unexpected looping errors too (is_cache_hit is always defined now)
                    if not is_cache_hit:
                        time.sleep(6)

        return stats

def generate_skills_for_subject(subject_name: str, module_name: Optional[str] = None) -> Dict[str, int]:
    """Entry point for CLI. Returns stats."""
    from core.gemini_processor import GeminiProcessor
    processor = GeminiProcessor()
    generator = SkillGenerator(processor)
    return generator.auto_scaffold_subject(subject_name, module_name)
