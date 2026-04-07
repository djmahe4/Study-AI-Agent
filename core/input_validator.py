"""
Input Validation and Semantic Classification Module for AI Learning Engine.

This module provides two main capabilities:

1. **Sanitization** – clean user-supplied text before it reaches LLM prompts
   or the database (bleach + markupsafe stack).

2. **Semantic query classification** – lightweight, fast hybrid classifier that
   decides *what kind* of query a user is asking so the RAG pipeline can
   choose the best aggregation strategy.

Security Stack
--------------
1. **markupsafe.escape** – converts HTML special characters (&, <, >, ", ')
   into their safe equivalents so that they cannot be executed as HTML/script.
2. **bleach.clean** – strips or escapes HTML tags from free-form text so that
   only plain text (or a small safe-list of tags) is kept.

Semantic Classification
-----------------------
``classify_query_semantics()`` uses a *fast hybrid approach*:

* **Tier 1 – keyword/regex heuristics** (~0 ms): pattern-matched signals for
  common query intents (factual, conceptual, procedural, comparative,
  generative, meta).
* **Tier 2 – TF-IDF cosine similarity** (optional, ~5–30 ms): when the keyword
  pass is inconclusive (< 0.45 confidence), a small in-process TF-IDF model
  is used to compare the query against representative seed phrases.

Each result is a :class:`QueryClassification` named-tuple containing:

- ``query_type``: primary label
  (``factual`` | ``conceptual`` | ``procedural`` | ``comparative`` |
  ``generative`` | ``meta`` | ``unknown``)
- ``labels``: ordered list of ``(label, confidence_0_to_1)`` pairs
- ``aggregation_strategy``: one of
  ``summarize-first`` | ``detailed-chunk-merge`` |
  ``source-priority`` | ``gap-analysis``
- ``confidence``: top confidence score (0.0–1.0)

Why does this matter for an LLM integration?
---------------------------------------------
When a user pastes a syllabus or types a question, the text is placed directly
inside a prompt string that is sent to the Gemini API and then stored in files.
Without sanitization, a malicious user could:
  - Inject HTML/script tags that get rendered in a browser (XSS).
  - Attempt *prompt-injection* by embedding instructions inside the input
    (e.g., "Ignore all previous instructions and do X").

This module adds a first-pass defence by:
  - Removing HTML markup with bleach.
  - Escaping any remaining special characters with markupsafe.
  - Trimming excessively long inputs to prevent denial-of-service.

Simple Explanation (for younger learners)
------------------------------------------
Imagine you have a magic box that repeats everything you say.
If someone says "Open the door!", the box might actually open the door.
*Sanitization* is like putting a filter on the box so that only safe,
plain words go through – not special commands.

Usage
-----
>>> from core.input_validator import sanitize_text, validate_subject_name
>>> safe = sanitize_text("<b>Hello</b>")
>>> print(safe)  # Hello
>>> name = validate_subject_name("  Data Structures!! ")
>>> print(name)  # Data Structures

>>> from core.input_validator import classify_query_semantics
>>> result = classify_query_semantics("What is the OSI model?")
>>> print(result.query_type)            # factual
>>> print(result.aggregation_strategy)  # summarize-first
>>> print(result.confidence)            # 0.9
"""

import re
import math
import logging
from typing import Optional, List, Tuple, NamedTuple, Dict

from markupsafe import escape as markup_escape

try:
    import bleach
    _BLEACH_AVAILABLE = True
except ImportError:  # pragma: no cover – bleach is in requirements.txt
    _BLEACH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum character lengths for different input categories
MAX_SYLLABUS_LENGTH: int = 50_000   # ~50 KB of raw syllabus text
MAX_SUBJECT_NAME_LENGTH: int = 128
MAX_QUESTION_LENGTH: int = 2_000
MAX_GENERIC_LENGTH: int = 10_000

