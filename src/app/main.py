"""V3-12 FastAPI app: authoritative read-only analytics and SSR page seams."""
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.app.dependencies import get_analytics_service, get_template_engine
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from src.app.routes.analytics import router as analytics_router
from src.app.routes.pages import router as pages_router
from src.app.services.analytics import AnalyticsService, DataInvalid, DataUnavailable, InvalidPeriod

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT / "data" / "processed"
FALLBACK_DIR = Path(__file__).resolve().parent / "templates" / "backend_fallback"


def create_app(*, data_directory: Path | None = None, template_directory: Path | None = None, static_directory: Path | None = None) -> FastAPI:
    data_dir = Path(data_directory) if data_directory is not None else DEFAULT_DATA_DIR
    template_dir = Path(template_directory) if template_directory is not None else ROOT / "templates"
    static_dir = Path(static_directory) if static_directory is not None else ROOT / "static"
    app = FastAPI(title="Olist Intelligence Analytics API", version="1.0.0", description="Read-only V3-12 analytics routes. Prediction POST is outside this task.")
    app.state.analytics_service = AnalyticsService(data_dir)
    template_paths = [str(template_dir), str(FALLBACK_DIR)]
    app.state.templates = Jinja2Templates(directory=str(template_dir))
    app.state.templates.env.loader = ChoiceLoader([FileSystemLoader(template_paths)])
    resolved_template_root = template_dir.resolve()
    app.state.page_template_names = {}
    for name in ("overview", "sales", "delivery", "predict"):
        candidate = template_dir / "pages" / f"{name}.html"
        if candidate.is_file() and candidate.resolve().is_relative_to(resolved_template_root):
            app.state.page_template_names[name] = f"pages/{name}.html"
        else:
            app.state.page_template_names[name] = f"{name}.html"

    @app.exception_handler(DataUnavailable)
    async def unavailable_handler(request: Request, exc: DataUnavailable):
        return JSONResponse(status_code=503, content={"detail": "Authoritative analytics source is unavailable", "code": "DATA_UNAVAILABLE"})

    @app.exception_handler(DataInvalid)
    async def invalid_handler(request: Request, exc: DataInvalid):
        return JSONResponse(status_code=500, content={"detail": "Authoritative analytics source is invalid", "code": "DATA_INVALID"})

    @app.exception_handler(InvalidPeriod)
    async def invalid_period_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": "period must be all or a valid YYYY-MM calendar month", "code": "INVALID_PERIOD"})

    @app.get("/health", tags=["health"], summary="Application health; does not indicate model readiness")
    def health():
        return {"status": "ok"}

    app.include_router(pages_router)
    app.include_router(analytics_router)
    if static_dir.is_dir() and not static_dir.is_symlink():
        app.mount("/static", StaticFiles(directory=str(static_dir), follow_symlink=False), name="static")
    return app


app = create_app()
