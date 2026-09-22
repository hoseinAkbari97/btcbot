"""Create Phase 1 market-data schema.

Revision ID: 20260922_0001
Revises:
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

timestamps = (
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
)


def upgrade() -> None:
    op.create_table(
        "markets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("venue", sa.String(64), nullable=False),
        sa.Column("market_type", sa.String(32), nullable=False),
        sa.Column("timezone", sa.String(16), nullable=False),
        *timestamps,
    )
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("base_url", sa.String(255)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        *timestamps,
    )
    op.create_table(
        "instruments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("market_id", sa.String(36), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("base_asset", sa.String(16), nullable=False),
        sa.Column("quote_asset", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("price_precision", sa.Integer()),
        sa.Column("quantity_precision", sa.Integer()),
        *timestamps,
        sa.UniqueConstraint("market_id", "symbol", name="uq_instruments_market_id"),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])
    op.create_table(
        "candles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("instrument_id", sa.String(36), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(28, 10), nullable=False),
        sa.Column("high", sa.Numeric(28, 10), nullable=False),
        sa.Column("low", sa.Numeric(28, 10), nullable=False),
        sa.Column("close", sa.Numeric(28, 10), nullable=False),
        sa.Column("volume", sa.Numeric(38, 18), nullable=False),
        sa.Column("quote_volume", sa.Numeric(38, 18)),
        sa.Column("trade_count", sa.Integer()),
        sa.Column("taker_buy_base_volume", sa.Numeric(38, 18)),
        sa.Column("taker_buy_quote_volume", sa.Numeric(38, 18)),
        sa.Column("is_closed", sa.Boolean(), nullable=False),
        *timestamps,
        sa.UniqueConstraint(
            "instrument_id",
            "source_id",
            "timeframe",
            "open_time",
            name="uq_candles_instrument_id",
        ),
    )
    op.create_index(
        "ix_candles_symbol_timeframe_timestamp",
        "candles",
        ["symbol", "timeframe", "open_time"],
    )
    op.create_table(
        "trades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("instrument_id", sa.String(36), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("external_trade_id", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(28, 10), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("buyer_is_maker", sa.Boolean()),
        *timestamps,
        sa.UniqueConstraint(
            "source_id", "symbol", "external_trade_id", name="uq_trades_source_id"
        ),
    )
    op.create_index("ix_trades_symbol_timestamp", "trades", ["symbol", "timestamp"])
    op.create_table(
        "order_book_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("instrument_id", sa.String(36), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_update_id", sa.BigInteger()),
        sa.Column("bids", sa.JSON(), nullable=False),
        sa.Column("asks", sa.JSON(), nullable=False),
        *timestamps,
    )
    op.create_index(
        "ix_order_books_symbol_timestamp", "order_book_snapshots", ["symbol", "timestamp"]
    )
    op.create_table(
        "data_quality_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("missing_count", sa.Integer(), nullable=False),
        sa.Column("invalid_count", sa.Integer(), nullable=False),
        sa.Column("anomaly_count", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("raw_file", sa.String(512)),
        sa.Column("parquet_files", sa.JSON(), nullable=False),
        *timestamps,
    )
    op.create_index(
        "ix_quality_symbol_timeframe_created",
        "data_quality_reports",
        ["symbol", "timeframe", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("data_quality_reports")
    op.drop_table("order_book_snapshots")
    op.drop_table("trades")
    op.drop_table("candles")
    op.drop_table("instruments")
    op.drop_table("data_sources")
    op.drop_table("markets")

