"""
Input Validation Module for AI Learning Engine.

This module provides functions to sanitize and validate all user-supplied
text before it is embedded into LLM prompts or stored in the database.

Security Stack
--------------
1. **markupsafe.escape** – converts HTML special characters (&, <, >, ", ')
   into their safe equivalents so that they cannot be executed as HTML/script.
2. **bleach.clean** – strips or escapes HTML tags from free-form text so that
   only plain text (or a small safe-list of tags) is kept.

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
"""

import re
import logging
from typing import Optional

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