# ---------------------------------------------------------------------------
# Core sanitization helpers
# ---------------------------------------------------------------------------


def _bleach_clean(text: str, allow_tags: Optional[list] = None) -> str:
    """
    Remove HTML tags from *text* using bleach.

    Parameters
    ----------
    text:
        Raw user-supplied string.
    allow_tags:
        Optional list of HTML tag names to preserve (e.g. ``["b", "i"]``).
        Defaults to an empty list (strip everything).

    Returns
    -------
    str
        Plain text with all disallowed HTML removed.
    """
    if not _BLEACH_AVAILABLE:
        # Fallback: use a simple regex to strip tags
        logger.warning("bleach not installed; falling back to regex tag stripping.")
        return re.sub(r"<[^>]*>", "", text)

    tags = allow_tags if allow_tags is not None else []
    return bleach.clean(text, tags=tags, strip=True)


def sanitize_text(
    text: str,
    *,
    allow_html_tags: Optional[list] = None,
    max_length: int = MAX_GENERIC_LENGTH,
    escape_html: bool = True,
) -> str:
    """
    Sanitize free-form user text for safe use in LLM prompts and storage.

    The function performs the following steps in order:

    1. Truncate the string to *max_length* characters.
    2. Strip HTML tags (via bleach).
    3. Escape remaining HTML special characters (via markupsafe), **unless**
       *escape_html* is ``False`` (used when you still want to preserve safe
       HTML for template rendering).

    Parameters
    ----------
    text:
        The raw input string from the user.
    allow_html_tags:
        HTML tags to preserve after bleach cleaning (e.g. ``["b", "i", "ul"]``).
        If ``None``, all HTML is removed.
    max_length:
        Maximum allowed length.  Text beyond this limit is silently truncated.
    escape_html:
        When ``True`` (default), any remaining ``<``, ``>``, ``&``, ``"`` and
        ``'`` characters are HTML-escaped **after** bleach has run.
        Set to ``False`` when passing text to a Jinja2/Flask template that
        auto-escapes (to avoid double-escaping).

    Returns
    -------
    str
        A sanitized, plain-text string safe for use in prompts.

    Examples
    --------
    >>> sanitize_text("<script>alert(1)</script>Hello!")
    'alert(1)Hello!'

    >>> sanitize_text("<b>bold text</b>", allow_html_tags=["b"], escape_html=False)
    '<b>bold text</b>'
    """
    if not isinstance(text, str):
        text = str(text)

    # 1. Truncate
    if len(text) > max_length:
        logger.warning(
            "Input truncated from %d to %d characters.", len(text), max_length
        )
        text = text[:max_length]

    # 2. bleach – strip HTML tags
    text = _bleach_clean(text, allow_tags=allow_html_tags)

    # 3. markupsafe – escape residual special chars
    if escape_html:
        text = str(markup_escape(text))

    return text


def sanitize_syllabus_text(raw_syllabus: str) -> str:
    """
    Sanitize raw syllabus text before it is embedded in a Gemini prompt.

    Strips all HTML and escapes special characters.  Syllabus inputs are
    typically plain text from a ``.txt`` file or a text box, so we do not
    allow any HTML tags.

    Parameters
    ----------
    raw_syllabus:
        The unsanitized syllabus string pasted or read from a file.

    Returns
    -------
    str
        Sanitized syllabus text.
    """
    return sanitize_text(raw_syllabus, max_length=MAX_SYLLABUS_LENGTH)


def sanitize_question_text(raw_question: str) -> str:
    """
    Sanitize a user-supplied question before sending it to the LLM.

    Parameters
    ----------
    raw_question:
        The raw question string entered by the user.

    Returns
    -------
    str
        Sanitized question text.
    """
    return sanitize_text(raw_question, max_length=MAX_QUESTION_LENGTH)


