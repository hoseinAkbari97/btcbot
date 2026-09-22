from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import Candle, DataSource, Instrument, Market
from app.schemas.market_data import CandleData, Timeframe


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
        dialect = self.session.bind.dialect.name if self.session.bind else "postgresql"
        insert = sqlite_insert(Candle) if dialect == "sqlite" else postgres_insert(Candle)
        statement = insert.values(rows)
        excluded = statement.excluded
        statement = statement.on_conflict_do_update(
            index_elements=["instrument_id", "source_id", "timeframe", "open_time"],
            set_={
                "close_time": excluded.close_time,
                "open": excluded.open,
                "high": excluded.high,
                "low": excluded.low,
                "close": excluded.close,
                "volume": excluded.volume,
                "quote_volume": excluded.quote_volume,
                "trade_count": excluded.trade_count,
                "taker_buy_base_volume": excluded.taker_buy_base_volume,
                "taker_buy_quote_volume": excluded.taker_buy_quote_volume,
                "is_closed": excluded.is_closed,
            },
        )
        await self.session.execute(statement)
        return len(rows)

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
