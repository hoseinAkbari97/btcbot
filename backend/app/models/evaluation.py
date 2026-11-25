"""Evaluation report persistence model.

``EvaluationService`` is read-only and deliberately does not store its reports.
Experiments persist a report snapshot here so a completed experiment can be
retrieved with its evaluation provenance intact.

Reports are append-only: a re-evaluation creates a new row with its own digest,
never a silent edit of an existing report.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


def _new_id() -> str:
    return str(uuid.uuid4())


class EvaluationReportRecord(TimestampMixin, Base):
    """Persisted snapshot of an evaluation report."""

    __tablename__ = "evaluation_reports"

    __table_args__ = (
        Index("ix_evaluation_reports_run", "run_id"),
        Index("ix_evaluation_reports_experiment", "experiment_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    #: Plain string, not a foreign key, to avoid a circular FK between
    #: experiments and evaluation_reports. Still validated by the service.
    experiment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("backtest_runs.id"), nullable=False
    )
    report: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    report_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    config_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    method_version: Mapped[str] = mapped_column(String(32), nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
