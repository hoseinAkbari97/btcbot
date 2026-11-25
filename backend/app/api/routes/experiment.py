"""Experiment API endpoints.

Research experiment lifecycle endpoints, following the same conventions as
backend/app/api/routes/backtest.py: FastAPI router, Depends(get_db_session),
Pydantic response models, research-only markers.

Endpoints:
- POST /api/v1/experiments — Submit a new experiment
- GET /api/v1/experiments — List experiments with filtering
- GET /api/v1/experiments/{experiment_id} — Retrieve one experiment
- GET /api/v1/experiments/{experiment_id}/status — Status retrieval
- POST /api/v1/experiments/{experiment_id}/compare — Compare compatible experiments
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.experiment import ExperimentRepository
from app.schemas.experiment import (
    ExperimentSubmission,
    ExperimentRetrieval,
    ExperimentComparisonRequest,
    ExperimentStatusResponse,
    ExperimentConfiguration,
)
from app.services.experiment.service import ExperimentOrchestrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


# --- Helper: get orchestration service ---

async def _get_orchestration_service(
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentOrchestrationService:
    return ExperimentOrchestrationService(session)


# --- Endpoint: Submit experiment ---

@router.post(
    "",
    response_model=ExperimentRetrieval,
    status_code=201,
    summary="Submit a new research experiment",
)
async def submit_experiment(
    request: ExperimentSubmission,
    session: AsyncSession = Depends(get_db_session),
    orchestration: ExperimentOrchestrationService = Depends(_get_orchestration_service),
) -> ExperimentRetrieval:
    """Submit a new research experiment.

    The platform validates the configuration, verifies strategy registration
    and data availability, runs the backtest, persists the result, invokes
    automatic evaluation, and returns a complete experiment record with all
    provenance and results.

    The experiment configuration is immutable after submission; use different
    parameter values to create distinct experiments.

    Idempotency: submitting the same configuration and data again creates a
    new experiment (different ID, different creation time) but the
    configuration fingerprint is preserved for comparison purposes.
    """
    try:
        result = await orchestration.submit_experiment(
            strategy=request.strategy,
            start=request.start,
            end=request.end,
            initial_capital=request.initial_capital,
            parameters=request.parameters,
            cost_scale=request.cost_scale,
            mode=request.mode,
            notes=request.notes,
            risk=request.risk_limits.model_dump() if request.risk_limits else None,
        )

        # Build retrieval response
        retrieval = ExperimentRetrieval(
            id=result.experiment.id,
            strategy_name=result.experiment.strategy_name,
            strategy_version=result.experiment.strategy_version,
            symbol=result.experiment.symbol,
            timeframe=result.experiment.timeframe,
            period_start=result.experiment.period_start,
            period_end=result.experiment.period_end,
            initial_capital=result.experiment.initial_capital,
            configuration=result.experiment.configuration,
            status=result.experiment.status,
            notes=result.experiment.notes or "",
            dataset_version=result.experiment.dataset_version,
            random_seed=result.experiment.random_seed,
            backtest_run_id=result.experiment.backtest_run_id,
            evaluation_report_id=result.experiment.evaluation_report_id,
            created_at=result.experiment.created_at,
            updated_at=result.experiment.updated_at,
        )

        return retrieval

    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.error("Unexpected error submitting experiment: %s", error, exc_info=True)
        raise HTTPException(
            status_code=500, detail="internal error submitting experiment"
        ) from error


# --- Endpoint: List experiments ---

@router.get(
    "",
    response_model=list[ExperimentRetrieval],
    summary="List experiments with filtering",
)
async def list_experiments(
    strategy: Optional[str] = Query(
        None, pattern=r"^[A-Za-z0-9_]+$", description="Filter by strategy name"
    ),
    symbol: Optional[str] = Query(
        None, pattern=r"^[A-Za-z0-9/]+$", description="Filter by symbol"
    ),
    timeframe: Optional[str] = Query(
        None, pattern=r"^[0-9]+[mhdw]?$", description="Filter by timeframe"
    ),
    status: Optional[str] = Query(
        None, pattern=r"^(DRAFT|VALIDATING|REJECTED|QUEUED|RUNNING|BACKTEST_COMPLETED|EVALUATING|COMPLETED|FAILED|CANCELLED)$",
        description="Filter by lifecycle status",
    ),
    start_after: Optional[datetime] = Query(
        None, description="List experiments created after this timestamp"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum experiments to return"),
    session: AsyncSession = Depends(get_db_session),
    orchestration: ExperimentOrchestrationService = Depends(_get_orchestration_service),
) -> list[ExperimentRetrieval]:
    """List experiments with optional filtering.

    Filters are applied at the database level where possible. Unrecognized
    filter values are silently ignored (not treated as errors).
    """
    from app.models.experiment import ExperimentRecord

    # Build query
    query = select(ExperimentRecord)

    if strategy is not None:
        query = query.where(ExperimentRecord.strategy_name == strategy)

    if symbol is not None:
        query = query.where(ExperimentRecord.symbol == symbol.upper())

    if timeframe is not None:
        query = query.where(ExperimentRecord.timeframe == timeframe)

    if status is not None:
        query = query.where(ExperimentRecord.status == status)

    if start_after is not None:
        query = query.where(ExperimentRecord.created_at > start_after)

    # Order by creation date, newest first
    query = query.order_by(ExperimentRecord.created_at.desc()).limit(limit)

    records = (await session.execute(query)).scalars().all()

    # Build retrieval responses
    results: list[ExperimentRetrieval] = []
    for record in records:
        retrieval = ExperimentRetrieval(
            id=record.id,
            strategy_name=record.strategy_name,
            strategy_version=record.strategy_version,
            symbol=record.symbol,
            timeframe=record.timeframe,
            period_start=record.period_start,
            period_end=record.period_end,
            initial_capital=str(record.initial_capital),
            configuration=record.configuration or {},
            status=record.status,
            notes=record.notes or "",
            dataset_version=record.dataset_version,
            random_seed=record.random_seed,
            backtest_run_id=record.backtest_run_id,
            evaluation_report_id=record.evaluation_report_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        results.append(retrieval)

    return results


# --- Endpoint: Retrieve one experiment ---

@router.get(
    "/{experiment_id}",
    response_model=ExperimentRetrieval,
    summary="Retrieve an experiment by ID",
)
async def get_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentRetrieval:
    """Retrieve an experiment by its immutable ID.

    The experiment ID never changes after creation. This endpoint returns the
    complete experiment record with its configuration, status, and all linked
    artefacts (backtest run, evaluation report).
    """
    from app.models.experiment import ExperimentRecord

    record = await session.get(ExperimentRecord, experiment_id)
    if record is None:
        raise HTTPException(
            status_code=404, detail=f"experiment {experiment_id} not found"
        )

    retrieval = ExperimentRetrieval(
        id=record.id,
        strategy_name=record.strategy_name,
        strategy_version=record.strategy_version,
        symbol=record.symbol,
        timeframe=record.timeframe,
        period_start=record.period_start,
        period_end=record.period_end,
        initial_capital=str(record.initial_capital),
        configuration=record.configuration or {},
        status=record.status,
        notes=record.notes or "",
        dataset_version=record.dataset_version,
        random_seed=record.random_seed,
        backtest_run_id=record.backtest_run_id,
        evaluation_report_id=record.evaluation_report_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )

    return retrieval


# --- Endpoint: Experiment status ---

@router.get(
    "/{experiment_id}/status",
    response_model=ExperimentStatusResponse,
    summary="Retrieve experiment status",
)
async def get_experiment_status(
    experiment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentStatusResponse:
    """Retrieve just the status and minimal provenance of an experiment.

    Useful for polling or monitoring without fetching the full configuration
    and artefacts.
    """
    from app.models.experiment import ExperimentRecord

    record = await session.get(ExperimentRecord, experiment_id)
    if record is None:
        raise HTTPException(
            status_code=404, detail=f"experiment {experiment_id} not found"
        )

    return ExperimentStatusResponse(
        id=record.id,
        status=record.status,
        strategy_name=record.strategy_name,
        symbol=record.symbol,
        timeframe=record.timeframe,
        period_start=record.period_start,
        period_end=record.period_end,
        initial_capital=str(record.initial_capital),
        created_at=record.created_at,
        updated_at=record.updated_at,
        backtest_run_id=record.backtest_run_id,
        evaluation_report_id=record.evaluation_report_id,
    )


# --- Endpoint: Compare compatible experiments ---

@router.post(
    "/compare",
    summary="Compare compatible experiments",
    response_model=dict[str, Any],
)
async def compare_experiments(
    request: ExperimentComparisonRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Compare multiple experiments using the existing comparison service.

    Selects compatible experiments (same strategy, same environmental assumptions)
    and returns a side-by-side comparison through the existing comparison service.

    If experiments are incompatible, returns the existing explicit incompatibility
    explanations (strategy differences, environmental differences, etc.).

    This endpoint reuses the existing comparison infrastructure; it does not
    duplicate comparison logic.
    """
    from app.services.backtest.comparison import compare_runs

    # Fetch the experiments
    from app.models.experiment import ExperimentRecord

    experiment_ids = request.experiment_ids
    experiments: list[ExperimentRecord] = []

    for exp_id in experiment_ids:
        record = await session.get(ExperimentRecord, exp_id)
        if record is None:
            raise HTTPException(
                status_code=404, detail=f"experiment {exp_id} not found"
            )
        if record.status != COMPLETED:
            raise HTTPException(
                status_code=422,
                detail=f"experiment {exp_id} is not in COMPLETED status; only completed experiments can be compared",
            )
        experiments.append(record)

    # Get the backtest runs for each experiment
    from app.repositories.backtest import BacktestRepository

    repo = BacktestRepository(session)
    run_ids: list[str] = []
    for experiment in experiments:
        run_id = experiment.backtest_run_id
        if run_id is None:
            raise HTTPException(
                status_code=422,
                detail=f"experiment {experiment.id} has no backtest run; cannot compare",
            )
        run_ids.append(run_id)

    # Use the existing comparison service
    try:
        comparison = await compare_runs(session, run_ids)
        return comparison.model_dump()
    except Exception as error:
        raise HTTPException(
            status_code=422, detail=f"comparison failed: {error}"
        ) from error