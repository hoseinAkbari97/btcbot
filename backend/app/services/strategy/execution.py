"""Execution planning: approved targets become proposed instructions.

Nothing in this module fills an order, moves cash or contacts a venue. The plan
is an explicit hand-off shape for a future execution layer; today the backtest
adapter translates it into the engine's legacy ``Signal`` and the engine alone
simulates latency, fills, costs, risk enforcement and accounting.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .contract import (
    DecisionContext,
    ExecutionAction,
    ExecutionInstruction,
    PortfolioTarget,
)


@runtime_checkable
class ExecutionPlanner(Protocol):
    def plan(
        self, targets: Sequence[PortfolioTarget], context: DecisionContext
    ) -> tuple[ExecutionInstruction, ...]: ...


@dataclass(frozen=True)
class NextBarMarketPlanner:
    """Plan a market-order attempt at the next available bar's open.

    ``latency_bars`` is carried as intent metadata only. The engine's cost model
    remains the authority on when and how a simulated fill happens.
    """

    latency_bars: int = 1

    def __post_init__(self) -> None:
        if self.latency_bars < 1:
            raise ValueError("latency_bars must be at least 1")

    def plan(
        self, targets: Sequence[PortfolioTarget], context: DecisionContext
    ) -> tuple[ExecutionInstruction, ...]:
        instructions: list[ExecutionInstruction] = []
        for target in targets:
            if target.desired_exposure > 0:
                action = ExecutionAction.OPEN_LONG
            elif target.desired_exposure < 0:
                action = ExecutionAction.OPEN_SHORT
            else:
                action = ExecutionAction.CLOSE
            decision = target.decision
            instructions.append(
                ExecutionInstruction(
                    instrument=target.instrument,
                    action=action,
                    sizing_fraction=abs(target.desired_exposure),
                    order_type="market_at_next_open",
                    stop_price=decision.stop_price,
                    target_price=decision.target_price,
                    valid_until=decision.valid_until,
                    group_id=target.group_id,
                    metadata={
                        "latency_bars": self.latency_bars,
                        "strategy_reason": decision.reason,
                        "confidence": decision.confidence,
                    },
                )
            )
        return tuple(instructions)


__all__ = ["ExecutionPlanner", "NextBarMarketPlanner"]
