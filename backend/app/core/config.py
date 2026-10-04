from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.resources import ResourceLimits


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
