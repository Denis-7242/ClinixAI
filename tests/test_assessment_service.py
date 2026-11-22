"""Integration tests for the assessment service."""

import pytest

from database.db import init_db
from services import assessment_service


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch):
    init_db("sqlite:///:memory:")


def fever_answers():
    return [
        {"symptom_id": "fever", "present": True,
         "severity": 5, "duration_days": 2},
        {"symptom_id": "cough", "present": True,
         "severity": 4, "duration_days": 3},
    ]


def test_typical_assessment_persists_and_returns_results():
    result = assessment_service.run_assessment(fever_answers())
    assert result["valid"] is True
    assert result["session_id"]
    assert len(result["results"]) == 10
    assert result["results"][0]["explanation"]
    assert assessment_service.get_assessment(result["session_id"])


def test_ambiguous_assessment():
    result = assessment_service.run_assessment([])
    assert result["valid"] is False


def test_red_flag_assessment_flag_not_suppressed():
    result = assessment_service.run_assessment([
        {"symptom_id": "chest_pain", "present": True,
         "severity": 8, "duration_days": 1},
        {"symptom_id": "shortness_of_breath", "present": True,
         "severity": 9, "duration_days": 1},
    ])
    assert result["red_flag_triggered"] is True
    assert result["red_flag_message"]
    assert len(result["results"]) == 10


def test_invalid_input_does_not_persist():
    before = len(assessment_service.get_history())
    result = assessment_service.run_assessment([
        {"symptom_id": "fever", "present": True, "severity": 11},
    ])
    assert result["valid"] is False
    assert result["session_id"] is None
    assert len(assessment_service.get_history()) == before


def test_empty_input():
    result = assessment_service.run_assessment([])
    assert result["valid"] is False
    assert result["results"] == []


def test_ml_missing_fallback(monkeypatch):
    def unavailable(_symptoms):
        raise FileNotFoundError("Retrain model")

    monkeypatch.setattr(assessment_service, "predict_proba", unavailable)
    result = assessment_service.run_assessment(fever_answers())
    assert result["valid"] is True
    assert result["versions"]["model"] == "math-only"
    assert any("Retrain" in warning for warning in result["warnings"])
    assert all("ml_score" in item for item in result["results"])


def test_history_delete_and_stats():
    result = assessment_service.run_assessment(fever_answers())
    assert len(assessment_service.get_history()) == 1
    assert assessment_service.get_assessment(result["session_id"])
    assert assessment_service.get_stats()["total_sessions"] == 1
    assert assessment_service.delete_assessment(result["session_id"]) is True
    assert assessment_service.get_assessment(result["session_id"]) is None
