"""Deterministic chronological split and train-only preprocessing for V3-07."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from numbers import Integral
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.ml.features import FEATURE_NAMES, FEATURE_TYPES, METADATA_NAMES, parse_purchase_timestamp
from src.ml.preprocessing import make_preprocessor, validate_feature_frame


SPLIT_VERSION = "v1"
BOUNDARIES = {
    "train": {"start_inclusive": "2017-01-01", "end_exclusive": "2018-01-01"},
    "validation": {"start_inclusive": "2018-01-01", "end_exclusive": "2018-04-01"},
    "test": {"start_inclusive": "2018-04-01", "end_exclusive": "2018-09-01"},
}
SPLIT_COLUMN = "split"
OUTPUT_COLUMNS = [*METADATA_NAMES, *FEATURE_NAMES, SPLIT_COLUMN]


def _dates(frame: pd.DataFrame) -> pd.Series:
    parsed = []
    for row_number, value in enumerate(frame["purchase_ts"].tolist()):
        try:
            parsed.append(parse_purchase_timestamp(value).date())
        except ValueError as exc:
            raise ValueError(f"Invalid purchase_ts at row {row_number}: {exc}") from exc
    return pd.Series(parsed, index=frame.index, dtype="object")


def assign_chronological_splits(features: pd.DataFrame) -> pd.DataFrame:
    """Assign fixed date windows; equal timestamps/dates can never cross a cut."""
    expected = [*METADATA_NAMES, *FEATURE_NAMES]
    if list(features.columns) != expected:
        raise ValueError(f"Feature dataset columns must be exactly: {', '.join(expected)}")
    if features["order_id"].isna().any() or features["order_id"].astype("string").duplicated().any():
        raise ValueError("Feature dataset order_id values must be present and unique")
    labels = pd.to_numeric(features["late"], errors="coerce")
    if labels.isna().any() or not labels.isin((0, 1)).all():
        raise ValueError("Feature dataset late target must contain only 0 or 1")
    ordered = features.sort_values(["purchase_ts", "order_id"], kind="mergesort").reset_index(drop=True)
    dates = _dates(ordered)
    boundaries = {
        name: (date.fromisoformat(bounds["start_inclusive"]), date.fromisoformat(bounds["end_exclusive"]))
        for name, bounds in BOUNDARIES.items()
    }
    split_names: list[str] = []
    for value in dates:
        if boundaries["train"][0] <= value < boundaries["train"][1]:
            split_names.append("train")
        elif boundaries["validation"][0] <= value < boundaries["validation"][1]:
            split_names.append("validation")
        elif boundaries["test"][0] <= value < boundaries["test"][1]:
            split_names.append("test")
        elif value < boundaries["train"][0]:
            split_names.append("excluded_pre_window")
        else:
            split_names.append("excluded_post_window")
    output = ordered.copy()
    output[SPLIT_COLUMN] = split_names
    return output.loc[:, OUTPUT_COLUMNS]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit_count(audit: dict[str, Any], key: str) -> int:
    if key not in audit:
        raise ValueError(f"Feature audit is missing required count: {key}")
    value = audit[key]
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or int(value) < 0:
        raise ValueError(f"Feature audit count {key} must be a nonnegative integer")
    return int(value)


def _validate_feature_audit(
    features: pd.DataFrame,
    audit: dict[str, Any],
    input_sha256: str,
) -> None:
    """Bind audit counts and labels to the exact feature artifact being split."""
    if not isinstance(audit, dict):
        raise ValueError("Feature audit must be a JSON object")

    count_fields = (
        "population_input_rows",
        "population_input_late",
        "feature_ready_rows",
        "feature_ready_late",
        "feature_ready_negative_rows",
        "feature_excluded_rows",
        "feature_excluded_late",
    )
    counts = {key: _audit_count(audit, key) for key in count_fields}
    population_rows = counts["population_input_rows"]
    population_late = counts["population_input_late"]
    feature_rows = counts["feature_ready_rows"]
    feature_late = counts["feature_ready_late"]
    feature_negative = counts["feature_ready_negative_rows"]
    excluded_rows = counts["feature_excluded_rows"]
    excluded_late = counts["feature_excluded_late"]

    if population_late > population_rows or feature_late > feature_rows or excluded_late > excluded_rows:
        raise ValueError("Feature audit label counts exceed their row counts")
    if feature_rows != len(features):
        raise ValueError("Feature audit feature_ready_rows does not match the feature artifact row count")
    labels = pd.to_numeric(features["late"], errors="coerce")
    if labels.isna().any() or not labels.isin((0, 1)).all():
        raise ValueError("Feature artifact late labels must contain only 0 or 1")
    actual_late = int(labels.sum())
    if feature_late != actual_late:
        raise ValueError("Feature audit feature_ready_late does not match feature artifact labels")
    if feature_negative != len(features) - actual_late:
        raise ValueError("Feature audit feature_ready_negative_rows does not match feature artifact labels")
    if population_rows != feature_rows + excluded_rows:
        raise ValueError("Feature audit target-population row accounting is inconsistent")
    if population_late != feature_late + excluded_late:
        raise ValueError("Feature audit target-population late-label accounting is inconsistent")
    if population_rows - population_late != feature_negative + (excluded_rows - excluded_late):
        raise ValueError("Feature audit target-population negative-label accounting is inconsistent")

    exclusion_counts = audit.get("exclusive_feature_exclusion_counts")
    if not isinstance(exclusion_counts, dict):
        raise ValueError("Feature audit is missing required exclusive_feature_exclusion_counts")
    validated_exclusions = {
        name: _audit_count(exclusion_counts, name) for name in exclusion_counts
    }
    if sum(validated_exclusions.values()) != excluded_rows:
        raise ValueError("Feature audit exclusion reasons do not sum to feature_excluded_rows")

    for field, expected in (
        ("input_target_label_counts", (population_late, population_rows - population_late)),
        ("feature_ready_label_counts", (feature_late, feature_negative)),
    ):
        distribution = audit.get(field)
        if not isinstance(distribution, dict):
            raise ValueError(f"Feature audit is missing required {field}")
        positive = _audit_count(distribution, "late_1")
        negative = _audit_count(distribution, "late_0")
        if (positive, negative) != expected:
            raise ValueError(f"Feature audit {field} does not reconcile with row and label counts")

    if not isinstance(input_sha256, str) or len(input_sha256) != 64 or any(c not in "0123456789abcdef" for c in input_sha256):
        raise ValueError("Feature artifact SHA-256 must be a lowercase 64-character hex digest")
    recorded_sha256 = audit.get("feature_artifact_sha256")
    if not isinstance(recorded_sha256, str) or recorded_sha256 != input_sha256:
        raise ValueError("Feature audit checksum does not match the feature artifact SHA-256")


def _repo_relative(path: Path) -> str:
    root = Path(__file__).resolve().parents[2]
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _validate_generated_paths(input_paths: list[Path], output_paths: list[Path]) -> None:
    root = Path(__file__).resolve().parents[2]
    processed_dir = (root / "data" / "processed").resolve()
    resolved_inputs = {path.resolve() for path in input_paths}
    resolved_outputs = [path.resolve() for path in output_paths]
    if len(set(resolved_outputs)) != len(resolved_outputs):
        raise ValueError("Generated output paths must be distinct")
    for output in resolved_outputs:
        if output in resolved_inputs:
            raise ValueError("Generated split output must not overwrite an input file")
        try:
            output.relative_to(processed_dir)
        except ValueError as exc:
            raise ValueError("Generated split artifacts must stay under ignored data/processed/") from exc


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "rows": 0, "positive": 0, "negative": 0, "positive_prevalence": None,
            "purchase_start": None, "purchase_end": None,
        }
    late = frame["late"].astype(int)
    times = [parse_purchase_timestamp(value) for value in frame["purchase_ts"].tolist()]
    return {
        "rows": int(len(frame)),
        "positive": int(late.sum()),
        "negative": int(len(frame) - late.sum()),
        "positive_prevalence": float(late.mean()),
        "purchase_start": min(times).strftime("%Y-%m-%d %H:%M:%S"),
        "purchase_end": max(times).strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_split_outputs(
    features: pd.DataFrame,
    feature_audit: dict[str, Any],
    input_sha256: str,
    input_path: str,
    output_path: str,
    manifest_path: str,
    preprocessor_path: str,
) -> tuple[pd.DataFrame, dict[str, Any], Any]:
    split_frame = assign_chronological_splits(features)
    _validate_feature_audit(features, feature_audit, input_sha256)
    train = split_frame.loc[split_frame[SPLIT_COLUMN].eq("train")]
    validation = split_frame.loc[split_frame[SPLIT_COLUMN].eq("validation")]
    test = split_frame.loc[split_frame[SPLIT_COLUMN].eq("test")]
    if train.empty or validation.empty or test.empty:
        raise ValueError("Each chronological train, validation, and test window must contain rows")

    # The unfitted transformer receives only the training feature columns.
    train_x = train.loc[:, FEATURE_NAMES]
    validate_feature_frame(train_x)
    preprocessor = make_preprocessor()
    preprocessor.fit(train_x)
    transformed_shapes: dict[str, int] = {}
    for name, subset in (("train", train), ("validation", validation), ("test", test)):
        transformed = preprocessor.transform(subset.loc[:, FEATURE_NAMES])
        if not np.isfinite(transformed).all():
            raise ValueError(f"Train-fitted preprocessing produced non-finite {name} values")
        transformed_shapes[name] = int(transformed.shape[1])

    pre_start = date.fromisoformat(BOUNDARIES["train"]["start_inclusive"])
    test_end = date.fromisoformat(BOUNDARIES["test"]["end_exclusive"])
    test_dates = _dates(test)
    pre_august_test = test.loc[test_dates < date(2018, 8, 1)]
    split_summaries = {
        name: _summary(split_frame.loc[split_frame[SPLIT_COLUMN].eq(name)])
        for name in ("train", "validation", "test")
    }
    split_summaries["test_without_august_2018_sensitivity"] = _summary(pre_august_test)
    excluded = {
        "pre_window": _summary(split_frame.loc[split_frame[SPLIT_COLUMN].eq("excluded_pre_window")]),
        "post_window": _summary(split_frame.loc[split_frame[SPLIT_COLUMN].eq("excluded_post_window")]),
    }
    missingness = {name: int(features[name].isna().sum()) for name in FEATURE_NAMES}
    train_missingness = {name: int(train[name].isna().sum()) for name in FEATURE_NAMES}
    monthly_tail = {
        month: metrics
        for month, metrics in feature_audit.get("source_population_monthly", {}).items()
        if month >= "2018-06"
    }
    manifest: dict[str, Any] = {
        "manifest_version": SPLIT_VERSION,
        "dataset": {
            "input_path": input_path,
            "input_sha256": input_sha256,
            "feature_ready_rows": int(len(features)),
            "feature_ready_negative_rows": int(feature_audit["feature_ready_negative_rows"]),
            "feature_artifact_sha256": input_sha256,
            "target_population_rows": int(feature_audit["population_input_rows"]),
            "target_population_late": int(feature_audit["population_input_late"]),
            "feature_exclusions": feature_audit["exclusive_feature_exclusion_counts"],
            "feature_ready_late": int(feature_audit["feature_ready_late"]),
        },
        "feature_contract": {
            "names_in_order": list(FEATURE_NAMES),
            "types": FEATURE_TYPES,
            "model_matrix_columns": list(FEATURE_NAMES),
            "metadata_columns_not_predictors": list(METADATA_NAMES),
            "feature_missingness_before_preprocessing": missingness,
            "train_feature_missingness_before_preprocessing": train_missingness,
        },
        "split_method": "Fixed purchase-calendar-date windows; no randomization, label-based boundary choice, or model-score tuning. Equal purchase dates remain together because boundaries are dates.",
        "boundaries": BOUNDARIES,
        "counts_and_label_distribution": split_summaries,
        "excluded_from_splits": excluded,
        "maturity_assessment": {
            "primary_evaluation_window": "2017-01-01 through 2018-08-31, following the T-00 recommendation to use January 2017–August 2018 for primary chronological evaluation.",
            "sparse_early_history": "Pre-2017 V3-06 rows are excluded from the split windows because T-00 reports only 1 eligible order in 2016-09, 265 in 2016-10, and 1 in 2016-12; these sparse cohorts are not used as a standalone period.",
            "sparse_right_tail": "T-00 reports 16 source orders in 2018-09 and 4 in 2018-10, with no delivered outcomes. The raw-source monthly audit is recorded in the feature audit and reproduced in the manifest. These rows do not enter the delivered-only V3-06 population; they are not labeled on-time.",
            "august_sensitivity": "August 2018 is included as the final test month because T-00 recommends the Jan-2017–Aug-2018 primary window. A count/prevalence sensitivity excluding August is recorded separately; it is not used to select model features or boundaries.",
            "limitation": "No extraction timestamp proves complete follow-up. The target is conditional on eventual delivery, so non-delivered/unresolved orders are excluded rather than labeled negative. Treat all test estimates as retrospective cohort diagnostics, not operational failure risk.",
            "raw_monthly_tail": monthly_tail,
        },
        "preprocessing": {
            "artifact_path": preprocessor_path,
            "fit_rows": int(len(train)),
            "fit_split": "train only",
            "validation_or_test_fit": False,
            "transform_output_dimensions": transformed_shapes,
            "transformed_feature_names": list(preprocessor.get_feature_names_out()),
            "numeric": "median imputation then StandardScaler; all learned values fit on train only",
            "categorical": "most-frequent imputation then OneHotEncoder(handle_unknown=ignore); categories fit on train only",
            "estimator_trained": False,
            "scikit_learn_version": sklearn.__version__,
        },
        "reproduction": {
            "feature_command": ".venv/bin/python -m src.ml.features",
            "split_command": ".venv/bin/python -m src.ml.split",
            "generated_files": [output_path, manifest_path, preprocessor_path],
        },
    }
    if pre_start >= test_end:
        raise AssertionError("Chronological split boundary configuration is invalid")
    return split_frame, manifest, preprocessor


def default_paths() -> tuple[Path, Path, Path, Path, Path]:
    root = Path(__file__).resolve().parents[2]
    processed = root / "data" / "processed"
    return (
        processed / "delivery_features.csv",
        processed / "delivery_feature_audit.json",
        processed / "delivery_feature_splits.csv",
        processed / "delivery_split_manifest.json",
        processed / "delivery_preprocessor.joblib",
    )


def run_from_files(
    input_path: Path,
    audit_path: Path,
    output_path: Path,
    manifest_path: Path,
    preprocessor_path: Path,
) -> dict[str, Any]:
    for path in (input_path, audit_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required V3-07 split input not found: {path}")
    _validate_generated_paths(
        [input_path, audit_path],
        [output_path, manifest_path, preprocessor_path],
    )
    features = pd.read_csv(input_path, dtype={"order_id": "string", "purchase_ts": "string", "customer_state": "string"})
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    split_frame, manifest, preprocessor = build_split_outputs(
        features, audit, _sha256(input_path), _repo_relative(input_path), _repo_relative(output_path),
        _repo_relative(manifest_path), _repo_relative(preprocessor_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    preprocessor_path.parent.mkdir(parents=True, exist_ok=True)
    split_frame.to_csv(output_path, index=False)
    joblib.dump(preprocessor, preprocessor_path)
    manifest["preprocessing"]["artifact_sha256"] = _sha256(preprocessor_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    default_input, default_audit, default_output, default_manifest, default_preprocessor = default_paths()
    parser = argparse.ArgumentParser(description="Create the fixed V3-07 chronological split and train-only preprocessor.")
    parser.add_argument("--input", type=Path, default=default_input)
    parser.add_argument("--audit", type=Path, default=default_audit)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--preprocessor", type=Path, default=default_preprocessor)
    args = parser.parse_args(argv)
    try:
        manifest = run_from_files(args.input, args.audit, args.output, args.manifest, args.preprocessor)
    except (OSError, ValueError, KeyError) as exc:
        print(f"V3-07 split build failed: {exc}", file=sys.stderr)
        return 2
    print(f"Feature-ready rows: {manifest['dataset']['feature_ready_rows']:,}")
    print(f"Train: {manifest['counts_and_label_distribution']['train']['rows']:,}")
    print(f"Validation: {manifest['counts_and_label_distribution']['validation']['rows']:,}")
    print(f"Test: {manifest['counts_and_label_distribution']['test']['rows']:,}")
    print(f"Wrote {args.output}, {args.manifest}, and {args.preprocessor}")
    print("No model estimator was trained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
