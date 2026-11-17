"""Trade-level statistics over the persisted ledger.

Every figure here is computed from observed trades. Gross and net are kept
apart, R multiples are used only when the whole ledger has them, and undefined
ratios (no losses, no wins) are reported as unavailable instead of as infinity
or zero.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .ledger import BoolArray, FloatArray, TradeLedger

R_PERCENTILES = (5, 25, 50, 75, 95)


def _max_run(mask: BoolArray) -> int:
    """Longest run of True values, vectorised over one dimension."""
    if not mask.size:
        return 0
    cumulative = np.cumsum(mask, dtype=np.int64)
    # Cumulative count at the last non-True cell: the offset of the current run.
    offset = np.maximum.accumulate(np.where(mask, 0, cumulative))
    lengths = np.where(mask, cumulative - offset, 0)
    return int(lengths.max())


def _finite_mean(values: FloatArray) -> float | None:
    if not values.size or not bool(np.isfinite(values).all()):
        return None
    return float(values.mean())


@dataclass(frozen=True)
class TradeStatistics:
    """Observed trade outcomes, gross and net, with cost attribution."""

    trades: int
    wins: int
    losses: int
    scratches: int
    win_rate: float
    loss_rate: float
    average_win: float
    average_loss: float
    payoff_ratio: float | None
    profit_factor: float | None
    gross_profit: float
    gross_profit_before_costs: float
    gross_loss: float
    net_pnl: float
    gross_pnl: float
    expectancy: float
    total_costs: float
    cost_per_trade: float
    cost_breakdown: dict[str, float]
    cost_to_gross_profit: float | None
    total_r: float | None
    average_r: float | None
    median_r: float | None
    stdev_r: float | None
    best_r: float | None
    worst_r: float | None
    r_percentiles: dict[str, float]
    max_consecutive_wins: int
    max_consecutive_losses: int
    win_rate_standard_error: float | None
    r_complete: bool
    long_trades: int
    short_trades: int
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "trades": self.trades,
            "wins": self.wins,
            "losses": self.losses,
            "scratches": self.scratches,
            "win_rate": self.win_rate,
            "loss_rate": self.loss_rate,
            "average_win": self.average_win,
            "average_loss": self.average_loss,
            "payoff_ratio": self.payoff_ratio,
            "profit_factor": self.profit_factor,
            "gross_profit": self.gross_profit,
            "gross_profit_before_costs": self.gross_profit_before_costs,
            "gross_loss": self.gross_loss,
            "net_pnl": self.net_pnl,
            "gross_pnl": self.gross_pnl,
            "expectancy": self.expectancy,
            "total_costs": self.total_costs,
            "cost_per_trade": self.cost_per_trade,
            "cost_breakdown": dict(self.cost_breakdown),
            "cost_to_gross_profit": self.cost_to_gross_profit,
            "total_r": self.total_r,
            "average_r": self.average_r,
            "median_r": self.median_r,
            "stdev_r": self.stdev_r,
            "best_r": self.best_r,
            "worst_r": self.worst_r,
            "r_percentiles": dict(self.r_percentiles),
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
            "win_rate_standard_error": self.win_rate_standard_error,
            "r_complete": self.r_complete,
            "long_trades": self.long_trades,
            "short_trades": self.short_trades,
            "warnings": list(self.warnings),
        }


def analyse_trades(ledger: TradeLedger, *, min_trades: int) -> TradeStatistics:
    """Compute trade statistics, omitting anything the ledger cannot support."""
    warnings: list[str] = []
    pnl = ledger.net_pnl
    trades = ledger.count

    wins_mask = pnl > 0
    losses_mask = pnl < 0
    wins = int(wins_mask.sum())
    losses = int(losses_mask.sum())
    scratches = trades - wins - losses

    gross_profit = float(pnl[wins_mask].sum()) if wins else 0.0
    gross_loss = float(-pnl[losses_mask].sum()) if losses else 0.0
    net_pnl = float(pnl.sum())
    total_costs = ledger.total_costs

    win_rate = wins / trades if trades else 0.0
    loss_rate = losses / trades if trades else 0.0
    average_win = gross_profit / wins if wins else 0.0
    average_loss = -gross_loss / losses if losses else 0.0

    if gross_loss > 0:
        profit_factor: float | None = gross_profit / gross_loss
    else:
        profit_factor = None
        if wins:
            warnings.append(
                "profit factor is undefined: the ledger has no losing trade, so the "
                "denominator would be zero"
            )

    payoff_ratio: float | None = None
    if average_win > 0 and average_loss < 0:
        payoff_ratio = average_win / abs(average_loss)

    cost_breakdown = {
        "fees": float(ledger.fees.sum()),
        "spread": float(ledger.spread.sum()),
        "slippage": float(ledger.slippage.sum()),
        "latency": float(ledger.latency.sum()),
        "other": float(ledger.other.sum()),
    }
    if total_costs > 0:
        cost_breakdown = {name: value / total_costs for name, value in cost_breakdown.items()}

    gross_winnings = float(ledger.gross_pnl[ledger.gross_pnl > 0].sum())
    cost_to_gross_profit = total_costs / gross_winnings if gross_winnings > 0 else None
    if cost_to_gross_profit is not None and cost_to_gross_profit > 1.0:
        warnings.append(
            "transaction costs exceed the winnings measured before costs, so the gross "
            "result is only positive because of the cost add-back"
        )

    if ledger.r_complete:
        r_values = ledger.net_r
        total_r: float | None = float(r_values.sum())
        average_r: float | None = float(r_values.mean())
        median_r: float | None = float(np.median(r_values))
        stdev_r: float | None = float(r_values.std(ddof=1)) if trades > 1 else None
        best_r: float | None = float(r_values.max())
        worst_r: float | None = float(r_values.min())
        r_percentiles = {
            f"p{level:02d}": float(np.percentile(r_values, level)) for level in R_PERCENTILES
        }
    else:
        missing = int((~np.isfinite(ledger.net_r)).sum())
        total_r = average_r = median_r = stdev_r = best_r = worst_r = None
        r_percentiles = {}
        warnings.append(
            f"R-based statistics are omitted: {missing} of {trades} trades have no net R "
            "multiple, and a partial R sample would not be comparable"
        )

    win_rate_standard_error: float | None = None
    if trades >= 2:
        win_rate_standard_error = math.sqrt(win_rate * (1.0 - win_rate) / trades)

    if trades < min_trades:
        warnings.append(
            f"only {trades} trades, below the {min_trades}-trade inference threshold; "
            "these statistics are descriptive, not inferential"
        )

    return TradeStatistics(
        trades=trades,
        wins=wins,
        losses=losses,
        scratches=scratches,
        win_rate=win_rate,
        loss_rate=loss_rate,
        average_win=average_win,
        average_loss=average_loss,
        payoff_ratio=payoff_ratio,
        profit_factor=profit_factor,
        gross_profit=gross_profit,
        gross_profit_before_costs=gross_winnings,
        gross_loss=gross_loss,
        net_pnl=net_pnl,
        gross_pnl=float(ledger.gross_pnl.sum()),
        expectancy=net_pnl / trades if trades else 0.0,
        total_costs=total_costs,
        cost_per_trade=total_costs / trades if trades else 0.0,
        cost_breakdown=cost_breakdown,
        cost_to_gross_profit=cost_to_gross_profit,
        total_r=total_r,
        average_r=average_r,
        median_r=median_r,
        stdev_r=stdev_r,
        best_r=best_r,
        worst_r=worst_r,
        r_percentiles=r_percentiles,
        max_consecutive_wins=_max_run(wins_mask),
        max_consecutive_losses=_max_run(losses_mask),
        win_rate_standard_error=win_rate_standard_error,
        r_complete=ledger.r_complete,
        long_trades=int(ledger.is_long.sum()),
        short_trades=int((~ledger.is_long).sum()),
        warnings=tuple(warnings),
    )
