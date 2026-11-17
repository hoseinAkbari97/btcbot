"""Run-level performance, read from the record and the ledger.

Two sources are kept apart on purpose. Equity-shaped figures come from the run
record, which is what the engine measured; trade-shaped figures come from the
persisted ledger. When the two disagree the report says so instead of picking
the more flattering one, and a statistic the sample cannot support is reported
as unavailable rather than as zero.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .ledger import TradeLedger
from .provenance import RunSnapshot

#: Stated once, so no caller has to guess why a duration is missing.
DRAWDOWN_DURATION_UNAVAILABLE = (
    "equity curve is not persisted; only the run-time maximum drawdown is stored"
)

#: Relative tolerance when cross-checking the record against the ledger.
_CONSISTENCY_TOLERANCE = 1e-6


def _metric_float(metrics: dict[str, object], key: str) -> float | None:
    """Read an optional float from the persisted metrics blob."""
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


@dataclass(frozen=True)
class PerformanceSummary:
    """Headline performance with explicit provenance per figure."""

    initial_capital: float
    final_equity: float
    total_return: float
    total_return_source: str
    net_pnl: float
    gross_pnl: float
    net_return_on_capital: float
    cagr: float | None
    annualized_volatility: float | None
    sharpe: float | None
    sortino: float | None
    calmar: float | None
    max_drawdown: float | None
    max_drawdown_source: str
    drawdown_duration_seconds: float | None
    drawdown_duration_reason: str | None
    exposure: float | None
    time_in_market_fraction: float | None
    average_holding_seconds: float | None
    trade_count: int
    bars_processed: int
    insufficient_sample: bool
    sample_span_seconds: float
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "initial_capital": self.initial_capital,
            "final_equity": self.final_equity,
            "total_return": self.total_return,
            "total_return_source": self.total_return_source,
            "net_pnl": self.net_pnl,
            "gross_pnl": self.gross_pnl,
            "net_return_on_capital": self.net_return_on_capital,
            "cagr": self.cagr,
            "annualized_volatility": self.annualized_volatility,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "calmar": self.calmar,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_source": self.max_drawdown_source,
            "drawdown_duration_seconds": self.drawdown_duration_seconds,
            "drawdown_duration_reason": self.drawdown_duration_reason,
            "exposure": self.exposure,
            "time_in_market_fraction": self.time_in_market_fraction,
            "average_holding_seconds": self.average_holding_seconds,
            "trade_count": self.trade_count,
            "bars_processed": self.bars_processed,
            "insufficient_sample": self.insufficient_sample,
            "sample_span_seconds": self.sample_span_seconds,
            "warnings": list(self.warnings),
        }


def analyse_performance(snapshot: RunSnapshot, ledger: TradeLedger) -> PerformanceSummary:
    """Summarise equity and trade PnL without inventing a missing statistic."""
    warnings: list[str] = []
    metrics = snapshot.metrics

    initial = float(snapshot.initial_capital)
    final = float(snapshot.final_equity)
    total_return = (final - initial) / initial if initial else 0.0

    persisted_return = _metric_float(metrics, "total_return")
    if persisted_return is not None and not math.isclose(
        persisted_return, total_return, rel_tol=_CONSISTENCY_TOLERANCE, abs_tol=1e-12
    ):
        warnings.append(
            "persisted total_return disagrees with final equity over initial capital; "
            "the record is reported as stored"
        )

    net_pnl = float(ledger.net_pnl.sum())
    gross_pnl = float(ledger.gross_pnl.sum())
    residual = (final - initial) - net_pnl
    if abs(residual) > _CONSISTENCY_TOLERANCE * max(abs(initial), 1.0):
        warnings.append(
            "final equity minus initial capital does not equal the summed trade PnL "
            f"({residual:.6f} residual); equity and ledger figures are reported separately"
        )

    insufficient_sample = bool(metrics.get("insufficient_sample", True))
    sample_span_seconds = _metric_float(metrics, "sample_span_seconds") or 0.0

    def annual_metric(key: str) -> float | None:
        if insufficient_sample:
            return None
        return _metric_float(metrics, key)

    if insufficient_sample:
        warnings.append(
            "annualised statistics (CAGR, volatility, Sharpe, Sortino, Calmar) are not "
            "reported: the persisted run flags an insufficient sample span"
        )

    max_drawdown = _metric_float(metrics, "max_drawdown")
    if max_drawdown is None:
        max_drawdown_source = "unavailable: no persisted max_drawdown"
    else:
        max_drawdown_source = "persisted with the run at execution time"

    exposure = _metric_float(metrics, "exposure")

    holding = ledger.holding_seconds
    if ledger.count and bool(np.isfinite(holding).all()):
        average_holding: float | None = float(holding.mean())
        observation = ledger.observation_seconds
        time_in_market: float | None = (
            float(holding.sum()) / observation if observation > 0 else None
        )
        if time_in_market is not None and time_in_market > 1.0:
            warnings.append(
                "summed holding time exceeds the observed span, which implies overlapping "
                "or same-bar positions; the fraction is reported unclamped"
            )
    else:
        average_holding = None
        time_in_market = None
        if ledger.count:
            warnings.append(
                "holding time is missing for at least one trade, so time-in-market is "
                "not reported"
            )

    return PerformanceSummary(
        initial_capital=initial,
        final_equity=final,
        total_return=total_return,
        total_return_source="final equity vs initial capital, as persisted with the run",
        net_pnl=net_pnl,
        gross_pnl=gross_pnl,
        net_return_on_capital=net_pnl / initial if initial else 0.0,
        cagr=annual_metric("cagr"),
        annualized_volatility=annual_metric("annualized_volatility"),
        sharpe=annual_metric("sharpe"),
        sortino=annual_metric("sortino"),
        calmar=annual_metric("calmar"),
        max_drawdown=max_drawdown,
        max_drawdown_source=max_drawdown_source,
        drawdown_duration_seconds=None,
        drawdown_duration_reason=DRAWDOWN_DURATION_UNAVAILABLE,
        exposure=exposure,
        time_in_market_fraction=time_in_market,
        average_holding_seconds=average_holding,
        trade_count=ledger.count,
        bars_processed=snapshot.candle_count,
        insufficient_sample=insufficient_sample,
        sample_span_seconds=sample_span_seconds,
        warnings=tuple(warnings),
    )
