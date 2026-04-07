"""
Skills Registry for the AI Learning Engine.

Discovers, loads, and validates agent skills stored under the ``skills/``
directory at the repository root.  Each skill is a directory containing a
``SKILL.md`` file with YAML front-matter.

Skills Convention
-----------------
Each skill directory (e.g. ``skills/concept-mastery/``) must contain a
``SKILL.md`` file whose first block is YAML front-matter delimited by ``---``:

.. code-block:: yaml

    ---
    name: concept-mastery
    description: One-sentence trigger description.
    version: 1.0
    tags: [learning, education]
    category: study | development
    priority: high | medium | low
    allowed_tools: []
    ---

    # Skill Body (Markdown instructions follow here)

Usage
-----
>>> from core.skills_registry import SkillsRegistry
>>> registry = SkillsRegistry()
>>> registry.list_skills()
['active-recall-tester', 'agent-dev-helper', 'concept-mastery', ...]
>>> result = registry.invoke_skill("concept-mastery", "Explain recursion")
>>> print(result["name"])
concept-mastery

Security
--------
All user-supplied inputs to ``invoke_skill`` are sanitized via
``sanitize_text()`` before being forwarded to any skill handler.
"""

import re
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.input_validator import (
    sanitize_text,
    classify_query_semantics,
    QueryClassification,
)

logger = logging.getLogger(__name__)

# YAML front-matter delimiter
_FM_DELIMITER = re.compile(r"^---\s*$", re.MULTILINE)

# Root of the skills directory (relative to this file's package parent)
_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"


class SkillMetadata:
    """
    Parsed metadata from a ``SKILL.md`` YAML front-matter block.

    Attributes
    ----------
    name:
        Kebab-case skill identifier.
    description:
        One-sentence description used for auto-matching.
    version:
        Semantic version string (e.g. ``"1.0"``).
    tags:
        List of keyword tags.
    category:
        Either ``"study"`` or ``"development"``.
    priority:
        One of ``"high"``, ``"medium"``, or ``"low"``.
    allowed_tools:
        List of tool names the skill is permitted to use.
    body:
        The full Markdown body (instructions) after the front-matter block.
    path:
        Absolute path to the ``SKILL.md`` file.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        tags: List[str],
        category: str,
        priority: str,
        allowed_tools: List[str],
        body: str,
        path: Path,
    ) -> None:
        self.name = name
        self.description = description
        self.version = version
        self.tags = tags
        self.category = category
        self.priority = priority
        self.allowed_tools = allowed_tools
        self.body = body
        self.path = path

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain-dict representation (safe to serialise to JSON)."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "category": self.category,
            "priority": self.priority,
            "allowed_tools": self.allowed_tools,
            "path": str(self.path),
        }

    def __repr__(self) -> str:
        return f"<SkillMetadata name={self.name!r} category={self.category!r}>"


def _parse_yaml_frontmatter(text: str) -> Dict[str, Any]:
    """
    Parse a minimal YAML front-matter block using PyYAML.

    Parameters
    ----------
    text:
        The raw content of the front-matter block (between the --- delimiters).

    Returns
    -------
    dict
        Parsed key-value pairs.
    """
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            # Normalization: ensure all keys are lower-case for registry lookups
            return {k.lower(): v for k, v in data.items()}
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse skill YAML front-matter: {e}")
        return {}


def _load_skill(skill_dir: Path) -> Optional[SkillMetadata]:
    """
    Load a single skill from its directory.

    Returns ``None`` if the directory does not contain a valid ``SKILL.md``.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        logger.debug("Skipping %s: no SKILL.md found.", skill_dir)
        return None

    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", skill_md, exc)
        return None

    # Split on front-matter delimiters
    parts = _FM_DELIMITER.split(content)
    if len(parts) < 3:
        logger.warning("SKILL.md in %s has no valid YAML front-matter.", skill_dir)
        return None

    # parts[0] may be empty; parts[1] is the YAML; parts[2+] is the body
    yaml_block = parts[1]
    body = "---".join(parts[2:]).strip()

    fm = _parse_yaml_frontmatter(yaml_block)

    name = str(fm.get("name", skill_dir.name))
    description = str(fm.get("description", ""))
    version = str(fm.get("version", "1.0"))
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    category = str(fm.get("category", "study"))
    priority = str(fm.get("priority", "medium"))
    allowed_tools = fm.get("allowed_tools", [])
    if isinstance(allowed_tools, str):
        allowed_tools = [allowed_tools]

    return SkillMetadata(
        name=name,
        description=description,
        version=version,
        tags=tags,
        category=category,
        priority=priority,
        allowed_tools=allowed_tools,
        body=body,
        path=skill_md,
    )


