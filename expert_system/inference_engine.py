"""Forward-chaining weighted symptom matching for ClinixAI.

Expert score formula:
  match = sum(weights for disease symptoms explicitly marked present)
          / sum(weights for all disease symptoms)
  contradiction = sum(weights of strongly expected symptoms explicitly absent
                   / total disease weight)
  score = match * (1 - contradiction)

Unknown answers are ignored. The formula is intentionally simple and not a
clinical diagnostic probability.
"""

from __future__ import annotations

from typing import Any

from knowledge_base.schema import KnowledgeBase


def expert_scores(
    symptoms: list[dict[str, Any]],
    kb: KnowledgeBase,
) -> dict[str, dict[str, Any]]:
    """Calculate an expert score and JSON-serializable explanation per disease."""
    answers = {
        item["symptom_id"]: item.get("present")
        for item in symptoms
        if isinstance(item, dict) and isinstance(item.get("symptom_id"), str)
    }
    results: dict[str, dict[str, Any]] = {}
    for disease in kb.diseases:
        total = sum(item.weight for item in disease.symptoms)
        if total == 0:
            results[disease.id] = {
                "expert_score": 0.0,
                "explanation": {
                    "symptoms_matched": [],
                    "symptoms_contradicted": [],
                    "weights_used": {},
                    "top_contributing_symptoms": [],
                },
            }
            continue

        matched: list[str] = []
        contradicted: list[str] = []
        weights: dict[str, float] = {}
        match_total = 0.0
        contradiction_total = 0.0
        for item in disease.symptoms:
            weights[item.symptom_id] = item.weight
            answer = answers.get(item.symptom_id)
            if answer is True:
                matched.append(item.symptom_id)
                match_total += item.weight
            elif answer is False and item.weight >= 0.5:
                contradicted.append(item.symptom_id)
                contradiction_total += item.weight

        contradiction = contradiction_total / total
        score = (match_total / total) * (1.0 - contradiction)
        score = min(1.0, max(0.0, score))
        ordered = sorted(
            ((answers.get(item.symptom_id) is True, item.weight, item.symptom_id)
             for item in disease.symptoms),
            key=lambda entry: (-entry[0], -entry[1], entry[2]),
        )
        top = [entry[2] for entry in ordered if entry[0]][:3]
        results[disease.id] = {
            "expert_score": score,
            "explanation": {
                "symptoms_matched": matched,
                "symptoms_contradicted": contradicted,
                "weights_used": weights,
                "top_contributing_symptoms": top,
            },
        }
    return results


def suggest_next_questions(
    current_answers: list[dict[str, Any]],
    kb: KnowledgeBase,
    n: int = 3,
) -> list[str]:
    """Suggest unanswered symptoms that most separate the current top diseases."""
    if n <= 0:
        return []
    known = {
        item["symptom_id"]
        for item in current_answers
        if isinstance(item, dict) and isinstance(item.get("symptom_id"), str)
    }
    math = __import__(
        "mathematics.bayes_theorem",
        fromlist=["naive_bayes_posteriors"],
    )
    posteriors = math.naive_bayes_posteriors(current_answers, kb)
    top_ids = sorted(
        posteriors,
        key=lambda disease_id: (-posteriors[disease_id]["posterior"], disease_id),
    )[:3]
    top_sets = {
        disease_id: {
            item.symptom_id: item.weight
            for item in next(
                disease for disease in kb.diseases if disease.id == disease_id
            ).symptoms
        }
        for disease_id in top_ids
    }

    candidates: list[tuple[float, str]] = []
    for symptom in kb.symptoms:
        if symptom.id in known:
            continue
        weights = [
            top_sets[disease_id].get(symptom.id, 0.05)
            for disease_id in top_ids
        ]
        spread = max(weights) - min(weights)
        candidates.append((spread, symptom.id))
    candidates.sort(key=lambda entry: (-entry[0], entry[1]))
    return [symptom_id for _, symptom_id in candidates[:n]]
