"""Train a clearly synthetic, knowledge-base-derived clinician prototype."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import cross_val_score, train_test_split

from knowledge_base.loader import load_knowledge_base
from knowledge_base.schema import KnowledgeBase

SEED = 7242
SAMPLES = 3000
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "clinixai_model.joblib"
METADATA_PATH = Path(__file__).resolve().parent.parent / "models" / "model_metadata.json"


def generate_synthetic_data(
    kb: KnowledgeBase,
    seed: int = SEED,
    n_samples: int = SAMPLES,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Generate deterministic synthetic rows from priors and symptom weights."""
    rng = np.random.default_rng(seed)
    priors = np.array(
        [max(disease.prior_probability, 0.03) for disease in kb.diseases],
        dtype=float,
    )
    priors /= priors.sum()
    disease_ids = [disease.id for disease in kb.diseases]
    symptom_ids = [symptom.id for symptom in kb.symptoms]
    feature_names = [
        f"{symptom_id}_{state}"
        for symptom_id in symptom_ids
        for state in ("present", "absent")
    ]
    features = np.zeros((n_samples, len(feature_names)), dtype=np.int8)
    labels = np.empty(n_samples, dtype="<U64")

    for row in range(n_samples):
        disease_index = int(rng.choice(len(disease_ids), p=priors))
        disease = kb.diseases[disease_index]
        listed = {
            item.symptom_id: item.weight
            for item in disease.symptoms
        }
        labels[row] = disease.id
        for symptom_index, symptom_id in enumerate(symptom_ids):
            if rng.random() < 0.12:
                continue
            probability = listed.get(symptom_id, 0.05)
            present = rng.random() < probability
            state_index = symptom_index * 2
            features[row, state_index] = int(present)
            features[row, state_index + 1] = int(not present)
    return features, labels, feature_names


def train_models(
    seed: int = SEED,
    n_samples: int = SAMPLES,
) -> dict[str, object]:
    """Train, compare, and persist the best of logistic and random forest."""
    kb = load_knowledge_base()
    features, labels, feature_names = generate_synthetic_data(kb, seed, n_samples)
    train_x, holdout_x, train_y, holdout_y = train_test_split(
        features,
        labels,
        test_size=0.4,
        random_state=seed,
        stratify=labels,
    )
    validation_x, test_x, validation_y, test_y = train_test_split(
        holdout_x,
        holdout_y,
        test_size=0.5,
        random_state=seed,
        stratify=holdout_y,
    )

    logistic = LogisticRegression(
        max_iter=1000,
        random_state=seed,
    )
    forest = RandomForestClassifier(
        n_estimators=200,
        random_state=seed,
        n_jobs=-1,
    )
    logistic.fit(train_x, train_y)
    forest.fit(train_x, train_y)

    candidates = {"logistic_regression": logistic, "random_forest": forest}
    metrics: dict[str, dict[str, object]] = {}
    for name, model in candidates.items():
        cv_scores = cross_val_score(
            model,
            train_x,
            train_y,
            cv=3,
            scoring="f1_macro",
        )
        predictions = model.predict(test_x)
        probabilities = model.predict_proba(test_x)
        matrix = confusion_matrix(test_y, predictions, labels=[d.id for d in kb.diseases])
        per_class_precision: dict[str, float] = {}
        per_class_recall: dict[str, float] = {}
        per_class_f1: dict[str, float] = {}
        for index, disease in enumerate(kb.diseases):
            true_positive = matrix[index, index]
            predicted_positive = int(matrix[:, index].sum())
            actual_positive = int(matrix[index, :].sum())
            precision = (
                true_positive / predicted_positive if predicted_positive else 0.0
            )
            recall = true_positive / actual_positive if actual_positive else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0
            )
            per_class_precision[disease.id] = precision
            per_class_recall[disease.id] = recall
            per_class_f1[disease.id] = f1
        top_three = 0.0
        for probabilities_row, actual in zip(probabilities, test_y):
            ranked = [
                disease_id
                for disease_id in model.classes_[np.argsort(probabilities_row)[::-1]][:3]
            ]
            top_three += float(actual in ranked)
        top_three /= len(test_y)
        metrics[name] = {
            "cross_validation_macro_f1_mean": float(cv_scores.mean()),
            "cross_validation_macro_f1_std": float(cv_scores.std()),
            "accuracy": float(accuracy_score(test_y, predictions)),
            "macro_f1": float(f1_score(test_y, predictions, average="macro")),
            "top_3_accuracy": top_three,
            "per_class_precision": per_class_precision,
            "per_class_recall": per_class_recall,
            "per_class_f1": per_class_f1,
            "confusion_matrix": matrix.tolist(),
            "labels": [disease.id for disease in kb.diseases],
        }

    best_name = max(metrics, key=lambda name: metrics[name]["accuracy"])
    best_model = candidates[best_name]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    metadata = {
        "knowledge_base_version": kb.version,
        "feature_list": feature_names,
        "seed": seed,
        "metrics": metrics,
        "data_type": "synthetic",
        "best_model": best_name,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    metadata = train_models()
    logging.basicConfig(level=logging.INFO)
    logging.info("%s", json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
