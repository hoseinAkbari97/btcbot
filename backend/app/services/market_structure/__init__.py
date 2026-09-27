"""Market structure analysis: swing detection, structural labels, BOS, liquidity levels."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from app.schemas.market_data import CandleData, Timeframe

# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------

EventType = Literal["HH", "HL", "LH", "LL", "BOS", "structure_shift"]


@dataclass(frozen=True)
class SwingPoint:
    """A confirmed local extremum in the price series."""

    index: int
    timestamp: datetime
    price: Decimal
    kind: Literal["high", "low"]


@dataclass(frozen=True)
class StructureEvent:
    """A detected market-structure event (HH/HL/LH/LL/BOS/shift)."""

    timestamp: datetime
    price: Decimal
    event_type: EventType
    source_swing_idx: int | None = None
    confidence: float = 0.0


@dataclass(frozen=True)
class LiquidityLevel:
    """An objective liquidity level derived from swing extrema."""

    price: Decimal
    level_type: Literal[
        "swing_high", "swing_low", "equal_highs", "equal_lows", "range_high", "range_low"
    ]
    strength: float  # 0.0 – 1.0
    first_seen: datetime
    last_seen: datetime
    touch_count: int = 0


@dataclass
class MarketStructureResult:
    """Aggregated output of a single structure analysis pass."""

    symbol: str
    timeframe: Timeframe
    swings: list[SwingPoint] = field(default_factory=list)
    events: list[StructureEvent] = field(default_factory=list)
    liquidity_levels: list[LiquidityLevel] = field(default_factory=list)
    recent_range: tuple[Decimal, Decimal] | None = None
    current_regime: Literal["TREND_UP", "TREND_DOWN", "RANGE", "UNKNOWN"] = "UNKNOWN"
