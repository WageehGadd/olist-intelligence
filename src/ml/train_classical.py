"""Train V3-08 classical baselines without evaluating final test labels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import warnings
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from src.ml.features import FEATURE_NAMES, METADATA_NAMES, parse_purchase_timestamp
from src.ml.preprocessing import make_preprocessor, validate_feature_frame
from src.ml.split import BOUNDARIES, SPLIT_COLUMN


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FEATURE_PATH = ROOT / "data/processed/delivery_features.csv"
DEFAULT_AUDIT_PATH = ROOT / "data/processed/delivery_feature_audit.json"
DEFAULT_SPLIT_PATH = ROOT / "data/processed/delivery_feature_splits.csv"
DEFAULT_MANIFEST_PATH = ROOT / "data/processed/delivery_split_manifest.json"
DEFAULT_MODEL_DIR = ROOT / "models/local/v3_08_classical"
DEFAULT_METRICS_PATH = ROOT / "data/processed/v3_08_classical_metrics.json"
MODEL_SEED = 42
EXPECTED_SPLIT_COLUMNS = [*METADATA_NAMES, *FEATURE_NAMES, SPLIT_COLUMN]
SPLIT_NAMES = ("train", "validation", "test", "excluded_pre_window", "excluded_post_window")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_count(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Split manifest {context} must be a nonnegative integer")
    return value


def _parse_model_feature_row(row: list[str], positions: dict[str, int]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in FEATURE_NAMES:
        raw = row[positions[name]]
        if name == "customer_state":
            values[name] = raw if raw else np.nan
        elif raw == "":
            values[name] = np.nan
        else:
            try:
                number = float(raw)
            except ValueError as exc:
                raise ValueError(f"Invalid numeric feature {name}: {raw!r}") from exc
            if not np.isfinite(number):
                raise ValueError(f"Non-finite numeric feature {name}")
            values[name] = number
    return values


def load_training_validation(
    feature_path: Path = DEFAULT_FEATURE_PATH,
    audit_path: Path = DEFAULT_AUDIT_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    """Validate V3-07 artifacts; only train/validation labels enter this function."""
    for path in (feature_path, audit_path, split_path, manifest_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required V3-07 artifact not found: {path}")

    feature_sha = _sha256(feature_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset = manifest.get("dataset")
    if not isinstance(dataset, dict):
        raise ValueError("Split manifest is missing dataset metadata")
    if audit.get("feature_artifact_sha256") != feature_sha:
        raise ValueError("Feature CSV checksum does not match its audit")
    if dataset.get("input_sha256") != feature_sha or dataset.get("feature_artifact_sha256") != feature_sha:
        raise ValueError("Feature CSV checksum does not match the split manifest")
    try:
        expected_feature_path = feature_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        expected_feature_path = str(feature_path.resolve())
    if dataset.get("input_path") != expected_feature_path:
        raise ValueError("Feature CSV path does not match the split manifest")
    if manifest.get("manifest_version") != "v1":
        raise ValueError("Unsupported V3-07 split manifest version")
    if manifest.get("boundaries") != BOUNDARIES:
        raise ValueError("Split manifest boundaries differ from the frozen V3-07 boundaries")

    contract = manifest.get("feature_contract", {})
    if contract.get("names_in_order") != list(FEATURE_NAMES):
        raise ValueError("Split manifest feature order differs from Shared Contracts")
    if contract.get("model_matrix_columns") != list(FEATURE_NAMES):
        raise ValueError("Split manifest model matrix includes unexpected columns")
    if contract.get("metadata_columns_not_predictors") != list(METADATA_NAMES):
        raise ValueError("Split manifest metadata denylist differs from V3-07")
    for audit_key, manifest_key in (
        ("feature_ready_rows", "feature_ready_rows"),
        ("feature_ready_late", "feature_ready_late"),
        ("feature_ready_negative_rows", "feature_ready_negative_rows"),
        ("population_input_rows", "target_population_rows"),
        ("population_input_late", "target_population_late"),
    ):
        if audit.get(audit_key) != dataset.get(manifest_key):
            raise ValueError(f"Feature audit and split manifest disagree on {audit_key}")
    if audit.get("exclusive_feature_exclusion_counts") != dataset.get("feature_exclusions"):
        raise ValueError("Feature audit exclusions do not match the split manifest")

    partition_manifest = manifest.get("counts_and_label_distribution")
    excluded_manifest = manifest.get("excluded_from_splits")
    if not isinstance(partition_manifest, dict) or not isinstance(excluded_manifest, dict):
        raise ValueError("Split manifest is missing partition summaries")
    for name in ("train", "validation", "test"):
        if not isinstance(partition_manifest.get(name), dict):
            raise ValueError(f"Split manifest is missing {name} summary")
    for name in ("pre_window", "post_window"):
        if not isinstance(excluded_manifest.get(name), dict):
            raise ValueError(f"Split manifest is missing {name} exclusion summary")

    counts = {name: 0 for name in SPLIT_NAMES}
    positives = {"train": 0, "validation": 0}
    ids: set[str] = set()
    model_rows: dict[str, list[dict[str, Any]]] = {"train": [], "validation": []}
    labels: dict[str, list[int]] = {"train": [], "validation": []}
    with split_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("Split CSV is empty") from exc
        if header != EXPECTED_SPLIT_COLUMNS:
            raise ValueError("Split CSV columns differ from the frozen feature/split schema")
        positions = {name: index for index, name in enumerate(header)}
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f"Split CSV row {row_number} has an invalid column count")
            partition = row[positions[SPLIT_COLUMN]]
            if partition not in counts:
                raise ValueError(f"Unknown split partition {partition!r} at row {row_number}")
            order_id = row[positions["order_id"]]
            if not order_id or order_id in ids:
                raise ValueError("Split artifact order IDs must be present and globally unique")
            ids.add(order_id)
            try:
                purchase_date = parse_purchase_timestamp(row[positions["purchase_ts"]]).date()
            except ValueError as exc:
                raise ValueError(f"Invalid purchase timestamp at split row {row_number}") from exc

            if partition in ("train", "validation", "test"):
                bounds = BOUNDARIES[partition]
                start = date.fromisoformat(bounds["start_inclusive"])
                end = date.fromisoformat(bounds["end_exclusive"])
                if not start <= purchase_date < end:
                    raise ValueError(f"Purchase date falls outside its {partition} partition")
            elif partition == "excluded_pre_window":
                start = date.fromisoformat(BOUNDARIES["train"]["start_inclusive"])
                if purchase_date >= start:
                    raise ValueError("Pre-window row is not before the frozen train boundary")
            else:
                end = date.fromisoformat(BOUNDARIES["test"]["end_exclusive"])
                if purchase_date < end:
                    raise ValueError("Post-window row is before the frozen test end")

            counts[partition] += 1
            if partition == "test" or partition.startswith("excluded_"):
                # Do not index the target or predictor columns for these rows.
                continue

            raw_label = row[positions["late"]]
            if raw_label not in ("0", "1"):
                raise ValueError(f"Invalid {partition} target label at split row {row_number}")
            label = int(raw_label)
            labels[partition].append(label)
            positives[partition] += label
            model_rows[partition].append(_parse_model_feature_row(row, positions))

    for name in ("train", "validation", "test"):
        expected = _manifest_count(partition_manifest[name].get("rows"), f"{name}.rows")
        if counts[name] != expected:
            raise ValueError(f"Split CSV {name} row count does not match the manifest")
    for name, manifest_name in (("excluded_pre_window", "pre_window"), ("excluded_post_window", "post_window")):
        expected = _manifest_count(excluded_manifest[manifest_name].get("rows"), f"{manifest_name}.rows")
        if counts[name] != expected:
            raise ValueError(f"Split CSV {name} row count does not match the manifest")

    total_feature_rows = _manifest_count(dataset.get("feature_ready_rows"), "dataset.feature_ready_rows")
    if sum(counts.values()) != total_feature_rows:
        raise ValueError("Split partition rows do not reconcile with the feature-ready population")
    for name in ("train", "validation"):
        summary = partition_manifest[name]
        expected_positive = _manifest_count(summary.get("positive"), f"{name}.positive")
        expected_negative = _manifest_count(summary.get("negative"), f"{name}.negative")
        actual_positive = positives[name]
        actual_negative = len(labels[name]) - actual_positive
        if (actual_positive, actual_negative) != (expected_positive, expected_negative):
            raise ValueError(f"Split CSV {name} labels do not match the split manifest")
        if not labels[name] or len(set(labels[name])) != 2:
            raise ValueError(f"{name} must contain both late classes for the declared metrics")

    train = pd.DataFrame(model_rows["train"], columns=FEATURE_NAMES)
    validation = pd.DataFrame(model_rows["validation"], columns=FEATURE_NAMES)
    validate_feature_frame(train)
    validate_feature_frame(validation)
    return {
        "train_x": train,
        "train_y": np.asarray(labels["train"], dtype=np.int8),
        "validation_x": validation,
        "validation_y": np.asarray(labels["validation"], dtype=np.int8),
        "partition_rows": counts,
        "feature_sha256": feature_sha,
        "split_sha256": _sha256(split_path),
        "manifest": manifest,
        "order_ids_disjoint": True,
    }


def build_pipelines(seed: int = MODEL_SEED) -> dict[str, Pipeline]:
    """Create three independent preprocessing+estimator pipelines."""
    estimators = {
        "DummyClassifier": DummyClassifier(strategy="prior"),
        "LogisticRegression": LogisticRegression(
            C=1.0, solver="lbfgs", max_iter=2000, random_state=seed, class_weight=None
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=5,
            max_features="sqrt",
            random_state=seed,
            n_jobs=-1,
            class_weight=None,
        ),
    }
    return {
        name: Pipeline([("preprocessor", make_preprocessor()), ("classifier", estimator)])
        for name, estimator in estimators.items()
    }


def positive_class_probability(pipeline: Pipeline, features: pd.DataFrame) -> np.ndarray:
    """Return predict_proba's column for label 1, independent of class order."""
    validate_feature_frame(features)
    classifier = pipeline.named_steps["classifier"]
    classes = np.asarray(classifier.classes_)
    positive_indices = np.flatnonzero(classes == 1)
    if len(positive_indices) != 1:
        raise ValueError("Fitted classifier must expose exactly one positive class labelled 1")
    probabilities = np.asarray(pipeline.predict_proba(features), dtype=float)
    if probabilities.ndim != 2 or probabilities.shape[1] != len(classes):
        raise ValueError("predict_proba output does not match fitted classifier classes")
    result = probabilities[:, int(positive_indices[0])]
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError("Positive-class probabilities must be finite and in [0, 1]")
    return result


