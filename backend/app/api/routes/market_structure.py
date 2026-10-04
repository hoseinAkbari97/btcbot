"""Market structure analysis endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_market_data_provider
from app.core.database import get_db_session
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe
from app.schemas.market_structure import (
    LiquidityLevelResponse,
    LiquidityLevelType,
    MarketStructureResponse,
    StructureEventResponse,
    StructureEventType,
    SwingKind,
    SwingPointResponse,
    MarketRegime,
)
from app.services.market_structure.analysis import analyze_market_structure

router = APIRouter(prefix="/api/v1/structure", tags=["market-structure"])


@router.get("/analyze", response_model=MarketStructureResponse)
async def analyze(
    symbol: str = Query("BTCUSDT", pattern=r"^[A-Za-z0-9/]{6,20}$"),
    timeframe: Timeframe = Query(Timeframe.M5),
    limit: int = Query(500, ge=50, le=2000),
    session: AsyncSession = Depends(get_db_session),
) -> MarketStructureResponse:
    """Return market-structure analysis for the most recent candles."""
    normalized_symbol = symbol.replace("/", "").upper()
    candles = await MarketDataRepository(session).list_candles(
        normalized_symbol, timeframe, None, None, limit
    )
    if not candles:
        return MarketStructureResponse(symbol=normalized_symbol, timeframe=timeframe.value)

    result = analyze_market_structure(candles, normalized_symbol, timeframe)

    return MarketStructureResponse(
        symbol=result.symbol,
        timeframe=result.timeframe.value,
        swings=[
            SwingPointResponse(
                index=s.index,
                timestamp=s.timestamp,
                price=str(s.price),
                kind=SwingKind.HIGH if s.kind == "high" else SwingKind.LOW,
                confirmation_index=s.confirmation_index,
                confirmation_time=s.confirmation_time,
            )
            for s in result.swings
        ],
        events=[
            StructureEventResponse(
                index=e.index,
                timestamp=e.timestamp,
                price=str(e.price),
                event_type=StructureEventType(e.event_type),
                source_swing_idx=e.source_swing_idx,
                confirmation_index=e.confirmation_index,
                confirmation_time=e.confirmation_time,
                direction=e.direction,
                broken_level=str(e.broken_level) if e.broken_level is not None else None,
                penetration=str(e.penetration) if e.penetration is not None else None,
                previous_state=e.previous_state,
                new_state=e.new_state,
            )
            for e in result.events
        ],
        liquidity_levels=[
            LiquidityLevelResponse(
                price=str(l.price),
                level_type=LiquidityLevelType(l.level_type),
                strength=l.strength,
                first_seen=l.first_seen,
                last_seen=l.last_seen,
                touch_count=l.touch_count,
                creation_index=l.creation_index,
                creation_time=l.creation_time,
                origin=l.origin,
            )
            for l in result.liquidity_levels
        ],
        recent_range_high=str(result.recent_range[1]) if result.recent_range else None,
        recent_range_low=str(result.recent_range[0]) if result.recent_range else None,
        current_regime=MarketRegime(result.current_regime),
        as_of_index=result.as_of_index,
    )
