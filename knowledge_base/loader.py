"""Loading and validation helpers for the bundled knowledge base."""

import json
import logging
from pathlib import Path
from typing import Iterable

from pydantic import ValidationError

from .schema import Disease, KnowledgeBase, Symptom

logger = logging.getLogger(__name__)
_knowledge_base: KnowledgeBase | None = None


def _ensure_unique(ids: Iterable[str], item_name: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise ValueError(f"Duplicate {item_name} id: '{item_id}'")
        seen.add(item_id)


def validate_knowledge_base(kb: KnowledgeBase) -> KnowledgeBase:
    """Validate cross-references and probabilistic totals."""
    _ensure_unique((item.id for item in kb.symptoms), "symptom")
    _ensure_unique((item.id for item in kb.diseases), "disease")
    _ensure_unique((item.id for item in kb.red_flags), "red flag")
    _ensure_unique((item.id for item in kb.sources), "source")

    symptom_ids = {item.id for item in kb.symptoms}
    source_ids = {item.id for item in kb.sources}

    for disease in kb.diseases:
        if not 0.0 <= disease.prior_probability <= 1.0:
            raise ValueError(
                f"Disease '{disease.id}' has prior_probability outside 0 to 1"
            )
        if not disease.source_ids and not disease.illustrative:
            raise ValueError(
                f"Disease '{disease.id}' has no source and is not marked illustrative"
            )
        unknown_sources = sorted(set(disease.source_ids) - source_ids)
        if unknown_sources:
            raise ValueError(
                f"Disease '{disease.id}' references unknown source ids: "
                f"{', '.join(unknown_sources)}"
            )
        for symptom_weight in disease.symptoms:
            if symptom_weight.symptom_id not in symptom_ids:
                raise ValueError(
                    f"Disease '{disease.id}' references unknown symptom id "
                    f"'{symptom_weight.symptom_id}'"
                )

    for red_flag in kb.red_flags:
        unknown_symptoms = sorted(set(red_flag.required_symptom_ids) - symptom_ids)
        if unknown_symptoms:
            raise ValueError(
                f"Red flag '{red_flag.id}' references unknown symptom ids: "
                f"{', '.join(unknown_symptoms)}"
            )

    prior_total = sum(disease.prior_probability for disease in kb.diseases)
    if not 0.9 <= prior_total <= 1.1:
        logger.warning(
            "Disease prior probabilities sum to %.3f; a total near 1.0 is recommended",
            prior_total,
        )
    return kb


def load_knowledge_base(path: str | Path | None = None) -> KnowledgeBase:
    """Load a JSON knowledge base from a path or the bundled data file."""
    global _knowledge_base

    data_path = (
        Path(path)
        if path is not None
        else Path(__file__).resolve().parent / "knowledge_base.json"
    )
    if not data_path.is_file():
        raise FileNotFoundError(f"Knowledge base file not found: {data_path}")

    try:
        with data_path.open("r", encoding="utf-8") as data_file:
            raw = json.load(data_file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in knowledge base '{data_path}': {exc}") from exc

    try:
        kb = KnowledgeBase.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid knowledge base schema in '{data_path}': {exc}") from exc

    _knowledge_base = validate_knowledge_base(kb)
    return _knowledge_base


def _active_knowledge_base() -> KnowledgeBase:
    if _knowledge_base is None:
        load_knowledge_base()
    assert _knowledge_base is not None
    return _knowledge_base


def get_disease(disease_id: str) -> Disease:
    """Return a disease by id, or raise LookupError."""
    kb = _active_knowledge_base()
    for disease in kb.diseases:
        if disease.id == disease_id:
            return disease
    raise LookupError(f"Unknown disease id: '{disease_id}'")


def get_symptom(symptom_id: str) -> Symptom:
    """Return a symptom by id, or raise LookupError."""
    kb = _active_knowledge_base()
    for symptom in kb.symptoms:
        if symptom.id == symptom_id:
            return symptom
    raise LookupError(f"Unknown symptom id: '{symptom_id}'")


def list_symptoms() -> list[Symptom]:
    """Return all symptoms in the active knowledge base."""
    return list(_active_knowledge_base().symptoms)


def list_diseases() -> list[Disease]:
    """Return all diseases in the active knowledge base."""
    return list(_active_knowledge_base().diseases)
