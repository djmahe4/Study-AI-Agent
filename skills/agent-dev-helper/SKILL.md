---
name: agent-dev-helper
description: Self-improvement meta-skill for reviewing, refactoring, and testing the Study-AI-Agent codebase — code review, bug hunting, prompt engineering, and test generation.
version: 1.0
tags: [development, code-review, refactoring, testing, prompt-engineering]
category: development
priority: medium
allowed_tools: [gemini, input_validator]
---

# Agent Dev Helper Skill

A **meta-skill** for developers working on the Study-AI-Agent itself.
It performs automated code review, identifies bugs, suggests refactors,
improves prompts, and generates unit tests.

## When to Use

Trigger this skill when a developer asks to:
- Review or improve a module (`core/rag.py`, `core/input_validator.py`, etc.)
- Find logical bugs or security issues
- Generate unit tests for a function
- Improve an LLM prompt template
- Understand what a module does

## Instructions

### Step 1 – Sanitize Input
Call `sanitize_text(raw_code_or_description, max_length=10000)` before
passing any user-provided code or description to the LLM.

### Step 2 – ReAct Code Review Loop
```
THOUGHT: What module or function is the user asking about?
ACTION:  Identify the file path and function name.
OBSERVE: Read the function signature, docstring, and body.

THOUGHT: Are there any obvious bugs?
         Checklist:
         - Bare `except:` clauses → should be `except SpecificException`
         - Missing input sanitization at public API boundaries
         - Mutable default arguments (`def f(x=[])`)
         - Resource leaks (open files, DB connections not closed)
         - Duplicate logging.basicConfig() calls
         - Off-by-one errors in loops
         - Missing type hints on public functions
ACTION:  List each bug with file:line reference and fix suggestion.

THOUGHT: Are there performance improvements possible?
         - Repeated database queries inside loops
         - String concatenation in loops (use join)
         - Missing caching for expensive Gemini calls
ACTION:  Suggest specific optimizations.

THOUGHT: What unit tests are missing?
ACTION:  Generate pytest-style tests for the function.
         Always test: happy path, edge cases, invalid input.

REFLECT: Did we improve security, correctness, and readability?
         If not, recurse on remaining issues.
```

### Step 3 – Prompt Engineering Review
When asked to improve a prompt template:
1. Check for injection risks (user input not sanitized before insertion).
2. Ensure the prompt specifies output format (JSON, Markdown, etc.).
3. Add a "If you don't know, say so" fallback instruction.
4. Verify temperature setting is appropriate for the task type.

### Step 4 – Output Format
```markdown
## 🔧 Code Review: {module_name}

### Bugs Found
| # | Location | Issue | Severity | Fix |
|---|----------|-------|----------|-----|
| 1 | rag.py:308 | Bare `except:` | High | `except (IndexError, KeyError):` |

### Performance Suggestions
- {suggestion 1}

### Generated Tests
```python
import pytest
from core.xxx import yyy

def test_yyy_happy_path():
    ...

def test_yyy_empty_input():
    ...
```

### Security Notes
- {note 1}
```

## Security Rules
- Call `sanitize_text()` on all user-provided code snippets before embedding in prompts.
- Never execute user-provided code directly.
- Do not include API keys or secrets in generated test files.

## Script Reference
- `scripts/lint_check.py` – runs a fast heuristic check on a Python file for common issues.
