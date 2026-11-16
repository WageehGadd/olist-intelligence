"""Verified local selected-model loading and inference shared by API and offline callers."""

from __future__ import annotations

import json
import pickle
import zlib
from numbers import Integral, Real
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd

from src.ml.features import BRAZIL_UFS, FEATURE_NAMES
from src.ml.preprocessing import validate_feature_frame
from src.ml.train_classical import positive_class_probability
from src.ml.train_mlp import DEFAULT_SELECTION_PATH, ROOT, sha256_file, verify_selection


class InferenceArtifactError(RuntimeError):
    """Selected model or metadata is unavailable or incompatible."""


def load_selected_model(selection_path: Path = DEFAULT_SELECTION_PATH) -> tuple[Any, dict[str, Any]]:
    try:
        selection = verify_selection(selection_path)
        artifact = ROOT / selection["selected_artifact_path"]
        model = joblib.load(artifact)
    except FileNotFoundError as exc:
        raise InferenceArtifactError("Selected model artifact is unavailable") from exc
    except (
        OSError, ValueError, KeyError, TypeError, AttributeError, ImportError,
        UnicodeError, json.JSONDecodeError, EOFError, pickle.UnpicklingError, zlib.error,
    ) as exc:
        raise InferenceArtifactError("Selected model artifact is invalid or unavailable") from exc
    if not hasattr(model, "predict_proba") or not hasattr(model, "named_steps"):
        raise InferenceArtifactError("Selected artifact is not a compatible fitted sklearn pipeline")
    if list(selection.get("feature_names_in_order", [])) != list(FEATURE_NAMES):
        raise InferenceArtifactError("Selected artifact feature schema is incompatible")
    if list(getattr(model, "feature_names_in_", [])) != list(FEATURE_NAMES):
        raise InferenceArtifactError("Loaded pipeline was fitted with a different feature schema")
    return model, selection


def _validate_rows(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("Inference batch must be a nonempty list of feature rows")
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or list(row.keys()) != list(FEATURE_NAMES):
            raise ValueError(f"Row {index} must contain exactly the frozen feature keys in contract order")
        for name in FEATURE_NAMES:
            value = row[name]
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Row {index} feature {name} is missing")
            if name == "customer_state":
                if not isinstance(value, str) or value not in BRAZIL_UFS:
                    raise ValueError(f"Row {index} customer_state must be an uppercase Brazilian UF")
            else:
                if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
                    raise ValueError(f"Row {index} feature {name} must be a finite number")
                if name in {"purchase_hour", "purchase_weekday", "purchase_month", "promised_lead_days", "item_count"} and (not isinstance(value, Integral) or isinstance(value, bool)):
                    raise ValueError(f"Row {index} feature {name} must be an integer")
                if name == "purchase_hour" and not 0 <= value <= 23:
                    raise ValueError(f"Row {index} purchase_hour must be between 0 and 23")
                if name == "purchase_weekday" and not 0 <= value <= 6:
                    raise ValueError(f"Row {index} purchase_weekday must be between 0 and 6")
                if name == "purchase_month" and not 1 <= value <= 12:
                    raise ValueError(f"Row {index} purchase_month must be between 1 and 12")
                if name in {"promised_lead_days", "item_count", "item_price_total", "freight_total"} and value < (1 if name == "item_count" else 0):
                    raise ValueError(f"Row {index} feature {name} must be nonnegative (item_count must be positive)")
        normalized.append(dict(row))
    frame = pd.DataFrame(normalized, columns=FEATURE_NAMES)
    validate_feature_frame(frame)
    return frame


def predict_batch(rows: Sequence[Mapping[str, Any]], *, selection_path: Path = DEFAULT_SELECTION_PATH) -> list[dict[str, Any]]:
    frame = _validate_rows(rows)
    model, selection = load_selected_model(selection_path)
    probabilities = positive_class_probability(model, frame)
    threshold = float(selection["selected_threshold"])
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise InferenceArtifactError("Frozen classification threshold is invalid")
    return [{"probability_late": float(probability), "prediction": "late" if probability >= threshold else "on_time", "threshold": threshold, "model_version": selection["selected_artifact_sha256"]} for probability in probabilities]


def predict_one(row: Mapping[str, Any], *, selection_path: Path = DEFAULT_SELECTION_PATH) -> dict[str, Any]:
    return predict_batch([row], selection_path=selection_path)[0]
