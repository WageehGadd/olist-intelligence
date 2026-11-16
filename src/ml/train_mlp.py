"""V3-09: one bounded MLP, validation-only selection, one-use final-test evaluation."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from src.ml.features import FEATURE_NAMES
from src.ml.preprocessing import make_preprocessor, validate_feature_frame
from src.ml.train_classical import (
    DEFAULT_AUDIT_PATH, DEFAULT_FEATURE_PATH, DEFAULT_MANIFEST_PATH, DEFAULT_SPLIT_PATH,
    _validate_output_paths, choose_f1_threshold, load_training_validation,
    positive_class_probability, threshold_metrics,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = ROOT / "models/local/v3_09_mlp"
DEFAULT_METRICS_PATH = ROOT / "data/processed/v3_09_mlp_metrics.json"
DEFAULT_SELECTION_PATH = ROOT / "data/processed/v3_09_model_selection.json"
DEFAULT_TEST_METRICS_PATH = ROOT / "data/processed/v3_09_final_test_metrics.json"
DEFAULT_TEST_CLAIM_PATH = ROOT / "data/processed/v3_09_final_test_claimed.json"
SEED = 42
HIDDEN_LAYERS = (32, 16)
MAX_EPOCHS = 120
PATIENCE = 12
MIN_DELTA = 1e-5
BATCH_SIZE = 256
LEARNING_RATE = 0.001


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _probabilities(estimator: Any, features: pd.DataFrame) -> np.ndarray:
    values = np.asarray(estimator.predict_proba(features), dtype=float)
    classes = np.asarray(estimator.classes_)
    indices = np.flatnonzero(classes == 1)
    if values.ndim != 2 or len(indices) != 1:
        raise ValueError("Fitted model must expose a unique positive class labelled 1")
    result = values[:, int(indices[0])]
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError("Model probabilities must be finite and in [0, 1]")
    return result


def fit_mlp(train_x: pd.DataFrame, train_y: np.ndarray, validation_x: pd.DataFrame, validation_y: np.ndarray, *, seed: int = SEED) -> tuple[Pipeline, dict[str, Any], np.ndarray]:
    """Fit one fixed MLP; validation log-loss controls patience/checkpoint only."""
    validate_feature_frame(train_x)
    validate_feature_frame(validation_x)
    train_y = np.asarray(train_y, dtype=np.int8)
    validation_y = np.asarray(validation_y, dtype=np.int8)
    if len(train_x) != len(train_y) or len(validation_x) != len(validation_y):
        raise ValueError("Feature and target row counts do not match")
    if set(np.unique(train_y)) != {0, 1} or set(np.unique(validation_y)) != {0, 1}:
        raise ValueError("Training and validation targets must each contain both binary classes")

    preprocessor = make_preprocessor()
    train_matrix = np.asarray(preprocessor.fit_transform(train_x), dtype=float)
    validation_matrix = np.asarray(preprocessor.transform(validation_x), dtype=float)
    if train_matrix.ndim != 2 or validation_matrix.ndim != 2 or train_matrix.shape[1] != validation_matrix.shape[1]:
        raise ValueError("Preprocessed train and validation dimensions differ")
    if not np.isfinite(train_matrix).all() or not np.isfinite(validation_matrix).all():
        raise ValueError("Preprocessed matrices must be finite")

    classifier = MLPClassifier(
        hidden_layer_sizes=HIDDEN_LAYERS, activation="relu", solver="adam",
        alpha=0.0001, batch_size=min(BATCH_SIZE, len(train_y)), learning_rate_init=LEARNING_RATE,
        max_iter=1, shuffle=True, random_state=seed, early_stopping=False,
        tol=0.0, n_iter_no_change=MAX_EPOCHS + 1,
    )
    best_loss = float("inf")
    best_epoch = 0
    best_weights: tuple[list[np.ndarray], list[np.ndarray]] | None = None
    stale_epochs = 0
    history: list[float] = []
    started = time.perf_counter()
    for epoch in range(1, MAX_EPOCHS + 1):
        classifier.partial_fit(train_matrix, train_y, classes=np.array([0, 1], dtype=np.int8))
        probabilities = _probabilities(classifier, validation_matrix)
        # Binary cross entropy, evaluated only on the fixed chronological validation set.
        eps = np.finfo(float).eps
        clipped = np.clip(probabilities, eps, 1 - eps)
        loss = float(-np.mean(validation_y * np.log(clipped) + (1 - validation_y) * np.log(1 - clipped)))
        if not np.isfinite(loss):
            raise RuntimeError("Validation log-loss became non-finite")
        history.append(loss)
        if loss < best_loss - MIN_DELTA:
            best_loss = loss
            best_epoch = epoch
            best_weights = ([np.array(weight, copy=True) for weight in classifier.coefs_], [np.array(bias, copy=True) for bias in classifier.intercepts_])
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= PATIENCE:
            break
    if best_weights is None:
        raise RuntimeError("MLP did not produce a restorable validation checkpoint")
    classifier.coefs_, classifier.intercepts_ = best_weights
    pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])
    validation_probability = positive_class_probability(pipeline, validation_x)
    info = {
        "architecture": {"hidden_layer_sizes": list(HIDDEN_LAYERS), "activation": "relu", "output": "binary logistic probability"},
        "solver": "adam", "alpha": 0.0001, "learning_rate_init": LEARNING_RATE,
        "batch_size": BATCH_SIZE, "random_state": seed, "early_stopping": "external chronological validation binary log-loss; no random internal holdout",
        "max_epochs": MAX_EPOCHS, "patience": PATIENCE, "min_delta": MIN_DELTA,
        "epochs_run": len(history), "best_epoch": best_epoch, "best_validation_log_loss": best_loss,
        "validation_log_loss_history": history, "best_checkpoint_restored": True,
        "fit_seconds": float(time.perf_counter() - started),
        "preprocessed_dimensions": int(train_matrix.shape[1]),
        "train_only_preprocessor_fit": True,
        "limitations": "scikit-learn partial_fit performs one epoch per call and maintains the estimator optimizer state; validation log-loss is reused for stopping, so its result is not an unbiased performance estimate. Random mini-batch ordering is seeded but platform/library-level bitwise identity is not guaranteed.",
    }
    return pipeline, info, validation_probability


def _metrics(y: np.ndarray, probability: np.ndarray, threshold: float) -> dict[str, Any]:
    return {
        "average_precision": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "at_validation_selected_threshold": threshold_metrics(y, probability, threshold),
        "at_threshold_0_5": threshold_metrics(y, probability, 0.5),
        "positive_prevalence": float(np.mean(y)),
    }


def select_candidate(candidates: dict[str, dict[str, Any]]) -> str:
    """Choose highest validation AP; resolve exact ties using frozen order."""
    tie_order = ["LogisticRegression", "RandomForestClassifier", "SmallMLP", "DummyClassifier"]
    if set(candidates) != set(tie_order):
        raise ValueError("Selection requires exactly Dummy, LR, RF, and SmallMLP candidates")
    scores = [candidates[name].get("validation_average_precision") for name in tie_order]
    if any(not isinstance(score, (int, float)) or not np.isfinite(score) or not 0 <= score <= 1 for score in scores):
        raise ValueError("Candidate validation AP values must be finite and in [0, 1]")
    return max(tie_order, key=lambda name: (candidates[name]["validation_average_precision"], -tie_order.index(name)))


def _verify_v3_08(metrics_path: Path) -> dict[str, Any]:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    expected = {"DummyClassifier", "LogisticRegression", "RandomForestClassifier"}
    if metrics.get("task") != "V3-08" or set(metrics.get("models", {})) != expected:
        raise ValueError("V3-08 metrics do not contain the expected three frozen candidates")
    if metrics.get("test_evaluated") is not False or metrics.get("test_metrics_generated") is not False:
        raise ValueError("V3-08 metadata indicates test evaluation already occurred")
    if metrics.get("feature_names_in_order") != list(FEATURE_NAMES):
        raise ValueError("V3-08 feature order differs from the frozen contract")
    for name in expected:
        artifact = metrics.get("model_artifacts", {}).get(name, {})
        path = ROOT / artifact.get("path", "")
        if not path.is_file() or sha256_file(path) != artifact.get("sha256"):
            raise ValueError(f"V3-08 artifact missing or checksum mismatch: {name}")
    return metrics


def _safe_output_paths(model_dir: Path, paths: list[Path], input_paths: tuple[Path, ...]) -> None:
    for path in paths:
        _validate_output_paths(model_dir, path, input_paths)
    destinations = [model_dir.resolve(), *(path.resolve() for path in paths)]
    for i, first in enumerate(destinations):
        for second in destinations[i + 1:]:
            if first == second or first in second.parents or second in first.parents:
                raise ValueError("V3-09 output paths overlap")


def run_validation_experiment(*, feature_path: Path = DEFAULT_FEATURE_PATH, audit_path: Path = DEFAULT_AUDIT_PATH, split_path: Path = DEFAULT_SPLIT_PATH, manifest_path: Path = DEFAULT_MANIFEST_PATH, model_dir: Path = DEFAULT_MODEL_DIR, metrics_path: Path = DEFAULT_METRICS_PATH, classical_metrics_path: Path = ROOT / "data/processed/v3_08_classical_metrics.json") -> dict[str, Any]:
    input_paths = (feature_path, audit_path, split_path, manifest_path, classical_metrics_path)
    selection_path = DEFAULT_SELECTION_PATH
    _safe_output_paths(model_dir, [metrics_path, selection_path], input_paths)
    for path in (metrics_path, selection_path, model_dir):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite V3-09 frozen output: {path}")
    data = load_training_validation(feature_path, audit_path, split_path, manifest_path)
    classical = _verify_v3_08(classical_metrics_path)
    if classical.get("feature_artifact_sha256") != data["feature_sha256"] or classical.get("split_artifact_sha256") != data["split_sha256"]:
        raise ValueError("V3-08 candidates were evaluated on different frozen feature or split artifacts")
    if classical.get("split_boundaries") != data["manifest"].get("boundaries") or classical.get("partition_rows") != data["partition_rows"]:
        raise ValueError("V3-08 candidate split boundaries or counts differ from the validated V3-07 split")
    pipeline, fit_info, validation_probability = fit_mlp(data["train_x"], data["train_y"], data["validation_x"], data["validation_y"])
    threshold = choose_f1_threshold(data["validation_y"], validation_probability)
    mlp_validation = _metrics(data["validation_y"], validation_probability, threshold)
    model_dir.mkdir(parents=True, exist_ok=False)
    model_path = model_dir / "small_mlp.joblib"
    joblib.dump(pipeline, model_path)
    reloaded = joblib.load(model_path)
    reloaded_probability = positive_class_probability(reloaded, data["validation_x"])
    if not np.allclose(reloaded_probability, validation_probability, rtol=0, atol=1e-12):
        raise RuntimeError("Reloaded MLP changed validation probabilities")
    mlp_artifact = {"path": model_path.resolve().relative_to(ROOT).as_posix(), "sha256": sha256_file(model_path), "size_bytes": model_path.stat().st_size, "reload_probability_check": "passed"}

    candidates: dict[str, dict[str, Any]] = {}
    tie_order = ["LogisticRegression", "RandomForestClassifier", "SmallMLP", "DummyClassifier"]
    for name in ("DummyClassifier", "LogisticRegression", "RandomForestClassifier"):
        source = classical["models"][name]
        candidates[name] = {
            "validation_average_precision": float(source["validation"]["average_precision"]),
            "validation_roc_auc": float(source["validation"]["roc_auc"]),
            "validation_threshold": float(source["selected_validation_threshold"]),
            "validation_at_selected_threshold": source["validation"]["at_validation_selected_threshold"],
            "validation_at_threshold_0_5": source["validation"]["at_threshold_0_5"],
            "positive_prevalence": float(classical["class_balance"]["validation"]["late_prevalence"]),
            "artifact": classical["model_artifacts"][name],
            "source_metrics_sha256": sha256_file(classical_metrics_path),
        }
    candidates["SmallMLP"] = {
        "validation_average_precision": mlp_validation["average_precision"],
        "validation_roc_auc": mlp_validation["roc_auc"],
        "validation_threshold": threshold,
        "validation_at_selected_threshold": mlp_validation["at_validation_selected_threshold"],
        "validation_at_threshold_0_5": mlp_validation["at_threshold_0_5"],
        "positive_prevalence": mlp_validation["positive_prevalence"],
        "artifact": mlp_artifact,
    }
    chosen = select_candidate(candidates)
    metrics = {
        "task": "V3-09", "seed": SEED, "feature_names_in_order": list(FEATURE_NAMES),
        "feature_artifact_sha256": data["feature_sha256"], "split_artifact_sha256": data["split_sha256"],
        "split_manifest_version": data["manifest"]["manifest_version"], "split_boundaries": data["manifest"]["boundaries"],
        "partition_rows": data["partition_rows"], "train_rows": len(data["train_y"]), "train_late": int(data["train_y"].sum()),
        "validation_rows": len(data["validation_y"]), "validation_late": int(data["validation_y"].sum()),
        "mlp": {"fit": fit_info, "validation": mlp_validation, "artifact": mlp_artifact},
        "candidates": candidates,
        "selection_policy": {"primary_metric": "validation Average Precision (sklearn average_precision_score)", "tie_order": tie_order, "tie_rule": "Exact AP ties prefer LogisticRegression, then RandomForestClassifier, then SmallMLP, then DummyClassifier.", "threshold_policy": "Each candidate retains its existing V3-08 validation-F1 threshold policy; MLP uses the same policy. Threshold does not affect AP ranking."},
        "selected_candidate": chosen, "selected_threshold": candidates[chosen]["validation_threshold"],
        "test_evaluated": False, "test_metrics": None,
        "versions": {"python": sys.version.split()[0], "scikit_learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
        "limitations": ["validation prevalence differs materially from training prevalence", "validation log-loss also controls MLP stopping", "no calibration performed", "delivered-only retrospective label and historical point-in-time availability remain limitations"],
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    metric_sha = sha256_file(metrics_path)
    selected_artifact = candidates[chosen]["artifact"]
    selection = {
        "manifest_version": "v1", "task": "V3-09", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "selected_candidate": chosen, "selected_threshold": candidates[chosen]["validation_threshold"],
        "selection_metric": "validation_average_precision", "selection_rationale": f"Highest validation Average Precision among four candidates; tie order={tie_order}.",
        "feature_names_in_order": list(FEATURE_NAMES), "feature_artifact_sha256": data["feature_sha256"],
        "split_artifact_sha256": data["split_sha256"], "split_manifest_version": data["manifest"]["manifest_version"],
        "split_boundaries": data["manifest"]["boundaries"], "selected_artifact_path": selected_artifact["path"],
        "selected_artifact_sha256": selected_artifact["sha256"], "validation_metrics_sha256": metric_sha,
        "selected_validation_average_precision": candidates[chosen]["validation_average_precision"],
        "threshold_policy": "V3-08 validation F1 maximization over observed validation probabilities plus 0, 0.5, and 1; ties choose the higher threshold",
        "classical_metrics_sha256": sha256_file(classical_metrics_path), "test_evaluated": False,
    }
    # Exclusive creation prevents silently replacing an existing selection.
    selection_path.parent.mkdir(parents=True, exist_ok=True)
    with selection_path.open("x", encoding="utf-8") as stream:
        json.dump(selection, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return {"metrics": metrics, "selection": selection, "selection_path": selection_path, "metrics_path": metrics_path}


def verify_selection(selection_path: Path = DEFAULT_SELECTION_PATH) -> dict[str, Any]:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection.get("manifest_version") != "v1" or selection.get("feature_names_in_order") != list(FEATURE_NAMES):
        raise ValueError("Selection manifest version or feature schema is invalid")
    if selection.get("test_evaluated") is not False:
        raise ValueError("Selection manifest does not prove test was unused")
    artifact_relative = Path(selection["selected_artifact_path"])
    if artifact_relative.is_absolute() or ".." in artifact_relative.parts:
        raise ValueError("Selected model artifact path must be a safe repository-relative path")
    artifact_path = ROOT / artifact_relative
    try:
        artifact_path.resolve().relative_to((ROOT / "models/local").resolve())
    except ValueError as exc:
        raise ValueError("Selected model artifact must be under ignored models/local/") from exc
    if artifact_path.is_symlink() or not artifact_path.is_file() or sha256_file(artifact_path) != selection.get("selected_artifact_sha256"):
        raise ValueError("Selected model artifact is missing or has a checksum mismatch")
    metrics_path = DEFAULT_METRICS_PATH
    if not metrics_path.is_file() or sha256_file(metrics_path) != selection.get("validation_metrics_sha256"):
        raise ValueError("Validation comparison metrics are missing or changed")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if metrics.get("selected_candidate") != selection.get("selected_candidate") or metrics.get("selected_threshold") != selection.get("selected_threshold"):
        raise ValueError("Selection manifest disagrees with validation comparison")
    if selection.get("selected_candidate") not in {"DummyClassifier", "LogisticRegression", "RandomForestClassifier", "SmallMLP"}:
        raise ValueError("Selection manifest names an unknown candidate")
    threshold = selection.get("selected_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Selection manifest threshold is invalid")
    candidate = metrics.get("candidates", {}).get(selection.get("selected_candidate"), {})
    if candidate.get("artifact", {}).get("path") != selection.get("selected_artifact_path") or candidate.get("artifact", {}).get("sha256") != selection.get("selected_artifact_sha256"):
        raise ValueError("Selection manifest candidate artifact differs from validation comparison")
    if candidate.get("validation_average_precision") != selection.get("selected_validation_average_precision"):
        raise ValueError("Selection manifest candidate score differs from validation comparison")
    classical_path = ROOT / "data/processed/v3_08_classical_metrics.json"
    if not classical_path.is_file() or sha256_file(classical_path) != selection.get("classical_metrics_sha256"):
        raise ValueError("Frozen V3-08 comparison provenance is missing or changed")
    return selection


@dataclass(frozen=True)
class _TestEvaluationPaths:
    root: Path
    feature_path: Path
    audit_path: Path
    split_path: Path
    manifest_path: Path
    selection_path: Path
    output_path: Path
    claim_path: Path
    classical_metrics_path: Path
    synthetic_fixture: bool = False


def _evaluation_paths(root: Path, *, synthetic_fixture: bool = False) -> _TestEvaluationPaths:
    processed = root / "data/processed"
    return _TestEvaluationPaths(
        root=root,
        feature_path=processed / "delivery_features.csv",
        audit_path=processed / "delivery_feature_audit.json",
        split_path=processed / "delivery_feature_splits.csv",
        manifest_path=processed / "delivery_split_manifest.json",
        selection_path=processed / "v3_09_model_selection.json",
        output_path=processed / "v3_09_final_test_metrics.json",
        claim_path=processed / "v3_09_final_test_claimed.json",
        classical_metrics_path=processed / "v3_08_classical_metrics.json",
        synthetic_fixture=synthetic_fixture,
    )


def _project_evaluation_paths() -> _TestEvaluationPaths:
    """Return the one fixed location for the real project's test evaluation."""
    return _evaluation_paths(ROOT)


