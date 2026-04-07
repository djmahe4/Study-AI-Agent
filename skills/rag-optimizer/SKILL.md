---
name: rag-optimizer
description: Inspect and improve RAG retrieval quality by running the semantic classifier and suggesting better aggregation strategies for a given query.
version: 1.0
tags: [rag, retrieval, optimization, faiss, semantic-search]
category: development
priority: high
allowed_tools: [gemini, faiss, input_validator]
---

# RAG Optimizer Skill

Meta-skill that analyzes a user query, classifies its semantics using
`classify_query_semantics()`, selects the best aggregation strategy, and
explains the retrieval decisions to help improve answer quality.

## When to Use

Trigger this skill when:
- The user asks why an answer was poor or incomplete
- You want to debug RAG retrieval for a specific query
- You need to choose between `summarize-first`, `detailed-chunk-merge`,
  `source-priority`, or `gap-analysis` strategies
- Retrieved chunks appear irrelevant or over-merged

## Instructions

### Step 1 – Sanitize Input
Call `sanitize_question_text(raw_query)` before analysis.

### Step 2 – Classify the Query
```python
from core.input_validator import classify_query_semantics
result = classify_query_semantics(clean_query)
```

Report:
- Primary type and confidence
- All label scores
- Recommended aggregation strategy

### Step 3 – ReAct Retrieval Inspection Loop
```
THOUGHT: What aggregation strategy does the classifier recommend?
ACTION:  Apply the strategy to retrieved chunks.

  summarize-first  → retrieve top-10, pass to LLM for a summary, then
                     extract the specific answer from the summary.
  detailed-chunk-merge → retrieve top-5 per source, interleave by relevance,
                         concatenate into a single context window.
  source-priority  → rank: textbook > PDF notes > YouTube transcript > web.
                     Take top-3 chunks per priority tier.
  gap-analysis     → diff retrieved chunks against syllabus key_points.
                     Flag any key_point not covered by the chunks.

OBSERVE: Did the strategy produce a satisfying answer?
THOUGHT: If not, what is the likely failure mode?
         - Low recall: increase k (top-k)
         - High noise: tighten cosine threshold
         - Missing source: add PDF or YouTube ingestion step
ACTION:  Suggest concrete fix (prompt change, k value, source addition).
REFLECT: Log the classification + strategy decision for future tuning.
```

### Step 4 – Output Format
```markdown
## 🔍 RAG Optimizer Report

**Query:** "{query}"
**Classified As:** {type}  (confidence: {score})
**Strategy Applied:** {strategy}

### Chunk Quality Assessment
| # | Source | Relevance | Coverage |
|---|--------|-----------|----------|
| 1 | syllabus.json | High | ✅ |
| 2 | notes/M1.md   | Medium | ⚠️ Partial |

### Recommendations
- {recommendation 1}
- {recommendation 2}
```

## Security Rules
- Call `sanitize_question_text()` on every user query.
- Do not log raw user queries to disk; log only sanitized versions.

## Script Reference
- `scripts/inspect_retrieval.py` – prints classifier output + mock strategy for a query.
