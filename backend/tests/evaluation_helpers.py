"""Synthetic records for evaluation tests.

Nothing here touches a database or a real market series: the helpers build the
persisted shapes the evaluator reads, with exact numbers, so an assertion can be
about arithmetic rather than about a strategy's behaviour.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.backtest import BacktestRunRecord, BacktestTradeRecord
from app.services.evaluation.ledger import TradeLedger, TradeLedgerBuilder
from app.services.evaluation.provenance import RunSnapshot

BASE_TIME = datetime(2024, 1, 1, tzinfo=UTC)


def _decimal(value: float | str | None, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


def trade_record(
    sequence: int,
    *,
    net_pnl: float | str,
    net_r: float | str | None = None,
    gross_pnl: float | str | None = None,
    risk_fraction: float | str | None = "0.01",
    risk_amount: float | str | None = "100",
    fees: float | str = "0",
    spread_cost: float | str = "0",
    slippage_cost: float | str = "0",
    latency_cost: float | str = "0",
    other_costs: float | str = "0",
    side: str = "long",
    exit_reason: str = "target",
    bars_held: int = 3,
    holding_seconds: float | None = 900.0,
    run_id: str = "run-1",
    trade_id: str | None = None,
) -> BacktestTradeRecord:
    costs = _decimal(fees) + _decimal(spread_cost) + _decimal(slippage_cost)
    costs += _decimal(latency_cost) + _decimal(other_costs)
    net = _decimal(net_pnl)
    entry = BASE_TIME + timedelta(minutes=5 * sequence)
    return BacktestTradeRecord(
        id=trade_id or f"trade-{sequence}",
        run_id=run_id,
        sequence=sequence,
        side=side,
        entry_time=entry,
        exit_time=entry + timedelta(minutes=5 * bars_held),
        entry_price=Decimal("50000"),
        exit_price=Decimal("50100"),
        size=Decimal("0.01"),
        notional_value=Decimal("500"),
        gross_pnl=_decimal(gross_pnl) if gross_pnl is not None else net + costs,
        fees=_decimal(fees),
        spread_cost=_decimal(spread_cost),
        slippage_cost=_decimal(slippage_cost),
        latency_cost=_decimal(latency_cost),
        other_costs=_decimal(other_costs),
        net_pnl=net,
        gross_r=_decimal(net_r) if net_r is not None else None,
        net_r=_decimal(net_r) if net_r is not None else None,
        risk_fraction=(
            _decimal(risk_fraction) if risk_fraction is not None else None
        ),
        risk_amount=_decimal(risk_amount) if risk_amount is not None else None,
        bars_held=bars_held,
        holding_seconds=holding_seconds,
        exit_reason=exit_reason,
    )


def ledger_from(
    net_pnls: Sequence[float],
    *,
    r_values: Sequence[float | None] | None = None,
    risk_fraction: float | str | None = "0.01",
    risk_amount: float | str | None = "100",
    costs: Sequence[float] | None = None,
    sides: Sequence[str] | None = None,
    exit_reasons: Sequence[str] | None = None,
    bars_held: Sequence[int] | None = None,
) -> TradeLedger:
    """Build a ledger whose net PnL is exactly ``net_pnls``."""
    builder = TradeLedgerBuilder()
    for index, pnl in enumerate(net_pnls):
        r_value = r_values[index] if r_values is not None else None
        if r_values is None and risk_amount is not None:
            r_value = pnl / float(risk_amount)
        cost = costs[index] if costs is not None else 0.0
        builder.add(
            [
                trade_record(
                    index,
                    net_pnl=pnl,
                    net_r=r_value,
                    risk_fraction=risk_fraction,
                    risk_amount=risk_amount,
                    fees=cost,
                    side=sides[index] if sides else "long",
                    exit_reason=exit_reasons[index] if exit_reasons else "target",
                    bars_held=bars_held[index] if bars_held else 3,
                )
            ]
        )
    return builder.build()


def run_record(
    *,
    run_id: str = "run-1",
    strategy: str = "sma_trend",
    mode: str | None = "research",
    dataset_version: str | None = "candles-v1",
    random_seed: int | None = None,
    initial_capital: str = "10000",
    final_equity: str = "10500",
    metrics: dict[str, object] | None = None,
    parameters: dict[str, object] | None = None,
    fee_rate: str = "0.001",
    spread_rate: str = "0.0002",
    slippage_rate: str = "0.0001",
) -> BacktestRunRecord:
    return BacktestRunRecord(
        id=run_id,
        strategy_name=strategy,
        strategy_version="1",
        symbol="BTCUSDT",
        timeframe="5m",
        period_start=BASE_TIME,
        period_end=BASE_TIME + timedelta(days=30),
        candle_count=8640,
        initial_capital=Decimal(initial_capital),
        final_equity=Decimal(final_equity),
        fee_rate=Decimal(fee_rate),
        spread_rate=Decimal(spread_rate),
        slippage_rate=Decimal(slippage_rate),
        latency_bars=1,
        cost_scale=Decimal("1"),
        parameters=parameters if parameters is not None else {"fast": 10, "slow": 30},
        metrics=metrics if metrics is not None else {"max_drawdown": 0.12, "trade_count": 5},
        dataset_version=dataset_version,
        random_seed=random_seed,
        mode=mode,
    )


def snapshot_from(record: BacktestRunRecord) -> RunSnapshot:
    return RunSnapshot.from_record(record)
