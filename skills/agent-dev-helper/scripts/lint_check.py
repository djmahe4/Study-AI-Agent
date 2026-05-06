#!/usr/bin/env python3
"""
lint_check.py – Heuristic static analysis for common Python issues.

Lightweight helper for the agent-dev-helper skill.
Checks a Python file for common bugs without external linter dependencies.

Usage:
    python skills/agent-dev-helper/scripts/lint_check.py core/rag.py
    python skills/agent-dev-helper/scripts/lint_check.py core/input_validator.py
"""

import sys
import re
import ast
from pathlib import Path


# ---------------------------------------------------------------------------
# Heuristic checks (regex-based, no AST needed)
# ---------------------------------------------------------------------------

_REGEX_CHECKS = [
    (
        r"^\s*except\s*:",
        "HIGH",
        "Bare `except:` clause – catches BaseException including KeyboardInterrupt. "
        "Use `except (SpecificError1, SpecificError2):`.",
    ),
    (
        r"logging\.basicConfig\(",
        "MEDIUM",
        "`logging.basicConfig()` called – ensure it is only called once at app startup "
        "to avoid duplicate handlers.",
    ),
    (
        r"def \w+\([^)]*=\[\][^)]*\):",
        "MEDIUM",
        "Mutable default argument `=[]` detected. Use `= None` and set inside the function.",
    ),
    (
        r"def \w+\([^)]*=\{\}[^)]*\):",
        "MEDIUM",
        "Mutable default argument `={}` detected. Use `= None` and set inside the function.",
    ),
    (
        r"print\s*\(.*password|secret|api_?key",
        "HIGH",
        "Possible secret/credential in print statement.",
    ),
    (
        r'open\s*\([^)]+\)(?!\s*(as\s+\w+|with\b))',
        "LOW",
        "`open()` used outside a `with` statement – resource may not be closed on error.",
    ),
]


def regex_checks(source: str) -> list:
    """Run all regex heuristics against source lines."""
    issues = []
    for i, line in enumerate(source.splitlines(), 1):
        for pattern, severity, message in _REGEX_CHECKS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "line": i,
                    "severity": severity,
                    "message": message,
                    "snippet": line.strip()[:80],
                })
    return issues


# ---------------------------------------------------------------------------
# AST-based checks
# ---------------------------------------------------------------------------

def ast_checks(source: str) -> list:
    """Run AST-based checks for missing type hints and docstrings."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [{"line": e.lineno, "severity": "ERROR", "message": f"SyntaxError: {e}"}]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check for missing docstring
            has_docstring = (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            )
            if not has_docstring and not node.name.startswith("_"):
                issues.append({
                    "line": node.lineno,
                    "severity": "LOW",
                    "message": f"Public function `{node.name}` is missing a docstring.",
                    "snippet": f"def {node.name}(...)",
                })

            # Check for missing return annotation on public functions
            if not node.returns and not node.name.startswith("_"):
                issues.append({
                    "line": node.lineno,
                    "severity": "LOW",
                    "message": f"Public function `{node.name}` has no return type annotation.",
                    "snippet": f"def {node.name}(...)",
                })

    return issues


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: lint_check.py <file.py>")
        sys.exit(1)

    file_path = sys.argv[1]
    source = Path(file_path).read_text(encoding="utf-8")

    issues = regex_checks(source) + ast_checks(source)
    issues.sort(key=lambda x: ({"ERROR": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x["severity"], 4), x.get("line", 0)))

    if not issues:
        print(f"✅ No issues found in {file_path}")
        return

    print(f"\n🔍 lint_check: {file_path}")
    print(f"   Found {len(issues)} issue(s)\n")
    for issue in issues:
        line_info = f"line {issue.get('line', '?')}"
        snippet = issue.get("snippet", "")
        print(f"  [{issue['severity']}] {line_info}: {issue['message']}")
        if snippet:
            print(f"         → {snippet}")
    print()


if __name__ == "__main__":
    main()
