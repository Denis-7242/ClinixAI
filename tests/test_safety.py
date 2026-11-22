"""Tests for independent ClinixAI safety behavior."""

import pytest

from knowledge_base.loader import load_knowledge_base
from safety.disclaimers import (
    DISCLAIMER_FULL,
    EMERGENCY_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
)
from safety.red_flags import check_red_flags
from safety.validation import validate_input
from safety import run_safety_checks


@pytest.fixture
def kb():
    return load_knowledge_base()


def test_every_knowledge_base_red_flag_fires(kb):
    for rule in kb.red_flags:
        symptoms = [
            {"symptom_id": symptom_id, "present": True, "severity": None, "duration_days": None}
            for symptom_id in rule.required_symptom_ids
        ]
        result = check_red_flags(symptoms, kb)
        assert result["triggered"] is True
        assert rule.id in result["trace"]


@pytest.mark.parametrize("present", [False, None])
def test_red_flag_missing_false_or_unknown(kb, present):
    rule = kb.red_flags[0]
    symptoms = [
        {"symptom_id": rule.required_symptom_ids[0], "present": present,
         "severity": None, "duration_days": None}
    ]
    assert check_red_flags(symptoms, kb)["triggered"] is False


def test_red_flag_requires_all_symptoms(kb):
    rule = kb.red_flags[0]
    first = rule.required_symptom_ids[0]
    result = check_red_flags(
        [{"symptom_id": first, "present": True, "severity": None, "duration_days": None}],
        kb,
    )
    assert result["triggered"] is False
    assert any("Near-miss" in warning for warning in result["warnings"])


def test_near_miss_warning(kb):
    rule = kb.red_flags[0]
    result = check_red_flags(
        [{"symptom_id": rule.required_symptom_ids[0], "present": True,
          "severity": None, "duration_days": None}],
        kb,
    )
    assert any("Near-miss" in warning for warning in result["warnings"])


def test_red_flag_is_identical_for_extra_symptoms_age_and_sex(kb):
    rule = kb.red_flags[0]
    complete = [
        {"symptom_id": sid, "present": True, "severity": None, "duration_days": None}
        for sid in rule.required_symptom_ids
    ]
    extra = complete + [
        {"symptom_id": "fever", "present": True, "severity": None, "duration_days": None}
    ]
    a = run_safety_checks(complete, None, None, kb)
    b = run_safety_checks(extra, "65_plus", "female", kb)
    assert a.red_flags == b.red_flags


@pytest.mark.parametrize(
    ("symptoms", "age_group", "sex", "error_fragment"),
    [
        ([], None, None, "At least one"),
        ([{"symptom_id": "fever", "present": True, "severity": 11}], None, None, "Severity"),
        ([{"symptom_id": "fever", "present": True, "duration_days": -1}], None, None, "Duration"),
        ([{"symptom_id": "fever", "present": True, "severity": "bad"}], None, None, "Severity"),
        ([{"symptom_id": "fever", "present": "yes"}], None, None, "Present"),
        ([None], None, None, "must be an object"),
        ([{"symptom_id": "fever", "present": True}], "invalid", None, "age_group"),
        ([{"symptom_id": "fever", "present": True}], None, "invalid", "sex"),
    ],
)
def test_validation_rejections(symptoms, age_group, sex, error_fragment):
    result = validate_input(symptoms, age_group, sex, {"fever"})
    assert result["is_valid"] is False
    assert any(error_fragment in error for error in result["errors"])


def test_duplicate_unknown_and_unicode_validation(kb):
    result = validate_input(
        [
            {"symptom_id": "  fever  ", "present": True, "severity": None, "duration_days": None},
            {"symptom_id": "fever", "present": True, "severity": None, "duration_days": None},
            {"symptom_id": "हे fever", "present": True, "severity": None, "duration_days": None},
        ],
        None,
        None,
        {item.id for item in kb.symptoms},
    )
    assert result["is_valid"] is False
    assert any("Duplicate" in error for error in result["errors"])
    assert any("Unknown symptom" in warning for warning in result["warnings"])


def test_empty_none_and_huge_input(kb):
    assert validate_input(None, None, None, {"fever"})["is_valid"] is False
    huge = [{"symptom_id": "fever", "present": True}] * 10001
    result = validate_input(huge, None, None, {"fever"})
    assert result["is_valid"] is False
    assert any("Too many" in error for error in result["errors"])


def test_disclaimer_exact_and_messages_have_no_medications():
    assert DISCLAIMER_FULL.startswith("ClinixAI is an educational")
    for message in (EMERGENCY_MESSAGE, OUT_OF_SCOPE_MESSAGE, DISCLAIMER_FULL):
        lowered = message.lower()
        assert "mg" not in lowered
        assert "tablet" not in lowered
        assert "prescription" not in lowered
