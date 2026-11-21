import json
from pathlib import Path
import pandas as pd

from app.ml.data_utils import load_dataset_csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_CSV = PROJECT_ROOT / "data" / "raw" / "Training.csv"
TEST_CSV = PROJECT_ROOT / "data" / "raw" / "Testing.csv"


def test_dataset_loading_and_basic_quality():
    train = load_dataset_csv(TRAIN_CSV)
    test = load_dataset_csv(TEST_CSV)
    assert train.raw_shape[0] == 4920
    assert train.raw_shape[1] == 134
    assert test.raw_shape[0] == 42
    assert test.raw_shape[1] == 133
    assert train.label_column == "prognosis"
    assert len(train.feature_columns) == 131  # duplicate fluid_overload merged
    assert train.y.nunique() == 41
    assert test.y.nunique() == 41
    # no missing values after clean
    assert train.X.isna().sum().sum() == 0
    assert set(train.X.columns) == set(train.feature_columns)


def test_feature_values_binary_and_duplicate_header_handled():
    bundle = load_dataset_csv(TRAIN_CSV)
    assert set(pd.unique(bundle.X.values.ravel())).issubset({0, 1})
    assert "fluid_overload" in bundle.feature_columns
    assert bundle.feature_columns.count("fluid_overload") == 1
    # merged duplicate had differing rows in raw data
    assert bundle.X["fluid_overload"].sum() > 0