def _synthetic_evaluation_paths_for_test(root: Path) -> _TestEvaluationPaths:
    """Private fixture path constructor; accepted only for isolated synthetic tests."""
    return _evaluation_paths(root, synthetic_fixture=True)


def _assert_evaluation_context(paths: _TestEvaluationPaths) -> None:
    if paths.root.is_symlink():
        raise ValueError("Evaluation root may not be a symlink alias")
    root = paths.root.resolve()
    expected = _evaluation_paths(root, synthetic_fixture=paths.synthetic_fixture)
    path_fields = (
        "feature_path", "audit_path", "split_path", "manifest_path", "selection_path",
        "output_path", "claim_path", "classical_metrics_path",
    )
    for field in path_fields:
        actual_path = getattr(paths, field)
        expected_path = getattr(expected, field)
        resolved_path = actual_path.resolve()
        if resolved_path != expected_path.resolve():
            raise ValueError(f"Noncanonical final-test path rejected: {field}")
        if actual_path.is_symlink():
            raise ValueError(f"Symlink alias rejected for final-test path: {field}")
        try:
            resolved_path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Final-test path escapes its permitted root: {field}") from exc
        parent = actual_path.parent
        while parent != paths.root and paths.root in parent.parents:
            if parent.is_symlink():
                raise ValueError(f"Symlink directory alias rejected for final-test path: {field}")
            parent = parent.parent

    if not paths.synthetic_fixture:
        if root != ROOT.resolve():
            raise ValueError("Real evaluation is restricted to the project's canonical root")
        return

    # Synthetic fixture evaluation must be isolated from the checkout and all its ancestors.
    if root == ROOT.resolve() or root in ROOT.resolve().parents or ROOT.resolve() in root.parents:
        raise ValueError("Synthetic final-test fixture must be isolated outside the project checkout")
    marker = root / ".v3_09_synthetic_test_fixture.json"
    try:
        contents = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Synthetic final-test fixture marker is missing or invalid") from exc
    if contents != {"purpose": "V3-09 test-gate regression fixture only", "version": 1}:
        raise ValueError("Synthetic final-test fixture marker is not recognized")