def validate_subject_name(name: str) -> str:
    """
    Validate and clean a subject name.

    Rules:
    - Strips leading/trailing whitespace.
    - Allows letters, digits, spaces, hyphens, parentheses, and commas.
    - Removes all other special characters to prevent path-traversal or
      injection issues when the name is used to create file-system paths.
    - Truncates to ``MAX_SUBJECT_NAME_LENGTH``.
    - Raises ``ValueError`` if the result is empty.

    Parameters
    ----------
    name:
        The raw subject name provided by the user.

    Returns
    -------
    str
        A cleaned subject name.

    Raises
    ------
    ValueError
        If the sanitized name is empty.

    Examples
    --------
    >>> validate_subject_name("  Data Structures!! ")
    'Data Structures'
    >>> validate_subject_name("OS/Networks<script>")
    'OSNetworks'
    """
    if not isinstance(name, str):
        raise ValueError("Subject name must be a string.")

    name = name.strip()[:MAX_SUBJECT_NAME_LENGTH]
    # Keep only safe characters
    name = re.sub(r"[^\w\s\-\(\),]", "", name).strip()

    if not name:
        raise ValueError(
            "Subject name is empty after sanitization. "
            "Please use only letters, digits, spaces, hyphens, parentheses, or commas."
        )
    return name


# Pre-compiled pattern for Mermaid label sanitization (module-level for performance)
_MERMAID_UNSAFE_RE = re.compile(r'["\(\)\[\]\{\}]')


def sanitize_mermaid_label(label: str, max_length: int = 80) -> str:
    """
    Sanitize a Mermaid diagram node label.

    Strips HTML, escapes special characters, then removes characters that
    break Mermaid syntax (``"``, ``(``, ``)``, ``[``, ``]``, ``{``, ``}``).

    Parameters
    ----------
    label:
        The raw node label text (e.g. from a syllabus line).
    max_length:
        Maximum length of the label.  Defaults to 80 characters.

    Returns
    -------
    str
        A safe, Mermaid-compatible node label.
        Falls back to ``"Untitled"`` if the result is empty.

    Examples
    --------
    >>> sanitize_mermaid_label("Module (1): Intro [Networks]")
    'Module 1: Intro Networks'
    >>> sanitize_mermaid_label("<b>Hello</b>")
    'Hello'
    """
    clean = sanitize_text(label.strip(), max_length=max_length, escape_html=False)
    clean = _MERMAID_UNSAFE_RE.sub("", clean).strip()
    return clean or "Untitled"


# ===========================================================================
# Semantic Query Classification
# ===========================================================================

class QueryClassification(NamedTuple):
    """
    Result of :func:`classify_query_semantics`.

    Attributes
    ----------
    query_type:
        Primary semantic label for the query.
        One of: ``factual``, ``conceptual``, ``procedural``, ``comparative``,
        ``generative``, ``meta``, ``unknown``.
    labels:
        All detected labels sorted by confidence descending.
        Each element is a ``(label: str, confidence: float)`` tuple.
    aggregation_strategy:
        Recommended RAG aggregation strategy for this query type:

        * ``summarize-first`` – retrieve broadly, then summarise.
        * ``detailed-chunk-merge`` – gather many specific chunks and merge.
        * ``source-priority`` – prefer authoritative sources (textbook > web).
        * ``gap-analysis`` – surface what the knowledge base is missing.
    confidence:
        Confidence score of the primary label (0.0–1.0).
    """
    query_type: str
    labels: List[Tuple[str, float]]
    aggregation_strategy: str
    confidence: float


# ---------------------------------------------------------------------------
# Internal: keyword/regex patterns (Tier 1)
# ---------------------------------------------------------------------------

