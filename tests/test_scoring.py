import math

from expert_system.inference_engine import expert_scores, suggest_next_questions
from knowledge_base.loader import load_knowledge_base
from mathematics.bayes_theorem import naive_bayes_posteriors


def test_bayes_hand_example_and_normalization():
    kb = load_knowledge_base()
    symptoms = [{"symptom_id": "fever", "present": True}]
    result = naive_bayes_posteriors(symptoms, kb)
    assert math.isclose(sum(item["posterior"] for item in result.values()), 1.0, abs_tol=1e-9)
    for item in result.values():
        assert "contributions" in item
        assert "fever" in item["contributions"]


def test_unknown_does_not_change_posterior():
    kb = load_knowledge_base()
    baseline = naive_bayes_posteriors([], kb)
    unknown = naive_bayes_posteriors(
        [{"symptom_id": "fever", "present": None}], kb
    )
    assert {k: v["posterior"] for k, v in baseline.items()} == {
        k: v["posterior"] for k, v in unknown.items()
    }


def test_high_weight_present_increases_disease_posterior():
    kb = load_knowledge_base()
    before = naive_bayes_posteriors([], kb)["influenza"]["posterior"]
    after = naive_bayes_posteriors(
        [{"symptom_id": "fever", "present": True}], kb
    )["influenza"]["posterior"]
    assert after > before


def test_numerical_stability_many_answers():
    kb = load_knowledge_base()
    symptoms = [
        {"symptom_id": symptom.id, "present": index % 2 == 0}
        for index, symptom in enumerate(kb.symptoms)
    ]
    result = naive_bayes_posteriors(symptoms, kb)
    assert math.isclose(sum(item["posterior"] for item in result.values()), 1.0)
    assert all(0.0 <= item["posterior"] <= 1.0 for item in result.values())


def test_expert_typical_match_and_contradiction():
    kb = load_knowledge_base()
    typical = [
        {"symptom_id": "fever", "present": True},
        {"symptom_id": "cough", "present": True},
    ]
    result = expert_scores(typical, kb)
    assert 0.0 <= result["influenza"]["expert_score"] <= 1.0
    assert "fever" in result["influenza"]["explanation"]["symptoms_matched"]

    contradicted = expert_scores([
        {"symptom_id": "fever", "present": False},
    ], kb)
    assert "fever" in contradicted["influenza"]["explanation"]["symptoms_contradicted"]


def test_expert_unknown_handling():
    kb = load_knowledge_base()
    result = expert_scores([{"symptom_id": "fever", "present": None}], kb)
    assert all(
        not item["explanation"]["symptoms_matched"]
        for item in result.values()
    )


def test_next_questions_are_unanswered_and_deterministic():
    kb = load_knowledge_base()
    answers = [{"symptom_id": "fever", "present": True}]
    first = suggest_next_questions(answers, kb, n=3)
    second = suggest_next_questions(answers, kb, n=3)
    assert first == second
    assert len(first) == 3
    assert "fever" not in first