def _validate_test_output_collisions(paths: _TestEvaluationPaths, selected_artifact: Path | None = None) -> None:
    outputs = [paths.claim_path.resolve(), paths.output_path.resolve()]
    protected = [
        paths.feature_path.resolve(), paths.audit_path.resolve(), paths.split_path.resolve(),
        paths.manifest_path.resolve(), paths.selection_path.resolve(), paths.classical_metrics_path.resolve(),
    ]
    if selected_artifact is not None:
        protected.append(selected_artifact.resolve())
    for index, output in enumerate(outputs):
        for other_output in outputs[index + 1:]:
            if output == other_output or output in other_output.parents or other_output in output.parents:
                raise ValueError("Final-test claim and metrics paths must be distinct and non-overlapping")
        for input_path in protected:
            if output == input_path or output in input_path.parents or input_path in output.parents:
                raise ValueError("Final-test output collides with or contains a protected input")
    allowed_processed = (paths.root / "data/processed").resolve()
    for output in outputs:
        if output.parent != allowed_processed:
            raise ValueError("Final-test outputs must use the fixed data/processed locations")


def _existing_test_evaluation_state(paths: _TestEvaluationPaths) -> None:
    claim = paths.claim_path
    metrics = paths.output_path
    claim_exists = claim.exists() or claim.is_symlink()
    metrics_exists = metrics.exists() or metrics.is_symlink()
    if not claim_exists and not metrics_exists:
        return
    if claim.is_symlink() or metrics.is_symlink():
        raise RuntimeError("Final-test claim/metrics state uses a symlink alias; evaluation is blocked for manual review")
    if not claim_exists:
        raise RuntimeError("Final-test metrics exist without the durable claim; refusing evaluation and requiring manual review")
    if not metrics_exists:
        raise RuntimeError("Final-test claim exists but metrics are missing/incomplete; refusing re-evaluation and requiring manual review")
    try:
        claim_record = json.loads(claim.read_text(encoding="utf-8"))
        metrics_record = json.loads(metrics.read_text(encoding="utf-8"))
        valid_claim = (
            isinstance(claim_record, dict)
            and isinstance(claim_record.get("claimed_at_utc"), str)
            and isinstance(claim_record.get("selection_manifest_sha256"), str)
            and len(claim_record["selection_manifest_sha256"]) == 64
            and claim_record.get("selection_manifest_version") == "v1"
            and claim_record.get("purpose") == "single authorized final evaluation; claim is never reset"
        )
        valid_metrics = (
            isinstance(metrics_record, dict)
            and metrics_record.get("task") == "V3-09"
            and metrics_record.get("test_evaluation_count") == 1
            and isinstance(metrics_record.get("evaluation_timestamp_utc"), str)
            and isinstance(claim_record, dict)
            and isinstance(metrics_record.get("selection_manifest_sha256"), str)
            and metrics_record.get("selection_manifest_sha256") == claim_record.get("selection_manifest_sha256")
            and all(isinstance(metrics_record.get(key), str) and len(metrics_record[key]) == 64 for key in ("selected_artifact_sha256", "feature_artifact_sha256", "split_artifact_sha256"))
        )
        if not valid_claim or not valid_metrics:
            raise ValueError("claim or metrics schema is incomplete")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Final-test claim/metrics state is malformed or incomplete; refusing re-evaluation and requiring manual review") from exc
    raise FileExistsError("Final-test evaluation is already recorded; refusing a second evaluation")


