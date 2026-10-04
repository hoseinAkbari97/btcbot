"""Performance metrics for backtest runs.

Annualisation uses the candle timeframe's own bar count, so 5m and 1d runs
are comparable without the caller having to remember the constant. All values
are Decimal-free floats; they are statistics, not accounting figures.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from app.schemas.market_data import Timeframe

if TYPE_CHECKING:
    from .engine import BacktestRun, EquityPoint

BARS_PER_YEAR = {
    Timeframe.M5: 365 * 24 * 12,
    Timeframe.M15: 365 * 24 * 4,
    Timeframe.H1: 365 * 24,
    Timeframe.H4: 365 * 6,
    Timeframe.D1: 365,
}

ZERO = 0.0
ONE = 1.0

# Annualising a sample shorter than this is meaningless: the exponent
# ``1 / years`` becomes so large that the power overflows, and a 40-minute
# window says nothing about an annual rate in any case.
MIN_CAGR_SPAN_SECONDS = 30 * 24 * 3600


@dataclass
class PerformanceMetrics:
    """Aggregate statistics for one backtest run."""

    initial_capital: float
    final_equity: float
    total_return: float
    cagr: float
    annualized_volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    profit_factor: float
    win_rate: float
    trade_count: int
    average_win: float
    average_loss: float
    expectancy: float
    average_r: float
    total_fees: float
    total_turnover: float
    average_bars_held: float
    exposure: float
    best_trade: float
    worst_trade: float
    monthly_returns: dict[str, float] = field(default_factory=dict)
    yearly_returns: dict[str, float] = field(default_factory=dict)
    #: True when the run spans less than :data:`MIN_CAGR_SPAN_SECONDS`. The
    #: annual figures above are then zero because they are *not reported*, not
    #: because they were measured to be zero — a consumer that treats `0.0` as
    #: "no annual return" rather than "not computable" will quietly draw the
    #: wrong conclusion on a short sample, which is exactly the failure this
    #: module exists to prevent. Check this flag before reading any of
    #: `cagr`, `sharpe`, `sortino`, `calmar`, `annualized_volatility`.
    insufficient_sample: bool = False
    #: The span that actually justifies the annualisation, so a reader can see
    #: how far short of it the run fell.
    sample_span_seconds: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "insufficient_sample": self.insufficient_sample,
            "sample_span_seconds": self.sample_span_seconds,
            "initial_capital": self.initial_capital,
            "final_equity": self.final_equity,
            "total_return": self.total_return,
            "cagr": self.cagr,
            "annualized_volatility": self.annualized_volatility,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "max_drawdown": self.max_drawdown,
            "calmar": self.calmar,
            "profit_factor": self.profit_factor,
            "win_rate": self.win_rate,
            "trade_count": self.trade_count,
            "average_win": self.average_win,
            "average_loss": self.average_loss,
            "expectancy": self.expectancy,
            "average_r": self.average_r,
            "total_fees": self.total_fees,
            "total_turnover": self.total_turnover,
            "average_bars_held": self.average_bars_held,
            "exposure": self.exposure,
            "best_trade": self.best_trade,
            "worst_trade": self.worst_trade,
            "monthly_returns": self.monthly_returns,
            "yearly_returns": self.yearly_returns,
        }


def _returns(curve: list[EquityPoint]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(curve, curve[1:], strict=False):
        if previous.equity == 0:
            continue
        returns.append(float(current.equity - previous.equity) / float(previous.equity))
    return returns


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return ZERO
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _max_drawdown_fraction(curve: list[EquityPoint]) -> float:
    peak = None
    worst = ZERO
    for point in curve:
        equity = float(point.equity)
        peak = equity if peak is None else max(peak, equity)
        if peak > 0:
            worst = min(worst, equity / peak - 1.0)
    return worst


def _period_returns(curve: list[EquityPoint], key) -> dict[str, float]:
    """Return per-period percentage change using the last point of each period."""
    closes: dict[str, float] = {}
    for point in curve:
        closes[key(point.time)] = float(point.equity)

    results: dict[str, float] = {}
    previous: float | None = None
    for bucket in sorted(closes):
        equity = closes[bucket]
        if previous is not None and previous > 0:
            results[bucket] = equity / previous - 1.0
        previous = equity
    return results


def compute_metrics(run: BacktestRun, bars_per_year: int | None = None) -> PerformanceMetrics:
    """Compute the full metric set for a completed run."""
    curve = run.equity_curve
    initial = float(run.initial_capital)
    final = float(run.final_equity)
    period = bars_per_year or BARS_PER_YEAR.get(run.timeframe, 365 * 24 * 12)

    if not curve:
        return PerformanceMetrics(
            initial_capital=initial,
            final_equity=final,
            total_return=ZERO,
            cagr=ZERO,
            annualized_volatility=ZERO,
            sharpe=ZERO,
            sortino=ZERO,
            max_drawdown=ZERO,
            calmar=ZERO,
            profit_factor=ZERO,
            win_rate=ZERO,
            trade_count=len(run.trades),
            average_win=ZERO,
            average_loss=ZERO,
            expectancy=ZERO,
            average_r=ZERO,
            total_fees=ZERO,
            total_turnover=ZERO,
            average_bars_held=ZERO,
            exposure=ZERO,
            best_trade=ZERO,
            worst_trade=ZERO,
            insufficient_sample=True,
            sample_span_seconds=ZERO,
        )

    total_return = (final / initial - 1.0) if initial > 0 else ZERO

    span_seconds = (run.end - run.start).total_seconds() if run.end and run.start else ZERO
    cagr = ZERO
    if span_seconds >= MIN_CAGR_SPAN_SECONDS and initial > 0 and final > 0:
        years = span_seconds / (365.25 * 24 * 3600)
        try:
            cagr = (final / initial) ** (1 / years) - 1.0
        except OverflowError:
            cagr = ZERO

    step_returns = _returns(curve)
    mean_return = sum(step_returns) / len(step_returns) if step_returns else ZERO
    # Whether annualised figures are meaningful at all. Decided before any of
    # them is computed so that every one of them obeys the same guard — an
    # annualised volatility that ignores the span while Sharpe respects it
    # would let a reader pair a meaningless number with a real one.
    annualise = span_seconds >= MIN_CAGR_SPAN_SECONDS
    # On a sub-annual window the sqrt(period) scaling dwarfs the underlying
    # dispersion, so volatility is left per-bar and the *ratio* statistics
    # (Sharpe, Sortino, Calmar) stay unannualised for comparability.
    volatility = _stdev(step_returns) * (math.sqrt(period) if annualise else ONE)
    # Sharpe and Sortino annualise the per-bar mean by sqrt(bars per year). Over
    # a short sample that scaling factor dwarfs the underlying dispersion and
    # produces headline numbers hundreds of times larger than any real ratio, so
    # on a sub-annual window they are reported unannualised instead — comparable
    # across runs, but not to be read as an annual figure.
    scale = math.sqrt(period) if annualise else ONE
    sharpe = (mean_return / _stdev(step_returns)) * scale if _stdev(step_returns) > 0 else ZERO

    downside = [r for r in step_returns if r < 0]
    downside_dev = math.sqrt(sum(r**2 for r in downside) / len(downside)) if downside else ZERO
    sortino = (mean_return / downside_dev) * scale if downside_dev > 0 else ZERO

    max_drawdown = _max_drawdown_fraction(curve)
    calmar = (cagr / abs(max_drawdown)) if max_drawdown < 0 and annualise else ZERO

    pnls = [float(trade.net_pnl) for trade in run.trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))

    r_values = [float(trade.r_multiple) for trade in run.trades if trade.r_multiple is not None]
    turnover = sum(
        float(trade.entry_price) * float(trade.size) + float(trade.exit_price) * float(trade.size)
        for trade in run.trades
    )
    exposed_bars = sum(1 for point in curve if point.position_side is not None)

    return PerformanceMetrics(
        initial_capital=initial,
        final_equity=final,
        total_return=total_return,
        cagr=cagr,
        annualized_volatility=volatility,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_drawdown,
        calmar=calmar,
        profit_factor=(gross_profit / gross_loss) if gross_loss > 0 else ZERO,
        win_rate=(len(wins) / len(pnls)) if pnls else ZERO,
        trade_count=len(run.trades),
        average_win=(gross_profit / len(wins)) if wins else ZERO,
        average_loss=(-gross_loss / len(losses)) if losses else ZERO,
        expectancy=(sum(pnls) / len(pnls)) if pnls else ZERO,
        average_r=(sum(r_values) / len(r_values)) if r_values else ZERO,
        total_fees=sum(float(trade.fees) for trade in run.trades),
        total_turnover=turnover,
        average_bars_held=(
            sum(trade.bars_held for trade in run.trades) / len(run.trades) if run.trades else ZERO
        ),
        exposure=(exposed_bars / len(curve)) if curve else ZERO,
        best_trade=max(pnls) if pnls else ZERO,
        worst_trade=min(pnls) if pnls else ZERO,
        monthly_returns=_period_returns(curve, lambda t: f"{t.year:04d}-{t.month:02d}"),
        yearly_returns=_period_returns(curve, lambda t: f"{t.year:04d}"),
        insufficient_sample=not annualise,
        sample_span_seconds=span_seconds,
    )


def group_monthly_pnl(run: BacktestRun) -> dict[str, float]:
    """Realized net PnL grouped by UTC calendar month."""
    buckets: dict[str, float] = defaultdict(float)
    for trade in run.trades:
        buckets[f"{trade.exit_time.year:04d}-{trade.exit_time.month:02d}"] += float(trade.net_pnl)
    return dict(sorted(buckets.items()))


def summarize_trade_exits(run: BacktestRun) -> dict[str, int]:
    """Count trades by exit reason — useful when auditing stop/target behaviour."""
    counts: dict[str, int] = defaultdict(int)
    for trade in run.trades:
        counts[trade.exit_reason] += 1
    return dict(sorted(counts.items()))