import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_market_data_provider
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import (
    CandlePage,
    CandleResponse,
    IngestionRequest,
    IngestionResultResponse,
    Timeframe,
)
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.ingestion import HistoricalIngestionService
from app.services.market_data.storage import ParquetCandleStore, RawDataStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["market-data"])


def require_utc(value: datetime | None, name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(status_code=422, detail=f"{name} must include a timezone")
    return value.astimezone(UTC)


@router.get("/candles", response_model=CandlePage)
async def get_candles(
    symbol: str = Query("BTCUSDT", pattern=r"^[A-Za-z0-9/]{6,20}$"),
    timeframe: Timeframe = Timeframe.M5,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_db_session),
) -> CandlePage:
    normalized_symbol = symbol.replace("/", "").upper()
    start = require_utc(start, "start")
    end = require_utc(end, "end")
    if start and end and start >= end:
        raise HTTPException(status_code=422, detail="start must be before end")
    candles = await MarketDataRepository(session).list_candles(
        normalized_symbol, timeframe, start, end, limit
    )
    return CandlePage(
        symbol=normalized_symbol,
        timeframe=timeframe,
        count=len(candles),
        candles=[CandleResponse.model_validate(candle) for candle in candles],
    )


@router.post("/market-data/ingest", response_model=list[IngestionResultResponse])
async def ingest_historical_data(
    request: IngestionRequest,
    session: AsyncSession = Depends(get_db_session),
    provider: MarketDataProvider = Depends(get_market_data_provider),
    settings: Settings = Depends(get_settings),
) -> list[IngestionResultResponse]:
    start = require_utc(request.start, "start")
    end = require_utc(request.end, "end")
    assert start is not None and end is not None
    if start >= end:
        raise HTTPException(status_code=422, detail="start must be before end")
    if end - start > timedelta(days=31):
        raise HTTPException(
            status_code=422,
            detail="API ingestion is limited to 31 days; use the CLI for larger backfills",
        )

    service = HistoricalIngestionService(
        session,
        provider,
        RawDataStore(settings.raw_data_path),
        ParquetCandleStore(settings.parquet_data_path),
    )
    results = []
    for timeframe in request.timeframes:
        result = await service.ingest(request.symbol, timeframe, start, end)
        results.append(
            IngestionResultResponse(
                symbol=result.symbol,
                timeframe=result.timeframe,
                fetched=result.fetched,
                stored=result.stored,
                duplicates=result.duplicates,
                missing=result.missing,
                invalid=result.invalid,
                anomalies=result.anomalies,
                passed=result.passed,
                quality_report_id=result.quality_report_id,
                raw_file=str(result.raw_file),
                parquet_files=[str(path) for path in result.parquet_files],
            )
        )
    return results


@router.websocket("/ws/candles/{symbol}/{timeframe}")
async def candle_stream(
    websocket: WebSocket,
    symbol: str,
    timeframe: Timeframe,
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> None:
    await websocket.accept()
    try:
        async for candle in provider.stream_candles(symbol, timeframe):
            await websocket.send_json(candle.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
    except Exception:
        logger.exception(
            "candle stream failed",
            extra={"event": "DATA_STREAM_FAILED", "symbol": symbol, "timeframe": timeframe},
        )
        await websocket.close(code=1011, reason="upstream market-data stream failed")
