"""
Synthetic test suite for SQLite schema and CSV loader (V3-02).
Uses purely synthetic fixtures — NO authentic Olist data is committed or used here.
"""

from __future__ import annotations

import csv
from pathlib import Path
import sqlite3
import pytest

from src.sql.load_sqlite import (
    TABLE_ALLOWLIST,
    TableSpec,
    build_database,
    load_schema,
    reconcile_database,
    stream_csv_and_insert,
)


@pytest.fixture
def schema_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    path = root / "src" / "sql" / "schema.sql"
    assert path.is_file(), f"Schema file not found at {path}"
    return path


@pytest.fixture
def synthetic_raw_dir(tmp_path: Path) -> Path:
    """Creates a complete synthetic set of CSV files matching expected headers."""
    raw = tmp_path / "raw"
    raw.mkdir()

    # 1. Customers
    with (raw / "olist_customers_dataset.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"])
        w.writerow(["cust_1", "unique_1", "12345", "Sao Paulo", "SP"])
        w.writerow(["cust_2", "unique_2", "54321", "Rio de Janeiro", "RJ"])

    # 2. Sellers
    with (raw / "olist_sellers_dataset.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"])
        w.writerow(["sell_1", "12345", "Sao Paulo", "SP"])

    # 3. Category Translation
    with (raw / "product_category_name_translation.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_category_name", "product_category_name_english"])
        w.writerow(["beleza_saude", "health_beauty"])

    # 4. Products
    with (raw / "olist_products_dataset.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "product_category_name", "product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"])
        w.writerow(["prod_1", "beleza_saude", "10", "50", "2", "200.0", "15.0", "10.0", "10.0"])

    # 5. Orders
    with (raw / "olist_orders_dataset.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"])
        w.writerow(["ord_1", "cust_1", "delivered", "2018-05-01 10:00:00", "2018-05-01 10:05:00", "2018-05-02 12:00:00", "2018-05-05 14:00:00", "2018-05-15 00:00:00"])
        w.writerow(["ord_2", "cust_2", "delivered", "2018-05-02 11:00:00", "2018-05-02 11:05:00", "2018-05-03 12:00:00", "2018-05-06 14:00:00", "2018-05-16 00:00:00"])

    # 6. Items
    with (raw / "olist_order_items_dataset.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"])
        w.writerow(["ord_1", "1", "prod_1", "sell_1", "2018-05-08 00:00:00", "50.00", "15.00"])
        w.writerow(["ord_1", "2", "prod_1", "sell_1", "2018-05-08 00:00:00", "25.00", "10.00"])

    # 7. Payments
    with (raw / "olist_order_payments_dataset.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"])
        w.writerow(["ord_1", "1", "credit_card", "2", "100.00"])

    return raw


def test_schema_loads_and_creates_all_tables(schema_path: Path):
    conn = sqlite3.connect(":memory:")
    load_schema(conn, schema_path)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    for spec in TABLE_ALLOWLIST:
        assert spec.table_name in tables
    conn.close()


def test_build_database_end_to_end(synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path):
    target_db = tmp_path / "output" / "olist.sqlite"
    report = build_database(synthetic_raw_dir, schema_path, target_db)

    assert target_db.is_file()
    assert report["foreign_key_violations"] == 0
    assert report["table_counts"]["orders"] == 2
    assert report["table_counts"]["order_items"] == 2
    assert report["table_counts"]["order_payments"] == 1


def test_foreign_key_enforcement(synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path):
    # Introduce an orphan order referencing a non-existent customer
    orders_csv = synthetic_raw_dir / "olist_orders_dataset.csv"
    with orders_csv.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ord_999", "non_existent_cust", "delivered", "2018-05-01 10:00:00", "", "", "", "2018-05-15 00:00:00"])

    target_db = tmp_path / "output" / "olist.sqlite"
    with pytest.raises(Exception):
        build_database(synthetic_raw_dir, schema_path, target_db)


def test_malformed_csv_row_fails_import(synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path):
    # Corrupt order_items with a short row
    items_csv = synthetic_raw_dir / "olist_order_items_dataset.csv"
    with items_csv.open("a", encoding="utf-8", newline="") as f:
        f.write("ord_1,3,prod_1\n")  # Only 3 fields instead of 7

    target_db = tmp_path / "output" / "olist.sqlite"
    with pytest.raises(ValueError, match="Row length error"):
        build_database(synthetic_raw_dir, schema_path, target_db)


def test_atomic_replacement_protects_existing_db(synthetic_raw_dir: Path, schema_path: Path, tmp_path: Path):
    target_db = tmp_path / "output" / "olist.sqlite"
    # First build succeeds
    build_database(synthetic_raw_dir, schema_path, target_db)
    original_mtime = target_db.stat().st_mtime

    # Corrupt a file to make subsequent build fail
    (synthetic_raw_dir / "olist_orders_dataset.csv").unlink()

    with pytest.raises(FileNotFoundError):
        build_database(synthetic_raw_dir, schema_path, target_db)

    # Previous valid DB must remain intact
    assert target_db.is_file()
    assert target_db.stat().st_mtime == original_mtime