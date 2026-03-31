---
name: concept-mastery
description: Explain any topic using analogies, examples, and Feynman-style simplification, then test understanding with a short quiz.
version: 1.0
tags: [learning, education, feynman, explanation, quiz]
category: study
priority: high
allowed_tools: [gemini, input_validator]
---

# Concept Mastery Skill

Help the user deeply understand any concept using the **Feynman Technique**:
explain it simply, identify gaps, then reinforce with a quiz.

## When to Use

Trigger this skill when the user asks to:
- Explain or understand a topic
- Simplify a complex idea
- Get analogies or real-world examples
- Self-test their understanding

## Instructions

### Step 1 – Sanitize Input
Always call `sanitize_text(user_input)` before processing. Reject empty strings.

### Step 2 – Classify Query
Call `classify_query_semantics(clean_input)`. If the result is `conceptual` or
`factual`, proceed. Otherwise, suggest a more appropriate skill.

### Step 3 – ReAct Reasoning Loop
```
THOUGHT: What is the core concept the user wants to understand?
ACTION:  Extract the key concept name and simplify it in ≤ 3 sentences.
OBSERVE: Does the simplification cover the syllabus key points?
THOUGHT: What analogy makes this concrete for a beginner?
ACTION:  Provide 1–2 real-world analogies.
OBSERVE: Are there common misconceptions to address?
THOUGHT: What practice question tests this concept?
ACTION:  Generate 1 multiple-choice and 1 open-ended question.
REFLECT: Did we cover all key sub-topics? If not, recurse on missing ones.
```

### Step 4 – Output Format
```markdown
## 🧠 Concept: {topic_name}

### Simple Explanation (ELI5)
{1–3 sentences, grade-school level}

### Analogy
{Real-world comparison}

### Key Points
- {point 1}
- {point 2}
- {point 3}

### Common Pitfalls
- {pitfall 1}

### Quick Quiz
**Q1 (MCQ):** {question}
a) {A}  b) {B}  c) {C}  d) {D}
**Answer:** {correct}

**Q2 (Open):** {question}
**Model Answer:** {answer}
```

## Security Rules
- Call `sanitize_text()` on every user-provided topic name and question.
- Maximum topic name length: 128 characters.
- If the topic contains HTML or script tags after sanitization, warn the user.

## Example Usage
```
User: Explain recursion to me like I'm 10.
→ Invoke concept-mastery skill
→ classify_query_semantics("Explain recursion to me like I'm 10") → conceptual
→ Run Feynman loop, output formatted explanation + quiz
```

## Script Reference
- `scripts/explain_topic.py` – CLI helper that runs the Feynman loop locally.
