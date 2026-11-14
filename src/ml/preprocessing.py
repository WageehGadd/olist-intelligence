"""Train-only preprocessing contract for V3 delivery features."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.ml.features import FEATURE_NAMES


NUMERIC_FEATURES = (
    "purchase_hour",
    "purchase_weekday",
    "purchase_month",
    "promised_lead_days",
    "item_price_total",
    "freight_total",
    "item_count",
)
CATEGORICAL_FEATURES = ("customer_state",)


def make_preprocessor() -> ColumnTransformer:
    """Create a fresh, unfitted transformer; callers fit it on training rows only."""
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, list(NUMERIC_FEATURES)),
            ("categorical", categorical, list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def validate_feature_frame(frame: pd.DataFrame) -> None:
    """Reject metadata, leakage fields, missing features, or reordered columns."""
    if list(frame.columns) != list(FEATURE_NAMES):
        raise ValueError(
            "Preprocessor input must contain exactly the eight Shared Contracts v1 "
            f"features in order: {', '.join(FEATURE_NAMES)}"
        )
    if frame.empty:
        raise ValueError("Cannot fit preprocessing on an empty feature frame")
