# Model Training Documentation

## Script
- `train_model.py` (project root) - reusable training pipeline for the provided symptom-disease dataset

## Inputs / Configuration
- `--train`: training CSV path
- `--test`: test CSV path
- `--artifacts`: output directory for model artifacts
- Label column handled via data utilities (`prognosis` in the provided dataset)

## Pipeline (actual implementation)
1. Load and clean datasets (drop empty columns, normalize headers/labels, merge duplicate symptom columns, ensure binary features)
2. Align train/test feature matrices to consistent feature columns/order
3. Train and compare candidate models using stratified CV weighted F1 (e.g. Logistic Regression, Random Forest)
4. Select best-performing model and fit on training data
5. Evaluate on train and test sets
6. Save artifacts and evaluation reports

## Saved Artifacts
Directory: `ml/artifacts/`
- `model.joblib` - trained classifier
- `feature_columns.json` - exact feature names/order for inference
- `labels.json` - class labels
- `metadata.json` - algorithm, metrics, dataset/feature info
- `train_classification_report.json`, `test_classification_report.json`
- `train_confusion_matrix.json`, `test_confusion_matrix.json`

## Actual Reported Results (from existing executed training artifacts/logs)
- Selected algorithm: **LogisticRegression** (selected by CV weighted F1 comparison)
- Features: **131** (after duplicate merge/cleaning)
- Classes: **41**
- Train: accuracy/precision/recall/F1 (weighted) = **1.0 / 1.0 / 1.0 / 1.0** (4920 samples)
- Test: accuracy/precision/recall/F1 (weighted) = **1.0 / 1.0 / 1.0 / 1.0** (42 samples)

References:
- `ml/training_run.log`
- `ml/artifacts/metadata.json`
- `ml/artifacts/*_classification_report.json`
- `ml/artifacts/*_confusion_matrix.json`

## Interpretation & Limitations
- Metrics are based on the provided dataset split and reflect dataset separability; they do **not** constitute clinical validation.
- The application must present outputs as **possible conditions (unconfirmed)**, not diagnoses.

## Retraining Command
```powershell
py train_model.py --train data/raw/Training.csv --test data/raw/Testing.csv --artifacts ml/artifacts
```
