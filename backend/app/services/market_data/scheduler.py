"""Background catch-up for candle data.

The database went stale in production because nothing ever wrote to it on a
schedule: ingestion was reachable only through ``POST /market-data/ingest``, so
the last bars sat at whatever date someone last clicked the button. This module
is the missing writer.

**It does not reuse `HistoricalIngestionService`**, deliberately. That service
is an archival tool: every call writes a raw JSON capture *and* a new
``part-<uuid>.parquet`` file per month. Running it on a loop would create a
permanent second copy of every month that the loop touched, growing without
bound -- unacceptable against a 256 GB SSD budget when the bars already live in
Postgres and are upserted on read. The scheduler fetches, validates and upserts
only. Parquet and raw capture stay the job of the backfill path that is
designed to keep them.

Correctness rests on one property already in the repository:
``upsert_candles`` is an ``ON CONFLICT DO UPDATE`` on
``(instrument, source, timeframe, open_time)``. Re-ingesting a bar that is
already stored therefore updates it in place rather than duplicating it, which
is what makes an overlapping catch-up window safe and makes a retry after a
crash idempotent.
"""

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.database import SessionFactory
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.provider import create_market_data_provider
from app.services.market_data.validation import CandleValidator

logger = logging.getLogger(__name__)


class CandleScheduler:
    """Periodically tops the candle tables up to the present.

    The loop is *catch-up*, not *streaming*. Each tick asks the database where
    the newest bar is and asks the provider for everything after it. That makes
    it self-healing: it does not matter whether the process has been up for ten
    minutes or ten days, because the resume point is read from the data rather
    than remembered in memory. A restart re-reads the same resume point and
    carries on.
    """

    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
        provider: MarketDataProvider | None = None,
    ) -> None:
        self._settings = settings
        self._sessions = session_factory
        self._provider = provider or create_market_data_provider(settings)
        self._validator = CandleValidator()
        self._task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ loop

    async def start(self) -> None:
        if not self._settings.scheduler_enabled:
            logger.info("candle scheduler disabled by configuration")
            return
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="candle-scheduler")
        logger.info(
            "candle scheduler started",
            extra={
                "event": "SCHEDULER_STARTED",
                "interval_seconds": self._settings.scheduler_interval_seconds,
                "symbol": self._settings.scheduler_symbol,
            },
        )

    async def stop(self) -> None:
        task, self._task = self._task, None
        if task is None:
            return
        # Cancel rather than await: the sleep between ticks can be minutes
        # long, and shutdown should not wait it out. The in-flight upsert is
        # already idempotent, so a cancelled tick costs at most one re-fetch.
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        logger.info("candle scheduler stopped")

    async def _run(self) -> None:
        interval = self._settings.scheduler_interval_seconds
        while True:
            try:
                await self.catch_up()
            except asyncio.CancelledError:
                raise
            except Exception:
                # A failing tick must not take the scheduler down with it. The
                # loop's job is to keep the data fresh over days; a single
                # provider blip is expected and the next tick retries from
                # the same read-from-the-database resume point.
                logger.exception(
                    "scheduled ingestion failed; will retry",
                    extra={"event": "SCHEDULER_TICK_FAILED"},
                )
            await asyncio.sleep(interval)

    # -------------------------------------------------------------- catch-up

    async def catch_up(self) -> dict[str, int]:
        """Top every configured timeframe up to now. Returns stored counts."""
        symbol = self._settings.scheduler_symbol
        stored: dict[str, int] = {}
        for timeframe in self._settings.scheduler_timeframes:
            try:
                stored[timeframe.value] = await self._catch_up_one(symbol, timeframe)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "scheduled ingestion failed for timeframe",
                    extra={
                        "event": "SCHEDULER_TICK_FAILED",
                        "timeframe": timeframe.value,
                    },
                )
                stored[timeframe.value] = 0
        return stored

    async def _catch_up_one(self, symbol: str, timeframe: Timeframe) -> int:
        # One session per timeframe: a failure or a long provider call in one
        # must not leave a transaction open against the next.
        async with self._sessions() as session:
            repository = MarketDataRepository(session)
            source, instrument = await repository.ensure_catalog(
                self._provider.name,
                getattr(self._provider, "rest_base_url", ""),
                symbol,
            )
            latest = await repository.latest_open_time(instrument.id, timeframe)
            now = datetime.now(UTC)
            start = self._resume_point(latest, timeframe, now)
            if start >= now:
                return 0

            fetched = await self._provider.get_historical_candles(symbol, timeframe, start, now)
            closed = [candle for candle in fetched.candles if candle.is_closed]
            if not closed:
                return 0
            validation = self._validator.validate(closed, timeframe)
            if not validation.valid_candles:
                logger.warning(
                    "scheduled ingestion produced no valid candles",
                    extra={
                        "event": "SCHEDULER_NO_VALID",
                        "timeframe": timeframe.value,
                        "fetched": len(closed),
                        "invalid": validation.invalid_count,
                    },
                )
                return 0

            count = await repository.upsert_candles(
                validation.valid_candles, source.id, instrument.id
            )
            await session.commit()
            logger.info(
                "scheduled ingestion completed",
                extra={
                    "event": "SCHEDULER_TICK",
                    "timeframe": timeframe.value,
                    "stored": count,
                    "invalid": validation.invalid_count,
                    "anomalies": validation.anomaly_count,
                    "from": start.isoformat(),
                },
            )
            return count

    def _resume_point(
        self, latest: datetime | None, timeframe: Timeframe, now: datetime
    ) -> datetime:
        """Where to start fetching, given what is already stored.

        Two subtleties, both of which have bitten this project before:

        * The overlap. Bars are re-fetched from slightly before the newest
          stored bar so that a bar which was still forming when the previous
          tick ran is re-read with its final values. Without it, the last bar
          of every tick would be frozen at whatever partial state it had.
          Re-upserting is harmless because the write is an upsert.
        * A brand-new table. With nothing stored there is no anchor, so it
          starts at the configured lookback rather than at the epoch. Asking a
          provider for the whole history on a cold database is the one request
          shape that can actually fail or hang.
        """
        overlap = timedelta(seconds=timeframe.seconds * 2)
        if latest is None:
            return now - self._settings.scheduler_initial_lookback
        resume = latest - overlap
        # Never ask for more than the catch-up window. If the process was down
        # for a month, the first ticks walk forward through the backlog a
        # window at a time instead of issuing one enormous request.
        floor = now - self._settings.scheduler_max_catchup
        return max(resume, floor)