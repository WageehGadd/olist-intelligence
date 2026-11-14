"""Build the frozen V3 delivery features from historical Olist inputs.

Only :func:`derive_model_features` defines predictor arithmetic. Historical
rows and future inference inputs call the same function.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from numbers import Number
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


FEATURE_NAMES = (
    "purchase_hour",
    "purchase_weekday",
    "purchase_month",
    "promised_lead_days",
    "customer_state",
    "item_price_total",
    "freight_total",
    "item_count",
)
FEATURE_TYPES = {
    "purchase_hour": "integer",
    "purchase_weekday": "integer",
    "purchase_month": "integer",
    "promised_lead_days": "integer",
    "customer_state": "string",
    "item_price_total": "numeric",
    "freight_total": "numeric",
    "item_count": "integer",
}
METADATA_NAMES = ("order_id", "purchase_ts", "late")
BRAZIL_UFS = frozenset(
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PE PI PR RJ RN RS RO RR SC SP SE TO".split()
)
_PURCHASE_PATTERNS = (
    (re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"), "%Y-%m-%dT%H:%M:%S"),
)
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SOURCE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class FeatureInputError(ValueError):
    """Invalid normalized feature input with a stable audit reason."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


def parse_purchase_timestamp(value: Any) -> datetime:
    """Parse either allowed source-naive boundary format, with no coercion."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise FeatureInputError("missing_purchase_timestamp", "purchase timestamp is missing")
    if not isinstance(value, str):
        raise FeatureInputError("invalid_purchase_timestamp", "purchase timestamp must be a string")
    for pattern, fmt in _PURCHASE_PATTERNS:
        if pattern.fullmatch(value):
            try:
                parsed = datetime.strptime(value, fmt)
            except ValueError as exc:
                raise FeatureInputError("invalid_purchase_timestamp", "invalid purchase timestamp") from exc
            if parsed.strftime(fmt) == value:
                return parsed
    raise FeatureInputError(
        "invalid_purchase_timestamp",
        "purchase timestamp must be strict source-naive YYYY-MM-DD HH:MM:SS or YYYY-MM-DDTHH:MM:SS",
    )


def _parse_calendar_date(value: Any) -> date:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise FeatureInputError("missing_estimated_delivery_date", "estimated delivery date is missing")
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise FeatureInputError("invalid_estimated_delivery_date", "estimated delivery date must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise FeatureInputError("invalid_estimated_delivery_date", "estimated delivery date is not a real calendar date") from exc
    if parsed.isoformat() != value:
        raise FeatureInputError("invalid_estimated_delivery_date", "estimated delivery date must be canonical YYYY-MM-DD")
    return parsed


def _decimal_amount(value: Any, field: str) -> Decimal:
    if value is None:
        raise FeatureInputError("missing_item_amount", f"item {field} is missing")
    if isinstance(value, bool) or isinstance(value, str) or not isinstance(value, (Number, Decimal)):
        raise FeatureInputError("invalid_item_amount", f"item {field} must be a JSON number")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FeatureInputError("invalid_item_amount", f"item {field} is not numeric") from exc
    if not amount.is_finite() or amount < 0:
        raise FeatureInputError("invalid_item_amount", f"item {field} must be finite and nonnegative")
    return amount


def derive_model_features(
    purchase_timestamp: str,
    estimated_delivery_date: str,
    customer_state: str,
    item_rows: Sequence[Mapping[str, Any]],
) -> dict[str, int | float | str]:
    """Return exactly the eight frozen predictors in contract order.

    Historical callers pass ``YYYY-MM-DD HH:MM:SS`` purchase strings; the API
    boundary passes strict ``YYYY-MM-DDTHH:MM:SS`` strings. Estimated dates
    are normalized to ``YYYY-MM-DD`` before this shared transformation.
    """
    purchase = parse_purchase_timestamp(purchase_timestamp)
    promised = _parse_calendar_date(estimated_delivery_date)
    if promised < purchase.date():
        raise FeatureInputError(
            "estimated_date_before_purchase_date",
            "estimated delivery calendar date precedes purchase calendar date",
        )
    if customer_state is None or (isinstance(customer_state, str) and not customer_state):
        raise FeatureInputError("missing_customer_state", "customer state is missing")
    if not isinstance(customer_state, str) or customer_state != customer_state.strip() or customer_state not in BRAZIL_UFS:
        raise FeatureInputError("invalid_customer_state", "customer state must be an uppercase Brazilian UF")
    if not isinstance(item_rows, (list, tuple)):
        raise FeatureInputError("invalid_item_rows", "items must be a list of item rows")
    if not item_rows:
        raise FeatureInputError("missing_item_rows", "at least one item row is required")

    price_total = Decimal("0")
    freight_total = Decimal("0")
    for item in item_rows:
        if not isinstance(item, Mapping) or set(item) != {"price", "freight_value"}:
            raise FeatureInputError(
                "invalid_item_rows",
                "each item must contain exactly price and freight_value",
            )
        price_total += _decimal_amount(item["price"], "price")
        freight_total += _decimal_amount(item["freight_value"], "freight_value")

    result: dict[str, int | float | str] = {
        "purchase_hour": int(purchase.hour),
        "purchase_weekday": int(purchase.weekday()),
        "purchase_month": int(purchase.month),
        "promised_lead_days": int((promised - purchase.date()).days),
        "customer_state": customer_state,
        "item_price_total": float(price_total),
        "freight_total": float(freight_total),
        "item_count": int(len(item_rows)),
    }
    if tuple(result) != FEATURE_NAMES:
        raise AssertionError("Feature construction order differs from Shared Contracts v1")
    return result


def _require_columns(frame: pd.DataFrame, required: Sequence[str], label: str) -> None:
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing required column(s): {', '.join(missing)}")


def _clean_ids(series: pd.Series, label: str) -> pd.Series:
    ids = series.astype("string")
    missing = ids.isna() | ids.str.strip().eq("").fillna(False)
    if missing.any():
        raise ValueError(f"{label} contains {int(missing.sum())} blank identifiers")
    return ids


def _source_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value):
        raise ValueError(f"{field} must use source-naive YYYY-MM-DD HH:MM:SS")
    try:
        parsed = datetime.strptime(value, _SOURCE_TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid source timestamp") from exc
    if parsed.strftime(_SOURCE_TIMESTAMP_FORMAT) != value:
        raise ValueError(f"{field} is not a canonical source timestamp")
    return parsed


def _source_date(value: Any, field: str) -> date:
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must use normalized YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid calendar date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field} is not a canonical calendar date")
    return parsed


def _amount_problem(value: Any) -> str | None:
    if pd.isna(value):
        return "missing"
    try:
        if isinstance(value, bool) or isinstance(value, str) or not isinstance(value, (Number, Decimal)):
            return "invalid"
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "invalid"
    return None if amount.is_finite() and amount >= 0 else "invalid"


def _validate_generated_paths(input_paths: Sequence[Path], output_paths: Sequence[Path]) -> None:
    root = Path(__file__).resolve().parents[2]
    processed_dir = (root / "data" / "processed").resolve()
    resolved_inputs = {path.resolve() for path in input_paths}
    resolved_outputs = [path.resolve() for path in output_paths]
    if len(set(resolved_outputs)) != len(resolved_outputs):
        raise ValueError("Generated output paths must be distinct")
    for output in resolved_outputs:
        if output in resolved_inputs:
            raise ValueError("Generated output path must not overwrite an input file")
        try:
            output.relative_to(processed_dir)
        except ValueError as exc:
            raise ValueError("Generated feature outputs must stay under ignored data/processed/") from exc


def build_historical_features(
    population: pd.DataFrame,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    customers: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build one row per representable V3-06 order, auditing every disposition."""
    _require_columns(
        population,
        ("order_id", "purchase_ts", "estimated_delivery_date", "delivered_date", "late", "population_version"),
        "V3-06 population",
    )
    _require_columns(
        orders,
        ("order_id", "customer_id", "order_status", "order_purchase_timestamp",
         "order_estimated_delivery_date", "order_delivered_customer_date"),
        "orders",
    )
    _require_columns(items, ("order_id", "order_item_id", "price", "freight_value"), "order items")
    _require_columns(customers, ("customer_id", "customer_state"), "customers")

    population = population.copy()
    orders = orders.copy()
    items = items.copy()
    customers = customers.copy()
    population["order_id"] = _clean_ids(population["order_id"], "V3-06 population.order_id")
    orders["order_id"] = _clean_ids(orders["order_id"], "orders.order_id")
    orders["customer_id"] = orders["customer_id"].astype("string")
    customers["customer_id"] = _clean_ids(customers["customer_id"], "customers.customer_id")
    items["order_id"] = _clean_ids(items["order_id"], "order_items.order_id")
    item_ids = items["order_item_id"].astype("string")
    missing_item_ids = items["order_item_id"].isna() | item_ids.str.strip().eq("").fillna(False)
    if missing_item_ids.any():
        raise ValueError("order_items.order_item_id must be present and nonblank")

    if population["order_id"].duplicated().any():
        raise ValueError("V3-06 population contains duplicate order_id values")
    if orders["order_id"].duplicated().any():
        raise ValueError("orders contains duplicate order_id values")
    if customers["customer_id"].duplicated().any():
        raise ValueError("customers contains duplicate customer_id values")
    if items.duplicated(["order_id", "order_item_id"]).any():
        raise ValueError("order_items contains duplicate (order_id, order_item_id) rows")

    order_lookup = orders.set_index("order_id", verify_integrity=True).to_dict("index")
    customer_lookup = customers.set_index("customer_id", verify_integrity=True)["customer_state"].to_dict()
    population_ids = set(population["order_id"])
    raw_order_ids = set(orders["order_id"])
    missing_order_matches = population_ids - raw_order_ids
    if missing_order_matches:
        raise ValueError(f"{len(missing_order_matches)} V3-06 orders have no source orders row")

    item_lists: dict[str, list[dict[str, Any]]] = defaultdict(list)
    item_diagnostics: Counter[str] = Counter()
    orphan_item_rows = 0
    for row in items.loc[:, ["order_id", "price", "freight_value"]].itertuples(index=False, name=None):
        order_id, price, freight = row
        if order_id not in raw_order_ids:
            orphan_item_rows += 1
        for name, value in (("price", price), ("freight_value", freight)):
            problem = _amount_problem(value)
            if problem:
                item_diagnostics[f"{name}_{problem}_rows"] += 1
        if order_id in population_ids:
            item_lists[order_id].append({
                "price": None if pd.isna(price) else price,
                "freight_value": None if pd.isna(freight) else freight,
            })

    records_by_id = population.set_index("order_id", verify_integrity=True).to_dict("index")
    source_order_monthly: dict[str, dict[str, int]] = {}
    source_date_invalid = 0
    for record in orders.to_dict("records"):
        try:
            month = _source_timestamp(record["order_purchase_timestamp"], "order_purchase_timestamp").strftime("%Y-%m")
        except ValueError:
            source_date_invalid += 1
            continue
        metrics = source_order_monthly.setdefault(month, {"source_orders": 0, "delivered_status_orders": 0})
        metrics["source_orders"] += 1
        metrics["delivered_status_orders"] += int(record["order_status"] == "delivered")

    exclusions: Counter[str] = Counter()
    excluded_late = 0
    output: list[dict[str, Any]] = []
    for order_id, row in records_by_id.items():
        source = order_lookup[order_id]
        # Reconcile the labeled V3-06 row with raw orders without using outcomes as predictors.
        purchase = _source_timestamp(row["purchase_ts"], "population.purchase_ts")
        source_purchase = _source_timestamp(source["order_purchase_timestamp"], "orders.order_purchase_timestamp")
        estimated = _source_date(row["estimated_delivery_date"], "population.estimated_delivery_date")
        delivered = _source_date(row["delivered_date"], "population.delivered_date")
        source_estimated = _source_timestamp(source["order_estimated_delivery_date"], "orders.order_estimated_delivery_date").date()
        source_delivered = _source_timestamp(source["order_delivered_customer_date"], "orders.order_delivered_customer_date").date()
        if source["order_status"] != "delivered":
            raise ValueError(f"V3-06 order {order_id} is not delivered in the raw source")
        if purchase != source_purchase or estimated != source_estimated or delivered != source_delivered:
            raise ValueError(f"V3-06 dates for order {order_id} do not reconcile to raw orders")
        if int(row["late"]) != int(delivered > estimated):
            raise ValueError(f"V3-06 label for order {order_id} does not reconcile to calendar dates")
        if row["population_version"] != "v1":
            raise ValueError(f"Unsupported V3-06 population_version for order {order_id}")

        customer_id = source["customer_id"]
        if pd.isna(customer_id) or not str(customer_id).strip():
            exclusions["missing_customer_id"] += 1
            excluded_late += int(row["late"])
            continue
        if customer_id not in customer_lookup:
            exclusions["customer_not_found"] += 1
            excluded_late += int(row["late"])
            continue
        try:
            derived = derive_model_features(
                row["purchase_ts"],
                row["estimated_delivery_date"],
                None if pd.isna(customer_lookup[customer_id]) else customer_lookup[customer_id],
                item_lists.get(order_id, []),
            )
        except FeatureInputError as exc:
            exclusions[exc.reason] += 1
            excluded_late += int(row["late"])
            continue
        output.append({
            "order_id": order_id,
            "purchase_ts": row["purchase_ts"],
            "late": int(row["late"]),
            **derived,
        })

    columns = [*METADATA_NAMES, *FEATURE_NAMES]
    feature_frame = pd.DataFrame(output, columns=columns)
    if len(feature_frame):
        feature_frame = feature_frame.sort_values(["purchase_ts", "order_id"], kind="mergesort").reset_index(drop=True)
    if feature_frame["order_id"].duplicated().any():
        raise AssertionError("Historical feature output has duplicate order IDs")
    if feature_frame.loc[:, FEATURE_NAMES].columns.tolist() != list(FEATURE_NAMES):
        raise AssertionError("Historical model feature columns differ from the frozen order")

    population_monthly: Counter[str] = Counter()
    population_late_monthly: Counter[str] = Counter()
    ready_monthly: Counter[str] = Counter()
    ready_late_monthly: Counter[str] = Counter()
    for row in population.to_dict("records"):
        month = _source_timestamp(row["purchase_ts"], "population.purchase_ts").strftime("%Y-%m")
        population_monthly[month] += 1
        population_late_monthly[month] += int(row["late"])
    for row in feature_frame.loc[:, ["purchase_ts", "late"]].to_dict("records"):
        month = _source_timestamp(row["purchase_ts"], "feature.purchase_ts").strftime("%Y-%m")
        ready_monthly[month] += 1
        ready_late_monthly[month] += int(row["late"])

    monthly = {}
    for month in sorted(set(source_order_monthly) | set(population_monthly) | set(ready_monthly)):
        monthly[month] = {
            **source_order_monthly.get(month, {"source_orders": 0, "delivered_status_orders": 0}),
            "v3_06_eligible": population_monthly[month],
            "v3_06_late": population_late_monthly[month],
            "feature_ready": ready_monthly[month],
            "feature_ready_late": ready_late_monthly[month],
        }

    reasons = sorted(set(exclusions) | {
        "missing_customer_id", "customer_not_found", "missing_customer_state", "invalid_customer_state",
        "unsupported_customer_state",
        "missing_item_rows", "invalid_item_rows", "missing_item_amount", "invalid_item_amount",
        "missing_purchase_timestamp", "invalid_purchase_timestamp", "missing_estimated_delivery_date",
        "invalid_estimated_delivery_date", "estimated_date_before_purchase_date",
    })
    audit: dict[str, Any] = {
        "audit_version": "v1",
        "population_input_rows": int(len(population)),
        "population_input_late": int(population["late"].astype(int).sum()),
        "feature_ready_rows": int(len(feature_frame)),
        "feature_ready_late": int(feature_frame["late"].sum()) if len(feature_frame) else 0,
        "feature_ready_negative_rows": int(len(feature_frame) - feature_frame["late"].sum()),
        "feature_excluded_rows": int(len(population) - len(feature_frame)),
        "feature_excluded_late": int(excluded_late),
        "exclusive_feature_exclusion_counts": {reason: int(exclusions[reason]) for reason in reasons},
        "raw_source_rows": {
            "orders": int(len(orders)), "order_items": int(len(items)), "customers": int(len(customers)),
        },
        "join_and_input_diagnostics": {
            "population_ids_missing_from_orders": 0,
            "orphan_item_rows_without_source_order": int(orphan_item_rows),
            "population_order_keys_unique": True,
            "raw_order_keys_unique": True,
            "customer_keys_unique": True,
            "order_item_keys_unique": True,
            "invalid_source_purchase_timestamps": int(source_date_invalid),
            "item_amount_rows": dict(sorted(item_diagnostics.items())),
        },
        "input_target_label_counts": {
            "late_1": int(population["late"].astype(int).sum()),
            "late_0": int(len(population) - population["late"].astype(int).sum()),
        },
        "feature_ready_label_counts": {
            "late_1": int(feature_frame["late"].sum()) if len(feature_frame) else 0,
            "late_0": int(len(feature_frame) - feature_frame["late"].sum()) if len(feature_frame) else 0,
        },
        "feature_missingness_before_preprocessing": {
            name: int(feature_frame[name].isna().sum()) for name in FEATURE_NAMES
        },
        "feature_names": list(FEATURE_NAMES),
        "feature_types": FEATURE_TYPES,
        "source_population_monthly": monthly,
    }
    if audit["feature_ready_rows"] + audit["feature_excluded_rows"] != audit["population_input_rows"]:
        raise AssertionError("Feature-ready and excluded rows do not account for the V3-06 population")
    if audit["feature_ready_late"] + audit["feature_excluded_late"] != audit["population_input_late"]:
        raise AssertionError("Internal target-count accounting failed")
    if orphan_item_rows:
        raise ValueError(f"Found {orphan_item_rows} item rows with no source order; inspect the data before proceeding")
    return feature_frame, audit


