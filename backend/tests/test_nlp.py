from pathlib import Path
from app.services.nlp_service import SymptomNLPProcessor
from app.ml.data_utils import load_dataset_csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_CSV = PROJECT_ROOT / "data" / "raw" / "Training.csv"


def make_processor():
    bundle = load_dataset_csv(TRAIN_CSV)
    return SymptomNLPProcessor(bundle.feature_columns)


def test_empty_symptoms_with_duration_only_message():
    p = make_processor()
    r = p.process("", "3 days")
    assert r.valid_for_prediction is False
    assert r.mapped_features == []
    assert r.validation_message == "Please enter your symptoms before starting the analysis."


def test_duration_only_input_does_not_invent_symptoms_or_trigger_prediction():
    p = make_processor()
    r = p.process("3 days", "")
    assert r.valid_for_prediction is False
    assert r.extracted_symptoms == [] or all(s.strip() == "" for s in r.extracted_symptoms) or r.mapped_features == []
    assert r.mapped_features == []
    assert r.normalized_symptoms == []
    assert r.validation_message is not None
    assert "duration" in r.validation_message.lower() or "symptom" in r.validation_message.lower()
    # must not invent common symptoms
    forbidden = {"headache", "fever", "unwell", "high fever", "cough"}
    assert forbidden.isdisjoint(set(r.normalized_symptoms))


def test_symptoms_with_duration_extracts_both_and_keeps_duration_separate():
    p = make_processor()
    r = p.process("Fever and cough", "3 days")
    assert r.valid_for_prediction is True
    assert r.duration == "3 days"
    assert "high_fever" in r.mapped_features or "mild_fever" in r.mapped_features
    assert "cough" in r.mapped_features
    # duration must not appear as mapped symptom feature
    assert "3_days" not in r.mapped_features
    assert "days" not in r.mapped_features


def test_duration_embedded_in_symptom_text_is_extracted_separately():
    p = make_processor()
    r = p.process("fever for 3 days", "")
    assert r.valid_for_prediction is True
    assert r.duration == "3 days"
    assert any(f in r.mapped_features for f in ["high_fever", "mild_fever"])
    assert "3_days" not in r.mapped_features


def test_unsupported_symptoms_reported_without_breaking_valid_mapping():
    p = make_processor()
    r = p.process("fever and mysteriousxyzsymptom", "2 days")
    assert r.valid_for_prediction is True
    assert any(f in r.mapped_features for f in ["high_fever", "mild_fever"])
    assert len(r.unsupported_symptoms) >= 1


def test_invalid_gibberish_input_rejected():
    p = make_processor()
    r = p.process("qwertyuiop", "")
    assert r.valid_for_prediction is False
    assert r.mapped_features == []