def _create_test_claim(path: Path, record: dict[str, Any]) -> None:
    """Atomically acquire the durable one-time claim without replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _evaluate_test_once_for_paths(paths: _TestEvaluationPaths) -> dict[str, Any]:
    """Core evaluator; synthetic paths are accepted only in a marked isolated fixture."""
    _assert_evaluation_context(paths)
    _validate_test_output_collisions(paths)
    _existing_test_evaluation_state(paths)

    selection = verify_selection(paths.selection_path)
    manifest = json.loads(paths.manifest_path.read_text(encoding="utf-8"))
    classical = _verify_v3_08(paths.classical_metrics_path)
    if selection["feature_artifact_sha256"] != classical["feature_artifact_sha256"] or selection["split_artifact_sha256"] != classical["split_artifact_sha256"]:
        raise ValueError("Selection provenance differs from the validated V3-08 frozen split")
    if selection["split_manifest_version"] != manifest.get("manifest_version") or selection["split_boundaries"] != manifest.get("boundaries"):
        raise ValueError("Selection provenance differs from split manifest")
    artifact_relative = Path(selection["selected_artifact_path"])
    if artifact_relative.is_absolute() or ".." in artifact_relative.parts:
        raise ValueError("Selected model artifact path must be relative to the evaluation root")
    selected_artifact = paths.root / artifact_relative
    try:
        selected_artifact.resolve().relative_to(paths.root.resolve())
    except ValueError as exc:
        raise ValueError("Selected model artifact escapes the evaluation root") from exc
    if selected_artifact.is_symlink():
        raise ValueError("Selected model artifact may not use a symlink alias")
    _validate_test_output_collisions(paths, selected_artifact)

    # Exclusive durable claim is acquired before the loader or any test feature/label extraction.
    claim = {
        "claimed_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_manifest_sha256": sha256_file(paths.selection_path),
        "selection_manifest_version": selection["manifest_version"],
        "purpose": "single authorized final evaluation; claim is never reset",
    }
    _create_test_claim(paths.claim_path, claim)

    data = load_training_validation(paths.feature_path, paths.audit_path, paths.split_path, paths.manifest_path)
    if selection["feature_artifact_sha256"] != data["feature_sha256"] or selection["split_artifact_sha256"] != data["split_sha256"]:
        raise ValueError("Selection manifest does not match the current verified feature/split artifacts")
    split_frame = pd.read_csv(paths.split_path, dtype={"order_id": "string", "purchase_ts": "string", "customer_state": "string"})
    test = split_frame.loc[split_frame["split"].eq("test")]
    if len(test) != int(manifest["counts_and_label_distribution"]["test"]["rows"]):
        raise ValueError("Test row count does not match validated split manifest")
    y = pd.to_numeric(test["late"], errors="raise").to_numpy(dtype=np.int8)
    if not np.isin(y, (0, 1)).all() or len(np.unique(y)) != 2:
        raise ValueError("Final test labels must contain both binary classes")
    X = test.loc[:, FEATURE_NAMES].copy()
    for column in FEATURE_NAMES:
        if column != "customer_state":
            X[column] = pd.to_numeric(X[column], errors="raise")
    model = joblib.load(selected_artifact)
    probability = positive_class_probability(model, X)
    threshold = float(selection["selected_threshold"])
    if not 0 <= threshold <= 1:
        raise ValueError("Frozen threshold is outside [0, 1]")
    result = {
        "task": "V3-09", "evaluation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "selected_candidate": selection["selected_candidate"],
        "selection_manifest_sha256": claim["selection_manifest_sha256"],
        "selection_manifest_version": selection["manifest_version"],
        "selected_artifact_path": selection["selected_artifact_path"],
        "selected_artifact_sha256": sha256_file(selected_artifact),
        "feature_artifact_sha256": data["feature_sha256"],
        "split_artifact_sha256": data["split_sha256"], "split_manifest_version": manifest["manifest_version"],
        "test_rows": int(len(y)), "late_count": int(y.sum()), "positive_prevalence": float(y.mean()),
        "average_precision": float(average_precision_score(y, probability)), "roc_auc": float(roc_auc_score(y, probability)),
        "threshold": threshold, "threshold_source": "frozen validation-only selection manifest",
        "at_frozen_threshold": threshold_metrics(y, probability, threshold),
        "test_evaluation_count": 1, "sensitivity_analysis": "not performed",
    }
    with paths.output_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return result


def evaluate_final_test_once() -> dict[str, Any]:
    """Evaluate the real project's selected model at its one fixed, durable location."""
    return _evaluate_test_once_for_paths(_project_evaluation_paths())


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run V3-09 validation comparison, then optionally claim the final test once.")
    parser.add_argument("--evaluate-test-once", action="store_true")
    args = parser.parse_args()
    if args.evaluate_test_once:
        test = evaluate_final_test_once()
        print("One-time final test results:", json.dumps(test, indent=2))
        return 0
    result = run_validation_experiment()
    print("Validation comparison selected:", result["selection"]["selected_candidate"])
    print("Selection manifest:", result["selection_path"], sha256_file(result["selection_path"]))
    print("Test remains unevaluated. Review the frozen manifest before invoking --evaluate-test-once.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
