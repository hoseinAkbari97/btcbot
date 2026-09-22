import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import DataQualityReport
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.storage import ParquetCandleStore, RawDataStore
from app.services.market_data.validation import CandleValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
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
    raw_file: Path
    parquet_files: list[Path]


class HistoricalIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        provider: MarketDataProvider,
        raw_store: RawDataStore,
        parquet_store: ParquetCandleStore,
        validator: CandleValidator | None = None,
    ) -> None:
        self.session = session
        self.provider = provider
        self.raw_store = raw_store
        self.parquet_store = parquet_store
        self.validator = validator or CandleValidator()

    async def ingest(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> IngestionResult:
        symbol = symbol.replace("/", "").upper()
        fetched = await self.provider.get_historical_candles(symbol, timeframe, start, end)
        raw_file = self.raw_store.write(
            self.provider.name,
            symbol,
            timeframe,
            fetched.raw_pages,
            fetched.request_metadata,
        )
        closed_candles = [candle for candle in fetched.candles if candle.is_closed]
        validation = self.validator.validate(closed_candles, timeframe)
        parquet_files = self.parquet_store.write(validation.valid_candles)

        repository = MarketDataRepository(self.session)
        provider_url = getattr(self.provider, "rest_base_url", "")
        source, instrument = await repository.ensure_catalog(
            self.provider.name, str(provider_url), symbol
        )
        stored = await repository.upsert_candles(validation.valid_candles, source.id, instrument.id)
        report = DataQualityReport(
            source_id=source.id,
            symbol=symbol,
            timeframe=timeframe.value,
            period_start=min((c.open_time for c in closed_candles), default=None),
            period_end=max((c.open_time for c in closed_candles), default=None),
            row_count=len(closed_candles),
            duplicate_count=validation.duplicate_count,
            missing_count=validation.missing_count,
            invalid_count=validation.invalid_count,
            anomaly_count=validation.anomaly_count,
            passed=validation.passed,
            issues=[issue.as_dict() for issue in validation.issues],
            raw_file=str(raw_file),
            parquet_files=[str(path) for path in parquet_files],
        )
        self.session.add(report)
        await self.session.commit()

        logger.info(
            "historical ingestion completed",
            extra={
                "event": "DATA_INGESTED",
                "symbol": symbol,
                "timeframe": timeframe.value,
            },
        )
        return IngestionResult(
            symbol=symbol,
            timeframe=timeframe,
            fetched=len(fetched.candles),
            stored=stored,
            duplicates=validation.duplicate_count,
            missing=validation.missing_count,
            invalid=validation.invalid_count,
            anomalies=validation.anomaly_count,
            passed=validation.passed,
            quality_report_id=report.id,
            raw_file=raw_file,
            parquet_files=parquet_files,
        )
