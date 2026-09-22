from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Timeframe(StrEnum):
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    @property
    def seconds(self) -> int:
        return {
            Timeframe.M5: 300,
            Timeframe.M15: 900,
            Timeframe.H1: 3600,
            Timeframe.H4: 14400,
            Timeframe.D1: 86400,
        }[self]


class CandleData(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    timeframe: Timeframe
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal | None = None
    trade_count: int | None = None
    taker_buy_base_volume: Decimal | None = None
    taker_buy_quote_volume: Decimal | None = None
    is_closed: bool = True

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.replace("/", "").upper()


class CandleResponse(CandleData):
    model_config = ConfigDict(from_attributes=True)


class CandlePage(BaseModel):
    symbol: str
    timeframe: Timeframe
    count: int
    candles: list[CandleResponse]


class IngestionRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframes: list[Timeframe] = Field(
        default_factory=lambda: [
            Timeframe.M5,
            Timeframe.M15,
            Timeframe.H1,
            Timeframe.H4,
            Timeframe.D1,
        ]
    )
    start: datetime
    end: datetime


class IngestionResultResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    fetched: int
    stored: int
    duplicates: int
    missing: int
    invalid: int
    anomalies: int
    passed: bool
    quality_report_id: str
    raw_file: str
    parquet_files: list[str]
