from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.resources import ResourceLimits
from app.schemas.market_data import Timeframe


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "BTC Quant Research Platform"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://btcbot:btcbot@localhost:5432/btcbot"
    redis_url: str = "redis://localhost:6379/0"
    market_data_provider: Literal["kraken", "binance"] = "kraken"
    kraken_rest_base_url: str = "https://api.kraken.com"
    kraken_ws_base_url: str = "wss://ws.kraken.com/v2"
    binance_rest_base_url: str = "https://api.binance.com"
    binance_ws_base_url: str = "wss://stream.binance.com:9443/ws"
    raw_data_path: Path = Path("data/raw")
    parquet_data_path: Path = Path("data/parquet")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    #: Memory, disk and segmentation budgets for heavy research jobs. Nested
    #: rather than flattened so the whole budget is one environment variable
    #: (``RESOURCE_LIMITS__SEGMENT_DAYS=90``) and no research module has to grow
    #: its own copy of a limit. The defaults are the project's measured ceiling,
    #: not the machine's: this project gets 6 GB of RAM and 256 GB of SSD, and a
    #: job is stopped at the *warning* threshold rather than at the point where
    #: the machine starts swapping.
    resources: ResourceLimits = Field(default_factory=ResourceLimits)

    # ------------------------------------------------------- candle scheduler
    # Background catch-up so the candle tables track the present instead of
    # freezing at whatever date someone last ran a manual ingest. Off by
    # default in the sense that it must be opted into per environment; on by
    # default in the sense that a deployment which forgets it gets a stale
    # chart, which is the failure this exists to prevent.
    scheduler_enabled: bool = True

    #: How long to wait between catch-up passes. The fastest timeframe is 5m,
    #: so this only sets how stale the data can get between passes, not how
    #: often a bar is stored.
    scheduler_interval_seconds: int = 60

    #: When a timeframe has nothing stored at all, fetch this far back rather
    #: than asking a provider for the whole history on one request.
    scheduler_initial_lookback: timedelta = timedelta(days=3)

    #: Ceiling on one fetch. A process that was down for a month walks forward
    #: through the backlog one window per tick rather than issuing one
    #: enormous request that could time out or blow up memory.
    scheduler_max_catchup: timedelta = timedelta(days=7)

    scheduler_symbol: str = "BTCUSDT"
    scheduler_timeframes: list[Timeframe] = Field(
        default_factory=lambda: [Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
