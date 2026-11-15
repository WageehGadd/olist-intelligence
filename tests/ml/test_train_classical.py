from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, roc_auc_score

from src.ml.features import FEATURE_NAMES, METADATA_NAMES
from src.ml.train_classical import (
    DEFAULT_METRICS_PATH,
    DEFAULT_MODEL_DIR,
    _validate_output_paths,
    build_pipelines,
    choose_f1_threshold,
    evaluate_candidate,
    load_training_validation,
    positive_class_probability,
    run_experiment,
    threshold_metrics,
)


def _feature_row(order_id: str, purchase_ts: str, late: int, state: str = "SP") -> dict[str, object]:
    return {
        "order_id": order_id,
        "purchase_ts": purchase_ts,
        "late": late,
        "purchase_hour": 10,
        "purchase_weekday": 1,
        "purchase_month": int(purchase_ts[5:7]),
        "promised_lead_days": 5,
        "customer_state": state,
        "item_price_total": 20.0,
        "freight_total": 4.0,
        "item_count": 1,
    }


def _fixture_artifacts(tmp_path: Path):
    feature_path = tmp_path / "delivery_features.csv"
    rows = [
        _feature_row("tr0", "2017-06-01 10:00:00", 0),
        _feature_row("tr1", "2017-06-02 10:00:00", 1),
        _feature_row("tr2", "2017-06-03 10:00:00", 0),
        _feature_row("tr3", "2017-06-04 10:00:00", 0),
        _feature_row("va0", "2018-01-01 10:00:00", 0, "PR"),
        _feature_row("va1", "2018-01-02 10:00:00", 1, "PR"),
        _feature_row("va2", "2018-02-01 10:00:00", 1, "PR"),
        _feature_row("va3", "2018-03-01 10:00:00", 0, "PR"),
        _feature_row("te0", "2018-04-01 10:00:00", 1),
        _feature_row("te1", "2018-04-02 10:00:00", 0),
        _feature_row("old", "2016-12-31 10:00:00", 0),
        _feature_row("new", "2018-09-01 10:00:00", 0),
    ]
    features = pd.DataFrame(rows, columns=[*METADATA_NAMES, *FEATURE_NAMES])
    features.to_csv(feature_path, index=False)
    feature_sha = hashlib.sha256(feature_path.read_bytes()).hexdigest()

    audit_path = tmp_path / "delivery_feature_audit.json"
    audit = {
        "feature_artifact_sha256": feature_sha,
        "feature_ready_rows": 12,
        "feature_ready_late": 4,
        "feature_ready_negative_rows": 8,
        "population_input_rows": 12,
        "population_input_late": 4,
        "feature_excluded_rows": 0,
        "feature_excluded_late": 0,
        "exclusive_feature_exclusion_counts": {},
    }
    audit_path.write_text(json.dumps(audit), encoding="utf-8")

    split_path = tmp_path / "delivery_feature_splits.csv"
    from src.ml.split import assign_chronological_splits

    assign_chronological_splits(features).to_csv(split_path, index=False)

    manifest_path = tmp_path / "delivery_split_manifest.json"
    manifest = {
        "manifest_version": "v1",
        "dataset": {
            "input_path": str(feature_path.resolve()),
            "input_sha256": feature_sha,
            "feature_artifact_sha256": feature_sha,
            "feature_ready_rows": 12,
            "feature_ready_late": 4,
            "feature_ready_negative_rows": 8,
            "target_population_rows": 12,
            "target_population_late": 4,
            "feature_exclusions": {},
        },
        "feature_contract": {
            "names_in_order": list(FEATURE_NAMES),
            "model_matrix_columns": list(FEATURE_NAMES),
            "metadata_columns_not_predictors": list(METADATA_NAMES),
        },
        "boundaries": {
            "train": {"start_inclusive": "2017-01-01", "end_exclusive": "2018-01-01"},
            "validation": {"start_inclusive": "2018-01-01", "end_exclusive": "2018-04-01"},
            "test": {"start_inclusive": "2018-04-01", "end_exclusive": "2018-09-01"},
        },
        "counts_and_label_distribution": {
            "train": {"rows": 4, "positive": 1, "negative": 3},
            "validation": {"rows": 4, "positive": 2, "negative": 2},
            "test": {"rows": 2, "positive": 1, "negative": 1},
        },
        "excluded_from_splits": {
            "pre_window": {"rows": 1},
            "post_window": {"rows": 1},
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return feature_path, audit_path, split_path, manifest_path


def test_loader_accepts_correct_deterministic_split_and_returns_only_train_validation_targets(tmp_path):
    paths = _fixture_artifacts(tmp_path)
    loaded = load_training_validation(*paths)
    assert list(loaded["train_x"].columns) == list(FEATURE_NAMES)
    assert list(loaded["validation_x"].columns) == list(FEATURE_NAMES)
    assert len(loaded["train_y"]) == 4
    assert len(loaded["validation_y"]) == 4
    assert loaded["partition_rows"] == {
        "train": 4, "validation": 4, "test": 2,
        "excluded_pre_window": 1, "excluded_post_window": 1,
    }
    assert loaded["order_ids_disjoint"] is True


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("feature_checksum", "checksum"),
        ("feature_order", "feature order"),
        ("boundary", "boundaries"),
        ("train_rows", "train row count"),
    ],
)
def test_mismatched_feature_or_split_manifest_is_rejected(tmp_path, mutation, match):
    feature_path, audit_path, split_path, manifest_path = _fixture_artifacts(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    if mutation == "feature_checksum":
        manifest["dataset"]["input_sha256"] = "0" * 64
    elif mutation == "feature_order":
        manifest["feature_contract"]["names_in_order"].reverse()
    elif mutation == "boundary":
        manifest["boundaries"]["test"]["end_exclusive"] = "2018-10-01"
    else:
        manifest["counts_and_label_distribution"]["train"]["rows"] = 99
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=match):
        load_training_validation(feature_path, audit_path, split_path, manifest_path)


