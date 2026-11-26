"""Deterministic, validated CSV-to-SQLite loading for V3-02."""

from __future__ import annotations

import csv
import math
import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple


ENCODING = "utf-8-sig"
INTEGER_MIN = -(2**63)
INTEGER_MAX = 2**63 - 1
TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?$"
)


class TableSpec(NamedTuple):
    csv_filename: str
    table_name: str
    expected_header: tuple[str, ...]
    primary_key: tuple[str, ...]


# Only the seven contract-required tables are imported. Parent tables precede
# their children so SQLite foreign-key checks run during each child insert.
TABLE_ALLOWLIST: tuple[TableSpec, ...] = (
    TableSpec(
        "olist_customers_dataset.csv", "customers",
        ("customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"),
        ("customer_id",),
    ),
    TableSpec(
        "olist_sellers_dataset.csv", "sellers",
        ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
        ("seller_id",),
    ),
    TableSpec(
        "product_category_name_translation.csv", "product_category_name_translation",
        ("product_category_name", "product_category_name_english"),
        ("product_category_name",),
    ),
    TableSpec(
        "olist_products_dataset.csv", "products",
        (
            "product_id", "product_category_name", "product_name_lenght",
            "product_description_lenght", "product_photos_qty", "product_weight_g",
            "product_length_cm", "product_height_cm", "product_width_cm",
        ),
        ("product_id",),
    ),
    TableSpec(
        "olist_orders_dataset.csv", "orders",
        (
            "order_id", "customer_id", "order_status", "order_purchase_timestamp",
            "order_approved_at", "order_delivered_carrier_date",
            "order_delivered_customer_date", "order_estimated_delivery_date",
        ),
        ("order_id",),
    ),
    TableSpec(
        "olist_order_items_dataset.csv", "order_items",
        (
            "order_id", "order_item_id", "product_id", "seller_id",
            "shipping_limit_date", "price", "freight_value",
        ),
        ("order_id", "order_item_id"),
    ),
    TableSpec(
        "olist_order_payments_dataset.csv", "order_payments",
        ("order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"),
        ("order_id", "payment_sequential"),
    ),
)

