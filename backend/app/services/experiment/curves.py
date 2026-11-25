"""Bounded curve projection from persisted closed trades.

The backtest engine's full mark-to-market equity curve is transient and is not
stored with a run. This module derives only what the persisted ledger supports:
equity after each closed trade, starting from the run's recorded initial
capital. It never re-runs a backtest, edits a run, or reconstructs intrabar
equity. The API labels the result accordingly so it cannot be mistaken for the
engine's original curve.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

#: Ordered ledger rows: sequence, exit time, already-net-of-costs PnL.
CurveTradeRow = tuple[int, datetime, Decimal]


@dataclass(frozen=True)
class CurvePoint:
    time: datetime
    equity: Decimal
    drawdown: Decimal


@dataclass(frozen=True)
class RealizedCurve:
    points: tuple[CurvePoint, ...]
    truncated: bool


def build_realized_curve(
    *,
    initial_capital: Decimal,
    period_start: datetime | None,
    trades: list[CurveTradeRow],
    limit: int,
) -> RealizedCurve:
    """Project realized equity and drawdown from at most ``limit`` trades.

    Trades are ordered by closing time, with sequence breaking ties. Duplicate
    closing times remain separate cumulative steps; the presentation layer
    collapses them without shifting their timestamp. A zero-trade run has no
    curve rather than a fabricated flat line.
    """
    ordered = sorted(trades, key=lambda row: (row[1], row[0]))
    truncated = len(ordered) > limit
    ordered = ordered[:limit]
    if not ordered:
        return RealizedCurve(points=(), truncated=truncated)

    equity = Decimal(initial_capital)
    peak = equity
    points: list[CurvePoint] = []
    if period_start is not None and period_start < ordered[0][1]:
        points.append(CurvePoint(time=period_start, equity=equity, drawdown=Decimal(0)))

    for _sequence, exit_time, net_pnl in ordered:
        equity += Decimal(net_pnl)
        peak = max(peak, equity)
        drawdown = equity / peak - Decimal(1) if peak > 0 else Decimal(0)
        points.append(CurvePoint(time=exit_time, equity=equity, drawdown=drawdown))

    return RealizedCurve(points=tuple(points), truncated=truncated)
