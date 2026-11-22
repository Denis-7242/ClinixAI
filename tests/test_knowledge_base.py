import logging

import pytest

from knowledge_base.loader import (
    get_disease,
    get_symptom,
    list_diseases,
    list_symptoms,
    load_knowledge_base,
)


FIXTURES = "tests/fixtures"


def test_bundled_file_loads_and_validates():
    kb = load_knowledge_base()
    assert kb.version == "1.0"
    assert 8 <= len(kb.diseases) <= 12
    assert 15 <= len(kb.symptoms) <= 25
    assert len(kb.red_flags) >= 5
    assert get_disease("malaria").name == "Malaria"
    assert get_symptom("fever").display_name == "Fever"
    assert len(list_diseases()) == len(kb.diseases)
    assert len(list_symptoms()) == len(kb.symptoms)


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ("duplicate_ids.json", "Duplicate symptom id"),
        ("unknown_disease_symptom.json", "unknown symptom id"),
        ("unknown_disease_source.json", "unknown source ids"),
        ("unknown_red_flag_symptom.json", "unknown symptom ids"),
        ("missing_source.json", "no source"),
        ("prior_out_of_range.json", "outside 0 to 1"),
    ],
)
def test_broken_fixtures_raise_clear_errors(fixture, message):
    with pytest.raises(ValueError, match=message):
        load_knowledge_base(f"{FIXTURES}/{fixture}")


def test_priors_not_summing_warn_instead_of_failing(caplog):
    with caplog.at_level(logging.WARNING):
        kb = load_knowledge_base(f"{FIXTURES}/priors_not_sum.json")
    assert kb.version == "broken"
    assert "sum to" in caplog.text


def test_every_disease_has_source_or_is_illustrative():
    kb = load_knowledge_base()
    for disease in kb.diseases:
        assert disease.source_ids or disease.illustrative


def test_every_disease_and_red_flag_reference_exists():
    kb = load_knowledge_base()
    symptom_ids = {symptom.id for symptom in kb.symptoms}
    source_ids = {source.id for source in kb.sources}
    for disease in kb.diseases:
        assert set(disease.source_ids).issubset(source_ids)
        assert {item.symptom_id for item in disease.symptoms}.issubset(symptom_ids)
    for red_flag in kb.red_flags:
        assert set(red_flag.required_symptom_ids).issubset(symptom_ids)
