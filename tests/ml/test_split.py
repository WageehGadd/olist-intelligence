from __future__ import annotations

import pandas as pd
import pytest

from src.ml.features import FEATURE_NAMES, METADATA_NAMES
from src.ml.preprocessing import make_preprocessor, validate_feature_frame
from src.ml.split import _validate_generated_paths, assign_chronological_splits, build_split_outputs


def _row(order_id, purchase_ts, late=0, hour=10, state="SP"):
    return {
        "order_id": order_id,
        "purchase_ts": purchase_ts,
        "late": late,
        "purchase_hour": hour,
        "purchase_weekday": 0,
        "purchase_month": int(purchase_ts[5:7]),
        "promised_lead_days": 5,
        "customer_state": state,
        "item_price_total": 20.0,
        "freight_total": 4.0,
        "item_count": 1,
    }


def _valid_audit(frame, checksum="a" * 64):
    rows = len(frame)
    positives = int(frame["late"].sum())
    negatives = rows - positives
    return {
        "population_input_rows": rows,
        "population_input_late": positives,
        "feature_ready_rows": rows,
        "feature_ready_late": positives,
        "feature_ready_negative_rows": negatives,
        "feature_excluded_rows": 0,
        "feature_excluded_late": 0,
        "exclusive_feature_exclusion_counts": {},
        "input_target_label_counts": {"late_1": positives, "late_0": negatives},
        "feature_ready_label_counts": {"late_1": positives, "late_0": negatives},
        "feature_artifact_sha256": checksum,
        "source_population_monthly": {
            "2018-08": {"source_orders": 10, "delivered_status_orders": 9, "v3_06_eligible": 8},
            "2018-09": {"source_orders": 2, "delivered_status_orders": 0, "v3_06_eligible": 0},
        },
    }


def _frame():
    return pd.DataFrame([
        _row("old", "2016-12-31 23:59:59", 1),
        _row("t1", "2017-01-01 00:00:00", 0, 0),
        _row("t2", "2017-12-31 23:59:59", 1, 2),
        _row("v1", "2018-01-01 00:00:00", 0, 100, "AC"),
        _row("v2", "2018-03-31 23:59:59", 1, 101, "AC"),
        _row("x1", "2018-04-01 00:00:00", 0, 102, "AC"),
        _row("x2", "2018-08-31 23:59:59", 1, 103, "AC"),
        _row("new", "2018-09-01 00:00:00", 1, 104, "AC"),
    ], columns=[*METADATA_NAMES, *FEATURE_NAMES])


def test_calendar_boundaries_are_chronological_and_equal_dates_stay_together():
    frame = pd.concat([
        _frame(),
        pd.DataFrame([_row("t0", "2017-01-01 00:00:00", 1, 0)]),
    ], ignore_index=True).sample(frac=1, random_state=7).reset_index(drop=True)
    split = assign_chronological_splits(frame)
    assert split.set_index("order_id")["split"].to_dict() == {
        "old": "excluded_pre_window",
        "t0": "train",
        "t1": "train",
        "t2": "train",
        "v1": "validation",
        "v2": "validation",
        "x1": "test",
        "x2": "test",
        "new": "excluded_post_window",
    }
    assert split.order_id.is_unique
    assert split.purchase_ts.tolist() == sorted(split.purchase_ts.tolist())
    tied = split.loc[split.purchase_ts.eq("2017-01-01 00:00:00"), "order_id"].tolist()
    assert tied == ["t0", "t1"]
    first = assign_chronological_splits(frame)
    second = assign_chronological_splits(frame)
    pd.testing.assert_frame_equal(first, second)


def test_duplicate_orders_or_leakage_columns_are_rejected():
    duplicate = pd.concat([_frame(), _frame().iloc[[1]]], ignore_index=True)
    with pytest.raises(ValueError, match="present and unique"):
        assign_chronological_splits(duplicate)
    leaky = _frame().assign(delivered_date="2017-01-01")
    with pytest.raises(ValueError, match="columns must be exactly"):
        assign_chronological_splits(leaky)


def test_preprocessor_only_sees_eight_features_and_fits_train_rows():
    frame = _frame()
    split = assign_chronological_splits(frame)
    train = split.loc[split.split.eq("train"), FEATURE_NAMES]
    validation = split.loc[split.split.eq("validation"), FEATURE_NAMES]
    validate_feature_frame(train)
    preprocessor = make_preprocessor().fit(train)
    scaler = preprocessor.named_transformers_["numeric"].named_steps["scaler"]
    assert scaler.mean_[0] == 1.0  # validation's 100+ hour values are not used in fit
    encoder = preprocessor.named_transformers_["categorical"].named_steps["onehot"]
    assert set(encoder.categories_[0]) == {"SP"}  # validation-only AC is unknown to train
    transformed = preprocessor.transform(validation)
    assert transformed.shape == (2, 8)  # seven numeric columns plus one fitted state category
    assert pd.notna(transformed).all()


