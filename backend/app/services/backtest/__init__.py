"""Event-driven backtesting: costs, execution, risk, metrics, baselines."""

from __future__ import annotations

from .baselines import build_strategy, default_parameters  # registers the baselines
from .costs import BacktestCosts, FillResult, apply_slippage, fill_price
from .engine import BacktestEngine, BacktestRun, OpenPosition, Signal, Trade
from .metrics import PerformanceMetrics, compute_metrics, group_monthly_pnl, summarize_trade_exits
from .registry import (
    STRATEGY_NAMES,
    Strategy,
    StrategyRegistry,
    default_registry,
    register_strategy,
)
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
    "Strategy",
    "StrategyRegistry",
    "Trade",
    "apply_slippage",
    "build_strategy",
    "compute_metrics",
    "default_parameters",
    "default_registry",
    "fill_price",
    "register_strategy",
    "group_monthly_pnl",
    "summarize_trade_exits",
]