"""Strategy-facing contracts, independent of the backtest engine.

A strategy produces decisions. Portfolio construction turns decisions into
targets; an execution planner turns approved targets into instructions; the
backtest engine remains the only place that simulates fills, costs, risk,
accounting and the trade ledger.
"""

from __future__ import annotations

from .contract import (
    DecisionContext,
    DecisionKind,
    DecisionStrategy,
    ExecutionAction,
    ExecutionInstruction,
    Finalizable,
    Initializable,
    PortfolioTarget,
    PortfolioView,
    PositionView,
    Stateful,
    StrategyDecision,
    normalize_decisions,
)

__all__ = [
    "DecisionContext",
    "DecisionKind",
    "DecisionStrategy",
    "ExecutionAction",
    "ExecutionInstruction",
    "Finalizable",
    "Initializable",
    "PortfolioTarget",
    "PortfolioView",
    "PositionView",
    "Stateful",
    "StrategyDecision",
    "normalize_decisions",
]
