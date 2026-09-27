"""Schemas for market structure API endpoints."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SwingKind(str, Enum):
    HIGH = "high"
    LOW = "low"


class StructureEventType(str, Enum):
    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"
    BOS = "BOS"
    STRUCTURE_SHIFT = "structure_shift"


class LiquidityLevelType(str, Enum):
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    EQUAL_HIGHS = "equal_highs"
    EQUAL_LOWS = "equal_lows"
    RANGE_HIGH = "range_high"
    RANGE_LOW = "range_low"


class MarketRegime(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    UNKNOWN = "UNKNOWN"


class SwingPointResponse(BaseModel):
    index: int
    timestamp: datetime
    price: str
    kind: SwingKind


class StructureEventResponse(BaseModel):
    timestamp: datetime
    price: str
    event_type: StructureEventType
    source_swing_idx: int | None = None
    confidence: float


class LiquidityLevelResponse(BaseModel):
    price: str
    level_type: LiquidityLevelType
    strength: float
    first_seen: datetime
    last_seen: datetime
    touch_count: int


class MarketStructureResponse(BaseModel):
    symbol: str
    timeframe: str
    swings: list[SwingPointResponse] = Field(default_factory=list)
    events: list[StructureEventResponse] = Field(default_factory=list)
    liquidity_levels: list[LiquidityLevelResponse] = Field(default_factory=list)
    recent_range_high: str | None = None
    recent_range_low: str | None = None
    current_regime: MarketRegime = MarketRegime.UNKNOWN
