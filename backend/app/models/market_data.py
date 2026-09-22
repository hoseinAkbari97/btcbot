import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


def new_id() -> str:
    return str(uuid.uuid4())


class Market(TimestampMixin, Base):
    __tablename__ = "markets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    venue: Mapped[str] = mapped_column(String(64), nullable=False)
    market_type: Mapped[str] = mapped_column(String(32), default="spot", nullable=False)
    timezone: Mapped[str] = mapped_column(String(16), default="UTC", nullable=False)


class DataSource(TimestampMixin, Base):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Instrument(TimestampMixin, Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("market_id", "symbol"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    base_asset: Mapped[str] = mapped_column(String(16), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    price_precision: Mapped[int | None] = mapped_column(Integer)
    quantity_precision: Mapped[int | None] = mapped_column(Integer)
    market: Mapped[Market] = relationship()


class Candle(TimestampMixin, Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("instrument_id", "source_id", "timeframe", "open_time"),
        Index("ix_candles_symbol_timeframe_timestamp", "symbol", "timeframe", "open_time"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    quote_volume: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    trade_count: Mapped[int | None] = mapped_column(Integer)
    taker_buy_base_volume: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    taker_buy_quote_volume: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    is_closed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("source_id", "symbol", "external_trade_id"),
        Index("ix_trades_symbol_timestamp", "symbol", "timestamp"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    external_trade_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    buyer_is_maker: Mapped[bool | None] = mapped_column(Boolean)


class OrderBookSnapshot(TimestampMixin, Base):
    __tablename__ = "order_book_snapshots"
    __table_args__ = (Index("ix_order_books_symbol_timestamp", "symbol", "timestamp"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_update_id: Mapped[int | None] = mapped_column(BigInteger)
    bids: Mapped[list[list[str]]] = mapped_column(JSON, nullable=False)
    asks: Mapped[list[list[str]]] = mapped_column(JSON, nullable=False)


class DataQualityReport(TimestampMixin, Base):
    __tablename__ = "data_quality_reports"
    __table_args__ = (
        Index("ix_quality_symbol_timeframe_created", "symbol", "timeframe", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    anomaly_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    raw_file: Mapped[str | None] = mapped_column(String(512))
    parquet_files: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
