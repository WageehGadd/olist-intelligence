"""Typed response contracts for the read-only V3-12 application."""
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(StrictModel):
    status: str


class KPIValue(StrictModel):
    value: int | float | None
    unit: str
    population: str
    numerator_count: int | None
    denominator_count: int | None
    definition_version: str


class SummaryResponse(StrictModel):
    period: str
    definition_version: str
    kpis: dict[str, KPIValue]


class DeliveryMonthlyRow(StrictModel):
    period: str
    value: int | float | None
    numerator_count: int
    denominator_count: int
    unit: str
    population: str
    definition_version: str


class CategoryItemValueRow(StrictModel):
    period: str
    category_name: str
    item_value_brl: int | float
    definition_version: str


class CategoryItemCountRow(StrictModel):
    category_name: str
    item_count: int
    population: str
    definition_version: str


class ItemPriceBinRow(StrictModel):
    bin_label: str
    bin_lower_brl: int | float
    bin_upper_brl: int | float | None
    item_count: int
    population: str
    definition_version: str


class ChartEnvelope(StrictModel, Generic[T]):
    definition_version: str
    series: list[T]
