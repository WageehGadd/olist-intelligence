"""Build the V3-06 order-grain delivery-delay target population."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd


POPULATION_VERSION = "v1"
SOURCE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_COLUMNS = {
    "order_purchase_timestamp": "purchase_ts",
    "order_estimated_delivery_date": "estimated_delivery_date",
    "order_delivered_customer_date": "delivered_date",
}
REQUIRED_COLUMNS = (
    "order_id",
    "order_status",
    *TIMESTAMP_COLUMNS.keys(),
)
OUTPUT_COLUMNS = (
    "order_id",
    "purchase_ts",
    "estimated_delivery_date",
    "delivered_date",
    "late",
    "population_version",
)
EXCLUSION_REASONS = (
    "not_delivered_or_missing_status",
    "missing_purchase_timestamp",
    "invalid_purchase_timestamp",
    "missing_estimated_delivery_timestamp",
    "invalid_estimated_delivery_timestamp",
    "missing_delivered_customer_timestamp",
    "invalid_delivered_customer_timestamp",
    "estimated_date_before_purchase_date",
    "actual_date_before_purchase_date",
)


def _parse_source_timestamp(values: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Parse source-naive timestamps; report missing and malformed values separately."""
    text = values.astype("string")
    missing = text.isna() | text.str.strip().eq("").fillna(False)
    parsed = pd.to_datetime(
        text,
        format=SOURCE_TIMESTAMP_FORMAT,
        errors="coerce",
    )
    invalid = ~missing & parsed.isna()
    return parsed, missing, invalid