@pytest.mark.parametrize(
    "mutation",
    ["train_feature", "validation_feature", "membership", "target", "stale_features"],
)
def test_loader_rejects_split_not_derived_from_verified_feature_artifact(tmp_path, mutation):
    feature_path, audit_path, split_path, manifest_path = _fixture_artifacts(tmp_path)
    if mutation == "train_feature":
        split = pd.read_csv(split_path)
        split.loc[split["order_id"] == "tr0", "item_price_total"] = 999.0
        split.to_csv(split_path, index=False)
    elif mutation == "validation_feature":
        split = pd.read_csv(split_path)
        split.loc[split["order_id"] == "va0", "item_price_total"] = 999.0
        split.to_csv(split_path, index=False)
    elif mutation == "membership":
        split = pd.read_csv(split_path)
        split.loc[split["order_id"] == "va0", "split"] = "train"
        split.loc[split["order_id"] == "tr0", "split"] = "validation"
        split.to_csv(split_path, index=False)
    elif mutation == "target":
        split = pd.read_csv(split_path)
        split.loc[split["order_id"] == "te0", "late"] = 0
        split.to_csv(split_path, index=False)
    else:
        features = pd.read_csv(feature_path)
        features.loc[features["order_id"] == "tr0", "item_price_total"] = 999.0
        features.to_csv(feature_path, index=False)
        # Keep the old split, audit, and manifest: they describe a different feature artifact.

    if mutation == "stale_features":
        expected_error = "Feature CSV checksum"
    else:
        expected_error = "Split CSV contents do not match deterministic reconstruction"
    with pytest.raises(ValueError, match=expected_error):
        load_training_validation(feature_path, audit_path, split_path, manifest_path)


def test_split_integrity_failure_precedes_fit_and_output_creation(tmp_path, monkeypatch):
    paths = list(_fixture_artifacts(tmp_path))
    split_path = paths[2]
    split = pd.read_csv(split_path)
    split.loc[split["order_id"] == "tr0", "item_count"] = 999
    split.to_csv(split_path, index=False)

    root = Path(__file__).resolve().parents[2]
    model_dir = root / "models/local/v3_08_integrity_guard_test"
    metrics_path = root / "data/processed/v3_08_integrity_guard_test.json"
    assert not model_dir.exists()
    assert not metrics_path.exists()
    monkeypatch.setattr(
        "src.ml.train_classical.build_pipelines",
        lambda *_: pytest.fail("model fitting must not begin after a split integrity failure"),
    )
    with pytest.raises(ValueError, match="Split CSV contents do not match deterministic reconstruction"):
        run_experiment(*paths, model_dir=model_dir, metrics_path=metrics_path)
    assert not model_dir.exists()
    assert not metrics_path.exists()


