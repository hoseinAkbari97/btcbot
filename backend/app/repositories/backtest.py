from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.models.backtest import BacktestRunRecord, BacktestTradeRecord
from app.schemas.market_data import Timeframe
from app.services.backtest.runner import BacktestResult

_COST_COLUMNS = ("spread_cost", "slippage_cost", "latency_cost", "other_costs")


class BacktestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _json_safe(value: object) -> object:
        """Coerce a parameter value into something JSON can hold.

        Strategy parameters are ``Decimal`` so that sizing arithmetic stays
        exact, but ``Decimal`` has no JSON representation. Storing the exact
        string preserves the value on a round trip; anything unrecognised is
        stored by its ``repr`` rather than silently dropped, so a
        reproducibility record never loses information.
        """
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {str(key): BacktestRepository._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [BacktestRepository._json_safe(item) for item in value]
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        return repr(value)

    async def save(self, result: BacktestResult, notes: str | None = None) -> BacktestRunRecord:
        """Persist a completed run and its trades.

        Runs are append-only. Nothing here edits an existing experiment.
        """
        run = result.run
        record = BacktestRunRecord(
            id=result.experiment_id or uuid.uuid4().hex,
            strategy_name=run.strategy_name,
            strategy_version=run.strategy_version if hasattr(run, "strategy_version") else "1",
            symbol=run.symbol,
            timeframe=run.timeframe.value,
            period_start=run.start,
            period_end=run.end,
            candle_count=run.bars_processed,
            initial_capital=run.initial_capital,
            final_equity=run.final_equity,
            fee_rate=run.costs.fee_rate,
            spread_rate=run.costs.spread_rate,
            slippage_rate=run.costs.slippage_rate,
            latency_bars=run.costs.latency_bars,
            parameters=self._json_safe(
                {**run.parameters, "run_mode": run.mode}
            ),
            metrics={
                **result.metrics.as_dict(),
                "exit_reasons": result.exit_reasons,
                "monthly_realized_pnl": result.monthly_pnl,
                # The R distribution is stored with the run so the numbers the
                # Monte Carlo project will be handed are the ones that were
                # actually computed here, not a later reconstruction of them.
                "r_distribution": (
                    result.r_distribution.as_dict() if result.r_distribution else None
                ),
            },
            dataset_version=result.dataset_version,
            git_commit=result.git_commit,
            mode=run.mode,
            # Reproducibility inputs are columns, not just parameter JSON. A
            # stored run whose seed is absent cannot be re-derived, and the
            # difference between "seeded at 7" and "not a seeded strategy" is
            # exactly what a later reader cannot reconstruct from `parameters`.
            random_seed=result.random_seed,
            notes=notes,
        )
        self.session.add(record)
        await self.session.flush()

        for trade in run.trades:
            self.session.add(
                BacktestTradeRecord(
                    run_id=record.id,
                    sequence=trade.id,
                    side=trade.side,
                    signal_time=trade.signal_time,
                    order_time=trade.order_time,
                    fill_time=trade.fill_time,
                    entry_time=trade.entry_time,
                    entry_price=trade.entry_price,
                    exit_time=trade.exit_time,
                    exit_price=trade.exit_price,
                    size=trade.size,
                    notional_value=trade.notional_value,
                    stop_price=trade.initial_stop,
                    target_price=trade.initial_target,
                    risk_fraction=trade.risk_fraction,
                    risk_amount=trade.risk_amount,
                    sizing_model=trade.sizing_model,
                    gross_pnl=trade.gross_pnl,
                    fees=trade.fees,
                    spread_cost=trade.spread_cost,
                    slippage_cost=trade.slippage_cost,
                    latency_cost=trade.latency_cost,
                    other_costs=trade.other_costs,
                    net_pnl=trade.net_pnl,
                    gross_r=trade.gross_r,
                    net_r=trade.net_r,
                    r_multiple=trade.r_multiple,
                    mae=trade.mae,
                    mae_price=trade.mae_price,
                    mfe=trade.mfe,
                    mfe_price=trade.mfe_price,
                    bars_held=trade.bars_held,
                    holding_seconds=trade.holding_seconds,
                    capital_fraction=trade.capital_fraction,
                    exposure_fraction=trade.exposure_fraction,
                    exit_reason=trade.exit_reason,
                    strategy_name=trade.strategy_name,
                    strategy_version=trade.strategy_version,
                    market_regime=trade.market_regime,
                    strategy_context=self._json_safe(trade.strategy_context),
                )
            )
        await self.session.flush()
        return record

    async def list_runs(
        self,
        symbol: str | None,
        timeframe: Timeframe | None,
        strategy_name: str | None,
        limit: int,
    ) -> list[BacktestRunRecord]:
        query: Select[tuple[BacktestRunRecord]] = select(BacktestRunRecord)
        if symbol:
            query = query.where(BacktestRunRecord.symbol == symbol)
        if timeframe:
            query = query.where(BacktestRunRecord.timeframe == timeframe.value)
        if strategy_name:
            query = query.where(BacktestRunRecord.strategy_name == strategy_name)
        query = query.order_by(BacktestRunRecord.created_at.desc()).limit(limit)
        return list((await self.session.scalars(query)).all())

    async def get_run(self, run_id: str) -> BacktestRunRecord | None:
        return await self.session.scalar(
            select(BacktestRunRecord).where(BacktestRunRecord.id == run_id)
        )

    async def get_runs_without_trades(
        self, run_ids: Sequence[str]
    ) -> list[BacktestRunRecord]:
        """Fetch run rows without eager-loading their trade lists.

        Comparison reads run-level columns only. ``trades`` is selectin-loaded by
        default, which would pull every trade of every run into memory for no
        reason; this query opts out explicitly.
        """
        query = (
            select(BacktestRunRecord)
            .where(BacktestRunRecord.id.in_(run_ids))
            .options(lazyload(BacktestRunRecord.trades))
        )
        return list((await self.session.scalars(query)).all())

    async def summarize_execution_costs(
        self, run_ids: Sequence[str]
    ) -> dict[str, dict[str, Decimal]]:
        """Sum persisted itemised trade costs, one aggregate row per run.

        The database does the addition, so a comparison never materialises a
        run's ledger merely to total four columns.
        """
        zero = Decimal(0)
        query = (
            select(
                BacktestTradeRecord.run_id,
                func.coalesce(func.sum(BacktestTradeRecord.spread_cost), zero).label(
                    "spread_cost"
                ),
                func.coalesce(func.sum(BacktestTradeRecord.slippage_cost), zero).label(
                    "slippage_cost"
                ),
                func.coalesce(func.sum(BacktestTradeRecord.latency_cost), zero).label(
                    "latency_cost"
                ),
                func.coalesce(func.sum(BacktestTradeRecord.other_costs), zero).label(
                    "other_costs"
                ),
            )
            .where(BacktestTradeRecord.run_id.in_(run_ids))
            .group_by(BacktestTradeRecord.run_id)
        )
        totals = {
            row.run_id: {
                "spread_cost": Decimal(row.spread_cost),
                "slippage_cost": Decimal(row.slippage_cost),
                "latency_cost": Decimal(row.latency_cost),
                "other_costs": Decimal(row.other_costs),
            }
            for row in await self.session.execute(query)
        }
        return {
            run_id: totals.get(run_id, {name: zero for name in _COST_COLUMNS})
            for run_id in run_ids
        }

    async def list_trades(
        self, run_id: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[BacktestTradeRecord]:
        query = select(BacktestTradeRecord).where(BacktestTradeRecord.run_id == run_id)
        if start:
            query = query.where(BacktestTradeRecord.entry_time >= start)
        if end:
            query = query.where(BacktestTradeRecord.entry_time < end)
        return list((await self.session.scalars(query.order_by(BacktestTradeRecord.sequence))).all())