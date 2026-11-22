"""Naive-Bayes-style posterior scoring for ClinixAI.

All symptom weights are illustrative and are treated as P(symptom present |
disease). The small background probability for an unlisted symptom and the
clipping constant EPS are smoothing assumptions documented in the guide.
"""

from __future__ import annotations

import math
from typing import Any

from knowledge_base.schema import KnowledgeBase

EPS = 0.01
BACKGROUND_PROBABILITY = 0.05


def _clipped(value: float, eps: float = EPS) -> float:
    return min(max(float(value), eps), 1.0 - eps)


def naive_bayes_posteriors(
    symptoms: list[dict[str, Any]],
    kb: KnowledgeBase,
    eps: float = EPS,
    background_probability: float = BACKGROUND_PROBABILITY,
) -> dict[str, dict[str, Any]]:
    """Compute normalized posteriors and per-symptom log-likelihood ratios.

    Unknown answers contribute no likelihood. Present and absent answers use
    Laplace-style clipping. The KB list is a closed-world candidate set.
    """
    answers = {
        item["symptom_id"]: item.get("present")
        for item in symptoms
        if isinstance(item, dict) and isinstance(item.get("symptom_id"), str)
    }
    log_posteriors: dict[str, float] = {}
    contributions: dict[str, dict[str, dict[str, float]]] = {}

    for disease in kb.diseases:
        listed = {
            item.symptom_id: _clipped(item.weight, eps)
            for item in disease.symptoms
        }
        log_score = math.log(max(float(disease.prior_probability), eps))
        disease_contributions: dict[str, dict[str, float]] = {}
        for symptom in kb.symptoms:
            present = answers.get(symptom.id)
            if present is None:
                continue
            probability = listed.get(symptom.id, _clipped(background_probability, eps))
            probability = _clipped(probability, eps)
            baseline = _clipped(background_probability, eps)
            if present is True:
                likelihood = probability
                alternative = baseline
                log_score += math.log(likelihood)
            else:
                likelihood = 1.0 - probability
                alternative = 1.0 - baseline
                log_score += math.log(likelihood)
            ratio = likelihood / alternative
            disease_contributions[symptom.id] = {
                "log_likelihood_ratio": math.log(ratio),
                "probability": likelihood,
            }
        log_posteriors[disease.id] = log_score
        contributions[disease.id] = disease_contributions

    largest = max(log_posteriors.values(), default=0.0)
    weights = {
        disease_id: math.exp(log_score - largest)
        for disease_id, log_score in log_posteriors.items()
    }
    normalizer = sum(weights.values())
    return {
        disease_id: {
            "posterior": weight / normalizer,
            "contributions": contributions[disease_id],
        }
        for disease_id, weight in weights.items()
    }
