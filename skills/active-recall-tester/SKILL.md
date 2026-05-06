---
name: active-recall-tester
description: Generate flashcards and practice questions for any topic, then auto-grade answers and track retention.
version: 1.0
tags: [learning, active-recall, flashcards, quiz, spaced-repetition]
category: study
priority: high
allowed_tools: [gemini, input_validator, faiss]
---

# Active Recall Tester Skill

Generate high-quality **flashcards** and **practice questions**, collect user
answers, auto-grade them, and track a simple retention score.

## When to Use

Trigger this skill when the user asks to:
- Create or review flashcards
- Test themselves on a topic
- Get practice questions
- Check their retention on previously studied material

## Instructions

### Step 1 – Sanitize Input
Call `sanitize_question_text(topic_or_question)` on any user-provided text.

### Step 2 – Classify Query
Call `classify_query_semantics(clean_input)`. This skill is relevant for
`generative` and `factual` query types.

### Step 3 – ReAct Generation Loop
```
THOUGHT: What type of recall exercise fits this topic best?
          (definition → flashcard, algorithm → MCQ, concept → open-ended)
ACTION:  Generate N flashcards (front: question, back: answer).
OBSERVE: Do the cards cover all key_points from the topic model?
THOUGHT: Are there higher-difficulty open-ended questions to add?
ACTION:  Add 2–3 open-ended questions at medium/hard difficulty.
REFLECT: Total cards ≤ 20 for a single session. Paginate if more needed.
```

### Step 4 – Grading Loop
For each question presented to the user:
1. Show front of flashcard (question).
2. Wait for user answer.
3. Compare against model answer (keyword overlap ≥ 60% → correct).
4. Record: correct / incorrect / skipped.
5. Update retention score = correct / total.

### Step 5 – Retention Tracking Output
```markdown
## 🎯 Session Results: {topic}

| # | Question | Your Answer | Correct? |
|---|----------|-------------|----------|
| 1 | What is... | ... | ✅ |
| 2 | Explain... | ... | ❌ |

**Retention Score:** {score}%
**Recommendation:** Review cards 2, 5 again in 3 days (spaced repetition).
```

## Security Rules
- Call `sanitize_question_text()` on all user-supplied answers before scoring.
- Call `sanitize_text()` on topic names before lookup in the knowledge base.

## Script Reference
- `scripts/flashcard_session.py` – interactive terminal flashcard runner.
