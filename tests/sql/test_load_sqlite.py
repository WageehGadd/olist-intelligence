"""Synthetic V3-02 schema, validation, reconciliation, and rebuild tests."""

from __future__ import annotations

import csv
import hashlib
import sqlite3
from pathlib import Path

import pytest

import src.sql.load_sqlite as loader
from src.sql.load_sqlite import TABLE_ALLOWLIST, build_database, load_schema


@pytest.fixture
def schema_path() -> Path:
    path = Path(__file__).resolve().parents[2] / "src" / "sql" / "schema.sql"
    assert path.is_file()
    return path


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def _csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    return rows[0], rows[1:]


def _replace_csv(path: Path, *, column: str, value: str, row_index: int = 0) -> None:
    header, rows = _csv_rows(path)
    rows[row_index][header.index(column)] = value
    _write_csv(path, header, rows)


@pytest.fixture
def synthetic_raw_dir(tmp_path: Path) -> Path:
    """Create a complete, tiny synthetic dataset; no Olist rows are used."""
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_csv(
        raw / "olist_customers_dataset.csv",
        ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
        [["cust_1", "person_1", "01234", "Sao Paulo", "SP"], ["cust_2", "person_2", "54321", "Rio", "RJ"]],
    )
    _write_csv(
        raw / "olist_sellers_dataset.csv",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
        [["seller_1", "00123", "Sao Paulo", "SP"]],
    )
    _write_csv(
        raw / "product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
        [["category_pt", "category_en"]],
    )
    _write_csv(
        raw / "olist_products_dataset.csv",
        [
            "product_id", "product_category_name", "product_name_lenght",
            "product_description_lenght", "product_photos_qty", "product_weight_g",
            "product_length_cm", "product_height_cm", "product_width_cm",
        ],
        [["product_1", "category_pt", "10", "50", "2", "200.5", "15", "10", "10"]],
    )
    _write_csv(
        raw / "olist_orders_dataset.csv",
        [
            "order_id", "customer_id", "order_status", "order_purchase_timestamp",
            "order_approved_at", "order_delivered_carrier_date",
            "order_delivered_customer_date", "order_estimated_delivery_date",
        ],
        [
            ["order_1", "cust_1", "delivered", "2018-05-01 10:00:00", "2018-05-01 10:05:00", "2018-05-02 12:00:00", "2018-05-05 14:00:00", "2018-05-15 00:00:00"],
            ["order_2", "cust_2", "delivered", "2018-05-02 11:00:00", "2018-05-02 11:05:00", "2018-05-03 12:00:00", "2018-05-06 14:00:00", "2018-05-16 00:00:00"],
        ],
    )
    _write_csv(
        raw / "olist_order_items_dataset.csv",
        ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"],
        [
            ["order_1", "1", "product_1", "seller_1", "2018-05-08 00:00:00", "50.00", "15.00"],
            ["order_1", "2", "product_1", "seller_1", "2018-05-08 00:00:00", "25.00", "10.00"],
        ],
    )
    _write_csv(
        raw / "olist_order_payments_dataset.csv",
        ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
        [["order_1", "1", "credit_card", "2", "100.00"]],
    )
    return raw


def _build(raw: Path, schema: Path, target: Path) -> dict:
    return build_database(raw, schema, target)


