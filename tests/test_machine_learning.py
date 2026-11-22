"""Tests for deterministic synthetic ML behavior."""

import json
from pathlib import Path

import numpy as np
import pytest

from knowledge_base.loader import load_knowledge_base
from machine_learning.preprocessing import encode_symptoms
from machine_learning.predict import predict_proba
from machine_learning.train_model import (
    METADATA_PATH,
    MODEL_PATH,
    generate_synthetic_data,
)


def test_synthetic_data_is_deterministic_and_right_shape():
    kb = load_knowledge_base()
    first = generate_synthetic_data(kb, seed=7242, n_samples=100)
    second = generate_synthetic_data(kb, seed=7242, n_samples=100)
    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])
    assert first[0].shape == (100, 2 * len(kb.symptoms))
    assert len(first[2]) == 2 * len(kb.symptoms)


def test_feature_encoder_shape_and_unknown():
    kb = load_knowledge_base()
    feature_names = [
        f"{symptom.id}_{state}"
        for symptom in kb.symptoms
        for state in ("present", "absent")
    ]
    row = encode_symptoms(
        [{"symptom_id": "fever", "present": None}],
        [symptom.id for symptom in kb.symptoms],
        feature_names,
    )
    assert row.shape == (1, 2 * len(kb.symptoms))
    assert row.sum() == 0


def test_saved_model_inference_returns_normalized_probabilities():
    probabilities = predict_proba(
        [{"symptom_id": "fever", "present": True}]
    )
    assert len(probabilities) == 10
    assert abs(sum(probabilities.values()) - 1.0) < 1e-6


def test_missing_model_file_is_handled(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "machine_learning.predict.MODEL_PATH",
        tmp_path / "missing.joblib",
    )
    monkeypatch.setattr(
        "machine_learning.predict.METADATA_PATH",
        tmp_path / "missing.json",
    )
    with pytest.raises(FileNotFoundError, match="Retrain"):
        predict_proba([])


def test_version_mismatch_raises_clear_error(monkeypatch, tmp_path):
    model_path = tmp_path / "model.joblib"
    metadata_path = tmp_path / "metadata.json"
    model_path.write_bytes(b"not needed")
    metadata_path.write_text(
        json.dumps({"knowledge_base_version": "0.0", "feature_list": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr("machine_learning.predict.MODEL_PATH", model_path)
    monkeypatch.setattr("machine_learning.predict.METADATA_PATH", metadata_path)
    with pytest.raises(ValueError, match="does not match.*Retrain"):
        predict_proba([])