def build_delivery_population(
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return eligible order rows and an exclusive exclusion/audit summary.

    Exclusions are assigned once, in the order listed by ``EXCLUSION_REASONS``.
    A row with multiple problems is counted under its first applicable reason.
    Independent missing/malformed timestamp diagnostics may overlap those reasons.
    Duplicate or missing order IDs are fatal input errors, never silently resolved.
    """
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in orders.columns]
    if missing_columns:
        raise ValueError(
            "Orders input is missing required column(s): " + ", ".join(missing_columns)
        )

    frame = orders.loc[:, REQUIRED_COLUMNS].copy()
    order_ids = frame["order_id"].astype("string")
    missing_ids = order_ids.isna() | order_ids.str.strip().eq("").fillna(False)
    if missing_ids.any():
        row_labels = frame.index[missing_ids].tolist()[:5]
        raise ValueError(
            "Orders input contains missing/blank order_id values at row index label(s) "
            f"{row_labels}"
        )

    duplicate_mask = order_ids.duplicated(keep=False)
    if duplicate_mask.any():
        duplicate_ids = order_ids.loc[duplicate_mask].drop_duplicates().tolist()[:5]
        duplicate_rows = int(duplicate_mask.sum())
        raise ValueError(
            f"Orders input contains {duplicate_rows} rows with duplicate order_id values; "
            f"examples: {duplicate_ids}. Resolve the input source; no rows were deduplicated."
        )

    frame["order_id"] = order_ids
    parsed: dict[str, pd.Series] = {}
    missing_values: dict[str, pd.Series] = {}
    invalid_values: dict[str, pd.Series] = {}
    for source_column in TIMESTAMP_COLUMNS:
        parsed[source_column], missing_values[source_column], invalid_values[source_column] = (
            _parse_source_timestamp(frame[source_column])
        )

    # One non-overlapping primary reason is assigned per excluded source row.
    remaining = pd.Series(True, index=frame.index, dtype=bool)
    exclusion_counts: dict[str, int] = {}

    def exclude(reason: str, condition: pd.Series) -> None:
        nonlocal remaining
        selected = remaining & condition.fillna(False).astype(bool)
        exclusion_counts[reason] = int(selected.sum())
        remaining = remaining & ~selected

    status = frame["order_status"].astype("string")
    exclude("not_delivered_or_missing_status", status.ne("delivered").fillna(True))

    quality_reasons = {
        "order_purchase_timestamp": (
            "missing_purchase_timestamp",
            "invalid_purchase_timestamp",
        ),
        "order_estimated_delivery_date": (
            "missing_estimated_delivery_timestamp",
            "invalid_estimated_delivery_timestamp",
        ),
        "order_delivered_customer_date": (
            "missing_delivered_customer_timestamp",
            "invalid_delivered_customer_timestamp",
        ),
    }
    for source_column, (missing_reason, invalid_reason) in quality_reasons.items():
        exclude(missing_reason, missing_values[source_column])
        exclude(invalid_reason, invalid_values[source_column])

    purchase_days = parsed["order_purchase_timestamp"].dt.normalize()
    estimated_days = parsed["order_estimated_delivery_date"].dt.normalize()
    delivered_days = parsed["order_delivered_customer_date"].dt.normalize()
    exclude(
        "estimated_date_before_purchase_date",
        estimated_days.lt(purchase_days),
    )
    exclude(
        "actual_date_before_purchase_date",
        delivered_days.lt(purchase_days),
    )

    eligible = remaining
    selected_indices = frame.index[eligible]
    late = delivered_days.loc[eligible].gt(estimated_days.loc[eligible]).astype("int8")
    population = pd.DataFrame(
        {
            "order_id": frame.loc[eligible, "order_id"].astype("string"),
            "purchase_ts": parsed["order_purchase_timestamp"]
            .loc[eligible]
            .dt.strftime(SOURCE_TIMESTAMP_FORMAT),
            "estimated_delivery_date": estimated_days.loc[eligible].dt.strftime("%Y-%m-%d"),
            "delivered_date": delivered_days.loc[eligible].dt.strftime("%Y-%m-%d"),
            "late": late,
            "population_version": POPULATION_VERSION,
        },
        index=selected_indices,
    )
    population = (
        population.loc[:, OUTPUT_COLUMNS]
        .sort_values("order_id", kind="mergesort")
        .reset_index(drop=True)
    )

    source_rows = int(len(frame))
    eligible_rows = int(len(population))
    late_rows = int(population["late"].sum())
    on_time_or_early_rows = eligible_rows - late_rows
    audit: dict[str, Any] = {
        "source_rows": source_rows,
        "exclusion_counts": exclusion_counts,
        "excluded_rows": sum(exclusion_counts.values()),
        "eligible_rows": eligible_rows,
        "late_rows": late_rows,
        "on_time_or_early_rows": on_time_or_early_rows,
        "late_prevalence": late_rows / eligible_rows if eligible_rows else None,
        "timestamp_diagnostics": {
            source_column: {
                "missing": int(missing_values[source_column].sum()),
                "invalid_nonmissing": int(invalid_values[source_column].sum()),
            }
            for source_column in TIMESTAMP_COLUMNS
        },
    }

    if tuple(exclusion_counts) != EXCLUSION_REASONS:
        raise AssertionError("Internal exclusion reason ordering differs from the documented contract")
    if audit["excluded_rows"] + eligible_rows != source_rows:
        raise AssertionError("Internal population accounting does not equal source row count")
    if not population["order_id"].is_unique:
        raise AssertionError("Internal error: output order_id is not unique")
    if not population["late"].isin((0, 1)).all():
        raise AssertionError("Internal error: late label is not binary")
    if list(population.columns) != list(OUTPUT_COLUMNS):
        raise AssertionError("Internal error: output schema differs from the frozen contract")

    return population, audit


def default_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "data" / "raw" / "olist_orders_dataset.csv",
        repo_root / "data" / "processed" / "delivery_population.csv",
    )


def build_from_csv(input_path: Path, output_path: Path) -> dict[str, Any]:
    """Load the original orders CSV, build the eligible population, and write output."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Orders CSV not found: {input_path}")
    resolved_input = input_path.resolve()
    resolved_output = output_path.resolve()
    if resolved_input == resolved_output:
        raise ValueError("Output path must differ from the input orders CSV; raw input is protected")
    raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    try:
        resolved_output.relative_to(raw_dir.resolve())
    except ValueError:
        pass
    else:
        raise ValueError(f"Output path must not be inside protected raw-data directory: {raw_dir}")
    try:
        orders = pd.read_csv(
            input_path,
            dtype={"order_id": "string", "order_status": "string"},
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read orders CSV {input_path}: {exc}") from exc

    population, audit = build_delivery_population(orders)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    population.to_csv(output_path, index=False)
    return audit


def _format_count(value: int | None) -> str:
    return "n/a" if value is None else f"{value:,}"


def main(argv: list[str] | None = None) -> int:
    default_input, default_output = default_paths()
    parser = argparse.ArgumentParser(
        description="Build the V3-06 eligible order-grain delivery-delay population."
    )
    parser.add_argument("--input", type=Path, default=default_input, help="source orders CSV")
    parser.add_argument("--output", type=Path, default=default_output, help="generated CSV path")
    args = parser.parse_args(argv)

    try:
        audit = build_from_csv(args.input, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"V3-06 population build failed: {exc}", file=sys.stderr)
        return 2

    print(f"Source rows: {_format_count(audit['source_rows'])}")
    print("Exclusive exclusions:")
    for reason, count in audit["exclusion_counts"].items():
        print(f"  {reason}: {_format_count(count)}")
    print(f"Excluded rows (exclusive total): {_format_count(audit['excluded_rows'])}")
    print(f"Eligible rows: {_format_count(audit['eligible_rows'])}")
    print(f"Late rows: {_format_count(audit['late_rows'])}")
    print(f"On-time/early rows: {_format_count(audit['on_time_or_early_rows'])}")
    prevalence = audit["late_prevalence"]
    print(f"Late prevalence: {prevalence:.8%}" if prevalence is not None else "Late prevalence: n/a")
    print("Timestamp diagnostics (may overlap exclusive exclusions):")
    for column, counts in audit["timestamp_diagnostics"].items():
        print(
            f"  {column}: missing={_format_count(counts['missing'])}, "
            f"invalid_nonmissing={_format_count(counts['invalid_nonmissing'])}"
        )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
