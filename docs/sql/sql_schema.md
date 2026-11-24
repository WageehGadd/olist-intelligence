# Olist SQLite Database & Schema Documentation (V3-02)

**Version:** 1.0 (V3 Baseline)  
**Author:** Hamza Ayman Saad Eid  
**Task:** V3-02 — SQLite schema and raw-table loading  
**Database Path:** `data/local/olist.sqlite` (Git-ignored)  
**DDL Source:** `src/sql/schema.sql`  
**Loader Script:** `src/sql/load_sqlite.py`  

---

## 1. How to Build / Recreate the Database

Prerequisites:
- Python 3.10 virtual environment active (`.venv`)
- Raw CSV files placed in `data/raw/`

Run command:
```bash
python src/sql/load_sqlite.py
```

To run automated synthetic tests:
```bash
python -m pytest tests/sql/test_load_sqlite.py -v
```

---

## 2. Table Schemas, Types, and Primary Keys

### `customers`
- **Grain:** One row per customer record attached to an order.
- **Columns:**
  - `customer_id` (TEXT, PRIMARY KEY): Unique customer transaction ID.
  - `customer_unique_id` (TEXT, NOT NULL): Persistent person identifier across orders.
  - `customer_zip_code_prefix` (INTEGER): Postal code prefix.
  - `customer_city` (TEXT): Customer city name.
  - `customer_state` (TEXT, NOT NULL): Two-letter Brazilian UF (e.g., SP, RJ).

### `sellers`
- **Grain:** One row per seller.
- **Columns:**
  - `seller_id` (TEXT, PRIMARY KEY): Unique seller ID.
  - `seller_zip_code_prefix` (INTEGER): Postal code prefix.
  - `seller_city` (TEXT): City.
  - `seller_state` (TEXT): Two-letter UF.

### `product_category_name_translation`
- **Grain:** One row per category name translation.
- **Columns:**
  - `product_category_name` (TEXT, PRIMARY KEY): Portuguese category string.
  - `product_category_name_english` (TEXT, NOT NULL): English translation.

### `products`
- **Grain:** One row per product.
- **Columns:**
  - `product_id` (TEXT, PRIMARY KEY): Unique product identifier.
  - `product_category_name` (TEXT, NULLABLE): Category in Portuguese.
  - `product_name_lenght` (INTEGER)
  - `product_description_lenght` (INTEGER)
  - `product_photos_qty` (INTEGER)
  - `product_weight_g` (REAL)
  - `product_length_cm` (REAL)
  - `product_height_cm` (REAL)
  - `product_width_cm` (REAL)

### `orders`
- **Grain:** One row per order.
- **Columns:**
  - `order_id` (TEXT, PRIMARY KEY): Unique order ID.
  - `customer_id` (TEXT, NOT NULL, FK -> `customers.customer_id`): Customer reference.
  - `order_status` (TEXT, NOT NULL): Order fulfillment status (`delivered`, `shipped`, etc.).
  - `order_purchase_timestamp` (TEXT, NOT NULL): Timestamp of purchase.
  - `order_approved_at` (TEXT): Payment approval timestamp.
  - `order_delivered_carrier_date` (TEXT): Hand-off to carrier timestamp.
  - `order_delivered_customer_date` (TEXT): Delivery to customer timestamp.
  - `order_estimated_delivery_date` (TEXT, NOT NULL): Estimated delivery date.

### `order_items`
- **Grain:** One row per order item.
- **Columns:**
  - `order_id` (TEXT, NOT NULL, FK -> `orders.order_id`): Order reference.
  - `order_item_id` (INTEGER, NOT NULL): Sequential item number within order.
  - `product_id` (TEXT, NOT NULL, FK -> `products.product_id`): Product reference.
  - `seller_id` (TEXT, NOT NULL, FK -> `sellers.seller_id`): Seller reference.
  - `shipping_limit_date` (TEXT): Seller shipping deadline.
  - `price` (REAL, NOT NULL): Item price in BRL.
  - `freight_value` (REAL, NOT NULL): Item shipping fee in BRL.
  - **PRIMARY KEY:** `(order_id, order_item_id)`

### `order_payments`
- **Grain:** One row per payment installment/method.
- **Columns:**
  - `order_id` (TEXT, NOT NULL, FK -> `orders.order_id`): Order reference.
  - `payment_sequential` (INTEGER, NOT NULL): Sequence of payment.
  - `payment_type` (TEXT, NOT NULL): Method (`credit_card`, `boleto`, etc.).
  - `payment_installments` (INTEGER, NOT NULL): Installment count.
  - `payment_value` (REAL, NOT NULL): Amount paid in BRL.
  - **PRIMARY KEY:** `(order_id, payment_sequential)`

---

## 3. Verified Row Counts (Authentic Olist Dataset)

| Table Name | Source CSV | Row Count | Primary Key | Key Uniqueness |
|---|---|---|---|---|
| `customers` | `olist_customers_dataset.csv` | 99,441 | `customer_id` | 100% Unique |
| `sellers` | `olist_sellers_dataset.csv` | 3,095 | `seller_id` | 100% Unique |
| `product_category_name_translation` | `product_category_name_translation.csv` | 71 | `product_category_name` | 100% Unique |
| `products` | `olist_products_dataset.csv` | 32,951 | `product_id` | 100% Unique |
| `orders` | `olist_orders_dataset.csv` | 99,441 | `order_id` | 100% Unique |
| `order_items` | `olist_order_items_dataset.csv` | 112,650 | `(order_id, order_item_id)` | 100% Unique |
| `order_payments` | `olist_order_payments_dataset.csv` | 103,886 | `(order_id, payment_sequential)` | 100% Unique |

---

## 4. Relationship Grains, Join Cardinality & Caveats

1. **Items to Payments Cross-Product Prevention**:
   - One order may have multiple items ($M$) and multiple payments ($N$).
   - **Never** join `order_items` directly to `order_payments` on `order_id` without prior aggregation, as this produces $M \times N$ rows and inflates sums.
   - Always pre-aggregate each child table to `(order_id)` before joining to `orders`.
2. **Missing Product Categories**:
   - 610 products in `products` have `NULL` for `product_category_name`.
   - 13 distinct Portuguese category values in `products` are not present in `product_category_name_translation.csv`.
   - Per contract, queries must use `LEFT JOIN` and map unmatched or null categories to `'unknown'`:
     ```sql
     COALESCE(t.product_category_name_english, 'unknown') AS category_name
     ```
3. **Excluded Tables**:
   - `olist_geolocation_dataset.csv` (>1M rows) is excluded per MVP scope.
   - `olist_order_reviews_dataset.csv` is excluded from the core SQL KPI deliverable.

---

## 5. Downstream Handoff Notes

- **To Wageeh (V3-12 / V3-14)**: The database is stored at `data/local/olist.sqlite`. Use `sqlite3.connect("data/local/olist.sqlite")`.
- **To Hasnaa (V3-04 / V3-05)**: Total order count is 99,441; delivered orders count is 96,478. The item price total is 13,591,643.70 BRL.