"""Strict, read-only mapping of authoritative producer CSVs to API data."""
from __future__ import annotations

import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


class DataUnavailable(Exception):
    pass


class DataInvalid(Exception):
    pass


class InvalidPeriod(ValueError):
    pass


KPI_HEADER = ["kpi_name", "period", "value", "unit", "population", "numerator_count", "denominator_count", "definition_version"]
CATEGORY_HEADER = ["period", "category_name", "item_value_brl", "definition_version"]
COUNT_HEADER = ["category_name", "item_count", "population", "definition_version"]
PRICE_HEADER = ["bin_label", "bin_lower_brl", "bin_upper_brl", "item_count", "population", "definition_version"]
CANONICAL_KPIS = {"orders_total", "customers_unique", "delivered_orders", "item_value_delivered", "freight_charged_delivered", "delivered_item_value_plus_freight", "category_item_value", "delay_rate_calendar", "eligible_late_orders"}
COUNT_KPIS = {"orders_total", "customers_unique", "delivered_orders", "eligible_late_orders"}
PERIOD_RE = re.compile(r"^(?:all|[0-9]{4}-(?:0[1-9]|1[0-2]))$")
PRICE_BINS = [("0-25", Decimal("0"), Decimal("25")), ("25-50", Decimal("25"), Decimal("50")), ("50-100", Decimal("50"), Decimal("100")), ("100-250", Decimal("100"), Decimal("250")), ("250-500", Decimal("250"), Decimal("500")), ("500+", Decimal("500"), None)]


def validate_period(value: str) -> str:
    if not isinstance(value, str) or not PERIOD_RE.fullmatch(value):
        raise InvalidPeriod("period must be all or a valid YYYY-MM calendar month")
    if value != "all":
        try:
            date.fromisoformat(value + "-01")
        except ValueError as exc:
            raise InvalidPeriod("period must be all or a valid YYYY-MM calendar month") from exc
    return value


def _read(path: Path, expected: list[str]) -> list[dict[str, str]]:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise DataUnavailable from exc
    except OSError as exc:
        raise DataInvalid from exc
    try:
        with handle:
            reader = csv.reader(handle, strict=True)
            try:
                header = next(reader)
            except StopIteration as exc:
                raise DataInvalid from exc
            if header != expected:
                raise DataInvalid
            rows: list[dict[str, str]] = []
            for fields in reader:
                if len(fields) != len(expected):
                    raise DataInvalid
                rows.append(dict(zip(expected, fields)))
            return rows
    except (csv.Error, UnicodeError, OSError) as exc:
        raise DataInvalid from exc


def _decimal(raw: str, *, nullable: bool = False, nonnegative: bool = False) -> int | float | None:
    if raw == "" and nullable:
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise DataInvalid from exc
    if not value.is_finite() or (nonnegative and value < 0):
        raise DataInvalid
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _integer(raw: str, *, nullable: bool = False) -> int | None:
    number = _decimal(raw, nullable=nullable, nonnegative=True)
    if number is None:
        return None
    if not isinstance(number, int):
        raise DataInvalid
    return number


def _period(raw: str) -> str:
    try:
        return validate_period(raw)
    except ValueError as exc:
        raise DataInvalid from exc


def _version(raw: str) -> None:
    if raw != "v1":
        raise DataInvalid


def _text(raw: str) -> str:
    if not raw.strip():
        raise DataInvalid
    return raw


