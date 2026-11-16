from __future__ import annotations

import pytest

from src.ml.features import FEATURE_NAMES
from src.ml.inference import _validate_rows


def _row():
    return {
        "purchase_hour": 10, "purchase_weekday": 3, "purchase_month": 5,
        "promised_lead_days": 22, "customer_state": "SP",
        "item_price_total": 29.9, "freight_total": 10.2, "item_count": 1,
    }


def test_inference_requires_exact_ordered_frozen_fields():
    row = _row()
    frame = _validate_rows([row])
    assert list(frame.columns) == list(FEATURE_NAMES)
    reordered = dict(reversed(list(row.items())))
    with pytest.raises(ValueError, match="contract order"):
        _validate_rows([reordered])
    extra = dict(row, order_id="forbidden")
    with pytest.raises(ValueError, match="contract order"):
        _validate_rows([extra])


@pytest.mark.parametrize("field,value", [("purchase_hour", None), ("purchase_month", True), ("item_count", float("inf")), ("customer_state", "ZZ")])
def test_inference_rejects_missing_or_invalid_values(field, value):
    row = _row()
    row[field] = value
    with pytest.raises(ValueError):
        _validate_rows([row])


@pytest.mark.parametrize(("field", "value"), [("purchase_hour", 24), ("purchase_weekday", 7), ("purchase_month", 0), ("promised_lead_days", -1), ("item_count", 0), ("item_price_total", -0.01)])
def test_inference_rejects_out_of_contract_ranges(field, value):
    row = _row()
    row[field] = value
    with pytest.raises(ValueError):
        _validate_rows([row])