@pytest.mark.parametrize("input_index", range(4), ids=["feature", "audit", "split", "manifest"])
def test_run_experiment_rejects_metrics_path_colliding_with_any_input_before_writing(
    tmp_path, monkeypatch, input_index
):
    paths = _fixture_artifacts(tmp_path)
    input_path = paths[input_index]
    original_bytes = input_path.read_bytes()
    monkeypatch.setattr(
        "src.ml.train_classical.build_pipelines",
        lambda *_: pytest.fail("model fitting must not begin after an output collision"),
    )
    with pytest.raises(ValueError, match="Output destination"):
        run_experiment(*paths, model_dir=DEFAULT_MODEL_DIR, metrics_path=input_path)
    assert input_path.read_bytes() == original_bytes


def test_output_path_policy_resolves_symlink_aliases_and_rejects_overlapping_destinations(tmp_path):
    root = Path(__file__).resolve().parents[2]
    input_file = tmp_path / "input.csv"
    input_file.write_text("synthetic\n", encoding="utf-8")
    alias = tmp_path / "input-alias.csv"
    alias.symlink_to(input_file)
    with pytest.raises(ValueError, match="Output destination"):
        _validate_output_paths(
            root / "models/local/allowed",
            alias,
            input_paths=(input_file,),
        )
    with pytest.raises(ValueError, match="must not overlap"):
        _validate_output_paths(
            root / "models/local/shared",
            root / "models/local/shared/metrics.json",
        )
    with pytest.raises(ValueError, match="must not overlap"):
        _validate_output_paths(
            root / "models/local/shared",
            root / "models/local/shared",
        )


def test_probability_extraction_uses_label_one_column_and_checks_range():
    features = pd.DataFrame([{
        "purchase_hour": 1, "purchase_weekday": 2, "purchase_month": 3,
        "promised_lead_days": 4, "customer_state": "SP",
        "item_price_total": 5.0, "freight_total": 6.0, "item_count": 1,
    }], columns=FEATURE_NAMES)

    class FakePipeline:
        named_steps = {"classifier": SimpleNamespace(classes_=np.array([1, 0]))}

        def predict_proba(self, _):
            return np.array([[0.8, 0.2]])

    assert positive_class_probability(FakePipeline(), features).tolist() == [0.8]

    class BadPipeline(FakePipeline):
        def predict_proba(self, _):
            return np.array([[1.1, -0.1]])

    with pytest.raises(ValueError, match="in \\[0, 1\\]"):
        positive_class_probability(BadPipeline(), features)


def test_validation_threshold_policy_uses_f1_and_highest_threshold_tie_break():
    y = np.array([1, 0, 0, 1])
    probabilities = np.array([0.9, 0.8, 0.2, 0.1])
    assert choose_f1_threshold(y, probabilities) == pytest.approx(0.9)


def test_metrics_known_answer_average_precision_and_threshold_confusion():
    y = np.array([0, 0, 1, 1])
    probability = np.array([0.1, 0.4, 0.35, 0.8])
    assert average_precision_score(y, probability) == pytest.approx(5 / 6)
    assert roc_auc_score(y, probability) == pytest.approx(0.75)
    result = threshold_metrics(y, probability, 0.5)
    assert result["confusion_matrix"] == [[2, 0], [1, 1]]
    assert result["precision"] == pytest.approx(1.0)
    assert result["recall"] == pytest.approx(0.5)
    assert result["f1"] == pytest.approx(2 / 3)
    assert result["predicted_positive_rate"] == pytest.approx(0.25)
    assert result["actual_positive_prevalence"] == pytest.approx(0.5)


