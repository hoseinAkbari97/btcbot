"""Backtest persistence models.

A run is stored so that every result can be traced back to the data, costs and
parameters that produced it (project principle 52). Runs are append-only: a
result is never edited after the fact, a new run is created instead.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


def _new_id() -> str:
    return str(uuid.uuid4())


class BacktestRunRecord(TimestampMixin, Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (
        Index("ix_backtest_runs_symbol_timeframe_created", "symbol", "timeframe", "created_at"),
        Index("ix_backtest_runs_strategy_created", "strategy_name", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str | None] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("data_sources.id"))

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    candle_count: Mapped[int] = mapped_column(Integer, nullable=False)

    initial_capital: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    final_equity: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)

    # Cost assumptions actually applied, so a run is reproducible.
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    spread_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    slippage_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    latency_bars: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_scale: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("1"), nullable=False)

    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    dataset_version: Mapped[str | None] = mapped_column(String(128))
    #: Present only for strategies that have a random component. Recorded so a
    #: seeded run can be reproduced exactly; absent means the run was
    #: deterministic, which is itself worth knowing.
    random_seed: Mapped[int | None] = mapped_column(Integer)
    feature_version: Mapped[str | None] = mapped_column(String(64))
    model_version: Mapped[str | None] = mapped_column(String(64))
    git_commit: Mapped[str | None] = mapped_column(String(40))
    #: Run mode governing risk enforcement (``research`` allows risk=None for
    #: control experiments; the others require it). Null on rows written before
    #: modes were recorded, and null must be read as "unknown", never as
    #: "research".
    mode: Mapped[str | None] = mapped_column(String(16))
    notes: Mapped[str | None] = mapped_column(Text)

    trades: Mapped[list[BacktestTradeRecord]] = relationship(
        back_populates="run", cascade="all, delete-orphan", lazy="selectin"
    )


class BacktestTradeRecord(TimestampMixin, Base):
    __tablename__ = "backtest_trades"
    __table_args__ = (Index("ix_backtest_trades_run", "run_id", "id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    side: Mapped[str] = mapped_column(String(8), nullable=False)

    # Timing provenance: the three moments that differ, and whose gap costs edge.
    signal_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    order_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fill_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    exit_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    size: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    notional_value: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), default=Decimal(0), nullable=False
    )
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))

    # Risk semantics, recorded rather than inferred.
    risk_fraction: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    risk_amount: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    #: Capital committed as a share of the account. Kept apart from
    #: ``risk_fraction`` so the two can never be conflated downstream.
    capital_fraction: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    #: Share of account notional the position held, populated only when
    #: ``sizing_model`` is ``notional_exposure``. Left null for the other two
    #: models rather than backfilled, so it can never be mistaken for a copy of
    #: ``capital_fraction``.
    exposure_fraction: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    sizing_model: Mapped[str] = mapped_column(String(24), default="stop_risk", nullable=False)

    gross_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    # Costs itemised rather than summed into fees, so a reader can see how much
    # of the edge each one destroyed.
    spread_cost: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), default=Decimal(0), nullable=False
    )
    slippage_cost: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), default=Decimal(0), nullable=False
    )
    latency_cost: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), default=Decimal(0), nullable=False
    )
    other_costs: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), default=Decimal(0), nullable=False
    )
    net_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)

    # Both R multiples are stored: gross overstates the edge, net is what the
    # Monte Carlo project should consume.
    gross_r: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    net_r: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    r_multiple: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    mae: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    mae_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    mfe: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    mfe_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))

    bars_held: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Wall-clock holding time. Bars are timeframe-dependent, so a holding-time
    #: distribution is not comparable across timeframes without it.
    holding_seconds: Mapped[float | None] = mapped_column(Float)
    exit_reason: Mapped[str] = mapped_column(String(32), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), default="1", nullable=False)
    market_regime: Mapped[str] = mapped_column(String(24), default="", nullable=False)
    strategy_context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    run: Mapped["BacktestRunRecord"] = relationship(back_populates="trades")