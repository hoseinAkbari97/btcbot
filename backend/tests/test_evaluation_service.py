"""Evaluation service: provenance gates, report shape, read-only behaviour."""

from __future__ import annotations

import pytest
from evaluation_helpers import run_record, trade_record
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest import BacktestRunRecord, BacktestTradeRecord
from app.services.evaluation.config import EvaluationConfig
from app.services.evaluation.provenance import EvaluationInputError
from app.services.evaluation.report import (
    EvaluationComparisonError,
    EvaluationReport,
    ReportFormatError,
    compare_reports,
)
from app.services.evaluation.service import EvaluationService

CONFIG = EvaluationConfig(resamples=200)

PROFITABLE_PNLS = [100.0, -40.0, 60.0, -20.0, 80.0, -30.0, 50.0, -10.0, 70.0, -20.0, 40.0, 30.0]


async def persist_run(
    session: AsyncSession,
    *,
    pnls: list[float] = PROFITABLE_PNLS,
    run_id: str = "run-1",
    mode: str | None = "research",
    dataset_version: str | None = "candles-v1",
    costs: float = 1.0,
    risk_fraction: str | None = "0.01",
) -> str:
    total = sum(pnls)
    metrics: dict[str, object] = {
        "max_drawdown": 0.08,
        "insufficient_sample": False,
        "sample_span_seconds": 2_592_000.0,
        "total_return": total / 10_000.0,
        "cagr": 0.1,
        "sharpe": 0.5,
        "trade_count": len(pnls),
    }
    session.add(
        run_record(
            run_id=run_id,
            mode=mode,
            dataset_version=dataset_version,
            final_equity=str(10_000 + total),
            metrics=metrics,
        )
    )
    for index, pnl in enumerate(pnls):
        session.add(
            trade_record(
                index,
                run_id=run_id,
                trade_id=f"{run_id}-trade-{index}",
                net_pnl=pnl,
                fees=costs,
                risk_fraction=risk_fraction,
            )
        )
    await session.flush()
    return run_id


async def test_report_covers_every_section(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session)

    report = await EvaluationService(db_session, CONFIG).evaluate(run_id)
    payload = report.as_dict()

    for section in ("provenance", "performance", "trades", "tail_risk", "sensitivity", "evidence"):
        assert section in payload
    assert payload["simulation"] is not None
    assert payload["config_fingerprint"] == CONFIG.fingerprint()
    assert payload["evidence"]["withheld_claims"]
    assert report.run_id == run_id


async def test_evaluation_is_deterministic_for_the_same_inputs(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session)
    service = EvaluationService(db_session, CONFIG)

    first = await service.evaluate(run_id)
    second = await service.evaluate(run_id)

    assert first.digest() == second.digest()
    assert first.input_fingerprint == second.input_fingerprint


async def test_evaluation_does_not_modify_the_original_run(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session)

    before_run = (
        await db_session.execute(
            select(
                BacktestRunRecord.final_equity,
                BacktestRunRecord.metrics,
                BacktestRunRecord.notes,
            ).where(BacktestRunRecord.id == run_id)
        )
    ).one()
    before_trades = await db_session.scalar(
        select(func.count()).select_from(BacktestTradeRecord).where(
            BacktestTradeRecord.run_id == run_id
        )
    )
    before_net = await db_session.scalar(
        select(func.sum(BacktestTradeRecord.net_pnl)).where(BacktestTradeRecord.run_id == run_id)
    )

    await EvaluationService(db_session, CONFIG).evaluate(run_id)

    after_run = (
        await db_session.execute(
            select(
                BacktestRunRecord.final_equity,
                BacktestRunRecord.metrics,
                BacktestRunRecord.notes,
            ).where(BacktestRunRecord.id == run_id)
        )
    ).one()
    after_trades = await db_session.scalar(
        select(func.count()).select_from(BacktestTradeRecord).where(
            BacktestTradeRecord.run_id == run_id
        )
    )
    after_net = await db_session.scalar(
        select(func.sum(BacktestTradeRecord.net_pnl)).where(BacktestTradeRecord.run_id == run_id)
    )

    assert before_run == after_run
    assert before_trades == after_trades
    assert before_net == after_net
    assert not db_session.new
    assert not db_session.dirty


