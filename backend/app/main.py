from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.market_data import router as market_data_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    configure_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        Path(config.raw_data_path).mkdir(parents=True, exist_ok=True)
        Path(config.parquet_data_path).mkdir(parents=True, exist_ok=True)
        yield

    application = FastAPI(
        title=config.app_name,
        version="0.1.0",
        description="Research-only BTC/USDT market-data infrastructure. No trading execution.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(market_data_router)
    return application


app = create_app()
