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


def _synthetic_gate_fixture(tmp_path, monkeypatch):
    import hashlib
    import json
    import joblib
    import src.ml.train_mlp as module
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from src.ml.preprocessing import make_preprocessor

    root = tmp_path / "isolated-v3-09-fixture"
    processed = root / "data/processed"
    processed.mkdir(parents=True)
    (root / ".v3_09_synthetic_test_fixture.json").write_text(json.dumps({"purpose": "V3-09 test-gate regression fixture only", "version": 1}))
    frame, labels = _rows(12)
    fitted = Pipeline([("preprocessor", make_preprocessor()), ("classifier", LogisticRegression(random_state=42))])
    fitted.fit(frame, labels)
    artifact = root / "models/local/selected.joblib"
    artifact.parent.mkdir(parents=True)
    joblib.dump(fitted, artifact)
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    feature_sha, split_sha = "a" * 64, "b" * 64
    bounds = {"train": {"start_inclusive": "2017-01-01", "end_exclusive": "2018-01-01"}, "validation": {"start_inclusive": "2018-01-01", "end_exclusive": "2018-04-01"}, "test": {"start_inclusive": "2018-04-01", "end_exclusive": "2018-09-01"}}
    paths = module._synthetic_evaluation_paths_for_test(root)
    paths.manifest_path.write_text(json.dumps({"manifest_version": "v1", "boundaries": bounds, "counts_and_label_distribution": {"test": {"rows": 4}}}))
    split_frame = frame.iloc[:4].copy()
    split_frame.insert(0, "order_id", [f"t{i}" for i in range(4)])
    split_frame.insert(1, "purchase_ts", [f"2018-04-0{i+1} 10:00:00" for i in range(4)])
    split_frame.insert(10, "late", labels[:4])
    split_frame["split"] = "test"
    split_frame.to_csv(paths.split_path, index=False)
    for path in (paths.feature_path, paths.audit_path, paths.classical_metrics_path):
        path.write_text("{}")
    selection = {"manifest_version": "v1", "selected_candidate": "LogisticRegression", "selected_threshold": 0.5, "feature_names_in_order": list(FEATURE_NAMES), "feature_artifact_sha256": feature_sha, "split_artifact_sha256": split_sha, "split_manifest_version": "v1", "split_boundaries": bounds, "selected_artifact_path": "models/local/selected.joblib", "selected_artifact_sha256": artifact_sha}
    paths.selection_path.write_text(json.dumps(selection))
    monkeypatch.setattr(module, "verify_selection", lambda path: selection)
    monkeypatch.setattr(module, "_verify_v3_08", lambda path: {"feature_artifact_sha256": feature_sha, "split_artifact_sha256": split_sha})
    calls = {"load": 0}
    def fake_load(*args, **kwargs):
        calls["load"] += 1
        return {"feature_sha256": feature_sha, "split_sha256": split_sha}
    monkeypatch.setattr(module, "load_training_validation", fake_load)
    return module, paths, calls


def test_synthetic_first_evaluation_and_alternate_path_bypass_are_refused(tmp_path, monkeypatch):
    from dataclasses import replace
    import src.ml.train_mlp as module
    module, paths, calls = _synthetic_gate_fixture(tmp_path, monkeypatch)
    result = module._evaluate_test_once_for_paths(paths)
    assert result["test_rows"] == 4 and result["test_evaluation_count"] == 1
    assert paths.claim_path.is_file() and paths.output_path.is_file()
    claim_bytes, metrics_bytes = paths.claim_path.read_bytes(), paths.output_path.read_bytes()
    with pytest.raises(TypeError):
        module.evaluate_final_test_once(claim_path=tmp_path / "alternate-claim.json", output_path=tmp_path / "alternate-result.json")
    alternate = replace(paths, claim_path=paths.root / "data/processed/alternate-claim.json", output_path=paths.root / "data/processed/alternate-result.json")
    with pytest.raises(ValueError, match="Noncanonical"):
        module._evaluate_test_once_for_paths(alternate)
    with pytest.raises(FileExistsError, match="already recorded"):
        module._evaluate_test_once_for_paths(paths)
    assert calls["load"] == 1
    assert paths.claim_path.read_bytes() == claim_bytes and paths.output_path.read_bytes() == metrics_bytes
    assert not (paths.root / "data/processed/alternate-claim.json").exists()
    assert not (paths.root / "data/processed/alternate-result.json").exists()


