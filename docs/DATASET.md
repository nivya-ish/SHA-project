# Dataset Documentation

## Source (Uploaded Dataset)
- `data/raw/Training.csv`
- `data/raw/Testing.csv`

These are working copies used by the project (original uploaded files were inspected before integration).

## Actual Inspected Structure
- **Training:** 4920 rows, 134 raw columns
  - 132 symptom columns (binary 0/1), 1 label column `prognosis`, 1 trailing empty column
  - Duplicate header: `fluid_overload` appears twice (merged during preprocessing)
  - 41 unique condition labels, balanced distribution (120 samples per class)
- **Testing:** 42 rows, 133 raw columns
  - 132 symptom columns (including duplicate `fluid_overload`), 1 label column `prognosis`
  - 41 labels represented (1–2 samples per class)
- **After cleaning/feature alignment:** 131 unique symptom features used by model/NLP mapping

## Preprocessing & Quality Handling
Implemented in `backend/app/ml/data_utils.py` and used by `train_model.py` and runtime services:
- Drops trailing empty/unnamed columns
- Normalizes column/header formatting quirks (e.g. spacing/underscores) for consistent mapping
- Merges duplicate symptom columns by OR (binary max) to preserve signal
- Trims/normalizes labels where needed
- Ensures binary integer feature values and no missing values after cleaning
- Persists exact feature columns/order in `ml/artifacts/feature_columns.json` for train/inference consistency

## Dataset Suitability for ML
- Suitable for supervised multi-class classification (symptom-feature patterns -> possible condition labels) in an academic prototype.
- High separability on this dataset can yield very high metrics on provided splits; this does **not** imply clinical validity or real-world generalization.

## Replacement / Retraining
- Replace CSVs in `data/raw/` (or update `TRAIN_DATA_PATH`/`TEST_DATA_PATH` env vars)
- Retrain and regenerate artifacts:
```powershell
py train_model.py --train data/raw/Training.csv --test data/raw/Testing.csv --artifacts ml/artifacts
```
- Keep generated artifacts (`model.joblib`, `feature_columns.json`, `labels.json`, `metadata.json`, reports/confusion matrices) for backend inference.

See also: `docs/dataset_analysis.json` (machine-readable analysis).
