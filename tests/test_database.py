import pytest

from database import repository as repo
from database.db import init_db


@pytest.fixture(autouse=True)
def fresh_db():
    # In-memory SQLite: isolated per test, nothing written to disk.
    init_db("sqlite:///:memory:")
    yield


SYMPTOMS = [
    {"symptom_id": "fever", "present": True, "severity": 7, "duration_days": 3},
    {"symptom_id": "cough", "present": True, "severity": 4, "duration_days": 5},
    {"symptom_id": "rash", "present": False},
    {"symptom_id": "headache", "present": None},
]
RESULTS = [
    {"disease_id": "flu", "disease_name": "Influenza", "final_score": 0.62,
     "expert_score": 0.7, "math_score": 0.6, "ml_score": 0.55, "confidence": 0.62,
     "explanation": {"rules": ["R1", "R4"]}, "advice": "Rest and see a clinician if worse."},
    {"disease_id": "cold", "disease_name": "Common Cold", "final_score": 0.25},
]


def test_create_and_read_session():
    sid = repo.create_session(age_group="18-29", sex="F", kb_version="1.0", model_version="1.0")
    data = repo.get_session_data(sid)
    assert data["id"] == sid
    assert data["age_group"] == "18-29"
    assert data["symptoms"] == [] and data["results"] == []


def test_save_symptoms_and_results_roundtrip():
    sid = repo.create_session()
    repo.save_symptoms(sid, SYMPTOMS)
    repo.save_results(sid, RESULTS, red_flag_triggered=True)
    data = repo.get_session_data(sid)
    assert len(data["symptoms"]) == 4
    assert [r["rank"] for r in data["results"]] == [1, 2]
    assert data["results"][0]["disease_id"] == "flu"
    assert data["results"][0]["explanation"] == {"rules": ["R1", "R4"]}
    assert data["red_flag_triggered"] is True


def test_save_symptoms_replaces_previous():
    sid = repo.create_session()
    repo.save_symptoms(sid, SYMPTOMS)
    repo.save_symptoms(sid, SYMPTOMS[:1])
    assert len(repo.get_session_data(sid)["symptoms"]) == 1


def test_invalid_severity_rejected():
    sid = repo.create_session()
    with pytest.raises(ValueError):
        repo.save_symptoms(sid, [{"symptom_id": "fever", "present": True, "severity": 11}])


def test_unknown_session_raises():
    with pytest.raises(LookupError):
        repo.save_symptoms("nope", SYMPTOMS)


def test_feedback_validation_and_stats():
    sid = repo.create_session()
    repo.save_results(sid, RESULTS)
    repo.add_feedback(sid, 4, "helpful")
    with pytest.raises(ValueError):
        repo.add_feedback(sid, 9)
    stats = repo.get_stats()
    assert stats["total_sessions"] == 1
    assert stats["average_rating"] == 4.0
    assert stats["top_conditions"][0] == {"disease_name": "Influenza", "count": 1}


def test_list_sessions_newest_first():
    a = repo.create_session()
    b = repo.create_session()
    ids = [s["id"] for s in repo.list_sessions()]
    assert set(ids) == {a, b}


def test_delete_session_cascades():
    sid = repo.create_session()
    repo.save_symptoms(sid, SYMPTOMS)
    repo.save_results(sid, RESULTS)
    assert repo.delete_session(sid) is True
    assert repo.get_session_data(sid) is None
    assert repo.delete_session(sid) is False
    assert repo.get_stats()["total_sessions"] == 0


def test_delete_all_data():
    repo.create_session()
    repo.create_session()
    repo.delete_all_data()
    assert repo.list_sessions() == []