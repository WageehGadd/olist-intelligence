"""Typed response and request contracts for the Olist FastAPI application."""
from datetime import date
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator

from src.ml.features import BRAZIL_UFS, FeatureInputError, parse_purchase_timestamp

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


CUSTOMER_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)
assert set(CUSTOMER_STATES) == set(BRAZIL_UFS)


class PredictionItem(BaseModel):
    """Exactly one synthetic or real item-grain request row."""

    model_config = ConfigDict(extra="forbid", strict=True)

    price: float = Field(ge=0, allow_inf_nan=False)
    freight_value: float = Field(ge=0, allow_inf_nan=False)


class PredictionRequest(BaseModel):
    """Strict V3-13 prediction inputs; no identifiers or outcome fields."""

    model_config = ConfigDict(extra="forbid", strict=True)

    purchase_timestamp: StrictStr = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
    estimated_delivery_date: StrictStr = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    customer_state: Literal[
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
        "MG", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    ]
    items: list[PredictionItem] = Field(min_length=1)

    @field_validator("purchase_timestamp")
    @classmethod
    def validate_purchase_timestamp(cls, value: str) -> str:
        try:
            parse_purchase_timestamp(value)
        except FeatureInputError as exc:
            raise ValueError("purchase_timestamp must be a real source-naive YYYY-MM-DDTHH:MM:SS") from exc
        return value

    @field_validator("estimated_delivery_date")
    @classmethod
    def validate_estimated_delivery_date(cls, value: str) -> str:
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("estimated_delivery_date must be a real YYYY-MM-DD calendar date") from exc
        if parsed.isoformat() != value:
            raise ValueError("estimated_delivery_date must be canonical YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def validate_date_order(self):
        purchase_date = parse_purchase_timestamp(self.purchase_timestamp).date()
        if date.fromisoformat(self.estimated_delivery_date) < purchase_date:
            raise ValueError("estimated_delivery_date cannot precede the purchase calendar date")
        return self


class PredictionResponse(StrictModel):
    prediction: Literal["late", "on_time"]
    probability_late: float = Field(ge=0, le=1, allow_inf_nan=False)
    model_version: str = Field(min_length=1)
    notice: str = Field(min_length=1)


PREDICTION_NOTICE = (
    "Retrospective academic estimate conditional on historically eligible delivered orders. "
    "It is not validated for live all-order predictions, and probability calibration has not been established."
)
