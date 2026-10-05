from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.backtest import router as backtest_router
from app.api.routes.health import router as health_router
from app.api.routes.market_data import router as market_data_router
from app.api.routes.market_structure import router as market_structure_router
from app.core.config import Settings, get_settings
from app.core.database import SessionFactory
from app.core.logging import configure_logging
from app.services.market_data.scheduler import CandleScheduler


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    configure_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        Path(config.raw_data_path).mkdir(parents=True, exist_ok=True)
        Path(config.parquet_data_path).mkdir(parents=True, exist_ok=True)
        scheduler = CandleScheduler(config, SessionFactory)
        await scheduler.start()
        try:
            yield
        finally:
            # Cancelled rather than awaited to completion: the scheduler sleeps
            # for a minute between ticks, and shutdown should not wait it out.
            await scheduler.stop()

    application = FastAPI(
        title=config.app_name,
        version="0.2.0",
        description=(
            "Research-only BTC/USDT market-data and backtesting infrastructure. "
            "No trading execution."
        ),
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
    application.include_router(market_structure_router)
    application.include_router(backtest_router)
    return application


app = create_app()