# Each entry: (label, list_of_compiled_patterns, base_score)
# Patterns are matched against the lower-cased, stripped query.
# Each *additional* matching pattern beyond the first adds +0.15 (capped at 0.95).
# Rule: one regex per distinct concept/signal so that multiple hits accumulate.
_QUERY_PATTERNS: List[Tuple[str, List[re.Pattern], float]] = [
    (
        "factual",
        [
            # Strong definitional / retrieval signals
            re.compile(r"\b(what\s+is|what\s+are|define|definition\s+of|meaning\s+of)\b"),
            re.compile(r"\b(who\s+is|when\s+did|where\s+is|how\s+many|which\s+one)\b"),
            re.compile(r"\b(acronym|abbreviation|full\s+form)\b"),
            # Bare question mark only adds a very small signal (0.1) – not enough alone
            re.compile(r"\?\s*$"),
        ],
        # base_score: low by itself; second match needed for certainty
        0.45,
    ),
    (
        "conceptual",
        [
            re.compile(r"\b(explain|describe|why\s+does|why\s+is|how\s+does|how\s+do)\b"),
            re.compile(r"\b(concept\s+of|understand|overview|summarize|significance|purpose\s+of)\b"),
            re.compile(r"\b(principle|theory|model|framework|paradigm|architecture)\b"),
        ],
        0.55,
    ),
    (
        "procedural",
        [
            # "how to" is almost exclusively procedural – give it its own strong pattern
            re.compile(r"\bhow\s+to\b"),
            re.compile(r"\b(steps?\s+(to|for)|guide\s+(to|for)|tutorial\s+(for|on))\b"),
            re.compile(r"\b(implement|create|build|configure|set\s+up|install|deploy|run|execute)\b"),
            re.compile(r"\b(process\s+of|procedure|workflow|walkthrough)\b"),
        ],
        0.55,
    ),
    (
        "comparative",
        [
            re.compile(r"\b(difference\s+between|differences?\s+of)\b"),
            re.compile(r"\b(compare|comparison\s+between|vs\.?|versus|contrast)\b"),
            re.compile(r"\b(similarities|advantages?\s+of|disadvantages?\s+of|pros?\s+and\s+cons?)\b"),
            re.compile(r"\b(better\s+than|worse\s+than|prefer\s+over)\b"),
        ],
        0.55,
    ),
    (
        "generative",
        [
            re.compile(r"\b(generate|produce|make|draft|design)\b"),
            re.compile(r"\b(create|write|give\s+me|list|enumerate|provide\s+examples?)\b"),
            re.compile(r"\b(quiz|flashcard|practice\s+questions?|exercise|problem|mindmap|diagram)\b"),
        ],
        0.55,
    ),
    (
        "meta",
        [
            # Keep each distinct signal as its own pattern for score accumulation
            re.compile(r"\bwhat\s+can\s+you\b"),
            re.compile(r"\b(help|help\s+me)\b"),
            re.compile(r"\b(show\s+me|capabilities|features|skills|available\s+commands?)\b"),
            re.compile(r"\b(study\s+plan|study\s+schedule|revision\s+plan|roadmap)\b"),
            re.compile(r"\bsummarize\s+my\s+syllabus\b"),
        ],
        0.50,
    ),
]

# Aggregation strategy mapping for each primary label
_STRATEGY_MAP: dict = {
    "factual": "summarize-first",
    "conceptual": "detailed-chunk-merge",
    "procedural": "detailed-chunk-merge",
    "comparative": "source-priority",
    "generative": "gap-analysis",
    "meta": "summarize-first",
    "unknown": "summarize-first",
}

# ---------------------------------------------------------------------------
# Internal: TF-IDF fallback (Tier 2)
# ---------------------------------------------------------------------------