def default_paths() -> tuple[Path, Path, Path, Path, Path, Path]:
    root = Path(__file__).resolve().parents[2]
    processed = root / "data" / "processed"
    return (
        processed / "delivery_population.csv",
        root / "data" / "raw" / "olist_orders_dataset.csv",
        root / "data" / "raw" / "olist_order_items_dataset.csv",
        root / "data" / "raw" / "olist_customers_dataset.csv",
        processed / "delivery_features.csv",
        processed / "delivery_feature_audit.json",
    )


def build_from_csv(
    population_path: Path,
    orders_path: Path,
    items_path: Path,
    customers_path: Path,
    output_path: Path,
    audit_path: Path,
) -> dict[str, Any]:
    for path in (population_path, orders_path, items_path, customers_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required V3-07 input not found: {path}")
    _validate_generated_paths(
        (population_path, orders_path, items_path, customers_path),
        (output_path, audit_path),
    )
    population = pd.read_csv(population_path, dtype={"order_id": "string", "purchase_ts": "string"})
    orders = pd.read_csv(
        orders_path,
        usecols=["order_id", "customer_id", "order_status", "order_purchase_timestamp",
                 "order_estimated_delivery_date", "order_delivered_customer_date"],
        dtype={"order_id": "string", "customer_id": "string", "order_status": "string"},
    )
    items = pd.read_csv(
        items_path,
        usecols=["order_id", "order_item_id", "price", "freight_value"],
        dtype={"order_id": "string"},
    )
    customers = pd.read_csv(
        customers_path,
        usecols=["customer_id", "customer_state"],
        dtype={"customer_id": "string", "customer_state": "string"},
    )
    features, audit = build_historical_features(population, orders, items, customers)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)
    digest = hashlib.sha256()
    with output_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    audit["feature_artifact_sha256"] = digest.hexdigest()
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audit


def main(argv: list[str] | None = None) -> int:
    default_population, default_orders, default_items, default_customers, default_output, default_audit = default_paths()
    parser = argparse.ArgumentParser(description="Build V3-07 order-grain features from the V3-06 population.")
    parser.add_argument("--population", type=Path, default=default_population)
    parser.add_argument("--orders", type=Path, default=default_orders)
    parser.add_argument("--items", type=Path, default=default_items)
    parser.add_argument("--customers", type=Path, default=default_customers)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--audit", type=Path, default=default_audit)
    args = parser.parse_args(argv)
    try:
        audit = build_from_csv(args.population, args.orders, args.items, args.customers, args.output, args.audit)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"V3-07 feature build failed: {exc}", file=sys.stderr)
        return 2
    print(f"V3-06 population rows: {audit['population_input_rows']:,}")
    print(f"Feature-ready rows: {audit['feature_ready_rows']:,}")
    print(f"Feature-excluded rows: {audit['feature_excluded_rows']:,}")
    print("Exclusive feature exclusions:")
    for reason, count in audit["exclusive_feature_exclusion_counts"].items():
        print(f"  {reason}: {count:,}")
    print(f"Wrote {args.output} and {args.audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
