"""Persistence for evaluation report snapshots.

The evaluation service itself stays read-only; experiments store an immutable
copy of the generated report here so results remain retrievable and attributable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationReportRecord


class EvaluationReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, record: EvaluationReportRecord) -> EvaluationReportRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, report_id: str) -> EvaluationReportRecord | None:
        result = await self.session.scalar(
            select(EvaluationReportRecord).where(EvaluationReportRecord.id == report_id)
        )
        return result if isinstance(result, EvaluationReportRecord) else None

    async def get_for_run(self, run_id: str) -> EvaluationReportRecord | None:
        result = await self.session.scalar(
            select(EvaluationReportRecord)
            .where(EvaluationReportRecord.run_id == run_id)
            .order_by(EvaluationReportRecord.created_at.desc())
            .limit(1)
        )
        return result if isinstance(result, EvaluationReportRecord) else None
