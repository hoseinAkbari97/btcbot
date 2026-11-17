"""End to end: a real engine run, persisted, then evaluated.

The other evaluation tests use hand-built rows. This one proves the evaluator
also reads what the backtest engine actually writes, including its risk units.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from test_backtest_comparison import make_series

from app.repositories.backtest import BacktestRepository
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.runner import run_backtest
from app.services.evaluation.config import EvaluationConfig
from app.services.evaluation.service import EvaluationService


async def test_engine_run_is_evaluated_without_modification(db_session: AsyncSession) -> None:
    candles = make_series(count=200)
    result = run_backtest(
        candles,
        symbol=candles[0].symbol,
        timeframe=candles[0].timeframe,
        strategy_name="sma_trend",
        costs=BacktestCosts(),
        initial_capital=10_000,
        parameters={},
    )
    record = await BacktestRepository(db_session).save(result)
    await db_session.flush()

    report = await EvaluationService(
        db_session, EvaluationConfig(resamples=200)
    ).evaluate(record.id)

    assert report.run_id == record.id
    assert report.provenance["run"]["strategy"] == "sma_trend"
    assert report.trades["trades"] == len(result.run.trades)
    assert report.simulation is not None
    assert report.simulation["sample_size"] == len(result.run.trades)
    assert report.evidence_level in {"insufficient", "descriptive", "conditional_inference"}
    assert report.sensitivity["scenarios"]
    assert report.segments is not None

    reloaded = await BacktestRepository(db_session).get_run_without_trades(record.id)
    assert reloaded is not None
    assert reloaded.final_equity == record.final_equity
    assert reloaded.metrics == record.metrics
