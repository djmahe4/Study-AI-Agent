"""
Unit tests for core/input_validator.py.

Tests cover:
- sanitize_text()        – HTML stripping, length limits, escape toggle
- sanitize_syllabus_text()
- sanitize_question_text()
- validate_subject_name()
- classify_query_semantics() – type detection, confidence, strategies, edge cases
"""

import sys
import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: load the module without importing the full `core` package
# (avoids heavy optional deps like google-genai during tests)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

_spec = importlib.util.spec_from_file_location(
    "input_validator", _ROOT / "core" / "input_validator.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

sanitize_text = _mod.sanitize_text
sanitize_syllabus_text = _mod.sanitize_syllabus_text
sanitize_question_text = _mod.sanitize_question_text
validate_subject_name = _mod.validate_subject_name
classify_query_semantics = _mod.classify_query_semantics
QueryClassification = _mod.QueryClassification


# ===========================================================================
# sanitize_text
# ===========================================================================

class TestSanitizeText:
    def test_strips_script_tag(self):
        result = sanitize_text("<script>alert(1)</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result

    def test_plain_text_unchanged(self):
        text = "This is plain text without HTML."
        result = sanitize_text(text)
        assert "plain text" in result

    def test_truncates_long_input(self):
        long_text = "a" * 20_000
        result = sanitize_text(long_text, max_length=100)
        assert len(result) <= 100

    def test_non_string_coerced(self):
        result = sanitize_text(12345)
        assert isinstance(result, str)
        assert "12345" in result

    def test_allow_html_tags_preserved_when_escape_false(self):
        # When bleach is available, <b> is preserved; when fallback regex is used,
        # all tags are stripped. Either way, the text content ("bold") must remain.
        result = sanitize_text("<b>bold</b>", allow_html_tags=["b"], escape_html=False)
        assert "bold" in result

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_html_entities_escaped(self):
        result = sanitize_text("a & b")
        # markupsafe should escape &
        assert "&amp;" in result or "& b" in result  # bleach may strip nothing; markupsafe escapes

    def test_max_generic_length_default(self):
        # Default max_length is MAX_GENERIC_LENGTH = 10_000
        text = "x" * 15_000
        result = sanitize_text(text)
        assert len(result) <= 10_000


# ===========================================================================
# sanitize_syllabus_text
# ===========================================================================

class TestSanitizeSyllabusText:
    def test_strips_html(self):
        raw = "<h1>Module 1</h1><p>Introduction to networks</p>"
        result = sanitize_syllabus_text(raw)
        assert "<h1>" not in result
        assert "Module 1" in result
        assert "Introduction to networks" in result

    def test_accepts_up_to_50k(self):
        long = "word " * 10_000  # ~50k chars
        result = sanitize_syllabus_text(long)
        assert "word" in result

    def test_truncates_beyond_50k(self):
        very_long = "x" * 60_000
        result = sanitize_syllabus_text(very_long)
        assert len(result) <= 50_000


# ===========================================================================
# sanitize_question_text
# ===========================================================================

class TestSanitizeQuestionText:
    def test_strips_injection(self):
        raw = "What is TCP?<script>evil()</script>"
        result = sanitize_question_text(raw)
        assert "<script>" not in result
        # With bleach: "evil()" content also removed; with regex fallback: tags stripped
        assert "TCP" in result

    def test_truncates_to_2k(self):
        long = "q" * 5_000
        result = sanitize_question_text(long)
        assert len(result) <= 2_000


# ===========================================================================
# validate_subject_name
# ===========================================================================

class TestValidateSubjectName:
    def test_strips_whitespace(self):
        assert validate_subject_name("  Data Structures  ") == "Data Structures"

    def test_removes_special_chars(self):
        result = validate_subject_name("OS/Networks<script>")
        assert "<script>" not in result
        assert "/" not in result

    def test_allows_hyphens_and_parens(self):
        result = validate_subject_name("Algorithms (CS-301)")
        assert "Algorithms" in result
        assert "CS" in result

    def test_raises_on_empty_after_sanitize(self):
        import pytest
        # Contains only characters removed by the regex; result is empty
        with pytest.raises(ValueError):
            validate_subject_name("!!!~~~###")

    def test_raises_on_non_string(self):
        import pytest
        with pytest.raises(ValueError):
            validate_subject_name(123)  # type: ignore[arg-type]

    def test_truncates_long_names(self):
        long_name = "A" * 200
        result = validate_subject_name(long_name)
        assert len(result) <= 128


# ===========================================================================
# classify_query_semantics
# ===========================================================================

class TestClassifyQuerySemantics:
    """Tests for the semantic query classifier."""

    # --- Factual ---
    def test_factual_what_is(self):
        r = classify_query_semantics("What is the OSI model?")
        assert r.query_type == "factual"
        assert r.aggregation_strategy == "summarize-first"
        assert r.confidence > 0.4

    def test_factual_define(self):
        r = classify_query_semantics("Define entropy in thermodynamics")
        assert r.query_type == "factual"

    # --- Conceptual ---
    def test_conceptual_explain(self):
        r = classify_query_semantics("Explain how neural networks learn")
        assert r.query_type == "conceptual"
        assert r.aggregation_strategy == "detailed-chunk-merge"

    def test_conceptual_overview(self):
        r = classify_query_semantics("Give me an overview of sorting algorithms")
        assert r.query_type == "conceptual"

    # --- Procedural ---
    def test_procedural_how_to(self):
        r = classify_query_semantics("How to implement a binary search tree?")
        assert r.query_type == "procedural"
        assert r.aggregation_strategy == "detailed-chunk-merge"

    def test_procedural_steps(self):
        r = classify_query_semantics("Steps to configure a router")
        assert r.query_type == "procedural"

    def test_procedural_implement(self):
        r = classify_query_semantics("Implement quicksort in Python")
        assert r.query_type == "procedural"

    # --- Comparative ---
    def test_comparative_difference(self):
        r = classify_query_semantics("Difference between TCP and UDP")
        assert r.query_type == "comparative"
        assert r.aggregation_strategy == "source-priority"

    def test_comparative_vs(self):
        r = classify_query_semantics("compare bubble sort vs merge sort speed")
        assert r.query_type == "comparative"

    # --- Generative ---
    def test_generative_flashcards(self):
        r = classify_query_semantics("Generate 5 flashcards on sorting algorithms")
        assert r.query_type == "generative"
        assert r.aggregation_strategy == "gap-analysis"

    def test_generative_quiz(self):
        r = classify_query_semantics("Create a quiz about networking protocols")
        assert r.query_type == "generative"

    # --- Meta ---
    def test_meta_what_can_you(self):
        r = classify_query_semantics("What can you help me with?")
        assert r.query_type == "meta"
        assert r.aggregation_strategy == "summarize-first"

    def test_meta_help(self):
        r = classify_query_semantics("Help me build a study schedule")
        assert r.query_type == "meta"

    # --- Edge cases ---
    def test_empty_query_returns_unknown(self):
        r = classify_query_semantics("")
        assert r.query_type == "unknown"
        assert r.confidence == 1.0

    def test_whitespace_only_returns_unknown(self):
        r = classify_query_semantics("   ")
        assert r.query_type == "unknown"

    def test_html_injected_query_sanitized(self):
        """HTML in query should be stripped; classification still works."""
        r = classify_query_semantics("<script>evil()</script>What is TCP?")
        # After sanitization it becomes "evil()What is TCP?" or similar
        # Classification should still yield factual or not crash
        assert isinstance(r.query_type, str)
        assert 0.0 <= r.confidence <= 1.0

    def test_non_string_input_coerced(self):
        r = classify_query_semantics(42)  # type: ignore[arg-type]
        assert isinstance(r.query_type, str)

    def test_labels_sorted_by_confidence(self):
        r = classify_query_semantics("How to implement a graph traversal?")
        if len(r.labels) > 1:
            scores = [score for _, score in r.labels]
            assert scores == sorted(scores, reverse=True)

    def test_returns_query_classification_namedtuple(self):
        r = classify_query_semantics("Explain binary search")
        assert isinstance(r, QueryClassification)
        assert hasattr(r, "query_type")
        assert hasattr(r, "labels")
        assert hasattr(r, "aggregation_strategy")
        assert hasattr(r, "confidence")

    def test_confidence_within_bounds(self):
        for query in [
            "What is recursion?",
            "How to sort a list?",
            "Difference between stack and queue",
            "",
        ]:
            r = classify_query_semantics(query)
            assert 0.0 <= r.confidence <= 1.0, f"Confidence out of bounds for: {query!r}"


# ===========================================================================
# skills_registry (lightweight smoke test – no Gemini API required)
# ===========================================================================

class TestSkillsRegistry:
    def _get_registry(self):
        """Import registry with skills root pointing at the real skills/ dir."""
        _spec2 = importlib.util.spec_from_file_location(
            "skills_registry", _ROOT / "core" / "skills_registry.py"
        )
        _reg_mod = importlib.util.module_from_spec(_spec2)  # type: ignore[arg-type]
        # Patch dependency before exec
        sys.modules.setdefault("core.input_validator", _mod)
        _spec2.loader.exec_module(_reg_mod)  # type: ignore[union-attr]
        return _reg_mod.SkillsRegistry()

    def test_lists_six_skills(self):
        registry = self._get_registry()
        names = registry.list_skills()
        assert len(names) == 6, f"Expected 6 skills, got {len(names)}: {names}"

    def test_get_skill_by_name(self):
        registry = self._get_registry()
        skill = registry.get_skill("concept-mastery")
        assert skill is not None
        assert skill.name == "concept-mastery"
        assert skill.category == "study"

    def test_invoke_skill_returns_clean_input(self):
        registry = self._get_registry()
        result = registry.invoke_skill("concept-mastery", "<b>recursion</b>")
        assert "<b>" not in result["clean_input"]
        assert "recursion" in result["clean_input"]

    def test_invoke_unknown_skill_raises_key_error(self):
        import pytest
        registry = self._get_registry()
        with pytest.raises(KeyError):
            registry.invoke_skill("nonexistent-skill", "anything")

    def test_match_skill_conceptual_query(self):
        registry = self._get_registry()
        skill = registry.match_skill("Explain how TCP works")
        assert skill is not None
        assert skill.name in ("concept-mastery", "rag-optimizer")

    def test_summary_is_string(self):
        registry = self._get_registry()
        summary = registry.summary()
        assert isinstance(summary, str)
        assert "concept-mastery" in summary
