"""Event-driven backtesting: costs, execution, risk, metrics, baselines."""

from __future__ import annotations

from .baselines import (
    STRATEGY_NAMES,
    build_strategy,
    default_parameters,
)
from .costs import BacktestCosts, FillResult, apply_slippage, fill_price
from .engine import BacktestEngine, BacktestRun, OpenPosition, Signal, Trade
from .metrics import PerformanceMetrics, compute_metrics, group_monthly_pnl, summarize_trade_exits
from .risk import RiskDecision, RiskEngine, RiskLimits

__all__ = [
    "STRATEGY_NAMES",
    "BacktestCosts",
    "BacktestEngine",
    "BacktestRun",
    "FillResult",
    "OpenPosition",
    "RiskDecision",
    "RiskEngine",
    "RiskLimits",
    "PerformanceMetrics",
    "Signal",
    "Trade",
    "apply_slippage",
    "build_strategy",
    "compute_metrics",
    "default_parameters",
    "fill_price",
    "group_monthly_pnl",
    "summarize_trade_exits",
]