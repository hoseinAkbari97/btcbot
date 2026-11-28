"""Experiment lifecycle API.

Research-only endpoints following the conventions of
``backend/app/api/routes/backtest.py``: FastAPI router, injected DB session,
Pydantic request/response models, 422 for correctable request errors, 404 for
unknown IDs, no authentication layer (none exists in this repository yet).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.backtest import BacktestRepository
from app.repositories.evaluation import EvaluationReportRepository
from app.repositories.experiment import ExperimentRepository
from app.schemas.experiment import (
    ExperimentBatchItem,
    ExperimentBatchRequest,
    ExperimentComparisonRequest,
    ExperimentCurveResponse,
    ExperimentEngineCurveResponse,
    ExperimentEvaluationResponse,
    ExperimentResultResponse,
    ExperimentRetrieval,
    ExperimentStatusResponse,
    ExperimentSubmission,
)
from app.schemas.verification import ExperimentVerificationResponse
from app.services.accounting.model import EQUITY_SERIES_BASIS
from app.services.backtest.comparison import (
    ComparisonError,
    RunsNotFoundError,
    compare_runs,
)
from app.services.experiment.curves import build_realized_curve
from app.services.experiment.service import (
    EXPERIMENT_STATES,
    ExperimentOrchestrationService,
)
from app.services.provenance.service import (
    VerificationConflictError,
    VerificationNotFoundError,
    VerificationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


def _orchestration(
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentOrchestrationService:
    return ExperimentOrchestrationService(session)


def _retrieval(record: Any) -> ExperimentRetrieval:
    return ExperimentRetrieval.model_validate(record, from_attributes=True)


def _status(record: Any) -> ExperimentStatusResponse:
    return ExperimentStatusResponse.model_validate(record, from_attributes=True)


async def _reject_if_failed(session: AsyncSession, result: Any) -> None:
    """Persist failed submissions, then explain them as correctable 422s."""
    await session.commit()
    if result.failure_stage is not None:
        raise HTTPException(
            status_code=422,
            detail={
                "experiment_id": result.experiment.id,
                "stage": result.failure_stage,
                "reason": result.failure_reason,
            },
        )


@router.post("", response_model=ExperimentRetrieval, status_code=201)
async def submit_experiment(
    request: ExperimentSubmission,
    session: AsyncSession = Depends(get_db_session),
    orchestration: ExperimentOrchestrationService = Depends(_orchestration),
) -> ExperimentRetrieval:
    """Validate, execute and evaluate one immutable experiment definition."""
    result = await orchestration.submit(request)
    await _reject_if_failed(session, result)
    # TimestampMixin's SQL-side onupdate expires this column after the flush;
    # load it before Pydantic reads the record in a sync serializer.
    await session.refresh(result.experiment, ["updated_at"])
    logger.info(
        "experiment submitted",
        extra={
            "event": "EXPERIMENT_SUBMITTED",
            "experiment_id": result.experiment.id,
            "status": result.experiment.status,
            "reused": result.reused,
        },
    )
    return _retrieval(result.experiment)


@router.post("/batch", response_model=list[ExperimentBatchItem])
async def submit_experiment_batch(
    request: ExperimentBatchRequest,
    session: AsyncSession = Depends(get_db_session),
    orchestration: ExperimentOrchestrationService = Depends(_orchestration),
) -> list[ExperimentBatchItem]:
    """Submit at most five explicit experiments sequentially.

    Each item has its own status; one rejection never aborts the others.
    """
    items = await orchestration.submit_batch(request.experiments)
    await session.commit()
    return items


@router.post("/compare", response_model=dict[str, Any])
async def compare_experiments(
    request: ExperimentComparisonRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Compare completed experiments through the existing run comparison rules."""
    experiments: list[Any] = []
    for experiment_id in request.experiment_ids:
        record = await ExperimentRepository(session).get(experiment_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")
        if record.status != "COMPLETED" or record.backtest_run_id is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"experiment {experiment_id} has no completed backtest run; "
                    "only completed experiments can be compared"
                ),
            )
        experiments.append(record)

    try:
        comparison = await compare_runs(
            session, [record.backtest_run_id for record in experiments]
        )
    except RunsNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ComparisonError as error:
        raise HTTPException(
            status_code=422,
            detail={"category": error.category, "reasons": [p.message for p in error.problems]},
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    payload = comparison.model_dump(mode="json")
    payload["experiment_ids"] = request.experiment_ids
    return payload


@router.get("", response_model=list[ExperimentRetrieval])
async def list_experiments(
    strategy: str | None = Query(None),
    status: str | None = Query(None),
    symbol: str | None = Query(None, pattern=r"^[A-Za-z0-9/]{6,20}$"),
    timeframe: str | None = Query(None),
    created_after: datetime | None = Query(None),
    created_before: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
) -> list[ExperimentRetrieval]:
    """List experiments, newest first, with optional filters."""
    if status is not None and status not in EXPERIMENT_STATES:
        raise HTTPException(status_code=422, detail=f"unknown status {status!r}")
    if timeframe is not None and timeframe not in {"5m", "15m", "1h", "4h", "1d"}:
        raise HTTPException(status_code=422, detail=f"unsupported timeframe {timeframe!r}")
    normalized_symbol = symbol.replace("/", "").upper() if symbol else None
    records = await ExperimentRepository(session).list_experiments(
        strategy=strategy,
        status=status,
        symbol=normalized_symbol,
        timeframe=timeframe,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
    )
    return [_retrieval(record) for record in records]


@router.get("/{experiment_id}", response_model=ExperimentRetrieval)
async def get_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentRetrieval:
    record = await ExperimentRepository(session).get(experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")
    return _retrieval(record)


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
async def get_experiment_status(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentStatusResponse:
    record = await ExperimentRepository(session).get(experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")
    return _status(record)


@router.get("/{experiment_id}/result", response_model=ExperimentResultResponse)
async def get_experiment_result(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentResultResponse:
    """Return the experiment together with its linked backtest and evaluation."""
    record = await ExperimentRepository(session).get(experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")

    backtest_run: dict[str, Any] | None = None
    if record.backtest_run_id is not None:
        run = await BacktestRepository(session).get_run_without_trades(
            record.backtest_run_id
        )
        if run is not None:
            backtest_run = {
                "id": run.id,
                "strategy_name": run.strategy_name,
                "strategy_version": run.strategy_version,
                "symbol": run.symbol,
                "timeframe": run.timeframe,
                "period_start": run.period_start,
                "period_end": run.period_end,
                "candle_count": run.candle_count,
                "initial_capital": str(run.initial_capital),
                "final_equity": str(run.final_equity),
                "costs": {
                    "fee_rate": str(run.fee_rate),
                    "spread_rate": str(run.spread_rate),
                    "slippage_rate": str(run.slippage_rate),
                    "latency_bars": run.latency_bars,
                    "cost_scale": str(run.cost_scale),
                },
                "parameters": run.parameters,
                # Null metrics stay null: never coerce an unverified metric to 0.
                "metrics": run.metrics,
                "dataset_version": run.dataset_version,
                "git_commit": run.git_commit,
                "mode": run.mode,
                "created_at": run.created_at,
            }

    evaluation_report: dict[str, Any] | None = None
    if record.evaluation_report_id is not None:
        report = await EvaluationReportRepository(session).get(
            record.evaluation_report_id
        )
        if report is not None:
            evaluation_report = report.report

    return ExperimentResultResponse(
        experiment=_retrieval(record),
        backtest_run=backtest_run,
        evaluation_report=evaluation_report,
    )


@router.get("/{experiment_id}/curves", response_model=ExperimentCurveResponse)
async def get_experiment_curves(
    experiment_id: str,
    limit: int = Query(5000, ge=1, le=5000),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentCurveResponse:
    """Return a bounded realized-equity projection of persisted closed trades.

    This is deliberately not the engine's transient per-candle equity curve:
    it starts at recorded capital, adds each stored net trade PnL at its exit
    time, and derives drawdown from that running realized peak.
    """
    record = await ExperimentRepository(session).get(experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")

    def unavailable(reason: str, run_id: str | None = None) -> ExperimentCurveResponse:
        return ExperimentCurveResponse(
            experiment_id=record.id,
            run_id=run_id,
            basis="closed_trade_net_pnl_additive; drawdown_fraction_from_running_peak; "
            "not_engine_mark_to_market",
            initial_capital=str(record.initial_capital),
            accounting_currency=record.accounting_currency,
            limit=limit,
            point_count=0,
            truncated=False,
            unavailable_reason=reason,
            points=[],
        )

    if record.backtest_run_id is None:
        return unavailable("no persisted backtest run for this experiment")
    run = await BacktestRepository(session).get_run_without_trades(record.backtest_run_id)
    if run is None:
        return unavailable(
            "linked backtest run is not persisted", record.backtest_run_id
        )

    rows = await BacktestRepository(session).list_curve_trade_rows(run.id, limit)
    curve = build_realized_curve(
        initial_capital=run.initial_capital,
        period_start=run.period_start,
        trades=rows,
        limit=limit,
    )
    return ExperimentCurveResponse(
        experiment_id=record.id,
        run_id=run.id,
        basis="closed_trade_net_pnl_additive; drawdown_fraction_from_running_peak; "
        "not_engine_mark_to_market",
        initial_capital=str(run.initial_capital),
        accounting_currency=record.accounting_currency,
        limit=limit,
        point_count=len(curve.points),
        truncated=curve.truncated,
        unavailable_reason=(
            "no persisted trades for this run" if not curve.points else None
        ),
        points=[
            {
                "time": point.time,
                "equity": str(point.equity),
                "drawdown": str(point.drawdown),
            }
            for point in curve.points
        ],
    )


@router.get(
    "/{experiment_id}/engine-curves", response_model=ExperimentEngineCurveResponse
)
async def get_experiment_engine_curves(
    experiment_id: str,
    limit: int = Query(5000, ge=1, le=5000),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentEngineCurveResponse:
    """Return a bounded prefix of the engine's persisted mark-to-market curve.

    These are the exact points the engine produced, ordered by the candle index
    that generated them. Timestamps are not unique, and ``drawdown`` is the
    engine's negative absolute quote-currency amount, never an evaluation
    fraction. Legacy runs without a stored series are reported as unavailable
    instead of being reconstructed.
    """
    record = await ExperimentRepository(session).get(experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")

    def unavailable(run_id: str | None, version: str = "unknown") -> ExperimentEngineCurveResponse:
        return ExperimentEngineCurveResponse(
            experiment_id=record.id,
            run_id=run_id,
            basis=EQUITY_SERIES_BASIS,
            accounting_model_version=version,
            accounting_currency=record.accounting_currency,
            limit=limit,
            total_points=0,
            point_count=0,
            truncated=False,
            unavailable_reason="no persisted engine equity series for this run",
            points=[],
        )

    if record.backtest_run_id is None:
        return unavailable(None)
    run = await BacktestRepository(session).get_run_without_trades(record.backtest_run_id)
    if run is None:
        return unavailable(record.backtest_run_id)

    repository = BacktestRepository(session)
    total_points = await repository.count_equity_points(run.id)
    rows = await repository.list_equity_point_rows(run.id, limit)
    points = rows[:limit]
    return ExperimentEngineCurveResponse(
        experiment_id=record.id,
        run_id=run.id,
        basis=EQUITY_SERIES_BASIS,
        accounting_model_version=run.accounting_model_version or "unknown",
        accounting_currency=record.accounting_currency,
        limit=limit,
        total_points=total_points,
        point_count=len(points),
        truncated=len(rows) > limit,
        unavailable_reason=(
            "no persisted engine equity series for this run" if total_points == 0 else None
        ),
        points=[
            {
                "bar_index": bar_index,
                "time": timestamp,
                "equity": str(equity),
                "cash": str(cash),
                "unrealized": str(unrealized),
                "position_side": side,
                "drawdown": str(drawdown),
            }
            for bar_index, timestamp, equity, cash, unrealized, side, drawdown in points
        ],
    )


@router.get("/{experiment_id}/evaluation", response_model=ExperimentEvaluationResponse)
async def get_experiment_evaluation(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentEvaluationResponse:
    record = await ExperimentRepository(session).get(experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")
    if record.evaluation_report_id is None:
        raise HTTPException(
            status_code=404, detail=f"experiment {experiment_id} has no evaluation report"
        )
    report = await EvaluationReportRepository(session).get(record.evaluation_report_id)
    if report is None:
        raise HTTPException(
            status_code=404, detail=f"evaluation report {record.evaluation_report_id} not found"
        )
    return ExperimentEvaluationResponse(
        experiment_id=record.id,
        report_id=report.id,
        report=report.report,
    )


@router.get(
    "/{experiment_id}/verification", response_model=ExperimentVerificationResponse
)
async def get_experiment_verification(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentVerificationResponse:
    """Read only: verify the recorded identity and integrity of an experiment.

    This never reruns a backtest, re-evaluates a report or changes lifecycle
    state. Absent historical evidence is returned explicitly, never inferred.
    """
    try:
        result = await VerificationService(session).verify_experiment(experiment_id)
    except VerificationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except VerificationConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ExperimentVerificationResponse.model_validate(result.as_dict())


@router.post("/{experiment_id}/cancel", response_model=ExperimentRetrieval)
async def cancel_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
    orchestration: ExperimentOrchestrationService = Depends(_orchestration),
) -> ExperimentRetrieval:
    """Cancel a non-terminal experiment without changing any linked results."""
    try:
        record = await orchestration.cancel(experiment_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await session.commit()
    await session.refresh(record, ["updated_at"])
    return _retrieval(record)
