"""Load the trained model and provide probability predictions."""

from __future__ import annotations

import json
from pathlib import Path

import joblib

from knowledge_base.loader import load_knowledge_base
from .preprocessing import encode_symptoms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "clinixai_model.joblib"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"


def predict_proba(symptoms: object) -> dict[str, float]:
    """Predict disease probabilities or raise a clear retraining error."""
    if not MODEL_PATH.is_file() or not METADATA_PATH.is_file():
        raise FileNotFoundError(
            "The ML model is unavailable. Retrain it with "
            "`python -m machine_learning.train_model`."
        )
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    kb = load_knowledge_base()
    if metadata.get("knowledge_base_version") != kb.version:
        raise ValueError(
            "The saved ML model does not match the current knowledge base version. "
            "Retrain it with `python -m machine_learning.train_model`."
        )
    feature_list = metadata.get("feature_list")
    if not isinstance(feature_list, list):
        raise ValueError(
            "The saved ML model metadata has no valid feature list. Retrain the model."
        )
    expected = [
        f"{symptom.id}_{state}"
        for symptom in kb.symptoms
        for state in ("present", "absent")
    ]
    if feature_list != expected:
        raise ValueError(
            "The saved ML model feature list does not match the current knowledge base. "
            "Retrain it with `python -m machine_learning.train_model`."
        )
    model = joblib.load(MODEL_PATH)
    row = encode_symptoms(
        symptoms,
        [symptom.id for symptom in kb.symptoms],
        feature_list,
    )
    probabilities = model.predict_proba(row)[0]
    return {
        str(disease_id): float(probability)
        for disease_id, probability in zip(model.classes_, probabilities)
    }