def choose_f1_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    """Maximize validation F1; resolve equal scores toward the higher threshold."""
    y_true = np.asarray(y_true, dtype=np.int8)
    probabilities = np.asarray(probabilities, dtype=float)
    if len(y_true) == 0 or len(y_true) != len(probabilities):
        raise ValueError("Threshold selection requires equally sized nonempty labels and scores")
    if not np.isin(y_true, (0, 1)).all():
        raise ValueError("Threshold selection labels must contain only 0 or 1")
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Threshold selection probabilities must be in [0, 1]")
    candidates = np.unique(np.concatenate(([0.0, 0.5, 1.0], probabilities)))
    scored = [
        (float(f1_score(y_true, probabilities >= threshold, zero_division=0)), float(threshold))
        for threshold in candidates
    ]
    return max(scored, key=lambda result: (result[0], result[1]))[1]


def threshold_metrics(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=np.int8)
    predicted = (np.asarray(probabilities, dtype=float) >= threshold).astype(np.int8)
    matrix = confusion_matrix(y_true, predicted, labels=[0, 1])
    tn, fp, fn, tp = (int(value) for value in matrix.ravel())
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "confusion_matrix_labels": ["actual_0", "actual_1"],
        "confusion_matrix_predicted_labels": ["predicted_0", "predicted_1"],
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "predicted_positive_rate": float(predicted.mean()),
        "actual_positive_prevalence": float(y_true.mean()),
    }


