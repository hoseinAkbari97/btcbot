"""Experiment persistence model.

An experiment ties together a strategy run, its evaluation, and all provenance
information. It is append-only: the configuration is immutable after submission,
and a new experiment is created for each variant.

Key invariants:
- Configuration is immutable after submission; changes create a new experiment.
- A completed experiment references its backtest run and evaluation report.
- Dataset fingerprints, strategy versions and execution assumptions are preserved.
- Lifecycle status tracks progression from DRAFT through COMPLETED/FAILED.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


def _new_id() -> str:
    return str(uuid.uuid4())


class ExperimentRecord(TimestampMixin, Base):
    """One immutable experiment submission.

    Submission-time fields are never rewritten. Only lifecycle columns
    (``status``, links, failure details) are updated as the experiment runs.
    """

    __tablename__ = "experiments"

    __table_args__ = (
        Index("ix_experiments_strategy_created", "strategy_name", "created_at"),
        Index(
            "ix_experiments_symbol_timeframe_created",
            "symbol",
            "timeframe",
            "created_at",
        ),
        Index("ix_experiments_status_created", "status", "created_at"),
        UniqueConstraint("idempotency_key", name="uq_experiments_idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    initial_capital: Mapped[Decimal] = mapped_column(
        Numeric(28, 10), nullable=False
    )
    accounting_currency: Mapped[str] = mapped_column(
        String(8), default="USDT", nullable=False
    )

    #: Complete frozen submission definition, including costs and evaluation
    #: settings. Never edited after the row is inserted.
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    configuration_fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    #: Hash of the immutable definition plus the dataset fingerprint, used as
    #: the idempotency key for duplicate submissions.
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    #: A repeat submission of an identical definition points at the original.
    parent_experiment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    failure_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    dataset_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    backtest_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("backtest_runs.id"), nullable=True
    )
    evaluation_report_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evaluation_reports.id"), nullable=True
    )
