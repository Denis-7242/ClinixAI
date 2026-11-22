"""Public knowledge base API."""

from .loader import (
    get_disease,
    get_symptom,
    list_diseases,
    list_symptoms,
    load_knowledge_base,
)
from .schema import Disease, KnowledgeBase, RedFlag, Source, Symptom, SymptomWeight

__all__ = [
    "Disease",
    "KnowledgeBase",
    "RedFlag",
    "Source",
    "Symptom",
    "SymptomWeight",
    "get_disease",
    "get_symptom",
    "list_diseases",
    "list_symptoms",
    "load_knowledge_base",
]