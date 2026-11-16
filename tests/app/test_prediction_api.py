"""V3-13 prediction tests use clearly synthetic inputs and local test doubles only."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.app.main import create_app
from src.ml.features import FEATURE_NAMES, FeatureInputError, derive_model_features
from src.ml.inference import InferenceArtifactError

SYNTHETIC_SHA = "a" * 64
FROZEN_THRESHOLD = 0.03604282618179219


def valid_payload(*, item_count: int = 1, state: str = "SP") -> dict:
    return {
        "purchase_timestamp": "2018-05-07T12:30:00",
        "estimated_delivery_date": "2018-05-09",
        "customer_state": state,
        "items": [{"price": 29.9, "freight_value": 10.2} for _ in range(item_count)],
    }


class _PositiveClassFirstClassifier:
    # Deliberately reverse the conventional order to verify label-1 probability selection.
    classes_ = np.asarray([1, 0])


class _SyntheticPipeline:
    feature_names_in_ = np.asarray(FEATURE_NAMES)
    named_steps = {"classifier": _PositiveClassFirstClassifier()}

    def predict_proba(self, frame):
        probability = frame["item_count"].map({1: 0.62, 2: 0.02, 3: FROZEN_THRESHOLD}).to_numpy(dtype=float)
        return np.column_stack((probability, 1.0 - probability))


def _app(predictor=None):
    return create_app(prediction_callable=predictor)


def test_valid_single_and_multi_item_requests_use_canonical_features_and_project_exact_response(monkeypatch):
    import src.ml.inference as inference

    selected_pipeline = _SyntheticPipeline()
    selection = {"selected_threshold": FROZEN_THRESHOLD, "selected_artifact_sha256": SYNTHETIC_SHA}
    monkeypatch.setattr(inference, "load_selected_model", lambda selection_path=None: (selected_pipeline, selection))
    received = []

    def predictor(row):
        received.append(dict(row))
        return inference.predict_one(row)

    client = TestClient(_app(predictor))
    single = valid_payload()
    late = client.post("/api/v1/predict", json=single)
    assert late.status_code == 200
    late_data = late.json()
    assert set(late_data) == {"prediction", "probability_late", "model_version", "notice"}
    assert late_data["prediction"] == "late"
    assert late_data["probability_late"] == pytest.approx(0.62)
    assert late_data["model_version"] == SYNTHETIC_SHA
    assert "retrospective academic estimate" in late_data["notice"].lower()
    assert "eligible delivered orders" in late_data["notice"]
    assert "live all-order predictions" in late_data["notice"]
    assert "calibration has not been established" in late_data["notice"]
    assert "threshold" not in late_data

    multiple = valid_payload(item_count=2, state="PR")
    on_time = client.post("/api/v1/predict", json=multiple)
    assert on_time.status_code == 200
    assert on_time.json()["prediction"] == "on_time"
    assert on_time.json()["probability_late"] == pytest.approx(0.02)
    assert received[1]["customer_state"] == "PR"

    threshold_case = valid_payload(item_count=3)
    at_threshold = client.post("/api/v1/predict", json=threshold_case)
    assert at_threshold.status_code == 200
    assert at_threshold.json()["prediction"] == "late"
    assert at_threshold.json()["probability_late"] == FROZEN_THRESHOLD

    for payload, actual in zip((single, multiple), received):
        expected = derive_model_features(
            payload["purchase_timestamp"], payload["estimated_delivery_date"],
            payload["customer_state"], payload["items"],
        )
        assert tuple(actual) == FEATURE_NAMES
        assert actual == expected
    assert received[0]["purchase_weekday"] == 0  # Monday=0
    assert received[0]["promised_lead_days"] == 2  # calendar-day difference
    assert received[0]["item_price_total"] == pytest.approx(29.9)
    assert received[1]["item_price_total"] == pytest.approx(59.8)
    assert received[1]["freight_total"] == pytest.approx(20.4)
    assert received[1]["item_count"] == 2


def _invalid_response(client, payload):
    try:
        response = client.post("/api/v1/predict", json=payload)
    except ValueError:
        # HTTPX correctly refuses to encode NaN/Infinity via its json= helper;
        # Python's JSON decoder accepts these extensions, which Pydantic must reject.
        response = client.post("/api/v1/predict", content=json.dumps(payload, allow_nan=True), headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid prediction request", "code": "INVALID_INPUT"}


@pytest.mark.parametrize("field", ["purchase_timestamp", "estimated_delivery_date", "customer_state", "items"])
def test_missing_top_level_fields_return_frozen_invalid_input(field):
    payload = valid_payload()
    del payload[field]
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


def test_extra_top_level_field_is_rejected():
    payload = valid_payload()
    payload["order_id"] = "forbidden"
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


@pytest.mark.parametrize("items", [[], {}, None, "not-an-array", [None], [{"price": 1}], [{"price": 1, "freight_value": 1, "product_id": "forbidden"}]])
def test_invalid_item_container_or_shape_is_rejected(items):
    payload = valid_payload()
    payload["items"] = items
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


@pytest.mark.parametrize("amount", [True, False, "1.25", None, -0.01, float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("field", ["price", "freight_value"])
def test_invalid_amount_types_ranges_and_nonfinite_values_are_rejected(field, amount):
    payload = valid_payload()
    payload["items"][0][field] = amount
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


@pytest.mark.parametrize("state", ["sp", " SP", "SP ", "XX", "", None, 12])
def test_invalid_state_is_rejected(state):
    payload = valid_payload()
    payload["customer_state"] = state
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


@pytest.mark.parametrize("timestamp", [
    "2018-05-07T12:30:00Z", "2018-05-07T12:30:00+00:00", "2018-05-07T12:30:00.000",
    "2018-05-07 12:30:00", "2018-05-07T12:30", "2018-02-30T12:30:00", 123, None,
])
def test_malformed_or_unsupported_purchase_timestamp_is_rejected(timestamp):
    payload = valid_payload()
    payload["purchase_timestamp"] = timestamp
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


@pytest.mark.parametrize("estimated", ["2018-02-30", "2018-05-09T00:00:00", "2018-05-09Z", "2018-05-06", 20180509, None])
def test_malformed_estimated_date_and_pre_purchase_date_are_rejected(estimated):
    payload = valid_payload()
    payload["estimated_delivery_date"] = estimated
    _invalid_response(TestClient(_app(lambda row: pytest.fail("invalid request reached inference"))), payload)


def test_wrong_json_top_level_types_are_rejected():
    client = TestClient(_app(lambda row: pytest.fail("invalid request reached inference")))
    for payload in (None, [], "not-an-object", 42):
        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_INPUT"


def test_aggregate_float_overflow_is_rejected_before_inference():
    payload = valid_payload(item_count=2)
    payload["items"] = [{"price": 1.7e308, "freight_value": 1.0}, {"price": 1.7e308, "freight_value": 1.0}]
    _invalid_response(TestClient(_app(lambda row: pytest.fail("overflow request reached inference"))), payload)


def test_feature_input_error_is_translated_without_leaking_details(monkeypatch):
    import src.app.routes.prediction as prediction_route
    monkeypatch.setattr(prediction_route, "derive_model_features", lambda **kwargs: (_ for _ in ()).throw(FeatureInputError("internal", "private parser detail")))
    response = TestClient(_app(lambda row: pytest.fail("feature error reached inference"))).post("/api/v1/predict", json=valid_payload())
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid prediction request", "code": "INVALID_INPUT"}
    assert "private parser detail" not in response.text


def test_model_artifact_failure_is_safe_503_and_unexpected_failure_stays_500():
    def unavailable(row):
        raise InferenceArtifactError("/private/path/model.joblib checksum mismatch")
    client = TestClient(_app(unavailable))
    response = client.post("/api/v1/predict", json=valid_payload())
    assert response.status_code == 503
    assert response.json() == {"detail": "Model artifact is unavailable", "code": "MODEL_UNAVAILABLE"}
    assert "/private" not in response.text and ".joblib" not in response.text

    def broken_code(row):
        raise RuntimeError("unexpected programming error")
    failing_client = TestClient(_app(broken_code), raise_server_exceptions=False)
    failure = failing_client.post("/api/v1/predict", json=valid_payload())
    assert failure.status_code == 500
    assert failure.text == "Internal Server Error"
    assert "MODEL_UNAVAILABLE" not in failure.text


def test_openapi_prediction_schema_and_v3_12_regression_routes():
    client = TestClient(_app(lambda row: pytest.fail("no prediction requested")))
    schema = client.get("/openapi.json").json()
    assert "/api/v1/predict" in schema["paths"]
    operation = schema["paths"]["/api/v1/predict"]["post"]
    body_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    if "$ref" in body_schema:
        body_schema = schema["components"]["schemas"][body_schema["$ref"].split("/")[-1]]
    assert set(body_schema["properties"]) == {"purchase_timestamp", "estimated_delivery_date", "customer_state", "items"}
    assert "PR" in body_schema["properties"]["customer_state"]["enum"]
    response_schema = schema["components"]["schemas"]["PredictionResponse"]
    assert set(response_schema["properties"]) == {"prediction", "probability_late", "model_version", "notice"}
    assert set(operation["responses"]) >= {"200", "422", "503"}

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/predict").status_code == 200
    assert client.get("/api/v1/analytics/summary?period=2024-13").json()["code"] == "INVALID_PERIOD"
    paths = schema["paths"]
    for route in ("/", "/sales", "/delivery", "/predict", "/api/v1/analytics/summary",
                  "/api/v1/analytics/delivery-monthly", "/api/v1/analytics/category-item-value",
                  "/api/v1/charts/category-item-counts", "/api/v1/charts/item-price-distribution"):
        assert route in paths


def test_prediction_page_context_has_exact_schema_and_academic_notice():
    client = TestClient(_app(lambda row: pytest.fail("no prediction requested")))
    response = client.get("/predict")
    assert response.status_code == 200
    assert "purchase_timestamp" in response.text and "PR" in response.text
    assert "eligible delivered orders" in response.text
    assert "MODEL_UNAVAILABLE" in response.text


def test_loader_maps_missing_manifest_to_artifact_error(tmp_path):
    from src.ml.inference import load_selected_model
    with pytest.raises(InferenceArtifactError):
        load_selected_model(tmp_path / "missing-selection.json")


def test_loader_maps_missing_selected_artifact_to_artifact_error(tmp_path, monkeypatch):
    import src.ml.inference as inference
    selection = {"selected_artifact_path": "models/local/missing.joblib", "feature_names_in_order": list(FEATURE_NAMES)}
    monkeypatch.setattr(inference, "ROOT", tmp_path)
    monkeypatch.setattr(inference, "verify_selection", lambda path: selection)
    with pytest.raises(InferenceArtifactError):
        inference.load_selected_model(tmp_path / "selection.json")


def test_loader_maps_real_manifest_checksum_mismatch_to_artifact_error(tmp_path, monkeypatch):
    import src.ml.inference as inference
    import src.ml.train_mlp as training
    root = tmp_path
    artifact = root / "models/local/synthetic.joblib"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"synthetic test bytes; never deserialized")
    manifest = root / "selection.json"
    manifest.write_text(json.dumps({
        "manifest_version": "v1", "feature_names_in_order": list(FEATURE_NAMES),
        "test_evaluated": False, "selected_artifact_path": "models/local/synthetic.joblib",
        "selected_artifact_sha256": "0" * 64,
    }), encoding="utf-8")
    monkeypatch.setattr(training, "ROOT", root)
    monkeypatch.setattr(inference, "verify_selection", training.verify_selection)
    with pytest.raises(InferenceArtifactError):
        inference.load_selected_model(manifest)


def test_loader_rejects_incompatible_artifact_without_fallback(tmp_path, monkeypatch):
    import src.ml.inference as inference
    selection = {"selected_artifact_path": "models/local/incompatible.joblib", "feature_names_in_order": list(FEATURE_NAMES)}
    monkeypatch.setattr(inference, "ROOT", tmp_path)
    monkeypatch.setattr(inference, "verify_selection", lambda path: selection)
    monkeypatch.setattr(inference.joblib, "load", lambda path: object())
    with pytest.raises(InferenceArtifactError, match="compatible"):
        inference.load_selected_model(tmp_path / "selection.json")


def test_loader_accepts_a_synthetic_fitted_pipeline(tmp_path, monkeypatch):
    import joblib
    import src.ml.inference as inference
    from src.ml.preprocessing import make_preprocessor

    frame = pd.DataFrame({
        "purchase_hour": [1, 2, 3, 4, 5, 6, 7, 8],
        "purchase_weekday": [0, 1, 2, 3, 4, 5, 6, 0],
        "purchase_month": [1, 2, 3, 4, 5, 6, 7, 8],
        "promised_lead_days": [1, 2, 3, 4, 5, 6, 7, 8],
        "customer_state": ["SP", "PR"] * 4,
        "item_price_total": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
        "freight_total": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "item_count": [1, 2, 1, 2, 1, 2, 1, 2],
    }, columns=FEATURE_NAMES)
    labels = np.asarray([0, 1, 0, 1, 0, 1, 0, 1])
    pipeline = Pipeline([("preprocessor", make_preprocessor()), ("classifier", LogisticRegression(random_state=7))])
    pipeline.fit(frame, labels)
    artifact = tmp_path / "models/local/synthetic-pipeline.joblib"
    artifact.parent.mkdir(parents=True)
    joblib.dump(pipeline, artifact)
    selection = {"selected_artifact_path": "models/local/synthetic-pipeline.joblib", "feature_names_in_order": list(FEATURE_NAMES)}
    monkeypatch.setattr(inference, "ROOT", tmp_path)
    monkeypatch.setattr(inference, "verify_selection", lambda path: selection)
    loaded, metadata = inference.load_selected_model(tmp_path / "selection.json")
    assert list(loaded.feature_names_in_) == list(FEATURE_NAMES)
    assert metadata["selected_artifact_path"] == selection["selected_artifact_path"]
    assert loaded.predict_proba(frame[:1]).shape == (1, 2)
