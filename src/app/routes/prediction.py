from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from fastapi import APIRouter, Depends
from src.app.dependencies import get_prediction_callable
from src.app.errors import InvalidPredictionInput
from src.app.schemas import PREDICTION_NOTICE, PredictionRequest, PredictionResponse
from src.ml.features import FEATURE_NAMES, FeatureInputError, derive_model_features
from src.ml.inference import InferenceArtifactError

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Estimate delivery lateness from order-creation inputs",
    description=(
        "Retrospective academic estimate for the historically eligible delivered-order population. "
        "The request accepts only purchase timestamp, estimated calendar date, customer UF, and item price/freight rows."
    ),
    responses={
        422: {"description": "Invalid prediction request", "content": {"application/json": {"example": {"detail": "Invalid prediction request", "code": "INVALID_INPUT"}}}},
        503: {"description": "Verified selected-model artifacts are unavailable", "content": {"application/json": {"example": {"detail": "Model artifact is unavailable", "code": "MODEL_UNAVAILABLE"}}}},
    },
)
def predict(
    payload: PredictionRequest,
    predictor: Callable[[Mapping[str, Any]], Mapping[str, Any]] = Depends(get_prediction_callable),
) -> PredictionResponse:
    try:
        features = derive_model_features(
            purchase_timestamp=payload.purchase_timestamp,
            estimated_delivery_date=payload.estimated_delivery_date,
            customer_state=payload.customer_state,
            item_rows=[item.model_dump() for item in payload.items],
        )
    except (FeatureInputError, OverflowError) as exc:
        raise InvalidPredictionInput from exc
    if tuple(features) != FEATURE_NAMES:
        raise RuntimeError("Canonical feature function returned an incompatible feature schema")
    for name, value in features.items():
        if name != "customer_state" and (isinstance(value, bool) or not math.isfinite(float(value))):
            raise InvalidPredictionInput

    # predict_one validates the ordered row, verifies manifest/checksum provenance,
    # loads the selected fitted pipeline, and applies the manifest threshold.
    result = predictor(features)
    return PredictionResponse(
        prediction=result["prediction"],
        probability_late=result["probability_late"],
        model_version=result["model_version"],
        notice=PREDICTION_NOTICE,
    )
