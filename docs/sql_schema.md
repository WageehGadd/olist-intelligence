# SQLite Database and Loader (V3-02)

**Task:** V3-02 — SQLite schema and raw-table loading
**Contributor:** Hamza Ayman Saad Eid (original implementation); review corrections preserve that authorship
**Database:** `data/local/olist.sqlite` (local and Git-ignored)
**DDL:** `src/sql/schema.sql`
**Loader:** `src/sql/load_sqlite.py`

## Rebuild and test

Use the repository's Python 3.10 environment. The loader uses only Python standard-library modules; it adds no runtime dependency. Keep the existing app setup in `requirements-app.txt` for the application workstream. No alternate `uv` environment is defined by V3-02.

```bash
.venv/bin/python --version
.venv/bin/python src/sql/load_sqlite.py
.venv/bin/python -m pytest -p no:cacheprovider -q tests/sql/test_load_sqlite.py
```

The command reads only the seven contract-required CSVs below. It builds a temporary SQLite file beside the destination, validates it, then atomically replaces the local database only after all checks succeed. On failure the prior database remains intact and the temporary file is removed. It never prints row-level data or identifiers.

## Imported tables and contracts

The CSV headers must match the listed columns exactly and in order. Empty strings in nullable columns become SQL `NULL`; required blanks, invalid numbers, non-finite real values, malformed timestamps, timestamps with time zones, bad row widths, duplicate primary keys and foreign-key violations fail the build. Timestamp text is retained in source-naive ISO form (`YYYY-MM-DD HH:MM:SS`, optional fractional seconds up to six digits).

| Table | Source CSV | Columns in order (SQLite type; `NOT NULL` marked `*`) | Grain / key |
|---|---|---|---|
| `customers` | `olist_customers_dataset.csv` | `customer_id` TEXT*, `customer_unique_id` TEXT*, `customer_zip_code_prefix` TEXT, `customer_city` TEXT, `customer_state` TEXT* | One customer-order record; PK `customer_id`. ZIP prefix is TEXT to preserve leading zeroes. |
| `sellers` | `olist_sellers_dataset.csv` | `seller_id` TEXT*, `seller_zip_code_prefix` TEXT, `seller_city` TEXT, `seller_state` TEXT | One seller; PK `seller_id`. ZIP prefix is TEXT to preserve leading zeroes. |
| `product_category_name_translation` | `product_category_name_translation.csv` | `product_category_name` TEXT*, `product_category_name_english` TEXT* | One translation per Portuguese category; PK `product_category_name`. |
| `products` | `olist_products_dataset.csv` | `product_id` TEXT*, `product_category_name` TEXT, `product_name_lenght` INTEGER, `product_description_lenght` INTEGER, `product_photos_qty` INTEGER, `product_weight_g` REAL, `product_length_cm` REAL, `product_height_cm` REAL, `product_width_cm` REAL | One product; PK `product_id`. The source spelling `lenght` is retained. |
| `orders` | `olist_orders_dataset.csv` | `order_id` TEXT*, `customer_id` TEXT*, `order_status` TEXT*, `order_purchase_timestamp` TEXT*, `order_approved_at` TEXT, `order_delivered_carrier_date` TEXT, `order_delivered_customer_date` TEXT, `order_estimated_delivery_date` TEXT* | One order; PK `order_id`; FK `customer_id` → `customers.customer_id`. |
| `order_items` | `olist_order_items_dataset.csv` | `order_id` TEXT*, `order_item_id` INTEGER*, `product_id` TEXT*, `seller_id` TEXT*, `shipping_limit_date` TEXT, `price` REAL*, `freight_value` REAL* | One item per order; composite PK (`order_id`, `order_item_id`); FKs to orders, products and sellers. |
| `order_payments` | `olist_order_payments_dataset.csv` | `order_id` TEXT*, `payment_sequential` INTEGER*, `payment_type` TEXT*, `payment_installments` INTEGER*, `payment_value` REAL* | One payment row per order sequence; composite PK (`order_id`, `payment_sequential`); FK to orders. |

Indexes support joins on `orders.customer_id`, `orders.order_purchase_timestamp`, `order_items.product_id`, `order_items.seller_id`, and `order_payments.order_id`. Foreign-key enforcement is enabled on the loader connection. The allowlist deliberately excludes geolocation and reviews from this database build.

## Validation and join guidance

For each source file, the loader compares streamed source rows to actual inserted rows. It then checks table counts, primary-key uniqueness and completeness, foreign-key integrity, and required relationship coverage: every order has a customer; every item has an order, product and seller; every payment has an order. It reports the number of orders having both an item and a customer, which is a subset count rather than a required equality.

An order may contain multiple items and multiple payments. Do not join the two raw child tables directly on `order_id` before aggregating: that creates an M×N fan-out and inflates sums. Aggregate each child table to order grain first. For category reporting, retain products with missing or untranslated categories using a `LEFT JOIN` and `COALESCE(translation, 'unknown')`.

## Reproduced local dataset checks

The loader was run against the original local Olist CSVs. Each source row count matched inserted rows, all candidate keys were unique and present, and foreign-key violations were zero.

| Table | Source and inserted rows |
|---|---:|
| `customers` | 99,441 |
| `sellers` | 3,095 |
| `product_category_name_translation` | 71 |
| `products` | 32,951 |
| `orders` | 99,441 |
| `order_items` | 112,650 |
| `order_payments` | 103,886 |

Relationship checks found 99,441 orders with customers, 112,650 items with their order/product/seller, 103,886 payments with orders, and 98,666 orders with both an item and customer. Thirteen product rows have non-null category names without a translation; those rows represent 2 distinct untranslated category names. Separately, 610 products have a missing category name. These row and distinct-name counts are consistent with the T-00 audit. The nine raw CSV hashes matched the existing T-00 hash manifest before the loader run; the raw files were not modified.

## Handoff

V3-03 may connect read-only to `data/local/olist.sqlite` and use these tables and keys as its input. Its query outputs and KPI definitions remain governed by the V3 Shared Contracts and V3-03 task specification. Do not add KPI queries or implement V3-03 as part of this loader task. V3-04/V3-05 handoffs should use their own approved CSV workflows; this database documentation does not replace those contracts.
