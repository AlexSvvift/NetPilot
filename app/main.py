import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import Settings, get_settings
from app.database import create_database, initialize_database
from app.repository import Repository
from app.services.scheduler import monitoring_loop

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    engine, session_factory = create_database(settings.database_url)
    initialize_database(engine)
    repository = Repository(session_factory)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        stop_event = asyncio.Event()
        monitor_task = None
        if settings.monitoring_enabled:
            monitor_task = asyncio.create_task(
                monitoring_loop(repository, settings.scheduler_tick_seconds, stop_event)
            )
        application.state.stop_event = stop_event
        application.state.monitor_task = monitor_task
        yield
        if monitor_task is not None:
            stop_event.set()
            await monitor_task

    application = FastAPI(
        title=settings.app_name,
        description="Мониторинг HTTP, TCP и UDP endpoints.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.repository = repository
    application.state.engine = engine

    origins = settings.cors_origin_list()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router)
    application.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def web_panel():
        return FileResponse(WEB_DIR / "index.html")

    return application


app = create_app()

