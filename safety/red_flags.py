"""Independent knowledge-base red-flag detection."""

from __future__ import annotations

from typing import Iterable

from knowledge_base.schema import KnowledgeBase


def check_red_flags(
    symptoms: object,
    kb: KnowledgeBase,
) -> dict[str, object]:
    """Return all red flags whose complete required symptom set is present."""
    present: set[str] = set()
    if isinstance(symptoms, list):
        for item in symptoms:
            if isinstance(item, dict) and item.get("present") is True:
                symptom_id = item.get("symptom_id")
                if isinstance(symptom_id, str):
                    present.add(symptom_id)

    triggered_flags: list[dict[str, object]] = []
    warnings: list[str] = []
    for rule in kb.red_flags:
        required = set(rule.required_symptom_ids)
        if required and required.issubset(present):
            triggered_flags.append(
                {
                    "id": rule.id,
                    "description": rule.description,
                    "required_symptom_ids": list(rule.required_symptom_ids),
                    "urgency": rule.urgency,
                    "trace": sorted(required & present),
                }
            )
        elif required:
            missing = required - present
            if len(required) >= 2 and len(missing) == 1:
                warnings.append(
                    f"Near-miss for red flag '{rule.id}': "
                    f"one required symptom is not marked present."
                )

    if triggered_flags:
        message = " ".join(str(flag["urgency"]) for flag in triggered_flags)
    else:
        message = ""

    return {
        "triggered": bool(triggered_flags),
        "flags": triggered_flags,
        "message": message,
        "trace": [flag["id"] for flag in triggered_flags],
        "warnings": warnings,
    }