def test_all_candidate_pipelines_are_train_only_deterministic_and_reloadable(tmp_path):
    train = pd.DataFrame([
        {"purchase_hour": 1, "purchase_weekday": 0, "purchase_month": 1, "promised_lead_days": 1, "customer_state": "SP", "item_price_total": 10.0, "freight_total": 2.0, "item_count": 1},
        {"purchase_hour": 2, "purchase_weekday": 1, "purchase_month": 2, "promised_lead_days": 2, "customer_state": "SP", "item_price_total": 20.0, "freight_total": 3.0, "item_count": 1},
        {"purchase_hour": 3, "purchase_weekday": 2, "purchase_month": 3, "promised_lead_days": 3, "customer_state": "SP", "item_price_total": 30.0, "freight_total": 4.0, "item_count": 2},
        {"purchase_hour": 4, "purchase_weekday": 3, "purchase_month": 4, "promised_lead_days": 4, "customer_state": "SP", "item_price_total": 40.0, "freight_total": 5.0, "item_count": 2},
        {"purchase_hour": 5, "purchase_weekday": 4, "purchase_month": 5, "promised_lead_days": 5, "customer_state": "SP", "item_price_total": 50.0, "freight_total": 6.0, "item_count": 3},
        {"purchase_hour": 6, "purchase_weekday": 5, "purchase_month": 6, "promised_lead_days": 6, "customer_state": "SP", "item_price_total": 60.0, "freight_total": 7.0, "item_count": 3},
    ], columns=FEATURE_NAMES)
    validation = pd.DataFrame([
        {"purchase_hour": 100, "purchase_weekday": 6, "purchase_month": 7, "promised_lead_days": 7, "customer_state": "PR", "item_price_total": 70.0, "freight_total": 8.0, "item_count": 4},
        {"purchase_hour": 101, "purchase_weekday": 0, "purchase_month": 8, "promised_lead_days": 8, "customer_state": "PR", "item_price_total": 80.0, "freight_total": 9.0, "item_count": 4},
        {"purchase_hour": 102, "purchase_weekday": 1, "purchase_month": 9, "promised_lead_days": 9, "customer_state": "PR", "item_price_total": 90.0, "freight_total": 10.0, "item_count": 5},
        {"purchase_hour": 103, "purchase_weekday": 2, "purchase_month": 10, "promised_lead_days": 10, "customer_state": "PR", "item_price_total": 100.0, "freight_total": 11.0, "item_count": 5},
    ], columns=FEATURE_NAMES)
    y_train = np.array([0, 1, 0, 0, 0, 1])
    y_validation = np.array([0, 1, 1, 0])

    first_pipeline = build_pipelines()[ "LogisticRegression" ]
    first_result, first_probability = evaluate_candidate(first_pipeline, train, y_train, validation, y_validation)
    scaler = first_pipeline.named_steps["preprocessor"].named_transformers_["numeric"].named_steps["scaler"]
    encoder = first_pipeline.named_steps["preprocessor"].named_transformers_["categorical"].named_steps["onehot"]
    assert scaler.mean_[0] == pytest.approx(train["purchase_hour"].mean())
    assert set(encoder.categories_[0]) == {"SP"}

    second_pipeline = build_pipelines()[ "LogisticRegression" ]
    second_result, second_probability = evaluate_candidate(second_pipeline, train, y_train, validation, y_validation)
    assert first_probability == pytest.approx(second_probability)
    assert first_result["selected_validation_threshold"] == pytest.approx(second_result["selected_validation_threshold"])

    import joblib

    artifact = tmp_path / "lr.joblib"
    joblib.dump(first_pipeline, artifact)
    loaded = joblib.load(artifact)
    assert positive_class_probability(loaded, validation).tolist() == pytest.approx(first_probability.tolist())

    all_pipelines = build_pipelines()
    preprocessors = [pipeline.named_steps["preprocessor"] for pipeline in all_pipelines.values()]
    assert len({id(preprocessor) for preprocessor in preprocessors}) == 3
    for name in ("DummyClassifier", "RandomForestClassifier"):
        pipeline = all_pipelines[name]
        _, probabilities = evaluate_candidate(pipeline, train, y_train, validation, y_validation)
        assert probabilities.shape == (len(validation),)
        assert np.isfinite(probabilities).all()
        assert ((probabilities >= 0) & (probabilities <= 1)).all()
        artifact = tmp_path / f"{name}.joblib"
        joblib.dump(pipeline, artifact)
        loaded = joblib.load(artifact)
        assert positive_class_probability(loaded, validation).tolist() == pytest.approx(probabilities.tolist())
        if name == "RandomForestClassifier":
            repeat = build_pipelines()[name]
            _, repeated_probabilities = evaluate_candidate(repeat, train, y_train, validation, y_validation)
            assert probabilities.tolist() == pytest.approx(repeated_probabilities.tolist())


def test_output_path_policy_rejects_raw_paths_and_allows_local_model_area():
    root = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError, match="models/local"):
        _validate_output_paths(root / "data/raw/models", root / "data/processed/metrics.json")
    with pytest.raises(ValueError, match="data/processed"):
        _validate_output_paths(root / "models/local/allowed", root / "data/raw/metrics.json")
    _validate_output_paths(root / "models/local/allowed", root / "data/processed/metrics.json")
    assert DEFAULT_MODEL_DIR.is_relative_to(root / "models/local")
    assert DEFAULT_METRICS_PATH.is_relative_to(root / "data/processed")
