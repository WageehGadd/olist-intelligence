from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ml.features import FEATURE_NAMES
from src.ml.train_mlp import fit_mlp, select_candidate


def _rows(n: int = 24) -> tuple[pd.DataFrame, np.ndarray]:
    y = np.asarray([i % 2 for i in range(n)], dtype=np.int8)
    frame = pd.DataFrame({
        "purchase_hour": np.arange(n) % 24,
        "purchase_weekday": np.arange(n) % 7,
        "purchase_month": np.arange(n) % 12 + 1,
        "promised_lead_days": np.arange(n) % 30,
        "customer_state": ["SP" if i % 2 else "PR" for i in range(n)],
        "item_price_total": np.arange(n, dtype=float) + 1,
        "freight_total": (np.arange(n, dtype=float) % 5) + 1,
        "item_count": np.arange(n) % 4 + 1,
    }, columns=FEATURE_NAMES)
    return frame, y


def test_mlp_uses_frozen_schema_finite_probabilities_and_deterministic_seed():
    frame, labels = _rows()
    first, details, first_probability = fit_mlp(frame.iloc[:16], labels[:16], frame.iloc[16:], labels[16:])
    second, details2, second_probability = fit_mlp(frame.iloc[:16], labels[:16], frame.iloc[16:], labels[16:])
    assert tuple(frame.columns) == FEATURE_NAMES
    assert first.named_steps["preprocessor"].named_transformers_["numeric"].named_steps["scaler"].n_samples_seen_ == 16
    assert details["train_only_preprocessor_fit"] is True
    assert details["best_checkpoint_restored"] is True
    assert details["best_validation_log_loss"] == details["validation_log_loss_history"][details["best_epoch"] - 1]
    assert np.isfinite(first_probability).all() and ((first_probability >= 0) & (first_probability <= 1)).all()
    np.testing.assert_allclose(first_probability, second_probability, rtol=0, atol=1e-12)
    assert details["best_epoch"] == details2["best_epoch"]


def test_mlp_rejects_reordered_or_extra_features():
    frame, labels = _rows(8)
    with pytest.raises(ValueError, match="exactly the eight"):
        fit_mlp(frame.loc[:, list(reversed(FEATURE_NAMES))], labels, frame, labels)


def test_selection_is_validation_ap_only_with_deterministic_ties():
    tied = {name: {"validation_average_precision": 0.25, "test_average_precision": 0.99 if name == "DummyClassifier" else 0.01} for name in ("DummyClassifier", "LogisticRegression", "RandomForestClassifier", "SmallMLP")}
    assert select_candidate(tied) == "LogisticRegression"
    tied["SmallMLP"]["validation_average_precision"] = 0.26
    assert select_candidate(tied) == "SmallMLP"
    tied["SmallMLP"]["validation_average_precision"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        select_candidate(tied)


def test_final_test_evaluation_claim_cannot_be_reused(tmp_path, monkeypatch):
    import hashlib
    import json
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import src.ml.train_mlp as module
    from src.ml.preprocessing import make_preprocessor

    frame, labels = _rows(12)
    fitted = Pipeline([("preprocessor", make_preprocessor()), ("classifier", LogisticRegression(random_state=42))])
    fitted.fit(frame, labels)
    root = tmp_path
    artifact = root / "selected.joblib"
    joblib.dump(fitted, artifact)
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    feature_sha, split_sha = "a" * 64, "b" * 64
    bounds = {"train": {"start_inclusive": "2017-01-01", "end_exclusive": "2018-01-01"}, "validation": {"start_inclusive": "2018-01-01", "end_exclusive": "2018-04-01"}, "test": {"start_inclusive": "2018-04-01", "end_exclusive": "2018-09-01"}}
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps({"manifest_version": "v1", "boundaries": bounds, "counts_and_label_distribution": {"test": {"rows": 4}}}))
    split_path = root / "split.csv"
    split_frame = frame.iloc[:4].copy()
    split_frame.insert(0, "order_id", [f"t{i}" for i in range(4)])
    split_frame.insert(1, "purchase_ts", [f"2018-04-0{i+1} 10:00:00" for i in range(4)])
    split_frame.insert(10, "late", labels[:4])
    split_frame["split"] = "test"
    split_frame.to_csv(split_path, index=False)
    other_paths = [root / name for name in ("features.csv", "audit.json", "classical.json")]
    for path in other_paths:
        path.write_text("{}")
    selection = {"manifest_version": "v1", "selected_candidate": "LogisticRegression", "selected_threshold": 0.5, "feature_names_in_order": list(FEATURE_NAMES), "feature_artifact_sha256": feature_sha, "split_artifact_sha256": split_sha, "split_manifest_version": "v1", "split_boundaries": bounds, "selected_artifact_path": "selected.joblib", "selected_artifact_sha256": artifact_sha}
    (root / "selection.json").write_text(json.dumps(selection))
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "verify_selection", lambda path: selection)
    monkeypatch.setattr(module, "_verify_v3_08", lambda path: {"feature_artifact_sha256": feature_sha, "split_artifact_sha256": split_sha})
    calls = {"load": 0}
    def fake_load(*args, **kwargs):
        calls["load"] += 1
        return {"feature_sha256": feature_sha, "split_sha256": split_sha}
    monkeypatch.setattr(module, "load_training_validation", fake_load)
    monkeypatch.setattr(module, "_validate_output_paths", lambda *args, **kwargs: None)
    output, claim = root / "result.json", root / "claimed.json"
    result = module.evaluate_final_test_once(feature_path=other_paths[0], audit_path=other_paths[1], split_path=split_path, manifest_path=manifest_path, selection_path=root / "selection.json", output_path=output, claim_path=claim, classical_metrics_path=other_paths[2])
    assert result["test_rows"] == 4 and result["test_evaluation_count"] == 1
    assert calls["load"] == 1 and output.exists() and claim.exists()
    with pytest.raises(FileExistsError, match="already been claimed"):
        module.evaluate_final_test_once(feature_path=other_paths[0], audit_path=other_paths[1], split_path=split_path, manifest_path=manifest_path, selection_path=root / "selection.json", output_path=output, claim_path=claim, classical_metrics_path=other_paths[2])
    assert calls["load"] == 1


def test_test_only_cli_does_not_rerun_validation(monkeypatch):
    import sys
    import src.ml.train_mlp as module
    monkeypatch.setattr(sys, "argv", ["train_mlp", "--evaluate-test-once"])
    monkeypatch.setattr(module, "run_validation_experiment", lambda: pytest.fail("validation reran"))
    monkeypatch.setattr(module, "evaluate_final_test_once", lambda: {"test_evaluation_count": 1})
    assert module.main() == 0
