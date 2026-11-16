from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.app.dependencies import get_analytics_service, get_template_engine
from src.app.services.analytics import AnalyticsService, DataUnavailable

router = APIRouter(tags=["server-rendered pages"])
PAGE_URLS = {"overview": "/", "sales": "/sales", "delivery": "/delivery", "predict": "/predict"}


def _chart_empty():
    return {"definition_version": "v1", "series": []}


def _page_data(name: str, service: AnalyticsService) -> dict:
    # A page remains useful when only some producer outputs have arrived.
    state = {"data_state": "ready", "message": None}
    def load(call, fallback):
        try:
            return call()
        except DataUnavailable:
            state["data_state"] = "unavailable"
            state["message"] = "Authoritative analytics data is not available yet."
            return fallback
    if name == "overview":
        result = {"period": "all", "kpis": load(lambda: service.summary("all")["kpis"], {})}
    elif name == "sales":
        result = {"period": "all",
                "category_item_value": load(lambda: service.category_item_value("all"), _chart_empty()),
                "category_item_counts": load(service.category_item_counts, _chart_empty()),
                "item_price_distribution": load(service.item_price_distribution, _chart_empty())}
    elif name == "delivery":
        result = {"period": "all", "kpis": load(lambda: service.summary("all")["kpis"], {}),
                "delivery_monthly": load(lambda: service.delivery_monthly("all"), _chart_empty())}
    else:
        result = {"request_schema": {
        "purchase_timestamp": "source-naive YYYY-MM-DDTHH:MM:SS string",
        "estimated_delivery_date": "YYYY-MM-DD string", "customer_state": "Brazilian UF",
        "items": "non-empty array of {price, freight_value} objects"},
        "notice": "Academic demonstration only. Prediction is not implemented in V3-12; no result is available.",
        "result": None, "error": None}
    return {**result, **state}


def _render(request: Request, name: str, service: AnalyticsService, templates: Jinja2Templates):
    payload = _page_data(name, service)
    context = {"request": request, **payload, "page_urls": PAGE_URLS,
               "asset_prefix": "/static", "data_state": payload["data_state"], "message": payload["message"]}
    if name == "sales":
        context["category_item_value"] = payload["category_item_value"]
        context["category_item_counts"] = payload["category_item_counts"]
        context["item_price_distribution"] = payload["item_price_distribution"]
    if name == "delivery":
        context["delivery_monthly"] = payload["delivery_monthly"]
    template_name = request.app.state.page_template_names[name]
    return templates.TemplateResponse(request=request, name=template_name, context=context)


@router.get("/", response_class=HTMLResponse, include_in_schema=True)
def overview(request: Request, service: AnalyticsService = Depends(get_analytics_service), templates: Jinja2Templates = Depends(get_template_engine)):
    return _render(request, "overview", service, templates)


@router.get("/sales", response_class=HTMLResponse)
def sales(request: Request, service: AnalyticsService = Depends(get_analytics_service), templates: Jinja2Templates = Depends(get_template_engine)):
    return _render(request, "sales", service, templates)


@router.get("/delivery", response_class=HTMLResponse)
def delivery(request: Request, service: AnalyticsService = Depends(get_analytics_service), templates: Jinja2Templates = Depends(get_template_engine)):
    return _render(request, "delivery", service, templates)


@router.get("/predict", response_class=HTMLResponse)
def predict(request: Request, service: AnalyticsService = Depends(get_analytics_service), templates: Jinja2Templates = Depends(get_template_engine)):
    return _render(request, "predict", service, templates)
