"""Experiment repository for database operations.

Provides CRUD and query operations for the ExperimentRecord model,
following the same patterns as backend/app/repositories/backtest.py.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.models.experiment import ExperimentRecord


class ExperimentRepository:
    """Repository for experiment persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _json_safe(value: object) -> object:
        """Coerce a value into JSON-safe form."""
        if isinstance(value, dict):
            return {str(key): ExperimentRepository._json_safe(item) for key, item in value.items()}
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        return repr(value)

    async def save(self, experiment: ExperimentRecord) -> ExperimentRecord:
        """Persist a new experiment record.

        Experiments are append-only. Nothing here edits an existing experiment.
        """
        self.session.add(experiment)
        await self.session.flush()
        return experiment

    async def get(self, experiment_id: str) -> ExperimentRecord | None:
        """Fetch one experiment by ID."""
        query = select(ExperimentRecord).where(ExperimentRecord.id == experiment_id)
        record = await self.session.scalar(query)
        return record if isinstance(record, ExperimentRecord) else None

    async def list_experiments(
        self,
        strategy: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ExperimentRecord]:
        """List experiments with optional filtering."""
        query = select(ExperimentRecord)

        if strategy is not None:
            query = query.where(ExperimentRecord.strategy_name == strategy)
        if symbol is not None:
            query = query.where(ExperimentRecord.symbol == symbol)
        if timeframe is not None:
            query = query.where(ExperimentRecord.timeframe == timeframe)
        if status is not None:
            query = query.where(ExperimentRecord.status == status)

        query = query.order_by(ExperimentRecord.created_at.desc()).limit(limit)
        return list((await self.session.scalars(query)).all())

    async def list_experiments_summary(
        self,
        strategy: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List experiments as summary dicts (lightweight, no full config)."""
        records = await self.list_experiments(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            status=status,
            limit=limit,
        )
        return [
            {
                "id": record.id,
                "strategy_name": record.strategy_name,
                "symbol": record.symbol,
                "timeframe": record.timeframe,
                "status": record.status,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "backtest_run_id": record.backtest_run_id,
                "evaluation_report_id": record.evaluation_report_id,
            }
            for record in records
        ]

    async def count_experiments(
        self,
        strategy: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> int:
        """Count experiments, optionally filtered."""
        query = select(func.count()).select_from(ExperimentRecord)

        if strategy is not None:
            query = query.where(ExperimentRecord.strategy_name == strategy)
        if symbol is not None:
            query = query.where(ExperimentRecord.symbol == symbol)
        if status is not None:
            query = query.where(ExperimentRecord.status == status)

        total = await self.session.scalar(query)
        return int(total or 0)

    async def exists(self, experiment_id: str) -> bool:
        """Check if an experiment exists."""
        record = await self.get(experiment_id)
        return record is not None