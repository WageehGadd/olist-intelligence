from fastapi import Request
from fastapi.templating import Jinja2Templates
from src.app.services.analytics import AnalyticsService


def get_analytics_service(request: Request) -> AnalyticsService:
    return request.app.state.analytics_service


def get_template_engine(request: Request) -> Jinja2Templates:
    return request.app.state.templates
