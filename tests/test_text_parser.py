"""Tests for rule-based free-text symptom extraction."""

import pytest

from knowledge_base.loader import load_knowledge_base
from services.assessment_service import parse_free_text, run_assessment
from services.text_parser import parse_symptom_text


@pytest.fixture
def kb():
    return load_knowledge_base()


def by_id(result, symptom_id):
    return next(item for item in result.symptoms if item["symptom_id"] == symptom_id)


def test_exact_and_synonym_matches(kb):
    exact = parse_symptom_text("I have a headache", kb)
    synonym = parse_symptom_text("I have a stomach ache", kb)
    assert by_id(exact, "headache")["present"] is True
    assert by_id(synonym, "abdominal_pain")["present"] is True


def test_fuzzy_typo_matches_headache(kb):
    result = parse_symptom_text("I have a hedache", kb)
    assert by_id(result, "headache")["present"] is True


def test_negation(kb):
    result = parse_symptom_text("no cough", kb)
    assert by_id(result, "cough")["present"] is False


def test_mixed_sentence_matches_multiple_symptoms(kb):
    result = parse_symptom_text(
        "I have a high temperature, a cough and a sore throat",
        kb,
    )
    assert {item["symptom_id"] for item in result.symptoms} == {
        "fever",
        "cough",
        "sore_throat",
    }


def test_duration_and_severity_attach_to_nearest_symptom(kb):
    result = parse_symptom_text(
        "severe tummy pain for 3 days and throwing up since yesterday",
        kb,
    )
    abdominal = by_id(result, "abdominal_pain")
    vomiting = by_id(result, "vomiting")
    assert abdominal["severity"] == 8
    assert abdominal["duration_days"] == 3
    assert vomiting["duration_days"] == 1


def test_very_bad_severity_uses_strongest_matching_phrase(kb):
    result = parse_symptom_text("very bad headache", kb)
    assert by_id(result, "headache")["severity"] == 9


def test_unrecognized_phrase_is_returned(kb):
    result = parse_symptom_text(
        "I have a cough and my left elbow is glowing",
        kb,
    )
    assert "left elbow is glowing" in result.unrecognized_phrases


def test_empty_long_and_non_string_input(kb):
    assert parse_symptom_text("", kb).symptoms == []
    long_result = parse_symptom_text("cough " + ("x" * 1100), kb)
    assert any("limited" in warning for warning in long_result.warnings)
    assert parse_symptom_text(None, kb).symptoms == []
    assert parse_symptom_text(None, kb).warnings


def test_unicode_and_non_english_text_do_not_crash(kb):
    result = parse_symptom_text("Nina homa 🤒; café pain", kb)
    assert isinstance(result.symptoms, list)
    assert isinstance(result.unrecognized_phrases, list)


@pytest.mark.parametrize(
    "text",
    ["happy", "running quickly", "the weather is lovely", "xyzzy"],
)
def test_unrelated_words_do_not_false_match(text, kb):
    assert parse_symptom_text(text, kb).symptoms == []


def test_free_text_path_runs_safety_and_flags_urgent_phrase():
    parsed = parse_free_text("I have fever and a stiff neck")
    assert {"fever", "stiff_neck"}.issubset(
        {item["symptom_id"] for item in parsed.symptoms}
    )
    result = run_assessment(parsed.symptoms)
    assert result["red_flag_triggered"] is True
    assert "emergency" in result["red_flag_message"].lower()