def test_preprocessor_rejects_metadata_and_feature_reordering():
    frame = _frame()
    with pytest.raises(ValueError, match="exactly the eight"):
        validate_feature_frame(frame.loc[:, [*METADATA_NAMES, *FEATURE_NAMES]])
    with pytest.raises(ValueError, match="exactly the eight"):
        validate_feature_frame(frame.loc[:, list(reversed(FEATURE_NAMES))])


def test_split_generator_output_paths_cannot_overwrite_inputs_or_leave_processed(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    input_path = root / "data/processed/delivery_features.csv"
    with pytest.raises(ValueError, match="must not overwrite"):
        _validate_generated_paths([input_path], [input_path])
    with pytest.raises(ValueError, match="ignored data/processed"):
        _validate_generated_paths([input_path], [root / "data/raw/new.csv"])
    with pytest.raises(ValueError, match="ignored data/processed"):
        _validate_generated_paths([input_path], [tmp_path / "outside.json"])


def test_split_manifest_counts_and_train_only_fit_are_reproducible():
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    checksum = "a" * 64
    audit = _valid_audit(frame, checksum)
    split, manifest, preprocessor = build_split_outputs(
        frame,
        audit,
        checksum,
        "input.csv",
        "splits.csv",
        "manifest.json",
        "preprocessor.joblib",
    )
    assert len(split) == len(frame)
    assert manifest["dataset"]["feature_artifact_sha256"] == checksum
    assert manifest["dataset"]["feature_ready_negative_rows"] == 3
    assert manifest["counts_and_label_distribution"]["train"]["rows"] == 2
    assert manifest["counts_and_label_distribution"]["validation"]["rows"] == 2
    assert manifest["counts_and_label_distribution"]["test"]["rows"] == 2
    assert manifest["preprocessing"]["fit_rows"] == 2
    assert manifest["preprocessing"]["validation_or_test_fit"] is False
    assert manifest["preprocessing"]["estimator_trained"] is False
    assert manifest["maturity_assessment"]["raw_monthly_tail"]["2018-09"]["source_orders"] == 2
    assert preprocessor.named_transformers_["numeric"].named_steps["scaler"].mean_[0] == 1.0


def _assert_audit_rejected_before_outputs(frame, audit, tmp_path, expected):
    checksum = "a" * 64
    outputs = [tmp_path / "splits.csv", tmp_path / "manifest.json", tmp_path / "preprocessor.joblib"]
    with pytest.raises(ValueError, match=expected):
        build_split_outputs(
            frame,
            audit,
            checksum,
            "input.csv",
            str(outputs[0]),
            str(outputs[1]),
            str(outputs[2]),
        )
    assert all(not output.exists() for output in outputs)


def test_stale_feature_ready_row_count_rejected_before_outputs(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    audit = _valid_audit(frame)
    audit["feature_ready_rows"] -= 1
    _assert_audit_rejected_before_outputs(frame, audit, tmp_path, "feature_ready_rows")


def test_wrong_feature_ready_late_count_rejected_before_outputs(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    audit = _valid_audit(frame)
    audit["feature_ready_late"] -= 1
    _assert_audit_rejected_before_outputs(frame, audit, tmp_path, "feature_ready_late")


def test_inconsistent_target_population_accounting_rejected_before_outputs(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    audit = _valid_audit(frame)
    audit["population_input_rows"] += 1
    _assert_audit_rejected_before_outputs(frame, audit, tmp_path, "row accounting")


def test_missing_or_noninteger_required_audit_count_rejected_before_outputs(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    missing = _valid_audit(frame)
    del missing["feature_excluded_rows"]
    _assert_audit_rejected_before_outputs(frame, missing, tmp_path, "missing required count")

    malformed = _valid_audit(frame)
    malformed["population_input_rows"] = "6"
    _assert_audit_rejected_before_outputs(frame, malformed, tmp_path, "nonnegative integer")


def test_exclusion_reason_counts_must_reconcile_before_outputs(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    audit = _valid_audit(frame)
    audit["population_input_rows"] += 1
    audit["feature_excluded_rows"] += 1
    _assert_audit_rejected_before_outputs(frame, audit, tmp_path, "exclusion reasons")


def test_incorrect_feature_artifact_checksum_rejected_before_outputs(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    audit = _valid_audit(frame, "b" * 64)
    _assert_audit_rejected_before_outputs(frame, audit, tmp_path, "checksum")


def test_invalid_labels_and_duplicate_ids_cannot_bypass_audit_guard(tmp_path):
    frame = _frame().loc[lambda x: ~x.order_id.isin(["old", "new"])].reset_index(drop=True)
    checksum = "a" * 64
    audit = _valid_audit(frame, checksum)
    invalid_labels = frame.copy()
    invalid_labels.loc[0, "late"] = 2
    _assert_audit_rejected_before_outputs(invalid_labels, audit, tmp_path, "only 0 or 1")
    duplicate_ids = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    duplicate_audit = _valid_audit(duplicate_ids, checksum)
    _assert_audit_rejected_before_outputs(duplicate_ids, duplicate_audit, tmp_path, "present and unique")
