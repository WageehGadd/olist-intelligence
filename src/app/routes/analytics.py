from fastapi import APIRouter, Depends, Query

from src.app.dependencies import get_analytics_service
from src.app.schemas import ChartEnvelope, CategoryItemCountRow, CategoryItemValueRow, DeliveryMonthlyRow, ItemPriceBinRow, SummaryResponse
from src.app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/v1", tags=["read-only analytics"])


@router.get("/analytics/summary", response_model=SummaryResponse)
def summary(period: str = Query("all"), service: AnalyticsService = Depends(get_analytics_service)):
    return service.summary(period)


@router.get("/analytics/delivery-monthly", response_model=ChartEnvelope[DeliveryMonthlyRow])
def delivery_monthly(period: str = Query("all"), service: AnalyticsService = Depends(get_analytics_service)):
    return service.delivery_monthly(period)


@router.get("/analytics/category-item-value", response_model=ChartEnvelope[CategoryItemValueRow])
def category_item_value(period: str = Query("all"), service: AnalyticsService = Depends(get_analytics_service)):
    return service.category_item_value(period)


@router.get("/charts/category-item-counts", response_model=ChartEnvelope[CategoryItemCountRow])
def category_item_counts(service: AnalyticsService = Depends(get_analytics_service)):
    return service.category_item_counts()


@router.get("/charts/item-price-distribution", response_model=ChartEnvelope[ItemPriceBinRow])
def item_price_distribution(service: AnalyticsService = Depends(get_analytics_service)):
    return service.item_price_distribution()
