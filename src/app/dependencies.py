from fastapi import Request
from fastapi.templating import Jinja2Templates
from src.app.services.analytics import AnalyticsService


def get_analytics_service(request: Request) -> AnalyticsService:
    return request.app.state.analytics_service


def get_template_engine(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def predict_with_selected_model(feature_row):
    """Load and verify the frozen selected pipeline through the V3-09 interface."""
    from src.ml.inference import predict_one
    return predict_one(feature_row)


def get_prediction_callable(request: Request):
    return request.app.state.prediction_callable
