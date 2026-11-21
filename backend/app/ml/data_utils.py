from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Any
import csv
import json
import re

import pandas as pd


@dataclass
class DatasetBundle:
    X: pd.DataFrame
    y: pd.Series
    feature_columns: List[str]
    label_column: str
    raw_shape: Tuple[int, int]
    cleaned_shape: Tuple[int, int]
    notes: Dict[str, Any]


def normalize_column_name(name: str) -> str:
    name = (name or "").strip().lower()
    name = name.replace(" ", "_")
    name = re.sub(r"_+", "_", name)
    return name


def _read_raw_header(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def load_dataset_csv(
    path: str | Path,
    label_column: str | None = None,
) -> DatasetBundle:
    path = Path(path)
    raw_header = _read_raw_header(path)

    # Read all rows without header interpretation to safely handle duplicate/empty column names
    df_all = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    if len(df_all) == 0:
        raise ValueError(f"Dataset is empty: {path}")

    file_header = [str(x) for x in df_all.iloc[0].tolist()]
    # Prefer csv-parsed header for fidelity; fall back to pandas-read header
    if len(file_header) != len(raw_header):
        raw_header = file_header
    data = df_all.iloc[1:].reset_index(drop=True).copy()
    raw_shape = (len(data), len(raw_header))

    tmp_cols = [f"__c{i}__" for i in range(len(raw_header))]
    data.columns = tmp_cols
    col_pairs = list(zip(tmp_cols, raw_header))

    # Drop empty/unnamed columns
    kept_pairs = [(tmp, orig) for tmp, orig in col_pairs if str(orig).strip() != "" and not str(orig).startswith("Unnamed")]
    dropped_columns = [orig for _, orig in col_pairs if str(orig).strip() == "" or str(orig).startswith("Unnamed")]

    # Determine label column
    if label_column is None:
        label_pairs = [p for p in kept_pairs if normalize_column_name(str(p[1])) in {"prognosis", "disease", "label", "condition", "target"}]
        label_pair = label_pairs[0] if label_pairs else kept_pairs[-1]
        label_column = label_pair[1]
    else:
        # allow passing normalized or raw name
        target_norm = normalize_column_name(str(label_column))
        match = [p for p in kept_pairs if str(p[1]) == label_column or normalize_column_name(str(p[1])) == target_norm]
        if not match:
            raise ValueError(f"Label column '{label_column}' not found in dataset columns")
        label_pair = match[0]
        label_column = label_pair[1]

    label_tmp = label_pair[0]
    y = data[label_tmp].astype(str).str.strip()

    feature_pairs = [p for p in kept_pairs if p[0] != label_tmp]

    # Group duplicate feature columns (by normalized name) preserving first-seen order
    groups: Dict[str, List[str]] = {}
    ordered_unique: List[str] = []
    duplicate_headers: List[str] = []
    for tmp, orig in feature_pairs:
        norm = normalize_column_name(str(orig))
        if norm in groups:
            groups[norm].append(tmp)
            duplicate_headers.append(str(orig))
        else:
            groups[norm] = [tmp]
            ordered_unique.append(norm)

    merged_data: Dict[str, Any] = {}
    for norm in ordered_unique:
        tmp_list = groups[norm]
        if len(tmp_list) == 1:
            series = pd.to_numeric(data[tmp_list[0]], errors="coerce").fillna(0)
        else:
            series = pd.to_numeric(data[tmp_list[0]], errors="coerce").fillna(0)
            for tmp in tmp_list[1:]:
                s2 = pd.to_numeric(data[tmp], errors="coerce").fillna(0)
                series = ((series > 0) | (s2 > 0)).astype(int)
        merged_data[norm] = (series > 0).astype(int).to_numpy()

    X = pd.DataFrame(merged_data, index=data.index, columns=ordered_unique)

    # Raw header duplicate names for notes
    raw_header_clean = [str(c) for c in raw_header if str(c).strip() != "" and not str(c).startswith("Unnamed")]
    raw_counts: Dict[str, int] = {}
    for c in raw_header_clean:
        n = normalize_column_name(str(c))
        raw_counts[n] = raw_counts.get(n, 0) + 1
    duplicate_header_names = sorted([k for k, v in raw_counts.items() if v > 1])

    notes = {
        "source_path": str(path),
        "raw_columns": raw_header,
        "dropped_empty_or_unnamed_columns": dropped_columns,
        "duplicate_headers_merged": duplicate_header_names or sorted(set(duplicate_headers)),
        "label_column": str(label_column),
        "num_features": len(ordered_unique),
        "num_classes": int(y.nunique()),
        "class_distribution": y.value_counts().to_dict(),
        "missing_values_before_clean": int((data[[p[0] for p in kept_pairs]].replace("", pd.NA)).isna().sum().sum()),
        "missing_values_after_clean": int(X.isna().sum().sum()),
    }

    return DatasetBundle(
        X=X,
        y=y,
        feature_columns=ordered_unique,
        label_column=str(label_column),
        raw_shape=raw_shape,
        cleaned_shape=(len(X), len(ordered_unique) + 1),
        notes=notes,
    )


def align_features(df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
    data = {}
    for col in feature_columns:
        if col in df.columns:
            data[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int).to_numpy()
        else:
            data[col] = 0
    return pd.DataFrame(data, index=df.index, columns=feature_columns)


def save_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
