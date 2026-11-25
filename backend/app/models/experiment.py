"""Experiment persistence model.

An experiment ties together a strategy run, its evaluation, and all provenance
information. It is append-only: the configuration is immutable after submission,
and a new experiment is created for each variant.

Key invariants:
- Configuration is immutable after submission; changes create a new experiment.
- A completed experiment references its backtest run and evaluation report.
- Dataset fingerprints are preserved for reproducibility.
- Lifecycle status tracks progression from DRAFT through COMPLETED/FAILED.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
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


class ExperimentRecord(TimestampMixin, Base):
    """One immutable experiment submission.

    Attributes:
        id: Unique experiment identifier.
        strategy_name: Registered strategy name from the default registry.
        strategy_version: Strategy version string (optional).
        symbol: Trading pair (e.g. BTCUSDT).
        timeframe: Candle timeframe (e.g. 15m).
        period_start / period_end: Historical window.
        initial_capital: Starting accounting currency amount.
        configuration: Immutable experiment configuration dict.
        status: Current lifecycle state.
        notes: Free-form researcher notes.
        dataset_version: Fingerprint of the candle data seen.
        random_seed: Recorded seed for reproducibility, if any.
        backtest_run_id: Link to the persisted backtest run, if any.
        evaluation_report_id: Link to the persisted evaluation report, if any.
    """

    __tablename__ = "experiments"

    __table_args__ = (
        Index(
            "ix_experiments_strategy_created",
            "strategy_name",
            "created_at",
        ),
        Index(
            "ix_experiments_symbol_timeframe_created",
            "symbol",
            "timeframe",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_id
    )
    strategy_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    strategy_version: Mapped[str | None] = mapped_column(
        String(32), nullable=True, default=None
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    initial_capital: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), nullable=False
    )
    configuration: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default=None
    )
    random_seed: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    backtest_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("backtest_runs.id"), nullable=True, default=None
    )
    evaluation_report_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evaluation_reports.id"), nullable=True, default=None
    )

    # Bidirectional links (back-populates managed by SQLAlchemy relationships
    # on the inverse sides if needed; here we keep it simple with FK references).