TIMESTAMP_COLUMNS = {
    "orders": {
        "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    },
    "order_items": {"shipping_limit_date"},
}


def _quoted_identifier(value: str) -> str:
    """Quote a fixed schema identifier for PRAGMA/SQL use."""
    return '"' + value.replace('"', '""') + '"'


def _table_info(conn: sqlite3.Connection, spec: TableSpec) -> list[dict[str, Any]]:
    rows = conn.execute(f"PRAGMA table_info({_quoted_identifier(spec.table_name)})").fetchall()
    if not rows:
        raise ValueError(f"Required table is missing from schema: {spec.table_name}")
    info = [
        {"name": row[1], "type": row[2].upper(), "notnull": bool(row[3]), "pk_order": int(row[5])}
        for row in rows
    ]
    actual_header = tuple(column["name"] for column in info)
    if actual_header != spec.expected_header:
        raise ValueError(
            f"Schema columns differ for {spec.table_name}: "
            f"expected {spec.expected_header}, found {actual_header}"
        )
    actual_pk = tuple(
        column["name"] for column in sorted(info, key=lambda item: item["pk_order"])
        if column["pk_order"]
    )
    if actual_pk != spec.primary_key:
        raise ValueError(
            f"Primary key differs for {spec.table_name}: "
            f"expected {spec.primary_key}, found {actual_pk}"
        )
    return info


def load_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    """Load the checked-in DDL and verify table columns and primary keys."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    conn.execute("PRAGMA foreign_keys = ON")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("SQLite foreign-key enforcement could not be enabled")
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    for spec in TABLE_ALLOWLIST:
        _table_info(conn, spec)


def _normalize_cell(
    raw_value: str,
    column: dict[str, Any],
    *,
    spec: TableSpec,
    line_number: int,
) -> str | int | float | None:
    name = column["name"]
    required = column["notnull"] or bool(column["pk_order"])
    location = f"{spec.csv_filename} line {line_number}, column {name}"

    if raw_value == "":
        if required:
            raise ValueError(f"Missing required value at {location}")
        return None

    if required and not raw_value.strip():
        raise ValueError(f"Blank required value at {location}")

    declared_type = column["type"]
    if declared_type == "INTEGER":
        if not re.fullmatch(r"[+-]?\d+", raw_value):
            raise ValueError(f"Invalid INTEGER value at {location}")
        value = int(raw_value)
        if not INTEGER_MIN <= value <= INTEGER_MAX:
            raise ValueError(f"INTEGER value is outside SQLite's supported range at {location}")
        return value

    if declared_type == "REAL":
        try:
            value = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"Invalid REAL value at {location}") from exc
        if not math.isfinite(value):
            raise ValueError(f"Non-finite REAL value at {location}")
        return value

    if declared_type != "TEXT":
        raise ValueError(f"Unsupported declared type {declared_type!r} for {location}")

    if name in TIMESTAMP_COLUMNS.get(spec.table_name, set()):
        if not TIMESTAMP_PATTERN.fullmatch(raw_value):
            raise ValueError(f"Malformed source-naive timestamp at {location}")
        try:
            parsed = datetime.fromisoformat(raw_value)
        except ValueError as exc:
            raise ValueError(f"Malformed source-naive timestamp at {location}") from exc
        if parsed.tzinfo is not None:
            raise ValueError(f"Timezone-bearing timestamp is unsupported at {location}")
    return raw_value


def stream_csv_and_insert(
    conn: sqlite3.Connection,
    csv_path: Path,
    spec: TableSpec,
    batch_size: int = 10000,
) -> tuple[int, int]:
    """Validate and batch-insert one allowed CSV; return source/inserted rows."""
    if spec not in TABLE_ALLOWLIST:
        raise ValueError(f"Table is not in the V3-02 import allowlist: {spec.table_name}")
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Required input CSV missing: {csv_path.name}")

    columns = _table_info(conn, spec)
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(_quoted_identifier(column["name"]) for column in columns)
    insert_sql = f"INSERT INTO {_quoted_identifier(spec.table_name)} ({column_sql}) VALUES ({placeholders})"
    before_count = conn.execute(
        f"SELECT COUNT(*) FROM {_quoted_identifier(spec.table_name)}"
    ).fetchone()[0]

    source_count = 0
    batch: list[list[str | int | float | None]] = []
    try:
        with csv_path.open("r", encoding=ENCODING, newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                header = next(reader)
            except StopIteration as exc:
                raise ValueError(f"CSV file is empty: {csv_path.name}") from exc
            except csv.Error as exc:
                raise ValueError(f"Malformed CSV header in {csv_path.name}") from exc

            if tuple(header) != spec.expected_header:
                raise ValueError(
                    f"Header mismatch in {csv_path.name}: expected {spec.expected_header}, found {tuple(header)}"
                )

            try:
                for row in reader:
                    line_number = reader.line_num
                    if len(row) != len(columns):
                        raise ValueError(
                            f"Row-width mismatch in {csv_path.name} line {line_number}: "
                            f"expected {len(columns)} fields, found {len(row)}"
                        )
                    source_count += 1
                    batch.append([
                        _normalize_cell(value, column, spec=spec, line_number=line_number)
                        for value, column in zip(row, columns)
                    ])
                    if len(batch) >= batch_size:
                        conn.executemany(insert_sql, batch)
                        batch.clear()
            except csv.Error as exc:
                raise ValueError(
                    f"Malformed CSV record in {csv_path.name} near line {reader.line_num}"
                ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"CSV is not valid {ENCODING}: {csv_path.name}") from exc

    if source_count == 0:
        raise ValueError(f"CSV contains a header but no data rows: {csv_path.name}")
    if batch:
        conn.executemany(insert_sql, batch)

    after_count = conn.execute(
        f"SELECT COUNT(*) FROM {_quoted_identifier(spec.table_name)}"
    ).fetchone()[0]
    inserted_count = after_count - before_count
    return source_count, inserted_count


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def reconcile_database(conn: sqlite3.Connection) -> dict[str, Any]:
    """Check keys, relationships, foreign keys and report privacy-safe counts."""
    table_counts: dict[str, int] = {}
    candidate_key_checks: dict[str, dict[str, int | bool]] = {}

    for spec in TABLE_ALLOWLIST:
        info = _table_info(conn, spec)
        table_name = _quoted_identifier(spec.table_name)
        table_count = _count(conn, f"SELECT COUNT(*) FROM {table_name}")
        table_counts[spec.table_name] = table_count
        key_sql = ", ".join(_quoted_identifier(column) for column in spec.primary_key)
        duplicate_count = _count(
            conn,
            f"SELECT COUNT(*) FROM (SELECT {key_sql} FROM {table_name} "
            f"GROUP BY {key_sql} HAVING COUNT(*) > 1)",
        )
        null_predicate = " OR ".join(
            f"{_quoted_identifier(column)} IS NULL OR "
            f"(typeof({_quoted_identifier(column)}) = 'text' AND trim({_quoted_identifier(column)}) = '')"
            for column in spec.primary_key
        )
        null_key_count = _count(
            conn, f"SELECT COUNT(*) FROM {table_name} WHERE {null_predicate}"
        )
        candidate_key_checks[spec.table_name] = {
            "rows": table_count,
            "duplicate_keys": duplicate_count,
            "null_or_blank_keys": null_key_count,
            "unique_and_present": duplicate_count == 0 and null_key_count == 0,
        }
        if duplicate_count or null_key_count:
            raise ValueError(f"Primary/candidate key check failed for {spec.table_name}")

    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_violations:
        raise ValueError(f"Foreign-key check failed with {len(fk_violations)} violation(s)")

    relationship_counts = {
        "orders_with_customer": _count(
            conn, "SELECT COUNT(*) FROM orders o JOIN customers c USING (customer_id)"
        ),
        "items_with_order_product_seller": _count(
            conn,
            """SELECT COUNT(*) FROM order_items i
               JOIN orders o USING (order_id)
               JOIN products p USING (product_id)
               JOIN sellers s USING (seller_id)""",
        ),
        "payments_with_order": _count(
            conn, "SELECT COUNT(*) FROM order_payments p JOIN orders o USING (order_id)"
        ),
        "orders_with_items_and_customer": _count(
            conn,
            """SELECT COUNT(DISTINCT o.order_id) FROM orders o
               JOIN customers c USING (customer_id)
               JOIN order_items i USING (order_id)""",
        ),
    }
    expected_relationship_counts = {
        "orders_with_customer": table_counts["orders"],
        "items_with_order_product_seller": table_counts["order_items"],
        "payments_with_order": table_counts["order_payments"],
    }
    for relationship, expected in expected_relationship_counts.items():
        if relationship_counts[relationship] != expected:
            raise ValueError(f"Relationship coverage check failed for {relationship}")

    untranslated_categories = _count(
        conn,
        """SELECT COUNT(DISTINCT p.product_category_name)
           FROM products p
           WHERE p.product_category_name IS NOT NULL
             AND p.product_category_name NOT IN (
               SELECT product_category_name FROM product_category_name_translation
             )""",
    )
    missing_product_categories = _count(
        conn, "SELECT COUNT(*) FROM products WHERE product_category_name IS NULL"
    )

    return {
        "table_counts": table_counts,
        "candidate_key_checks": candidate_key_checks,
        "foreign_key_violations": 0,
        "relationship_counts": relationship_counts,
        "untranslated_category_count": untranslated_categories,
        "products_with_missing_category": missing_product_categories,
    }


def build_database(raw_dir: Path, schema_path: Path, db_path: Path) -> dict[str, Any]:
    """Build and verify a temporary DB, then atomically replace the destination."""
    raw_dir = Path(raw_dir)
    schema_path = Path(schema_path)
    db_path = Path(db_path)
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Required raw-data directory is missing: {raw_dir}")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{db_path.stem}.", suffix=".sqlite", dir=db_path.parent
    )
    os.close(fd)
    temporary_db_path = Path(temporary_name)
    try:
        conn = sqlite3.connect(temporary_db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise RuntimeError("SQLite foreign-key enforcement is disabled")
            load_schema(conn, schema_path)

            source_reconciliation: dict[str, dict[str, int]] = {}
            for spec in TABLE_ALLOWLIST:
                source_count, inserted_count = stream_csv_and_insert(
                    conn, raw_dir / spec.csv_filename, spec
                )
                if source_count != inserted_count:
                    raise ValueError(
                        f"Source/inserted row-count mismatch for {spec.table_name}: "
                        f"source={source_count}, inserted={inserted_count}"
                    )
                source_reconciliation[spec.table_name] = {
                    "source_rows": source_count,
                    "inserted_rows": inserted_count,
                }
            conn.commit()
            report = reconcile_database(conn)
            report["source_reconciliation"] = source_reconciliation
        finally:
            conn.close()

        os.replace(temporary_db_path, db_path)
        return report
    except Exception:
        temporary_db_path.unlink(missing_ok=True)
        raise


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    schema_path = project_root / "src" / "sql" / "schema.sql"
    db_path = project_root / "data" / "local" / "olist.sqlite"
    try:
        report = build_database(raw_dir, schema_path, db_path)
    except Exception as exc:
        print(f"[ERROR] Ingestion failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Database built and verified: {db_path}")
    print("Source/inserted rows:")
    for table, counts in report["source_reconciliation"].items():
        print(
            f"  {table}: source={counts['source_rows']}, "
            f"inserted={counts['inserted_rows']}"
        )
    print("Candidate-key checks:")
    for table, check in report["candidate_key_checks"].items():
        print(
            f"  {table}: rows={check['rows']}, duplicates={check['duplicate_keys']}, "
            f"null_or_blank={check['null_or_blank_keys']}"
        )
    print("Foreign-key violations: 0")
    print("Relationship counts:")
    for name, count in report["relationship_counts"].items():
        print(f"  {name}: {count}")
    print(f"Distinct untranslated categories: {report['untranslated_category_count']}")
    print(f"Products with no category: {report['products_with_missing_category']}")


if __name__ == "__main__":
    main()
