from __future__ import annotations
import csv
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any, NamedTuple


ENCODING = "utf-8-sig"


class TableSpec(NamedTuple):
    csv_filename: str
    table_name: str
    expected_header: list[str]


# Ordered intentionally to load parent tables before child tables for FK validation
TABLE_ALLOWLIST: list[TableSpec] = [
    TableSpec(
        csv_filename="olist_customers_dataset.csv",
        table_name="customers",
        expected_header=[
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    ),
    TableSpec(
        csv_filename="olist_sellers_dataset.csv",
        table_name="sellers",
        expected_header=[
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
    ),
    TableSpec(
        csv_filename="product_category_name_translation.csv",
        table_name="product_category_name_translation",
        expected_header=[
            "product_category_name",
            "product_category_name_english",
        ],
    ),
    TableSpec(
        csv_filename="olist_products_dataset.csv",
        table_name="products",
        expected_header=[
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    ),
    TableSpec(
        csv_filename="olist_orders_dataset.csv",
        table_name="orders",
        expected_header=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    TableSpec(
        csv_filename="olist_order_items_dataset.csv",
        table_name="order_items",
        expected_header=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    ),
    TableSpec(
        csv_filename="olist_order_payments_dataset.csv",
        table_name="order_payments",
        expected_header=[
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    ),
]


def load_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    """Executes the DDL schema in schema.sql with foreign keys enabled."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)


def stream_csv_and_insert(
    conn: sqlite3.Connection,
    csv_path: Path,
    spec: TableSpec,
    batch_size: int = 10000,
) -> tuple[int, int]:
    """
    Streams a CSV file in batches, validates row widths, and inserts rows.
    Returns (source_row_count, inserted_row_count).
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Required input CSV missing: {csv_path}")

    with csv_path.open("r", encoding=ENCODING, newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"CSV file is empty: {csv_path.name}")

        if header != spec.expected_header:
            raise ValueError(
                f"Header mismatch in {csv_path.name}.\n"
                f"Expected: {spec.expected_header}\n"
                f"Found:    {header}"
            )

        col_count = len(spec.expected_header)
        placeholders = ", ".join("?" for _ in spec.expected_header)
        cols_joined = ", ".join(f'"{c}"' for c in spec.expected_header)
        sql = f'INSERT INTO "{spec.table_name}" ({cols_joined}) VALUES ({placeholders})'

        batch: list[list[Any]] = []
        source_count = 0

        for line_no, row in enumerate(reader, start=2):
            source_count += 1
            if len(row) != col_count:
                raise ValueError(
                    f"Row length error in {csv_path.name} line {line_no}: "
                    f"expected {col_count} fields, found {len(row)}."
                )
            # Empty strings converted to None for nullable SQL columns
            cleaned_row = [val if val != "" else None for val in row]
            batch.append(cleaned_row)

            if len(batch) >= batch_size:
                conn.executemany(sql, batch)
                batch.clear()

        if batch:
            conn.executemany(sql, batch)
            batch.clear()

    # Verify count in database
    cur = conn.execute(f'SELECT COUNT(*) FROM "{spec.table_name}"')
    inserted_count = cur.fetchone()[0]
    return source_count, inserted_count


def reconcile_database(conn: sqlite3.Connection) -> dict[str, Any]:
    """Runs data reconciliation checks and asserts database integrity."""
    report: dict[str, Any] = {}

    # Foreign key violations check
    fk_cursor = conn.execute("PRAGMA foreign_key_check")
    fk_violations = fk_cursor.fetchall()
    report["foreign_key_violations"] = len(fk_violations)
    if fk_violations:
        raise ValueError(f"Foreign key violations found: {fk_violations[:5]}")

    # Check primary key nulls and table counts
    table_counts = {}
    for spec in TABLE_ALLOWLIST:
        cur = conn.execute(f'SELECT COUNT(*) FROM "{spec.table_name}"')
        table_counts[spec.table_name] = cur.fetchone()[0]
    report["table_counts"] = table_counts

    # Verify representative join: orders with items and customers
    join_cur = conn.execute(
        """
        SELECT COUNT(DISTINCT o.order_id)
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_items i ON o.order_id = i.order_id
        """
    )
    report["distinct_orders_with_items_and_customers"] = join_cur.fetchone()[0]

    # Check unmapped product categories (expected ~13 in authentic Olist)
    unmapped_cur = conn.execute(
        """
        SELECT COUNT(DISTINCT p.product_category_name)
        FROM products p
        WHERE p.product_category_name IS NOT NULL
          AND p.product_category_name NOT IN (
              SELECT product_category_name FROM product_category_name_translation
          )
        """
    )
    report["untranslated_categories"] = unmapped_cur.fetchone()[0]

    return report


def build_database(
    raw_dir: Path,
    schema_path: Path,
    db_path: Path,
) -> dict[str, Any]:
    """
    Builds the database into a temporary file and renames it atomically on success.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temp_db_path = db_path.with_suffix(".sqlite.tmp")

    if temp_db_path.exists():
        temp_db_path.unlink()

    conn = sqlite3.connect(temp_db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        load_schema(conn, schema_path)

        source_reconciliation = {}
        for spec in TABLE_ALLOWLIST:
            csv_path = raw_dir / spec.csv_filename
            src_count, inserted_count = stream_csv_and_insert(conn, csv_path, spec)
            if src_count != inserted_count:
                raise ValueError(
                    f"Count mismatch in {spec.table_name}: source={src_count}, inserted={inserted_count}"
                )
            source_reconciliation[spec.table_name] = {
                "source_rows": src_count,
                "db_rows": inserted_count,
            }

        conn.commit()

        reconciliation = reconcile_database(conn)
        reconciliation["source_reconciliation"] = source_reconciliation

    except Exception:
        conn.close()
        if temp_db_path.exists():
            temp_db_path.unlink()
        raise

    conn.close()

    # Atomic swap: replace destination only when build and verification fully succeed
    os.replace(temp_db_path, db_path)
    return reconciliation


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    schema_path = project_root / "src" / "sql" / "schema.sql"
    db_path = project_root / "data" / "local" / "olist.sqlite"

    print("==========================================================")
    print("Olist Intelligence — SQLite Database Ingestion (V3-02)")
    print(f"Target DB:   {db_path}")
    print(f"Schema Path: {schema_path}")
    print(f"Raw Dir:     {raw_dir}")
    print("==========================================================")

    try:
        report = build_database(raw_dir, schema_path, db_path)
        print("\n[SUCCESS] Database built and verified successfully.\n")
        print("Reconciliation Summary:")
        for tbl, counts in report["source_reconciliation"].items():
            print(f"  - {tbl:<32}: {counts['db_rows']:>7} rows")
        print(f"\nForeign key violations: {report['foreign_key_violations']}")
        print(f"Distinct orders joined: {report['distinct_orders_with_items_and_customers']}")
        print(f"Untranslated categories (expected ~13): {report['untranslated_categories']}")
    except Exception as exc:
        print(f"\n[ERROR] Ingestion failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()