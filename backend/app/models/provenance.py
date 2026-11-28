"""Immutable provenance manifests for persisted backtest runs.

A manifest is written once when a run completes and is never updated. Historical
runs remain without a manifest; their absence is reported as unavailable rather
than reconstructed from the current code checkout.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class RunManifestRecord(Base):
    """One canonical identity document for one backtest run."""

    __tablename__ = "run_manifests"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_run_manifests_run_id"),
        Index("ix_run_manifests_experiment_id", "experiment_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("backtest_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    experiment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=True,
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    manifest_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
