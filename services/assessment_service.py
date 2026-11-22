"""Only application entry point for clinical assessments."""

from __future__ import annotations

from typing import Any

import streamlit as st

from database import repository
from expert_system.inference_engine import expert_scores, suggest_next_questions
from knowledge_base.loader import load_knowledge_base
from mathematics.bayes_theorem import naive_bayes_posteriors
from machine_learning.predict import predict_proba
from safety import run_safety_checks
from safety.disclaimers import (
    DISCLAIMER_FULL,
    DISCLAIMER_SHORT,
)
from safety.red_flags import check_red_flags
from safety.validation import validate_input
from services.text_parser import ParseResult, parse_symptom_text

MATH_WEIGHT = 0.6
ML_WEIGHT = 0.4


def parse_free_text(text: object) -> ParseResult:
    """Parse text and preflight it through the safety validation and red flags."""
    kb = load_knowledge_base()
    parsed = parse_symptom_text(text, kb)
    validation = validate_input(
        parsed.symptoms,
        None,
        None,
        {symptom.id for symptom in kb.symptoms},
    )
    if validation["errors"] and not parsed.symptoms:
        parsed.warnings.append(
            "No recognized symptoms are ready for assessment; add or confirm symptoms."
        )
    red_flag_result = check_red_flags(validation["cleaned_symptoms"], kb)
    if red_flag_result["triggered"]:
        parsed.warnings.append(
            "A possible urgent symptom combination was detected. Confirm the "
            "symptoms, then submit for the full safety assessment."
        )
    return parsed


def run_assessment(
    symptoms: object,
    age_group: object = None,
    sex: object = None,
) -> dict[str, Any]:
    """Validate, assess, reconcile, persist, and explain one session."""
    kb = load_knowledge_base()
    safety = run_safety_checks(symptoms, age_group, sex, kb)
    base_warnings = list(safety.warnings)
    if not safety.can_proceed_to_scoring:
        return {
            "session_id": None,
            "valid": False,
            "errors": safety.errors,
            "warnings": base_warnings,
            "disclaimer": DISCLAIMER_FULL,
            "red_flag_triggered": safety.red_flag_triggered,
            "red_flag_message": safety.message,
            "results": [],
            "suggested_questions": [],
            "models_disagree": False,
            "versions": {"knowledge_base": kb.version, "model": "unavailable"},
        }

    cleaned = safety.cleaned_symptoms
    expert = expert_scores(cleaned, kb)
    math = naive_bayes_posteriors(cleaned, kb)
    ml_available = True
    ml: dict[str, float] = {}
    try:
        ml = predict_proba(cleaned)
    except (FileNotFoundError, ValueError) as exc:
        ml_available = False
        base_warnings.append(str(exc))

    disease_by_id = {disease.id: disease for disease in kb.diseases}
    final_results: list[dict[str, Any]] = []
    for disease_id, disease in disease_by_id.items():
        math_score = float(math[disease_id]["posterior"])
        ml_score = float(ml.get(disease_id, 0.0))
        if ml_available:
            final_score = MATH_WEIGHT * math_score + ML_WEIGHT * ml_score
        else:
            final_score = math_score
        expert_result = expert[disease_id]
        explanation = dict(expert_result["explanation"])
        explanation["math_contributions"] = math[disease_id]["contributions"]
        final_results.append(
            {
                "disease_id": disease_id,
                "disease_name": disease.name,
                "final_score": final_score,
                "expert_score": float(expert_result["expert_score"]),
                "math_score": math_score,
                "ml_score": ml_score,
                "confidence": final_score,
                "explanation": explanation,
                "advice": disease.advice,
            }
        )

    final_results.sort(
        key=lambda result: (-result["final_score"], result["disease_name"])
    )
    math_top = max(
        math,
        key=lambda disease_id: (math[disease_id]["posterior"], disease_id),
    )
    ml_top = max(
        ml,
        key=lambda disease_id: (ml[disease_id], disease_id),
    ) if ml_available and ml else math_top
    models_disagree = ml_available and math_top != ml_top

    session_id = repository.create_session(
        age_group=age_group if isinstance(age_group, str) else None,
        sex=sex if isinstance(sex, str) else None,
        kb_version=kb.version,
        model_version="synthetic-v1" if ml_available else "math-only",
    )
    repository.save_symptoms(session_id, cleaned)
    repository.save_results(
        session_id,
        final_results,
        red_flag_triggered=safety.red_flag_triggered,
    )

    return {
        "session_id": session_id,
        "valid": True,
        "errors": [],
        "warnings": base_warnings,
        "disclaimer": safety.disclaimer,
        "red_flag_triggered": safety.red_flag_triggered,
        "red_flag_message": safety.message,
        "results": final_results,
        "suggested_questions": get_questions_for_ui(
            suggest_next_questions(cleaned, kb, n=3)
        ),
        "models_disagree": models_disagree,
        "versions": {
            "knowledge_base": kb.version,
            "model": "synthetic-v1" if ml_available else "math-only",
        },
    }


@st.cache_resource
def get_all_symptom_questions() -> list[dict[str, str]]:
    """Return every KB symptom question for the guided assessment UI."""
    kb = load_knowledge_base()
    return [
        {"symptom_id": symptom.id, "question": symptom.question}
        for symptom in kb.symptoms
    ]


def get_history(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    return repository.list_sessions(limit=limit, offset=offset)


def get_assessment(session_id: str) -> dict[str, Any] | None:
    return repository.get_session_data(session_id)


def delete_assessment(session_id: str) -> bool:
    return repository.delete_session(session_id)


def delete_all_assessments() -> None:
    repository.delete_all_data()


def get_stats() -> dict[str, Any]:
    return repository.get_stats()


def get_questions_for_ui(symptom_ids: list[str]) -> list[dict[str, str]]:
    """Return symptom ids with their plain-language questions."""
    kb = load_knowledge_base()
    by_id = {symptom.id: symptom for symptom in kb.symptoms}
    return [
        {
            "symptom_id": symptom_id,
            "question": by_id[symptom_id].question,
        }
        for symptom_id in symptom_ids
        if symptom_id in by_id
    ]