def test_synthetic_gate_rejects_symlink_alias_and_output_input_collision(tmp_path, monkeypatch):
    from dataclasses import replace
    import src.ml.train_mlp as module
    module, paths, calls = _synthetic_gate_fixture(tmp_path, monkeypatch)
    alias = paths.root / "data/processed/claim-alias.json"
    alias.symlink_to(paths.claim_path.name)
    with pytest.raises(ValueError, match="Noncanonical|Symlink"):
        module._evaluate_test_once_for_paths(replace(paths, claim_path=alias))
    with pytest.raises(ValueError, match="Noncanonical"):
        module._evaluate_test_once_for_paths(replace(paths, output_path=paths.split_path))
    with pytest.raises(ValueError, match="collides with or contains"):
        module._validate_test_output_collisions(replace(paths, output_path=paths.split_path))
    assert calls["load"] == 0
    assert not paths.claim_path.exists() and not paths.output_path.exists()


def test_synthetic_fixture_cannot_load_an_artifact_outside_its_root(tmp_path, monkeypatch):
    import src.ml.train_mlp as module
    module, paths, calls = _synthetic_gate_fixture(tmp_path, monkeypatch)
    selection = module.verify_selection(paths.selection_path)
    selection["selected_artifact_path"] = "../../outside.joblib"
    monkeypatch.setattr(module, "verify_selection", lambda path: selection)
    with pytest.raises(ValueError, match="safe|relative"):
        module._evaluate_test_once_for_paths(paths)
    assert calls["load"] == 0
    assert not paths.claim_path.exists() and not paths.output_path.exists()


@pytest.mark.parametrize("state", ["claim_missing_metrics", "metrics_missing_claim", "malformed_records"])
def test_existing_incomplete_or_malformed_test_state_fails_closed(tmp_path, monkeypatch, state):
    import json
    import src.ml.train_mlp as module
    module, paths, calls = _synthetic_gate_fixture(tmp_path, monkeypatch)
    if state == "claim_missing_metrics":
        paths.claim_path.write_text("{}")
        expected = "claim exists but metrics are missing"
    elif state == "metrics_missing_claim":
        paths.output_path.write_text("{}")
        expected = "metrics exist without the durable claim"
    else:
        paths.claim_path.write_text("[]")
        paths.output_path.write_text("{}")
        expected = "malformed or incomplete"
    with pytest.raises(RuntimeError, match=expected):
        module._evaluate_test_once_for_paths(paths)
    assert calls["load"] == 0


def test_atomic_claim_allows_only_one_concurrent_creator(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import src.ml.train_mlp as module
    claim = tmp_path / "one-time-claim.json"
    record = {"purpose": "synthetic concurrency test"}
    def attempt():
        try:
            module._create_test_claim(claim, record)
            return "created"
        except FileExistsError:
            return "refused"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(outcomes) == ["created", "refused"]


def test_test_only_cli_does_not_rerun_validation(monkeypatch):
    import sys
    import src.ml.train_mlp as module
    monkeypatch.setattr(sys, "argv", ["train_mlp", "--evaluate-test-once"])
    monkeypatch.setattr(module, "run_validation_experiment", lambda: pytest.fail("validation reran"))
    monkeypatch.setattr(module, "evaluate_final_test_once", lambda: {"test_evaluation_count": 1})
    assert module.main() == 0
