"""Feature encoding for knowledge-base-derived symptom answers."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def encode_symptoms(
    symptoms: object,
    symptom_ids: Iterable[str],
    feature_list: Iterable[str],
) -> np.ndarray:
    """Encode present/absent answers; unknown answers leave both columns zero."""
    feature_names = list(feature_list)
    answer_map: dict[str, object] = {}
    if isinstance(symptoms, list):
        for item in symptoms:
            if isinstance(item, dict) and isinstance(item.get("symptom_id"), str):
                answer_map[item["symptom_id"]] = item.get("present")

    row = np.zeros(len(feature_names), dtype=np.float64)
    for symptom_id in symptom_ids:
        answer = answer_map.get(symptom_id)
        present_index = feature_names.index(f"{symptom_id}_present")
        absent_index = feature_names.index(f"{symptom_id}_absent")
        if answer is True:
            row[present_index] = 1.0
        elif answer is False:
            row[absent_index] = 1.0
    return row.reshape(1, -1)