class SkillsRegistry:
    """
    Registry that discovers, loads, and invokes agent skills.

    The registry is **lazy-loaded**: it discovers skills the first time
    :meth:`list_skills` or :meth:`get_skill` is called, or when
    :meth:`reload` is explicitly invoked.

    Parameters
    ----------
    skills_root:
        Path to the directory containing skill sub-directories.
        Defaults to ``<repo_root>/skills/``.

    Examples
    --------
    >>> registry = SkillsRegistry()
    >>> names = registry.list_skills()
    >>> skill = registry.get_skill("concept-mastery")
    >>> print(skill.description)
    >>> result = registry.invoke_skill("rag-optimizer", "How to improve retrieval?")
    """

    def __init__(self, skills_root: Optional[Path] = None) -> None:
        self._root = skills_root or _SKILLS_ROOT
        self._skills: Dict[str, SkillMetadata] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def reload(self) -> int:
        """
        Scan the skills directory and reload all skills.

        Returns
        -------
        int
            Number of skills successfully loaded.
        """
        self._skills = {}
        self._loaded = True

        if not self._root.exists():
            logger.warning("Skills root directory does not exist: %s", self._root)
            return 0

        for entry in sorted(self._root.iterdir()):
            if not entry.is_dir():
                continue
            skill = _load_skill(entry)
            if skill:
                self._skills[skill.name] = skill
                logger.debug("Loaded skill: %s", skill.name)

        logger.info("SkillsRegistry: loaded %d skill(s) from %s", len(self._skills), self._root)
        return len(self._skills)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_skills(self, category: Optional[str] = None) -> List[str]:
        """
        Return a sorted list of registered skill names.

        Parameters
        ----------
        category:
            If provided, filter by ``"study"`` or ``"development"``.

        Returns
        -------
        list[str]
            Sorted skill name list.
        """
        self._ensure_loaded()
        skills = self._skills.values()
        if category:
            skills = (s for s in skills if s.category == category)
        return sorted(s.name for s in skills)

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        Return the :class:`SkillMetadata` for a skill by name.

        Parameters
        ----------
        name:
            Exact kebab-case skill name (e.g. ``"concept-mastery"``).

        Returns
        -------
        SkillMetadata or None
            ``None`` if no skill with that name is registered.
        """
        self._ensure_loaded()
        return self._skills.get(name)

    def match_skill(self, user_query: str) -> Optional[SkillMetadata]:
        """
        Automatically match a user query to the most relevant skill.

        Uses :func:`~core.input_validator.classify_query_semantics` to
        determine query type, then maps it to the best-fit skill.

        Parameters
        ----------
        user_query:
            Raw user input (will be sanitized internally).

        Returns
        -------
        SkillMetadata or None
        """
        self._ensure_loaded()
        clean_query = sanitize_text(user_query)
        classification: QueryClassification = classify_query_semantics(clean_query)

        # Simple heuristic mapping from query type → skill name
        type_to_skill = {
            "factual": "concept-mastery",
            "conceptual": "concept-mastery",
            "procedural": "rag-optimizer",
            "comparative": "concept-mastery",
            "generative": "active-recall-tester",
            "meta": "study-planner",
        }

        preferred_name = type_to_skill.get(classification.query_type)
        if preferred_name and preferred_name in self._skills:
            logger.debug(
                "match_skill: query_type=%s → skill=%s",
                classification.query_type,
                preferred_name,
            )
            return self._skills[preferred_name]

        # Fallback: keyword search in descriptions
        query_lower = clean_query.lower()
        for skill in self._skills.values():
            if any(tag in query_lower for tag in skill.tags):
                return skill

        return None

    def invoke_skill(self, name: str, user_input: str) -> Dict[str, Any]:
        """
        Invoke a skill by name and return its metadata + sanitized context.

        This method does **not** call an LLM directly; it prepares a
        structured context dict that an agent can use to construct a prompt.
        All user input is sanitized before inclusion.

        Parameters
        ----------
        name:
            The skill name (e.g. ``"concept-mastery"``).
        user_input:
            The raw user message/query.

        Returns
        -------
        dict
            Contains keys:
            ``name``, ``description``, ``instructions``, ``clean_input``,
            ``classification``, ``aggregation_strategy``.

        Raises
        ------
        KeyError
            If no skill with the given name is registered.
        """
        self._ensure_loaded()

        skill = self._skills.get(name)
        if skill is None:
            available = ", ".join(sorted(self._skills.keys()))
            raise KeyError(
                f"Skill {name!r} not found. Available skills: {available}"
            )

        # Sanitize user input
        clean_input = sanitize_text(user_input)
        classification = classify_query_semantics(clean_input)

        logger.info(
            "invoke_skill: skill=%s query_type=%s strategy=%s",
            name,
            classification.query_type,
            classification.aggregation_strategy,
        )

        return {
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.body,
            "clean_input": clean_input,
            "classification": {
                "query_type": classification.query_type,
                "confidence": classification.confidence,
                "labels": classification.labels,
            },
            "aggregation_strategy": classification.aggregation_strategy,
        }

    def summary(self) -> str:
        """
        Return a human-readable summary of all registered skills.

        Returns
        -------
        str
            Formatted table of skills.
        """
        self._ensure_loaded()
        if not self._skills:
            return "No skills registered."

        lines = ["Skills Registry", "=" * 60]
        for skill in sorted(self._skills.values(), key=lambda s: s.name):
            lines.append(f"  {skill.name:<25} [{skill.category:<11}] {skill.description[:50]}")
        lines.append("=" * 60)
        lines.append(f"Total: {len(self._skills)} skill(s)")
        return "\n".join(lines)


# Module-level singleton for convenient import
_registry: Optional[SkillsRegistry] = None


def get_skills_registry() -> SkillsRegistry:
    """
    Return the module-level singleton :class:`SkillsRegistry`.

    Creates the instance on first call (lazy initialization).

    Returns
    -------
    SkillsRegistry
    """
    global _registry
    if _registry is None:
        _registry = SkillsRegistry()
    return _registry