async def test_unknown_run_is_refused(db_session: AsyncSession) -> None:
    with pytest.raises(EvaluationInputError, match="no backtest run"):
        await EvaluationService(db_session, CONFIG).evaluate("missing")


async def test_holdout_mode_is_refused(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session, mode="validation")

    with pytest.raises(EvaluationInputError, match="not evaluable here"):
        await EvaluationService(db_session, CONFIG).evaluate(run_id)


async def test_unrecorded_mode_is_refused(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session, mode=None)

    with pytest.raises(EvaluationInputError, match="mode was not recorded"):
        await EvaluationService(db_session, CONFIG).evaluate(run_id)


async def test_run_without_trades_is_refused(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session, pnls=[])

    with pytest.raises(EvaluationInputError, match="no persisted trades"):
        await EvaluationService(db_session, CONFIG).evaluate(run_id)


async def test_small_sample_is_reported_as_insufficient(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session, pnls=[10.0, -5.0, 8.0, -4.0])

    report = await EvaluationService(db_session, CONFIG).evaluate(run_id)

    assert report.evidence_level == "insufficient"
    assert "Insufficient evidence" in str(report.evidence["headline"])
    assert any("inference threshold" in reason for reason in report.evidence["reasons"])


async def test_missing_provenance_is_carried_as_warnings(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session, dataset_version=None)

    report = await EvaluationService(db_session, CONFIG).evaluate(run_id)
    provenance = report.provenance

    assert any("dataset version was not recorded" in item for item in provenance["warnings"])
    assert provenance["read_only"] is True


async def test_report_round_trips_through_a_dict(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session)
    report = await EvaluationService(db_session, CONFIG).evaluate(run_id)

    restored = EvaluationReport.from_dict(report.as_dict())

    assert restored.digest() == report.digest()
    assert restored.run_id == run_id


async def test_incomplete_report_is_rejected(db_session: AsyncSession) -> None:
    run_id = await persist_run(db_session)
    payload = (await EvaluationService(db_session, CONFIG).evaluate(run_id)).as_dict()
    payload.pop("trades")

    with pytest.raises(ReportFormatError, match="trades"):
        EvaluationReport.from_dict(payload)


async def test_reports_compare_and_refuse_mismatched_data(db_session: AsyncSession) -> None:
    first_id = await persist_run(db_session, run_id="run-1")
    second_id = await persist_run(
        db_session, run_id="run-2", pnls=[80.0, -60.0, 40.0, -20.0, 60.0, -30.0, 50.0, -10.0]
    )
    service = EvaluationService(db_session, CONFIG)

    left = await service.evaluate(first_id)
    right = await service.evaluate(second_id)
    comparison = compare_reports(left, right)

    assert comparison.left_run_id == first_id
    assert any(delta.metric == "performance.net_pnl" for delta in comparison.deltas)
    assert any("not a ranking" in note for note in comparison.notes)

    await persist_run(db_session, run_id="run-3", dataset_version="candles-v2", pnls=[10.0, -5.0])
    other = await service.evaluate("run-3")
    with pytest.raises(EvaluationComparisonError, match="dataset versions differ"):
        compare_reports(left, other)


async def test_two_runs_are_evaluated_one_at_a_time(db_session: AsyncSession) -> None:
    first_id = await persist_run(db_session, run_id="run-1")
    second_id = await persist_run(db_session, run_id="run-2", pnls=[5.0, -2.0, 3.0])

    reports = await EvaluationService(db_session, CONFIG).evaluate_many([first_id, second_id])

    assert [report.run_id for report in reports] == [first_id, second_id]
