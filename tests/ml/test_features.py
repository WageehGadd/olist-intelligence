from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.ml.features import (
    FEATURE_NAMES,
    BRAZIL_UFS,
    FeatureInputError,
    _validate_generated_paths,
    build_historical_features,
    derive_model_features,
)


def _derive(purchase="2017-05-01 23:59:59", promise="2017-05-02", state="SP", items=None):
    return derive_model_features(
        purchase,
        promise,
        state,
        items if items is not None else [
            {"price": 29.90, "freight_value": 10.20},
            {"price": 15, "freight_value": 5},
        ],
    )


def test_frozen_feature_order_types_and_training_inference_parity():
    historical = _derive()
    inference = _derive(purchase="2017-05-01T23:59:59")
    assert tuple(historical) == FEATURE_NAMES
    assert historical == inference
    assert historical == {
        "purchase_hour": 23,
        "purchase_weekday": 0,
        "purchase_month": 5,
        "promised_lead_days": 1,
        "customer_state": "SP",
        "item_price_total": 44.9,
        "freight_total": 15.2,
        "item_count": 2,
    }
    assert all(type(historical[name]) is int for name in (
        "purchase_hour", "purchase_weekday", "purchase_month", "promised_lead_days", "item_count"
    ))
    assert type(historical["customer_state"]) is str
    assert type(historical["item_price_total"]) is float
    assert type(historical["freight_total"]) is float


def test_parana_is_accepted_by_contract_and_historical_inference_paths_match():
    assert len(BRAZIL_UFS) == 27
    assert "PR" in BRAZIL_UFS
    historical = _derive(state="PR")
    inference = _derive(purchase="2017-05-01T23:59:59", state="PR")
    assert historical == inference
    assert historical["customer_state"] == "PR"
    assert tuple(historical) == FEATURE_NAMES


def test_feature_generator_output_paths_cannot_overwrite_inputs_or_raw_files(tmp_path):
    root = Path(__file__).resolve().parents[2]
    input_path = root / "data/raw/olist_orders_dataset.csv"
    with pytest.raises(ValueError, match="must not overwrite"):
        _validate_generated_paths([input_path], [input_path])
    with pytest.raises(ValueError, match="ignored data/processed"):
        _validate_generated_paths([input_path], [root / "data/raw/new.csv"])
    with pytest.raises(ValueError, match="ignored data/processed"):
        _validate_generated_paths([input_path], [tmp_path / "outside.csv"])


@pytest.mark.parametrize(
    "purchase,promise,reason",
    [
        ("2017-05-01T23:59:59Z", "2017-05-02", "invalid_purchase_timestamp"),
        ("2017-05-01T23:59:59+00:00", "2017-05-02", "invalid_purchase_timestamp"),
        ("2017-05-01T23:59:59.000", "2017-05-02", "invalid_purchase_timestamp"),
        ("2017-02-30T23:59:59", "2017-03-02", "invalid_purchase_timestamp"),
        ("2017-05-01T23:59:59", "2017-05-02T00:00:00", "invalid_estimated_delivery_date"),
        ("2017-05-01T23:59:59", "2017-05-02Z", "invalid_estimated_delivery_date"),
        ("2017-05-01T23:59:59", "2017-02-30", "invalid_estimated_delivery_date"),
        ("2017-05-02T00:00:00", "2017-05-01", "estimated_date_before_purchase_date"),
    ],
)
def test_strict_source_naive_date_rules(purchase, promise, reason):
    with pytest.raises(FeatureInputError) as exc:
        _derive(purchase=purchase, promise=promise)
    assert exc.value.reason == reason


@pytest.mark.parametrize(
    "state,items,reason",
    [
        (None, [{"price": 1, "freight_value": 1}], "missing_customer_state"),
        ("sp", [{"price": 1, "freight_value": 1}], "invalid_customer_state"),
        ("XX", [{"price": 1, "freight_value": 1}], "invalid_customer_state"),
        ("SP", [], "missing_item_rows"),
        ("SP", [{"price": 1, "freight_value": 1, "seller_id": "x"}], "invalid_item_rows"),
        ("SP", [{"price": True, "freight_value": 1}], "invalid_item_amount"),
        ("SP", [{"price": "1", "freight_value": 1}], "invalid_item_amount"),
        ("SP", [{"price": float("inf"), "freight_value": 1}], "invalid_item_amount"),
        ("SP", [{"price": float("nan"), "freight_value": 1}], "invalid_item_amount"),
        ("SP", [{"price": -0.01, "freight_value": 1}], "invalid_item_amount"),
        ("SP", [{"price": None, "freight_value": 1}], "missing_item_amount"),
    ],
)
def test_invalid_state_and_item_inputs_have_explicit_reasons(state, items, reason):
    with pytest.raises(FeatureInputError) as exc:
        _derive(state=state, items=items)
    assert exc.value.reason == reason


