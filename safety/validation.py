"""Defensive validation for assessment inputs."""

from __future__ import annotations

import re
from typing import Iterable


_ALLOWED_AGE_GROUPS = {
    None,
    "under_18",
    "18-29",
    "30-49",
    "50-64",
    "65_plus",
    "unknown",
}
_ALLOWED_SEXES = {None, "female", "male", "intersex", "prefer_not_to_say", "unknown"}


def _clean_string(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def validate_input(
    symptoms: object,
    age_group: object,
    sex: object,
    known_symptom_ids: Iterable[str],
) -> dict[str, object]:
    """Validate and clean user input without raising for bad user data."""
    errors: list[str] = []
    warnings: list[str] = []
    cleaned: list[dict[str, object]] = []
    known = set(known_symptom_ids)

    if not isinstance(symptoms, list):
        errors.append("Symptoms must be provided as a list.")
        symptoms = []

    if len(symptoms) > 10000:
        errors.append("Too many symptom entries were provided.")

    seen: set[str] = set()
    present_count = 0
    for index, item in enumerate(symptoms[:10000]):
        if not isinstance(item, dict):
            errors.append(f"Symptom entry {index + 1} must be an object.")
            continue

        raw_id = item.get("symptom_id")
        symptom_id = _clean_string(raw_id)
        if not symptom_id:
            errors.append(f"Symptom entry {index + 1} has no valid symptom id.")
            continue
        if symptom_id not in known:
            warnings.append(f"Unknown symptom id ignored: '{symptom_id}'.")
        if symptom_id in seen:
            errors.append(f"Duplicate symptom id: '{symptom_id}'.")
            continue
        seen.add(symptom_id)

        present = item.get("present")
        if present not in (True, False, None):
            errors.append(f"Present value for '{symptom_id}' must be true, false, or null.")
            present = None
        if present is True:
            present_count += 1

        severity = item.get("severity")
        if severity is not None:
            if isinstance(severity, bool) or not isinstance(severity, (int, float)):
                errors.append(f"Severity for '{symptom_id}' must be an integer from 1 to 10.")
                severity = None
            else:
                if isinstance(severity, float) and not severity.is_integer():
                    errors.append(
                        f"Severity for '{symptom_id}' must be an integer from 1 to 10."
                    )
                    severity = None
                elif not 1 <= int(severity) <= 10:
                    errors.append(
                        f"Severity for '{symptom_id}' must be from 1 to 10."
                    )
                    severity = None
                else:
                    severity = int(severity)

        duration = item.get("duration_days")
        if duration is not None:
            if isinstance(duration, bool) or not isinstance(duration, int):
                errors.append(
                    f"Duration for '{symptom_id}' must be a whole number from 0 to 3650."
                )
                duration = None
            elif not 0 <= duration <= 3650:
                errors.append(
                    f"Duration for '{symptom_id}' must be from 0 to 3650."
                )
                duration = None

        cleaned.append(
            {
                "symptom_id": symptom_id,
                "present": present,
                "severity": severity,
                "duration_days": duration,
            }
        )

    if not symptoms:
        errors.append("At least one symptom entry is required.")
    elif present_count == 0:
        warnings.append("No symptoms are marked present.")

    if age_group is not None and age_group not in _ALLOWED_AGE_GROUPS:
        errors.append("Unsupported age_group value.")
    if sex is not None and sex not in _ALLOWED_SEXES:
        errors.append("Unsupported sex value.")

    return {
        "is_valid": not errors,
        "cleaned_symptoms": cleaned,
        "errors": errors,
        "warnings": warnings,
    }
