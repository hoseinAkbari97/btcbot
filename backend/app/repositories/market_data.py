from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import Candle, DataSource, Instrument, Market
from app.schemas.market_data import CandleData, Timeframe


#: PostgreSQL caps a single statement at 32767 bind parameters (protocol limit,
#: not a configuration choice). A multi-week backfill is a few thousand rows and
#: exceeds it, and asyncpg reports only "the number of query arguments cannot
#: exceed 32767" with no hint that the batch size is the cause.
#:
#: The cost per row is *measured*, not derived from the column count: compiling
#: one 16-column candle insert binds 17 parameters, so dividing the limit by the
#: column count overshoots by a row and lands just over the cap. One spare is
#: carried as headroom on top of the measured figure.
_MAX_BIND_PARAMS = 32_767
_PARAMS_PER_ROW = 18


class MarketDataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_catalog(
        self, provider_name: str, provider_url: str, symbol: str
    ) -> tuple[DataSource, Instrument]:
        source = await self.session.scalar(
            select(DataSource).where(DataSource.name == provider_name)
        )
        if source is None:
            source = DataSource(
                name=provider_name,
                provider_type="exchange",
                base_url=provider_url,
                metadata_json={"market_data_only": True},
            )
            self.session.add(source)

        market = await self.session.scalar(select(Market).where(Market.name == "binance_spot"))
        if market is None:
            market = Market(name="binance_spot", venue="Binance", market_type="spot")
            self.session.add(market)
            await self.session.flush()

        instrument = await self.session.scalar(
            select(Instrument).where(Instrument.market_id == market.id, Instrument.symbol == symbol)
        )
        if instrument is None:
            base_asset, quote_asset = self._split_symbol(symbol)
            instrument = Instrument(
                market_id=market.id,
                symbol=symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
            )
            self.session.add(instrument)
        await self.session.flush()
        return source, instrument

    async def upsert_candles(
        self,
        candles: list[CandleData],
        source_id: str,
        instrument_id: str,
    ) -> int:
        if not candles:
            return 0
        rows = [
            {
                "instrument_id": instrument_id,
                "source_id": source_id,
                **candle.model_dump(mode="python"),
                "timeframe": candle.timeframe.value,
            }
            for candle in candles
        ]
        # Chunked rather than one statement: a single INSERT this large exceeds
        # the protocol's 32767 bind-parameter ceiling, and the driver reports
        # that as an InterfaceError with no mention of batch size. Each chunk is
        # an independent upsert, so a partial failure leaves a prefix written --
        # and re-running is safe, since re-upserting is a no-op.
        chunk_size = max(1, _MAX_BIND_PARAMS // _PARAMS_PER_ROW)
        dialect = self.session.bind.dialect.name if self.session.bind else "postgresql"
        insert = sqlite_insert(Candle) if dialect == "sqlite" else postgres_insert(Candle)

        # A fresh statement per chunk, not one statement built up with repeated
        # .values() calls: SQLAlchemy's .values() is additive, so accumulating
        # chunks onto a single statement re-binds every earlier row each time
        # and the final execute still carries the whole set -- which is the
        # original limit, unchanged, just spread over more statements.
        conflict = {
            column: insert.excluded[column]
            for column in (
                "close_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "quote_volume",
                "trade_count",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "is_closed",
            )
        }
        for start in range(0, len(rows), chunk_size):
            statement = insert.values(rows[start : start + chunk_size]).on_conflict_do_update(
                index_elements=["instrument_id", "source_id", "timeframe", "open_time"],
                set_=conflict,
            )
            await self.session.execute(statement)
        return len(rows)

    async def latest_open_time(
        self, instrument_id: str, timeframe: Timeframe
    ) -> datetime | None:
        """Newest stored bar for this instrument and timeframe, or None if empty.

        The scheduled ingestion path reads its resume point from here rather
        than remembering it in memory, which is what makes the job restartable:
        a fresh process re-reads the same answer and carries on. Filtering on
        ``instrument_id`` rather than the denormalized ``symbol`` column matters
        once more than one instrument exists, since ``symbol`` alone cannot
        distinguish the same ticker across venues.
        """
        return await self.session.scalar(
            select(func.max(Candle.open_time)).where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == timeframe.value,
            )
        )

    async def list_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[Candle]:
        query: Select[tuple[Candle]] = select(Candle).where(
            Candle.symbol == symbol, Candle.timeframe == timeframe.value
        )
        if start:
            query = query.where(Candle.open_time >= start)
        if end:
            query = query.where(Candle.open_time < end)
        query = query.order_by(Candle.open_time.desc()).limit(limit)
        candles = list((await self.session.scalars(query)).all())
        candles.reverse()
        return candles

    @staticmethod
    def _split_symbol(symbol: str) -> tuple[str, str]:
        for quote in ("USDT", "USDC", "BTC", "ETH"):
            if symbol.endswith(quote):
                return symbol[: -len(quote)], quote
        raise ValueError(f"cannot infer base and quote assets from {symbol}")