def _historical_fixture():
    population = pd.DataFrame([
        {"order_id": "o1", "purchase_ts": "2017-01-02 10:15:00", "estimated_delivery_date": "2017-01-05",
         "delivered_date": "2017-01-06", "late": 1, "population_version": "v1"},
        {"order_id": "o2", "purchase_ts": "2017-01-03 08:00:00", "estimated_delivery_date": "2017-01-06",
         "delivered_date": "2017-01-06", "late": 0, "population_version": "v1"},
    ])
    orders = pd.DataFrame([
        {"order_id": "o1", "customer_id": "c1", "order_status": "delivered",
         "order_purchase_timestamp": "2017-01-02 10:15:00", "order_estimated_delivery_date": "2017-01-05 00:00:00",
         "order_delivered_customer_date": "2017-01-06 12:00:00"},
        {"order_id": "o2", "customer_id": "c2", "order_status": "delivered",
         "order_purchase_timestamp": "2017-01-03 08:00:00", "order_estimated_delivery_date": "2017-01-06 00:00:00",
         "order_delivered_customer_date": "2017-01-06 12:00:00"},
    ])
    items = pd.DataFrame([
        {"order_id": "o1", "order_item_id": 1, "price": 10.25, "freight_value": 2.50},
        {"order_id": "o1", "order_item_id": 2, "price": 20.00, "freight_value": 3.00},
        {"order_id": "o2", "order_item_id": 1, "price": 7.75, "freight_value": 1.25},
    ])
    customers = pd.DataFrame([
        {"customer_id": "c1", "customer_state": "SP"},
        {"customer_id": "c2", "customer_state": "RJ"},
    ])
    return population, orders, items, customers


def test_historical_builder_aggregates_items_and_preserves_order_grain():
    population, orders, items, customers = _historical_fixture()
    customers.loc[customers.customer_id.eq("c1"), "customer_state"] = "PR"
    frame, audit = build_historical_features(population, orders, items, customers)
    assert len(frame) == 2
    assert frame.order_id.is_unique
    assert list(frame.columns) == ["order_id", "purchase_ts", "late", *FEATURE_NAMES]
    assert frame.loc[frame.order_id.eq("o1"), "item_price_total"].item() == 30.25
    assert frame.loc[frame.order_id.eq("o1"), "freight_total"].item() == 5.5
    assert frame.loc[frame.order_id.eq("o1"), "item_count"].item() == 2
    assert frame.loc[frame.order_id.eq("o2"), "item_count"].item() == 1
    assert frame.loc[frame.order_id.eq("o1"), "customer_state"].item() == "PR"
    assert not {"delivered_date", "order_status", "customer_id", "order_item_id"}.intersection(frame.columns)
    assert audit["population_input_rows"] == audit["feature_ready_rows"] == 2
    assert audit["exclusive_feature_exclusion_counts"]["unsupported_customer_state"] == 0
    assert audit["population_input_late"] == audit["feature_ready_late"] == 1
    assert audit["exclusive_feature_exclusion_counts"]["missing_item_rows"] == 0


def test_historical_builder_audits_unrepresentable_empty_cart_without_imputation():
    population, orders, items, customers = _historical_fixture()
    items = items.loc[items.order_id.ne("o2")].copy()
    frame, audit = build_historical_features(population, orders, items, customers)
    assert frame.order_id.tolist() == ["o1"]
    assert audit["feature_excluded_rows"] == 1
    assert audit["exclusive_feature_exclusion_counts"]["missing_item_rows"] == 1
    assert audit["feature_ready_late"] + audit["feature_excluded_late"] == audit["population_input_late"]


def test_historical_builder_rejects_duplicate_item_grain_and_target_mismatch():
    population, orders, items, customers = _historical_fixture()
    duplicate = pd.concat([items, items.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match=r"duplicate \(order_id, order_item_id\)"):
        build_historical_features(population, orders, duplicate, customers)
    population.loc[0, "late"] = 0
    with pytest.raises(ValueError, match="does not reconcile"):
        build_historical_features(population, orders, items, customers)


@pytest.mark.parametrize(
    "state,expected_reason",
    [(None, "missing_customer_state"), ("XX", "invalid_customer_state")],
)
def test_historical_builder_audits_bad_customer_state(state, expected_reason):
    population, orders, items, customers = _historical_fixture()
    customers.loc[0, "customer_state"] = state
    frame, audit = build_historical_features(population, orders, items, customers)
    assert "o1" not in set(frame.order_id)
    assert audit["exclusive_feature_exclusion_counts"][expected_reason] == 1


def test_historical_builder_audits_invalid_amount_and_missing_customer_join():
    population, orders, items, customers = _historical_fixture()
    items.loc[items.order_id.eq("o1") & items.order_item_id.eq(1), "price"] = -1.0
    customers = customers.loc[customers.customer_id.ne("c2")].copy()
    frame, audit = build_historical_features(population, orders, items, customers)
    assert frame.order_id.tolist() == []
    reasons = audit["exclusive_feature_exclusion_counts"]
    assert reasons["invalid_item_amount"] == 1
    assert reasons["customer_not_found"] == 1
    assert audit["join_and_input_diagnostics"]["item_amount_rows"]["price_invalid_rows"] == 1
