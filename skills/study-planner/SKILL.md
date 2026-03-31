---
name: study-planner
description: Analyze a syllabus and generate a personalized daily/weekly study plan with spaced repetition and active recall slots.
version: 1.0
tags: [learning, planning, spaced-repetition, schedule, syllabus]
category: study
priority: high
allowed_tools: [gemini, input_validator]
---

# Study Planner Skill

Turn a raw syllabus into an actionable, personalized study schedule that
incorporates **spaced repetition** and **active recall** checkpoints.

## When to Use

Trigger this skill when the user asks to:
- Create a study plan or timetable
- Organize their revision schedule
- Prioritize topics based on exam weight
- Plan Pomodoro sessions across modules

## Instructions

### Step 1 – Sanitize Input
Call `sanitize_syllabus_text(raw_syllabus)` if the user pastes a syllabus, or
`sanitize_text(user_request)` for a plain instruction.

### Step 2 – Extract Modules & Topics
Parse the sanitized syllabus to identify:
- Number of modules
- Topics per module
- Estimated complexity per topic (low/medium/high)
- Any importance_score hints from the question bank (if available)

### Step 3 – ReAct Planning Loop
```
THOUGHT: How many study days are available? (ask user if not provided; default 30)
ACTION:  Distribute modules evenly, weight by importance_score.
OBSERVE: Are any modules overloaded (> 3 topics/day)?
THOUGHT: Add spaced repetition gaps (review after 1 day, 3 days, 7 days).
ACTION:  Insert review slots at Days +1, +3, +7 after first exposure.
OBSERVE: Are there Pomodoro sessions planned (25 min work + 5 min break)?
ACTION:  Assign 2–4 Pomodoro sessions per topic based on complexity.
REFLECT: Does the plan end 3 days before the exam (buffer for full revision)?
```

### Step 4 – Output Format
```markdown
## 📅 Study Plan: {subject_name}

**Duration:** {N} days  |  **Exam Date:** {date or TBD}

### Week 1
| Day | Module | Topic | Sessions | Type |
|-----|--------|-------|----------|------|
| 1   | M1     | OSI Model | 2× Pomodoro | New |
| 2   | M1     | OSI Model | 1× Pomodoro | Review (Day+1) |
...

### Spaced Repetition Schedule
- First review: Day +1 after first study
- Second review: Day +3
- Final review: Day +7 (or before exam)

### Active Recall Checkpoints
- End of each day: write 3 key facts from memory
- End of each week: attempt 5 practice questions per module
```

## Security Rules
- Call `sanitize_syllabus_text()` on pasted syllabus content.
- Validate that the syllabus length ≤ 50 000 characters.

## Script Reference
- `scripts/generate_plan.py` – produces a JSON study plan from syllabus text.
