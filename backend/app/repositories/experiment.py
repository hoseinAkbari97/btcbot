"""Experiment repository.

Only the submission definition is immutable. Lifecycle columns (status, links,
failure details) are the only fields this repository ever updates.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import ExperimentRecord


class ExperimentRepository:
    """Persistence operations for experiments."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, experiment: ExperimentRecord) -> ExperimentRecord:
        self.session.add(experiment)
        await self.session.flush()
        return experiment

    async def get(self, experiment_id: str) -> ExperimentRecord | None:
        query = select(ExperimentRecord).where(ExperimentRecord.id == experiment_id)
        record = await self.session.scalar(query)
        return record if isinstance(record, ExperimentRecord) else None

    async def find_by_idempotency_key(self, key: str) -> ExperimentRecord | None:
        query = select(ExperimentRecord).where(ExperimentRecord.idempotency_key == key)
        return await self.session.scalar(query)

    async def list_experiments(
        self,
        *,
        strategy: str | None = None,
        status: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 50,
    ) -> list[ExperimentRecord]:
        query: Select[tuple[ExperimentRecord]] = select(ExperimentRecord)
        if strategy is not None:
            query = query.where(ExperimentRecord.strategy_name == strategy)
        if status is not None:
            query = query.where(ExperimentRecord.status == status)
        if symbol is not None:
            query = query.where(ExperimentRecord.symbol == symbol)
        if timeframe is not None:
            query = query.where(ExperimentRecord.timeframe == timeframe)
        if created_after is not None:
            query = query.where(ExperimentRecord.created_at > created_after)
        if created_before is not None:
            query = query.where(ExperimentRecord.created_at < created_before)
        query = query.order_by(ExperimentRecord.created_at.desc()).limit(limit)
        return list((await self.session.scalars(query)).all())

    async def count(
        self,
        *,
        strategy: str | None = None,
        status: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(ExperimentRecord)
        if strategy is not None:
            query = query.where(ExperimentRecord.strategy_name == strategy)
        if status is not None:
            query = query.where(ExperimentRecord.status == status)
        if symbol is not None:
            query = query.where(ExperimentRecord.symbol == symbol)
        if timeframe is not None:
            query = query.where(ExperimentRecord.timeframe == timeframe)
        return int(await self.session.scalar(query) or 0)

    async def set_status(self, experiment: ExperimentRecord, status: str) -> None:
        experiment.status = status
        await self.session.flush()

    async def set_failure(
        self, experiment: ExperimentRecord, stage: str, reason: str
    ) -> None:
        experiment.failure_stage = stage
        experiment.failure_reason = reason
        await self.session.flush()

    async def link_backtest(
        self,
        experiment: ExperimentRecord,
        run_id: str,
        *,
        dataset_version: str | None,
        engine_version: str | None,
        random_seed: int | None,
    ) -> None:
        """Link a persisted run; never edits the run itself."""
        experiment.backtest_run_id = run_id
        experiment.dataset_version = dataset_version
        experiment.engine_version = engine_version
        experiment.random_seed = random_seed
        await self.session.flush()

    async def link_evaluation(
        self, experiment: ExperimentRecord, report_id: str
    ) -> None:
        experiment.evaluation_report_id = report_id
        await self.session.flush()

    async def cancel(self, experiment: ExperimentRecord) -> None:
        experiment.status = "CANCELLED"
        await self.session.flush()
