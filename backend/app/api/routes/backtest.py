"""Backtest endpoints.

Research only. Nothing here places, routes or simulates an order against an
exchange.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.backtest import BacktestRepository
from app.schemas.backtest import (
    BacktestRequest,
    BacktestRunResponse,
    BacktestRunSummary,
    EquityPointResponse,
    MetricsResponse,
    TradeResponse,
)
from app.schemas.market_data import Timeframe
from app.services.backtest.baselines import STRATEGY_NAMES
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import BacktestRun
from app.services.backtest.risk import RiskEngine
from app.services.backtest.runner import LIBRARY_VERSION, load_candles, run_backtest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])


def _to_summary(record) -> BacktestRunSummary:  # noqa: ANN001 - SQLAlchemy row
    metrics = record.metrics or {}
    return BacktestRunSummary(
        id=record.id,
        strategy_name=record.strategy_name,
        symbol=record.symbol,
        timeframe=record.timeframe,
        period_start=record.period_start,
        period_end=record.period_end,
        candle_count=record.candle_count,
        initial_capital=str(record.initial_capital),
        final_equity=str(record.final_equity),
        total_return=float(metrics.get("total_return", 0.0)),  # type: ignore[arg-type]
        sharpe=float(metrics.get("sharpe", 0.0)),  # type: ignore[arg-type]
        max_drawdown=float(metrics.get("max_drawdown", 0.0)),  # type: ignore[arg-type]
        profit_factor=float(metrics.get("profit_factor", 0.0)),  # type: ignore[arg-type]
        trade_count=int(metrics.get("trade_count", 0)),  # type: ignore[arg-type]
        git_commit=record.git_commit,
        created_at=record.created_at,
    )


def _run_response(result, run_id: str) -> BacktestRunResponse:  # noqa: ANN001
    run: BacktestRun = result.run
    return BacktestRunResponse(
        run_id=run_id,
        strategy=run.strategy_name,
        symbol=run.symbol,
        timeframe=run.timeframe.value,
        period_start=run.start,
        period_end=run.end,
        candle_count=run.bars_processed,
        metrics=MetricsResponse(
            **result.metrics.as_dict(),
            r_distribution=(
                result.r_distribution.as_dict() if result.r_distribution else None
            ),
        ),
        exit_reasons=result.exit_reasons,
        costs={
            "fee_rate": str(run.costs.fee_rate),
            "spread_rate": str(run.costs.spread_rate),
            "slippage_rate": str(run.costs.slippage_rate),
            "latency_bars": run.costs.latency_bars,
            "round_trip_cost_rate": str(run.costs.round_trip_cost_rate()),
        },
        parameters=run.parameters,
        git_commit=result.git_commit,
        mode=run.mode,
        library_version=LIBRARY_VERSION,
        trades=[
            TradeResponse(
                id=trade.id,
                side=trade.side,
                entry_time=trade.entry_time,
                entry_price=str(trade.entry_price),
                exit_time=trade.exit_time,
                exit_price=str(trade.exit_price),
                size=str(trade.size),
                stop_price=str(trade.initial_stop) if trade.initial_stop is not None else None,
                target_price=str(trade.initial_target) if trade.initial_target is not None else None,
                gross_pnl=str(trade.gross_pnl),
                fees=str(trade.fees),
                net_pnl=str(trade.net_pnl),
                r_multiple=float(trade.r_multiple) if trade.r_multiple is not None else None,
                bars_held=trade.bars_held,
                exit_reason=trade.exit_reason,
                signal_time=trade.signal_time,
                order_time=trade.order_time,
                fill_time=trade.fill_time,
                notional_value=str(trade.notional_value),
                risk_fraction=float(trade.risk_fraction) if trade.risk_fraction is not None else None,
                risk_amount=str(trade.risk_amount) if trade.risk_amount is not None else None,
                sizing_model=str(trade.sizing_model),
                spread_cost=str(trade.spread_cost),
                slippage_cost=str(trade.slippage_cost),
                latency_cost=str(trade.latency_cost),
                other_costs=str(trade.other_costs),
                gross_r=float(trade.gross_r) if trade.gross_r is not None else None,
                net_r=float(trade.net_r) if trade.net_r is not None else None,
                mae=float(trade.mae) if trade.mae is not None else None,
                mae_price=str(trade.mae_price) if trade.mae_price is not None else None,
                mfe=float(trade.mfe) if trade.mfe is not None else None,
                mfe_price=str(trade.mfe_price) if trade.mfe_price is not None else None,
                strategy_name=trade.strategy_name,
                strategy_version=trade.strategy_version,
                market_regime=trade.market_regime,
            )
            for trade in run.trades
        ],
        equity_curve=[
            EquityPointResponse(
                time=point.time,
                equity=str(point.equity),
                cash=str(point.cash),
                unrealized=str(point.unrealized),
                position_side=point.position_side,
                drawdown=str(point.drawdown),
            )
            for point in run.equity_curve
        ],
        rejected_signals=run.rejected_signals,
        risk_violations=run.risk_violations,
    )


@router.get("/strategies", response_model=list[str])
async def list_strategies() -> list[str]:
    """Registered baseline strategies available for research runs."""
    return sorted(STRATEGY_NAMES)


@router.post("/run", response_model=BacktestRunResponse)
async def run_backtest_endpoint(
    request: BacktestRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BacktestRunResponse:
    """Run one baseline strategy over stored candles and persist the result."""
    symbol = request.symbol.replace("/", "").upper()
    try:
        timeframe = Timeframe(request.timeframe)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"unsupported timeframe {request.timeframe!r}")

    candles = await load_candles(
        session,
        symbol,
        timeframe,
        request.start,
        request.end,
        request.max_candles,
    )
    if len(candles) < 2:
        raise HTTPException(
            status_code=422,
            detail=(
                "not enough candles for a backtest; ingest data for this symbol/timeframe first "
                f"(found {len(candles)}, need at least 2)"
            ),
        )

    costs = BacktestCosts(
        fee_rate=request.fee_rate,
        spread_rate=request.spread_rate,
        slippage_rate=request.slippage_rate,
        latency_bars=request.latency_bars,
    ).scaled(request.cost_scale)

    risk = (
        RiskEngine(request.risk_limits.to_limits(), request.initial_capital)
        if request.risk_limits is not None
        else None
    )

    try:
        result = run_backtest(
            candles,
            symbol=symbol,
            timeframe=timeframe,
            strategy_name=request.strategy,
            costs=costs,
            initial_capital=request.initial_capital,
            parameters=request.parameters,
            allow_short=request.allow_short,
            risk=risk,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    record = await BacktestRepository(session).save(result, notes=request.notes)
    await session.commit()

    logger.info(
        "backtest completed",
        extra={
            "event": "BACKTEST_COMPLETED",
            "run_id": record.id,
            "strategy": request.strategy,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "candles": result.run.bars_processed,
            "trades": result.metrics.trade_count,
        },
    )
    return _run_response(result, record.id)


@router.get("/runs", response_model=list[BacktestRunSummary])
async def list_backtest_runs(
    symbol: str | None = Query(None, pattern=r"^[A-Za-z0-9/]{6,20}$"),
    timeframe: Timeframe | None = None,
    strategy: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
) -> list[BacktestRunSummary]:
    """List stored backtest runs, newest first."""
    if strategy is not None and strategy not in STRATEGY_NAMES:
        raise HTTPException(status_code=422, detail=f"unknown strategy {strategy!r}")
    normalized = symbol.replace("/", "").upper() if symbol else None
    records = await BacktestRepository(session).list_runs(
        normalized, timeframe, strategy, limit
    )
    return [_to_summary(record) for record in records]


@router.get("/runs/{run_id}", response_model=BacktestRunSummary)
async def get_backtest_run(
    run_id: str, session: AsyncSession = Depends(get_db_session)
) -> BacktestRunSummary:
    record = await BacktestRepository(session).get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"backtest run {run_id} not found")
    return _to_summary(record)