def evaluate_candidate(
    pipeline: Pipeline,
    train_x: pd.DataFrame,
    train_y: np.ndarray,
    validation_x: pd.DataFrame,
    validation_y: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray]:
    """Fit on train, choose threshold on validation, and report train/validation."""
    validate_feature_frame(train_x)
    validate_feature_frame(validation_x)
    if len(train_x) != len(train_y) or len(validation_x) != len(validation_y):
        raise ValueError("Feature and target row counts do not match")
    if set(train_y).difference({0, 1}) or set(validation_y).difference({0, 1}):
        raise ValueError("Targets must contain only 0 or 1")

    captured: list[str] = []
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        pipeline.fit(train_x, train_y)
    elapsed = time.perf_counter() - start
    for warning in records:
        captured.append(f"{warning.category.__name__}: {warning.message}")

    train_probability = positive_class_probability(pipeline, train_x)
    validation_probability = positive_class_probability(pipeline, validation_x)
    threshold = choose_f1_threshold(validation_y, validation_probability)

    train_metrics = {
        "average_precision": float(average_precision_score(train_y, train_probability)),
        "roc_auc": float(roc_auc_score(train_y, train_probability)),
        "at_validation_selected_threshold": threshold_metrics(train_y, train_probability, threshold),
        "at_threshold_0_5": threshold_metrics(train_y, train_probability, 0.5),
    }
    validation_metrics = {
        "average_precision": float(average_precision_score(validation_y, validation_probability)),
        "roc_auc": float(roc_auc_score(validation_y, validation_probability)),
        "at_validation_selected_threshold": threshold_metrics(validation_y, validation_probability, threshold),
        "at_threshold_0_5": threshold_metrics(validation_y, validation_probability, 0.5),
    }
    return {
        "fit_seconds": float(elapsed),
        "threshold_policy": "maximize validation F1 over observed validation probabilities plus 0, 0.5, and 1; ties choose the highest threshold",
        "selected_validation_threshold": threshold,
        "training": train_metrics,
        "validation": validation_metrics,
        "warnings": captured,
    }, validation_probability


