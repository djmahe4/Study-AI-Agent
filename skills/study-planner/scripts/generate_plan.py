#!/usr/bin/env python3
"""
generate_plan.py – Generate a basic JSON study plan from a syllabus text file.

Lightweight script for the study-planner skill.
Reads a plain-text syllabus and outputs a JSON study schedule to stdout.

Usage:
    python skills/study-planner/scripts/generate_plan.py syllabus.txt [--days 30]
"""

import sys
import json
import math
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))

from core.input_validator import sanitize_syllabus_text

# Pre-compiled patterns for module/unit header detection
_MODULE_HEADER_RE = re.compile(r"^(module|unit)\s*\d+", re.IGNORECASE)
_NUMBERED_HEADING_RE = re.compile(r"^\d+[\.\)]\s+[A-Z]")


def parse_modules(text: str) -> list:
    """
    Heuristically extract module/unit names from plain-text syllabus.
    Returns a list of dicts: {name, topics, complexity}.
    """
    modules = []
    current: dict = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Module header heuristic: starts with "Module", "Unit", or numbered heading
        if _MODULE_HEADER_RE.match(stripped) or _NUMBERED_HEADING_RE.match(stripped):
            if current:
                modules.append(current)
            current = {"name": stripped, "topics": [], "complexity": "medium"}
        elif current and len(stripped) > 5:
            current["topics"].append(stripped)

    if current:
        modules.append(current)

    # Fallback: treat each non-empty line as its own "module"
    if not modules:
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip():
                modules.append({"name": f"Topic {i}: {line.strip()}", "topics": [], "complexity": "medium"})

    return modules


def build_plan(modules: list, days: int = 30) -> dict:
    """
    Distribute modules across available study days.
    """
    total_topics = sum(max(1, len(m["topics"])) for m in modules)
    days_per_topic = max(1, math.floor(days / max(total_topics, 1)))

    schedule = []
    day = 1
    for mod in modules:
        topic_list = mod["topics"] if mod["topics"] else [mod["name"]]
        for topic in topic_list:
            sessions = 3 if mod["complexity"] == "high" else 2
            entry = {
                "day": day,
                "module": mod["name"],
                "topic": topic,
                "pomodoro_sessions": sessions,
                "type": "New Study",
            }
            schedule.append(entry)
            # Spaced repetition reviews
            for gap in (1, 3, 7):
                review_day = day + gap
                if review_day <= days:
                    schedule.append({
                        "day": review_day,
                        "module": mod["name"],
                        "topic": topic,
                        "pomodoro_sessions": 1,
                        "type": f"Review (+{gap}d)",
                    })
            day += days_per_topic

    return {
        "total_days": days,
        "total_modules": len(modules),
        "schedule": sorted(schedule, key=lambda x: x["day"]),
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: generate_plan.py <syllabus.txt> [--days N]")
        sys.exit(1)

    syllabus_file = sys.argv[1]
    days = 30
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        try:
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Warning: invalid or missing value for --days; using default of 30 days.", file=sys.stderr)

    raw = Path(syllabus_file).read_text(encoding="utf-8")
    clean = sanitize_syllabus_text(raw)
    modules = parse_modules(clean)
    plan = build_plan(modules, days)
    print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
