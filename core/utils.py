"""
Utility functions for the AI Learning Engine.
"""
from pathlib import Path
import re

def normalize_subject_name(subject_name: str) -> str:
    """
    Normalize a subject name to a safe folder name.
    Example: "Algorithm Analysis and Design" -> "algorithm_analysis_and_design"
    """
    return subject_name.lower().replace(" ", "_").replace("/", "_").strip()

def get_subject_dir(subject_name: str, base_path: str = "data/subjects") -> Path:
    """
    Get the directory path for a subject using normalized name.
    """
    safe_name = normalize_subject_name(subject_name)
    return Path(base_path) / safe_name