def test_schema_has_contract_tables_types_keys_and_indexes(schema_path: Path):
    conn = sqlite3.connect(":memory:")
    try:
        load_schema(conn, schema_path)
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {spec.table_name for spec in TABLE_ALLOWLIST} <= tables

        customers = {row[1]: row for row in conn.execute("PRAGMA table_info(customers)")}
        assert customers["customer_id"][2].upper() == "TEXT"
        assert customers["customer_id"][3] == 1
        assert customers["customer_zip_code_prefix"][2].upper() == "TEXT"
        items = list(conn.execute("PRAGMA table_info(order_items)"))
        assert [(row[1], row[5]) for row in items if row[5]] == [("order_id", 1), ("order_item_id", 2)]
        indexes = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert {
            "idx_orders_customer_id", "idx_orders_purchase_ts", "idx_order_items_product_id",
            "idx_order_items_seller_id", "idx_order_payments_order_id",
        } <= indexes
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_successful_import_reconciles_rows_keys_and_relationships(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    target = tmp_path / "local" / "olist.sqlite"
    report = _build(synthetic_raw_dir, schema_path, target)

    assert target.is_file()
    assert report["foreign_key_violations"] == 0
    assert report["source_reconciliation"]["orders"] == {"source_rows": 2, "inserted_rows": 2}
    assert report["source_reconciliation"]["order_items"] == {"source_rows": 2, "inserted_rows": 2}
    assert report["table_counts"]["orders"] == 2
    assert report["table_counts"]["order_items"] == 2
    assert report["table_counts"]["order_payments"] == 1
    assert report["candidate_key_checks"]["order_items"]["unique_and_present"] is True
    assert report["relationship_counts"] == {
        "orders_with_customer": 2,
        "items_with_order_product_seller": 2,
        "payments_with_order": 1,
        "orders_with_items_and_customer": 1,
    }


def test_successful_rebuild_replaces_database_without_duplicate_records(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    target = tmp_path / "local" / "olist.sqlite"
    first = _build(synthetic_raw_dir, schema_path, target)
    second = _build(synthetic_raw_dir, schema_path, target)
    assert second["table_counts"] == first["table_counts"]
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 2


def test_source_and_inserted_row_mismatch_fails_before_publishing_database(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path, monkeypatch
):
    real_stream = loader.stream_csv_and_insert

    def mismatched_stream(conn, csv_path, spec, batch_size=10000):
        source, inserted = real_stream(conn, csv_path, spec, batch_size)
        if spec.table_name == "customers":
            return source + 1, inserted
        return source, inserted

    monkeypatch.setattr(loader, "stream_csv_and_insert", mismatched_stream)
    target = tmp_path / "olist.sqlite"
    with pytest.raises(ValueError, match="Source/inserted row-count mismatch"):
        _build(synthetic_raw_dir, schema_path, target)
    assert not target.exists()


def test_duplicate_single_column_primary_key_fails(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    path = synthetic_raw_dir / "olist_customers_dataset.csv"
    header, rows = _csv_rows(path)
    rows.append(rows[0].copy())
    _write_csv(path, header, rows)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE|PRIMARY KEY"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


def test_duplicate_composite_primary_key_fails(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    path = synthetic_raw_dir / "olist_order_items_dataset.csv"
    header, rows = _csv_rows(path)
    rows.append(rows[0].copy())
    _write_csv(path, header, rows)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE|PRIMARY KEY"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


@pytest.mark.parametrize(
    "filename,new_header",
    [
        ("olist_order_items_dataset.csv", ["order_id", "order_item_id", "product_id", "seller_id", "price", "shipping_limit_date", "freight_value"]),
        ("olist_products_dataset.csv", ["product_id", "product_category_name", "product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm"]),
    ],
    ids=["unexpected-order", "missing-column"],
)
def test_wrong_or_missing_required_header_fails(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path, filename: str, new_header: list[str]
):
    path = synthetic_raw_dir / filename
    _, rows = _csv_rows(path)
    _write_csv(path, new_header, rows)
    with pytest.raises(ValueError, match="Header mismatch"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


@pytest.mark.parametrize(
    "filename,column,value",
    [
        ("olist_order_items_dataset.csv", "order_item_id", "one"),
        ("olist_order_items_dataset.csv", "price", "not-a-number"),
        ("olist_order_items_dataset.csv", "freight_value", "NaN"),
        ("olist_products_dataset.csv", "product_weight_g", "Infinity"),
        ("olist_order_payments_dataset.csv", "payment_installments", "1.5"),
    ],
    ids=["invalid-integer", "invalid-real", "nan-real", "infinite-real", "fractional-integer"],
)
def test_invalid_numeric_values_fail_instead_of_being_coerced(
    synthetic_raw_dir: Path,
    schema_path: Path,
    tmp_path: Path,
    filename: str,
    column: str,
    value: str,
):
    _replace_csv(synthetic_raw_dir / filename, column=column, value=value)
    with pytest.raises(ValueError, match=f"Invalid|Non-finite"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


@pytest.mark.parametrize(
    "filename,column",
    [
        ("olist_customers_dataset.csv", "customer_id"),
        ("olist_orders_dataset.csv", "customer_id"),
        ("olist_orders_dataset.csv", "order_purchase_timestamp"),
        ("olist_orders_dataset.csv", "order_estimated_delivery_date"),
        ("olist_order_items_dataset.csv", "price"),
    ],
    ids=["primary-key", "foreign-key", "purchase-time", "estimated-time", "amount"],
)
def test_missing_required_values_fail_explicitly(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path, filename: str, column: str
):
    _replace_csv(synthetic_raw_dir / filename, column=column, value="")
    with pytest.raises(ValueError, match="Missing required value"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


@pytest.mark.parametrize(
    "column,value",
    [
        ("order_purchase_timestamp", "2018-02-30 10:00:00"),
        ("order_estimated_delivery_date", "not-a-date"),
        ("order_delivered_customer_date", "2018-05-05T14:00:00+00:00"),
    ],
    ids=["invalid-calendar-date", "not-a-timestamp", "timezone-bearing-optional"],
)
def test_malformed_timestamps_fail(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path, column: str, value: str
):
    _replace_csv(synthetic_raw_dir / "olist_orders_dataset.csv", column=column, value=value)
    with pytest.raises(ValueError, match="timestamp"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


def test_foreign_key_violation_fails_with_sqlite_constraint_error(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    _replace_csv(
        synthetic_raw_dir / "olist_orders_dataset.csv", column="customer_id", value="missing_customer"
    )
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "olist.sqlite")


def test_valid_nullable_values_remain_sql_null_and_codes_keep_leading_zeroes(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    _replace_csv(synthetic_raw_dir / "olist_products_dataset.csv", column="product_category_name", value="")
    _replace_csv(synthetic_raw_dir / "olist_products_dataset.csv", column="product_weight_g", value="")
    _replace_csv(synthetic_raw_dir / "olist_orders_dataset.csv", column="order_approved_at", value="")
    target = tmp_path / "olist.sqlite"
    _build(synthetic_raw_dir, schema_path, target)
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT product_category_name, product_weight_g FROM products").fetchone() == (None, None)
        assert conn.execute("SELECT order_approved_at FROM orders WHERE order_id='order_1'").fetchone() == (None,)
        assert conn.execute("SELECT customer_zip_code_prefix FROM customers WHERE customer_id='cust_1'").fetchone() == ("01234",)
        assert conn.execute("SELECT seller_zip_code_prefix FROM sellers WHERE seller_id='seller_1'").fetchone() == ("00123",)


def test_invalid_foreign_key_in_late_import_preserves_previous_database(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    target = tmp_path / "local" / "olist.sqlite"
    _build(synthetic_raw_dir, schema_path, target)
    original_digest = hashlib.sha256(target.read_bytes()).hexdigest()
    _replace_csv(
        synthetic_raw_dir / "olist_order_payments_dataset.csv", column="order_id", value="missing_order"
    )
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        _build(synthetic_raw_dir, schema_path, target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == original_digest
    assert list(target.parent.glob(".*.sqlite")) == []


def test_missing_or_empty_mandatory_source_fails(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    missing = synthetic_raw_dir / "olist_order_payments_dataset.csv"
    missing.unlink()
    with pytest.raises(FileNotFoundError, match="olist_order_payments_dataset.csv"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "missing.sqlite")

    empty = synthetic_raw_dir / "olist_order_payments_dataset.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "empty.sqlite")


def test_header_only_source_fails_instead_of_creating_empty_table(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    _write_csv(
        synthetic_raw_dir / "olist_order_payments_dataset.csv",
        ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
        [],
    )
    with pytest.raises(ValueError, match="no data rows"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "empty-table.sqlite")


def test_row_width_mismatch_is_not_truncated_or_padded(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    path = synthetic_raw_dir / "olist_order_items_dataset.csv"
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write("order_1,3,product_1\n")
    with pytest.raises(ValueError, match="Row-width mismatch"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "bad-width.sqlite")


def test_malformed_csv_quoting_is_rejected(
    synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path
):
    with (synthetic_raw_dir / "olist_order_payments_dataset.csv").open("a", encoding="utf-8") as stream:
        stream.write('"unterminated,1,credit_card,2,100.00\n')
    with pytest.raises(ValueError, match="Malformed CSV record"):
        _build(synthetic_raw_dir, schema_path, tmp_path / "malformed.sqlite")
