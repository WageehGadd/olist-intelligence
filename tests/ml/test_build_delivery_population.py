from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.ml.build_delivery_population import (
    OUTPUT_COLUMNS,
    build_delivery_population,
    build_from_csv,
)


def make_order(
    order_id: str,
    *,
    status: str = "delivered",
    purchase: str = "2017-01-01 10:00:00",
    estimated: str = "2017-01-03 00:00:00",
    actual: str = "2017-01-03 00:00:00",
) -> dict[str, str | None]:
    return {
        "order_id": order_id,
        "order_status": status,
        "order_purchase_timestamp": purchase,
        "order_estimated_delivery_date": estimated,
        "order_delivered_customer_date": actual,
    }


def test_calendar_day_labels_follow_contract() -> None:
    orders = pd.DataFrame(
        [
            make_order("same-exact", actual="2017-01-03 00:00:00"),
            make_order("same-later", actual="2017-01-03 23:59:59"),
            make_order("next-day", actual="2017-01-04 00:00:00"),
            make_order("early", actual="2017-01-02 20:00:00"),
        ]
    )

    population, audit = build_delivery_population(orders)
    labels = population.set_index("order_id")["late"].to_dict()

    assert labels == {"early": 0, "next-day": 1, "same-exact": 0, "same-later": 0}
    assert audit["eligible_rows"] == 4
    assert audit["late_rows"] == 1
    assert audit["on_time_or_early_rows"] == 3


def test_missing_invalid_status_and_invalid_chronology_are_excluded_once() -> None:
    orders = pd.DataFrame(
        [
            make_order("eligible"),
            make_order("missing-purchase", purchase=""),
            make_order("invalid-purchase", purchase="bad-purchase-time"),
            make_order("timezone-purchase", purchase="2017-01-01T10:00:00+00:00"),
            make_order("missing-promise", estimated=""),
            make_order("missing-actual", actual=""),
            make_order("invalid-actual", actual="not-a-timestamp"),
            make_order("invalid-promise", estimated="not-a-timestamp"),
            make_order("cancelled", status="canceled", actual=""),
            make_order("actual-before-purchase", actual="2016-12-31 23:59:59"),
            make_order("promise-before-purchase", estimated="2016-12-31 23:59:59"),
        ]
    )

    population, audit = build_delivery_population(orders)

    assert population["order_id"].tolist() == ["eligible"]
    assert audit["source_rows"] == 11
    assert audit["excluded_rows"] == 10
    assert audit["eligible_rows"] == 1
    assert audit["exclusion_counts"] == {
        "not_delivered_or_missing_status": 1,
        "missing_purchase_timestamp": 1,
        "invalid_purchase_timestamp": 2,
        "missing_estimated_delivery_timestamp": 1,
        "invalid_estimated_delivery_timestamp": 1,
        "missing_delivered_customer_timestamp": 1,
        "invalid_delivered_customer_timestamp": 1,
        "estimated_date_before_purchase_date": 1,
        "actual_date_before_purchase_date": 1,
    }
    assert sum(audit["exclusion_counts"].values()) + audit["eligible_rows"] == 11
    assert audit["timestamp_diagnostics"]["order_purchase_timestamp"] == {
        "missing": 1,
        "invalid_nonmissing": 2,
    }
    assert audit["timestamp_diagnostics"]["order_estimated_delivery_date"] == {
        "missing": 1,
        "invalid_nonmissing": 1,
    }


def test_missing_required_column_is_rejected() -> None:
    orders = pd.DataFrame([make_order("one")]).drop(columns="order_status")

    with pytest.raises(ValueError, match="missing required column.*order_status"):
        build_delivery_population(orders)


def test_duplicate_order_ids_are_rejected_without_deduplication() -> None:
    orders = pd.DataFrame([make_order("duplicate"), make_order("duplicate")])

    with pytest.raises(ValueError, match="duplicate order_id"):
        build_delivery_population(orders)


def test_missing_order_id_is_rejected() -> None:
    orders = pd.DataFrame([make_order(" ")])

    with pytest.raises(ValueError, match="missing/blank order_id"):
        build_delivery_population(orders)


def test_output_cannot_overwrite_or_write_inside_raw_data(tmp_path: Path) -> None:
    input_path = tmp_path / "orders.csv"
    pd.DataFrame([make_order("synthetic")]).to_csv(input_path, index=False)
    raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"

    with pytest.raises(ValueError, match="inside protected raw-data directory"):
        build_from_csv(input_path, raw_dir / "never-write-this-file.csv")


def test_missing_input_path_has_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Orders CSV not found"):
        build_from_csv(tmp_path / "missing-orders.csv", tmp_path / "output.csv")


def test_schema_binary_labels_unique_grain_and_deterministic_order() -> None:
    orders = pd.DataFrame(
        [
            make_order("z-order", actual="2017-01-04 00:00:00"),
            make_order("a-order", actual="2017-01-03 18:00:00"),
        ]
    )

    first, first_audit = build_delivery_population(orders)
    second, second_audit = build_delivery_population(orders.iloc[::-1].reset_index(drop=True))

    pd.testing.assert_frame_equal(first, second)
    assert first_audit == second_audit
    assert list(first.columns) == list(OUTPUT_COLUMNS)
    assert first["order_id"].is_unique
    assert first["late"].dtype == "int8"
    assert set(first["late"].tolist()) <= {0, 1}
    assert first["population_version"].eq("v1").all()
    assert first["order_id"].tolist() == ["a-order", "z-order"]
    assert first.loc[0, "purchase_ts"] == "2017-01-01 10:00:00"
    assert first.loc[0, "estimated_delivery_date"] == "2017-01-03"
    assert first.loc[0, "delivered_date"] == "2017-01-03"


def test_empty_input_produces_contract_schema_and_balanced_counts() -> None:
    columns = [
        "order_id",
        "order_status",
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
        "order_delivered_customer_date",
    ]
    population, audit = build_delivery_population(pd.DataFrame(columns=columns))

    assert list(population.columns) == list(OUTPUT_COLUMNS)
    assert population.empty
    assert audit["source_rows"] == 0
    assert audit["eligible_rows"] == 0
    assert audit["late_prevalence"] is None
