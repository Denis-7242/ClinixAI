"""Safety checks for ClinixAI."""

from dataclasses import dataclass
from typing import Any

from knowledge_base.schema import KnowledgeBase

from .disclaimers import DISCLAIMER_FULL
from .red_flags import check_red_flags
from .validation import validate_input


@dataclass
class SafetyResult:
    is_valid: bool
    cleaned_symptoms: list[dict[str, Any]]
    errors: list[str]
    warnings: list[str]
    red_flag_triggered: bool
    red_flags: list[dict[str, Any]]
    message: str
    disclaimer: str
    can_proceed_to_scoring: bool

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


def run_safety_checks(
    symptoms: object,
    age_group: object,
    sex: object,
    kb: KnowledgeBase,
) -> SafetyResult:
    """Run independent input validation and red-flag detection."""
    known_ids = {item.id for item in kb.symptoms}
    validation = validate_input(symptoms, age_group, sex, known_ids)
    red_flag = check_red_flags(validation["cleaned_symptoms"], kb)

    return SafetyResult(
        is_valid=validation["is_valid"],
        cleaned_symptoms=validation["cleaned_symptoms"],
        errors=validation["errors"],
        warnings=validation["warnings"] + red_flag["warnings"],
        red_flag_triggered=red_flag["triggered"],
        red_flags=red_flag["flags"],
        message=red_flag["message"],
        disclaimer=DISCLAIMER_FULL,
        can_proceed_to_scoring=validation["is_valid"],
    )