def _validate_output_paths(model_dir: Path, metrics_path: Path) -> None:
    model_root = (ROOT / "models" / "local").resolve()
    metrics_root = (ROOT / "data" / "processed").resolve()
    try:
        model_dir.resolve().relative_to(model_root)
    except ValueError as exc:
        raise ValueError("Model artifacts must be written under ignored models/local/") from exc
    try:
        metrics_path.resolve().relative_to(metrics_root)
    except ValueError as exc:
        raise ValueError("Metrics artifacts must be written under ignored data/processed/") from exc


def run_experiment(
    feature_path: Path = DEFAULT_FEATURE_PATH,
    audit_path: Path = DEFAULT_AUDIT_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    model_dir: Path = DEFAULT_MODEL_DIR,
    metrics_path: Path = DEFAULT_METRICS_PATH,
    seed: int = MODEL_SEED,
) -> dict[str, Any]:
    _validate_output_paths(model_dir, metrics_path)
    data = load_training_validation(feature_path, audit_path, split_path, manifest_path)
    train_x, train_y = data["train_x"], data["train_y"]
    validation_x, validation_y = data["validation_x"], data["validation_y"]

    results: dict[str, Any] = {}
    pipelines = build_pipelines(seed)
    validation_probabilities: dict[str, np.ndarray] = {}
    total_start = time.perf_counter()
    for name, pipeline in pipelines.items():
        result, validation_probability = evaluate_candidate(
            pipeline, train_x, train_y, validation_x, validation_y
        )
        results[name] = result
        validation_probabilities[name] = validation_probability

    model_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, dict[str, Any]] = {}
    for name, pipeline in pipelines.items():
        path = model_dir / f"{name.lower()}.joblib"
        joblib.dump(pipeline, path)
        loaded = joblib.load(path)
        reloaded_probability = positive_class_probability(loaded, validation_x)
        if not np.allclose(reloaded_probability, validation_probabilities[name], rtol=0, atol=1e-12):
            raise RuntimeError(f"Reloaded {name} pipeline changed validation probabilities")
        artifacts[name] = {
            "path": path.resolve().relative_to(ROOT).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
            "reload_probability_check": "passed",
        }

    provisional = max(results, key=lambda name: results[name]["validation"]["average_precision"])
    elapsed = float(time.perf_counter() - total_start)
    manifest = data["manifest"]
    metrics = {
        "task": "V3-08",
        "seed": seed,
        "positive_class": 1,
        "feature_names_in_order": list(FEATURE_NAMES),
        "model_input_columns": list(FEATURE_NAMES),
        "metadata_excluded_from_model_input": list(METADATA_NAMES),
        "feature_artifact_sha256": data["feature_sha256"],
        "split_artifact_sha256": data["split_sha256"],
        "split_manifest_version": manifest["manifest_version"],
        "split_boundaries": manifest["boundaries"],
        "partition_rows": data["partition_rows"],
        "training_validation_order_ids_disjoint": data["order_ids_disjoint"],
        "class_balance": {
            "training": {
                "rows": int(len(train_y)), "late": int(train_y.sum()),
                "on_time_or_early": int(len(train_y) - train_y.sum()),
                "late_prevalence": float(train_y.mean()),
            },
            "validation": {
                "rows": int(len(validation_y)), "late": int(validation_y.sum()),
                "on_time_or_early": int(len(validation_y) - validation_y.sum()),
                "late_prevalence": float(validation_y.mean()),
            },
        },
        "models": results,
        "model_artifacts": artifacts,
        "provisional_classical_candidate_by_validation_average_precision": provisional,
        "selection_note": "Provisional classical candidate only; final selection waits for V3-09 and does not use test outcomes.",
        "test_evaluated": False,
        "test_labels_accessed": False,
        "test_metrics": None,
        "warnings": {name: result["warnings"] for name, result in results.items()},
        "runtime_seconds": {
            "models_fit": {name: result["fit_seconds"] for name, result in results.items()},
            "total_experiment": elapsed,
        },
        "configuration": {
            "DummyClassifier": {"strategy": "prior"},
            "LogisticRegression": {
                "C": 1.0, "solver": "lbfgs", "max_iter": 2000,
                "random_state": seed, "class_weight": None,
            },
            "RandomForestClassifier": {
                "n_estimators": 200, "max_depth": 12, "min_samples_leaf": 5,
                "max_features": "sqrt", "random_state": seed, "n_jobs": -1,
                "class_weight": None,
            },
            "class_weight_rationale": "No weighting used to keep candidates on the same observed training objective; imbalance is reported and addressed through validation-only threshold selection.",
        },
        "versions": {
            "python": sys.version.split()[0],
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "regeneration_command": ".venv/bin/python -m src.ml.train_classical",
        "limitations": [
            "Delivered-only outcome is retrospective and conditional on eventual delivery.",
            "No extraction timestamp proves complete follow-up; unresolved orders are not negative labels.",
            "Promise-date, cart/item, and customer-state availability at order creation is not proven.",
            "Validation prevalence differs materially from training prevalence; thresholds may not transfer or remain calibrated.",
            "Average Precision is sklearn average_precision_score, not trapezoidal PR-AUC.",
        ],
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train V3-08 Dummy, Logistic Regression, and Random Forest baselines."
    )
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURE_PATH)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--seed", type=int, default=MODEL_SEED)
    args = parser.parse_args(argv)
    try:
        metrics = run_experiment(
            args.features, args.audit, args.split, args.manifest,
            args.model_dir, args.metrics, args.seed,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"V3-08 classical training failed: {exc}", file=sys.stderr)
        return 2

    print("V3-08 completed; test labels were not read and no test metrics were generated.")
    print("Training/validation class balance:", json.dumps(metrics["class_balance"], indent=2))
    print("Validation metrics:")
    for name, result in metrics["models"].items():
        val = result["validation"]
        selected = val["at_validation_selected_threshold"]
        conventional = val["at_threshold_0_5"]
        print(
            f"  {name}: AP={val['average_precision']:.6f}, ROC-AUC={val['roc_auc']:.6f}, "
            f"selected_threshold={selected['threshold']:.6f}, "
            f"F1={selected['f1']:.6f}, F1@0.5={conventional['f1']:.6f}"
        )
    print("Provisional AP leader:", metrics["provisional_classical_candidate_by_validation_average_precision"])
    print("Metrics written to", DEFAULT_METRICS_PATH)
    print("Local pipelines written under", DEFAULT_MODEL_DIR)
    print("Warnings:", json.dumps(metrics["warnings"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