# Seed phrases per label used to build the micro TF-IDF corpus
_SEED_PHRASES: dict = {
    "factual": [
        "what is machine learning",
        "define recursion",
        "what are the layers of OSI model",
        "meaning of entropy",
    ],
    "conceptual": [
        "explain how neural networks work",
        "why does the internet use TCP IP",
        "describe the concept of virtual memory",
        "overview of sorting algorithms",
    ],
    "procedural": [
        "how to implement binary search",
        "steps to configure a router",
        "guide to building a REST API",
        "how to run the study agent",
    ],
    "comparative": [
        "difference between TCP and UDP",
        "compare bubble sort and merge sort",
        "TCP vs UDP advantages",
        "SQL versus NoSQL databases",
    ],
    "generative": [
        "generate flashcards for data structures",
        "create a quiz about networking",
        "produce a mindmap of operating systems",
        "give me example problems on trees",
    ],
    "meta": [
        "what can you do",
        "show me available commands",
        "help me make a study plan",
        "summarize my syllabus for me",
    ],
}



def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer (no external dependency)."""
    return re.findall(r"[a-z]+", text.lower())


def _tf(tokens: List[str]) -> dict:
    """Compute term frequencies for a token list."""
    freq: dict = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = len(tokens) or 1
    return {t: c / total for t, c in freq.items()}


# Pre-calculate seed phrase vectors once at module load to avoid redundant work in Tier 2
_SEED_PHRASE_VECTORS: Dict[str, Dict[str, float]] = {}
for _label, _phrases in _SEED_PHRASES.items():
    _combined: Dict[str, float] = {}
    _denominator = len(_phrases) or 1
    for _phrase in _phrases:
        _tokens = _tokenize(_phrase)
        _tf_map = _tf(_tokens)
        for _token, _freq in _tf_map.items():
            _combined[_token] = _combined.get(_token, 0.0) + (_freq / _denominator)
    _SEED_PHRASE_VECTORS[_label] = _combined


def _cosine(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two TF dicts."""
    keys = set(vec_a) & set(vec_b)
    if not keys:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tfidf_classify(query_tokens: List[str]) -> List[Tuple[str, float]]:
    """
    Compute per-label cosine similarity between the query and seed phrases.

    Returns a list of ``(label, score)`` sorted by score descending.
    The scores are *not* probabilities – they are raw cosine similarities
    in [0, 1].  The caller normalises them.
    """
    query_tf = _tf(query_tokens)
    scores: List[Tuple[str, float]] = []

    for label, combined_vector in _SEED_PHRASE_VECTORS.items():
        sim = _cosine(query_tf, combined_vector)
        scores.append((label, round(sim, 4)))

    return sorted(scores, key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_query_semantics(raw_query: str) -> QueryClassification:
    """
    Classify the semantic type of a user query for RAG pipeline routing.

    Uses a two-tier hybrid approach:

    * **Tier 1** (always runs, ~0 ms): keyword/regex pattern matching against
      curated signal lists for each query type.
    * **Tier 2** (runs when Tier 1 confidence < 0.45, ~5–30 ms): TF-IDF
      cosine similarity against labelled seed phrases.

    The input is automatically sanitized via :func:`sanitize_question_text`
    before any analysis so this function is safe to call with raw user input.

    Parameters
    ----------
    raw_query:
        The raw question or instruction typed by the user.

    Returns
    -------
    QueryClassification
        Named-tuple with fields:
        ``query_type``, ``labels``, ``aggregation_strategy``, ``confidence``.

    Examples
    --------
    >>> r = classify_query_semantics("What is the TCP/IP model?")
    >>> r.query_type
    'factual'
    >>> r.aggregation_strategy
    'summarize-first'
    >>> r.confidence >= 0.5
    True

    >>> r2 = classify_query_semantics("How to implement a binary search tree?")
    >>> r2.query_type
    'procedural'

    >>> r3 = classify_query_semantics("Difference between TCP and UDP")
    >>> r3.query_type
    'comparative'

    Notes
    -----
    * Confidence scores are heuristic estimates, not calibrated probabilities.
    * For mixed/ambiguous queries all matching labels are returned in ``labels``
      so callers can implement their own threshold logic.
    * This function is designed to complete in well under 50 ms on typical
      hardware, making it suitable for real-time interactive sessions.
    """
    if not isinstance(raw_query, str):
        raw_query = str(raw_query)

    # Always sanitize input first
    clean_query = sanitize_question_text(raw_query)
    query_lower = clean_query.lower().strip()

    if not query_lower:
        logger.warning("classify_query_semantics received an empty query after sanitization.")
        return QueryClassification(
            query_type="unknown",
            labels=[("unknown", 1.0)],
            aggregation_strategy=_STRATEGY_MAP["unknown"],
            confidence=1.0,
        )

    # ------------------------------------------------------------------
    # Tier 1: keyword/regex heuristics
    # ------------------------------------------------------------------
    tier1_scores: dict = {}

    WEAK_QM_IDX = 3  # Index of bare-? pattern in _QUERY_PATTERNS["factual"]
    for label, patterns, base_score in _QUERY_PATTERNS:
        # Check specific pattern matches to implement heuristics
        matches = [p.search(query_lower) for p in patterns]
        matched_indices = [idx for idx, m in enumerate(matches) if m]
        matched_count = len(matched_indices)

        if matched_count > 0:
            # Each additional pattern match adds 0.15, capped at 0.95.
            # Special case: for "factual", the bare-? pattern (index 3) is weak on its
            # own – only promote to base_score when there is at least one
            # *strong* definitional signal too (i.e., matched_count >= 2).
            if label == "factual" and matched_count == 1 and matched_indices[0] == WEAK_QM_IDX:
                # Only the weak trailing-? matched; give a very small signal
                score = 0.35
            else:
                score = min(base_score + (matched_count - 1) * 0.15, 0.95)
            tier1_scores[label] = max(tier1_scores.get(label, 0.0), score)

    # Sort by score descending
    tier1_sorted = sorted(tier1_scores.items(), key=lambda x: x[1], reverse=True)
    top_score = tier1_sorted[0][1] if tier1_sorted else 0.0

    # ------------------------------------------------------------------
    # Tier 2: TF-IDF fallback (only when Tier 1 is inconclusive)
    # ------------------------------------------------------------------
    if top_score < 0.45:
        query_tokens = _tokenize(query_lower)
        tfidf_scores = _tfidf_classify(query_tokens)

        # Blend Tier 1 and Tier 2 scores
        blended: dict = {}
        for label, score in tfidf_scores:
            t1 = tier1_scores.get(label, 0.0)
            # Weighted blend: 40% TF-IDF + 60% keyword (if keyword hit exists)
            if t1 > 0:
                blended[label] = 0.4 * score + 0.6 * t1
            else:
                blended[label] = 0.4 * score

        # Merge with any Tier 1 scores not in TF-IDF
        for label, score in tier1_sorted:
            if label not in blended:
                blended[label] = score

        final_sorted = sorted(blended.items(), key=lambda x: x[1], reverse=True)
        logger.debug(
            "classify_query_semantics – Tier 2 activated. Top: %s",
            final_sorted[:3],
        )
    else:
        final_sorted = tier1_sorted
        logger.debug(
            "classify_query_semantics – Tier 1 sufficient. Top: %s",
            final_sorted[:3],
        )

    # ------------------------------------------------------------------
    # Build output
    # ------------------------------------------------------------------
    if not final_sorted:
        primary_label = "unknown"
        top_confidence = 0.5
    else:
        primary_label, top_confidence = final_sorted[0]

    labels_out: List[Tuple[str, float]] = [
        (lbl, round(score, 4)) for lbl, score in final_sorted
    ]

    # Ensure we always have an "unknown" fallback entry if nothing matched
    if not labels_out:
        labels_out = [("unknown", 0.5)]

    return QueryClassification(
        query_type=primary_label,
        labels=labels_out,
        aggregation_strategy=_STRATEGY_MAP.get(primary_label, "summarize-first"),
        confidence=round(top_confidence, 4),
    )