class AnalyticsService:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def summary(self, period: str) -> dict:
        period = validate_period(period)
        rows = _read(self.data_dir / "sql_kpis.csv", KPI_HEADER)
        result: dict[str, dict] = {}
        seen: set[tuple[str, str]] = set()
        for row in rows:
            name, row_period = _text(row["kpi_name"]), _period(row["period"])
            key = (name, row_period)
            if key in seen or name not in CANONICAL_KPIS:
                raise DataInvalid
            seen.add(key)
            _version(row["definition_version"])
            unit, population = _text(row["unit"]), _text(row["population"])
            rate = name == "delay_rate_calendar"
            value = _decimal(row["value"], nullable=rate, nonnegative=True)
            numerator = _integer(row["numerator_count"], nullable=not rate)
            denominator = _integer(row["denominator_count"], nullable=not rate)
            if rate:
                if unit != "fraction" or population != "eligible delivered orders" or numerator is None or denominator is None:
                    raise DataInvalid
                if denominator == 0:
                    if value is not None or numerator != 0:
                        raise DataInvalid
                elif value is None or not 0 <= value <= 1 or numerator > denominator:
                    raise DataInvalid
            elif numerator is not None or denominator is not None or value is None or (name in COUNT_KPIS and not isinstance(value, int)):
                raise DataInvalid
            if (period == "all" and row_period != "all") or (period != "all" and row_period != period):
                continue
            result[name] = {"value": value, "unit": unit, "population": population, "numerator_count": numerator, "denominator_count": denominator, "definition_version": "v1"}
        return {"period": period, "definition_version": "v1", "kpis": result}

    def delivery_monthly(self, period: str) -> dict:
        period = validate_period(period)
        # Validate the complete authoritative source before projecting its rate series.
        self.summary(period)
        rows = _read(self.data_dir / "sql_kpis.csv", KPI_HEADER)
        series = []
        seen: set[str] = set()
        for row in rows:
            if row["kpi_name"] != "delay_rate_calendar":
                continue
            month = _period(row["period"])
            if month == "all":
                continue
            if month in seen:
                raise DataInvalid
            seen.add(month)
            if period != "all" and month != period:
                continue
            _version(row["definition_version"])
            if row["unit"] != "fraction" or row["population"] != "eligible delivered orders":
                raise DataInvalid
            numerator = _integer(row["numerator_count"])
            denominator = _integer(row["denominator_count"])
            value = _decimal(row["value"], nullable=True)
            if numerator is None or denominator is None or (denominator == 0 and (value is not None or numerator != 0)) or (denominator > 0 and (value is None or not 0 <= value <= 1 or numerator > denominator)):
                raise DataInvalid
            series.append({"period": month, "value": value, "numerator_count": numerator, "denominator_count": denominator, "unit": row["unit"], "population": row["population"], "definition_version": "v1"})
        return {"definition_version": "v1", "series": sorted(series, key=lambda item: item["period"])}

    def category_item_value(self, period: str) -> dict:
        period = validate_period(period)
        rows = _read(self.data_dir / "sql_category_item_value.csv", CATEGORY_HEADER)
        series, seen = [], set()
        for row in rows:
            row_period = _period(row["period"])
            category = _text(row["category_name"])
            key = (row_period, category)
            if key in seen:
                raise DataInvalid
            seen.add(key)
            _version(row["definition_version"])
            value = _decimal(row["item_value_brl"], nonnegative=True)
            if period != "all" and row_period != period:
                continue
            series.append({"period": row_period, "category_name": category, "item_value_brl": value, "definition_version": "v1"})
        return {"definition_version": "v1", "series": series}

    def category_item_counts(self) -> dict:
        rows = _read(self.data_dir / "eda_category_item_counts.csv", COUNT_HEADER)
        series, seen = [], set()
        for row in rows:
            category = _text(row["category_name"])
            count = _integer(row["item_count"])
            _version(row["definition_version"])
            if category in seen or row["population"] != "delivered_order_items" or count is None:
                raise DataInvalid
            seen.add(category)
            series.append({"category_name": category, "item_count": count, "population": row["population"], "definition_version": "v1"})
        if series != sorted(series, key=lambda item: (-item["item_count"], item["category_name"])):
            raise DataInvalid
        return {"definition_version": "v1", "series": series}

    def item_price_distribution(self) -> dict:
        rows = _read(self.data_dir / "eda_item_price_distribution.csv", PRICE_HEADER)
        if len(rows) != len(PRICE_BINS):
            raise DataInvalid
        series = []
        for row, (label, lower, upper) in zip(rows, PRICE_BINS):
            _version(row["definition_version"])
            if row["bin_label"] != label or row["population"] != "all_items_finite_nonnegative_price":
                raise DataInvalid
            got_lower = _decimal(row["bin_lower_brl"], nonnegative=True)
            got_upper = _decimal(row["bin_upper_brl"], nullable=True, nonnegative=True)
            count = _integer(row["item_count"])
            if Decimal(str(got_lower)) != lower or ((upper is None) != (got_upper is None)) or (upper is not None and Decimal(str(got_upper)) != upper) or count is None:
                raise DataInvalid
            series.append({"bin_label": label, "bin_lower_brl": got_lower, "bin_upper_brl": got_upper, "item_count": count, "population": row["population"], "definition_version": "v1"})
        return {"definition_version": "v1", "series": series}
