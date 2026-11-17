"""Synthetic demonstration strategies for the Stage 3C contract.

These are architecture probes, **not** trading hypotheses. Each class shows one
style of strategy that the common contract can express without editing the
engine. None of them can submit an order, move cash or touch the engine; they
only read a :class:`~app.services.strategy.contract.DecisionContext` and return
decisions. ``capabilities`` is a class attribute (no annotation) so it is not
mistaken for a configurable dataclass field.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.schemas.market_data import CandleData

from .capabilities import ConfigField, StrategyCapabilities
from .contract import (
    DecisionContext,
    DecisionKind,
    Finalizable,
    Initializable,
    Stateful,
    StrategyDecision,
)


def _sma(history: Sequence[CandleData], period: int) -> Decimal | None:
    if len(history) < period:
        return None
    window = history[-period:]
    return sum((candle.close for candle in window), Decimal(0)) / Decimal(period)


@dataclass
class SmaCrossoverStrategy:
    """Simple directional: enter long on a cross-up, exit on a cross-down."""

    name: str = "sma_crossover_demo"
    fast: int = 3
    slow: int = 10

    capabilities = StrategyCapabilities(
        name="sma_crossover_demo",
        input_data=frozenset({"ohlcv"}),
        instruments="single",
        warmup_bars=2,
        outputs=frozenset(
            {DecisionKind.HOLD, DecisionKind.ENTER_LONG, DecisionKind.EXIT_LONG}
        ),
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        fast = _sma(context.history, self.fast)
        slow = _sma(context.history, self.slow)
        if fast is None or slow is None:
            return StrategyDecision(DecisionKind.HOLD, reason="warming up")
        if context.position is None:
            if fast > slow:
                return StrategyDecision(DecisionKind.ENTER_LONG, reason="fast above slow")
            return StrategyDecision(DecisionKind.HOLD, reason="no cross-up")
        if fast < slow:
            return StrategyDecision(DecisionKind.EXIT_LONG, reason="fast below slow")
        return StrategyDecision(DecisionKind.HOLD, reason="trend intact")


@dataclass
class StatefulExitStrategy(Initializable, Finalizable, Stateful):
    """Stateful: enter once, then exit after a configured number of bars."""

    name: str = "stateful_exit_demo"
    hold_bars: int = 4

    capabilities = StrategyCapabilities(
        name="stateful_exit_demo",
        input_data=frozenset({"ohlcv"}),
        instruments="single",
        stateful=True,
        outputs=frozenset(
            {DecisionKind.HOLD, DecisionKind.ENTER_LONG, DecisionKind.EXIT_LONG}
        ),
    )

    def __post_init__(self) -> None:
        self._bars_seen = 0
        self._entry_index: int | None = None
        self._finalized = False

    def initialize(self, context: DecisionContext) -> None:
        self._bars_seen = 0
        self._entry_index = None
        self._finalized = False

    def decide(self, context: DecisionContext) -> StrategyDecision:
        self._bars_seen += 1
        if context.position is None:
            if self._entry_index is None:
                self._entry_index = context.index
                return StrategyDecision(DecisionKind.ENTER_LONG, reason="stateful entry")
            return StrategyDecision(DecisionKind.HOLD, reason="waiting for fill")
        entry = self._entry_index if self._entry_index is not None else context.index
        held = context.index - entry
        if held >= self.hold_bars:
            return StrategyDecision(DecisionKind.EXIT_LONG, reason="hold period elapsed")
        return StrategyDecision(DecisionKind.HOLD, reason="still holding")

    def finalize(self, context: DecisionContext) -> None:
        self._finalized = True

    def state(self) -> dict[str, Any]:
        return {
            "bars_seen": self._bars_seen,
            "entry_index": self._entry_index,
            "finalized": self._finalized,
        }

    def restore_state(self, state: Mapping[str, Any]) -> None:
        self._bars_seen = int(state["bars_seen"])
        self._entry_index = state["entry_index"]
        self._finalized = bool(state["finalized"])


@dataclass
class GroupedPairsStrategy:
    """Multi-instrument: one coordinated group with a long and a short leg.

    The current engine is single-instrument, so this strategy is *rejected* by a
    capability check rather than silently run with one leg missing. It is kept
    here to prove the contract can describe grouped, multi-instrument intent.
    """

    name: str = "grouped_pairs_demo"
    group: str = "pair"

    capabilities = StrategyCapabilities(
        name="grouped_pairs_demo",
        input_data=frozenset({"ohlcv"}),
        instruments="multi",
        outputs=frozenset(
            {
                DecisionKind.HOLD,
                DecisionKind.ENTER_LONG,
                DecisionKind.ENTER_SHORT,
            }
        ),
    )

    def decide(self, context: DecisionContext) -> list[StrategyDecision]:
        if len(context.instruments) < 2:
            raise ValueError("grouped pairs requires at least two instruments")
        long_leg, short_leg = context.instruments[0], context.instruments[1]
        return [
            StrategyDecision(
                DecisionKind.ENTER_LONG,
                instrument=long_leg,
                group_id=self.group,
                reason="relative-value long leg",
            ),
            StrategyDecision(
                DecisionKind.ENTER_SHORT,
                instrument=short_leg,
                group_id=self.group,
                reason="relative-value short leg",
            ),
        ]


@dataclass
class TargetExposureStrategy:
    """Portfolio style: express a desired exposure, not a unit quantity."""

    name: str = "target_exposure_demo"
    exposure: Decimal = Decimal("0.25")

    capabilities = StrategyCapabilities(
        name="target_exposure_demo",
        input_data=frozenset({"ohlcv"}),
        instruments="single",
        outputs=frozenset({DecisionKind.HOLD, DecisionKind.SET_TARGET_EXPOSURE}),
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        sma = _sma(context.history, 5)
        if sma is None:
            return StrategyDecision(DecisionKind.HOLD, reason="warming up")
        target = self.exposure if context.bar.close > sma else Decimal(0)
        return StrategyDecision(
            DecisionKind.SET_TARGET_EXPOSURE,
            target_exposure=target,
            reason="price versus short SMA target",
        )


@dataclass
class ProbabilityStrategy:
    """ML style: a synthetic probability becomes confidence, never a size.

    The decision carries only direction and confidence. Portfolio construction,
    not this strategy, decides what exposure a directional decision means.
    """

    name: str = "probability_demo"
    buy_threshold: float = 0.6
    sell_threshold: float = 0.4

    capabilities = StrategyCapabilities(
        name="probability_demo",
        input_data=frozenset({"ohlcv"}),
        instruments="single",
        outputs=frozenset(
            {DecisionKind.HOLD, DecisionKind.ENTER_LONG, DecisionKind.ENTER_SHORT}
        ),
        config_schema={
            "name": ConfigField(str),
            "buy_threshold": ConfigField(float, minimum=0.0, maximum=1.0),
            "sell_threshold": ConfigField(float, minimum=0.0, maximum=1.0),
        },
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        if len(context.history) < 2:
            return StrategyDecision(DecisionKind.HOLD, reason="warming up")
        previous = context.history[-2].close
        change = (context.bar.close - previous) / previous
        probability = min(1.0, max(0.0, float(Decimal("0.5") + change / Decimal(2))))
        if probability >= self.buy_threshold:
            return StrategyDecision(
                DecisionKind.ENTER_LONG, confidence=probability, reason="predicted up"
            )
        if probability <= self.sell_threshold:
            return StrategyDecision(
                DecisionKind.ENTER_SHORT, confidence=probability, reason="predicted down"
            )
        return StrategyDecision(
            DecisionKind.HOLD, confidence=probability, reason="no directional edge"
        )


@dataclass
class OrderBookStrategy:
    """Requires order-book data, which the OHLCV environment cannot provide."""

    name: str = "order_book_demo"

    capabilities = StrategyCapabilities(
        name="order_book_demo",
        input_data=frozenset({"order_book"}),
        instruments="single",
        outputs=frozenset({DecisionKind.HOLD, DecisionKind.ENTER_LONG}),
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        if "order_book" not in context.features:
            return StrategyDecision(DecisionKind.HOLD, reason="no order book")
        return StrategyDecision(DecisionKind.ENTER_LONG, reason="order-book imbalance")


@dataclass
class EventDrivenStrategy:
    """Requires a trade event stream, absent from bar-only environments."""

    name: str = "event_driven_demo"

    capabilities = StrategyCapabilities(
        name="event_driven_demo",
        input_data=frozenset({"ohlcv"}),
        event_types=frozenset({"trade"}),
        instruments="single",
        outputs=frozenset({DecisionKind.HOLD, DecisionKind.ENTER_LONG}),
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        if not context.events:
            return StrategyDecision(DecisionKind.HOLD, reason="no events")
        return StrategyDecision(DecisionKind.ENTER_LONG, reason="trade event")


class MalformedOutputStrategy:
    """Probe: returns something that is not a decision at all."""

    name: str = "malformed_output_demo"

    def decide(self, context: DecisionContext) -> Any:
        return "not a decision"


@dataclass
class UndeclaredOutputStrategy:
    """Probe: emits a decision kind it did not declare."""

    name: str = "undeclared_output_demo"

    capabilities = StrategyCapabilities(
        name="undeclared_output_demo",
        input_data=frozenset({"ohlcv"}),
        instruments="single",
        outputs=frozenset({DecisionKind.HOLD}),
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        return StrategyDecision(DecisionKind.ENTER_LONG, reason="not declared")


__all__ = [
    "EventDrivenStrategy",
    "GroupedPairsStrategy",
    "MalformedOutputStrategy",
    "OrderBookStrategy",
    "ProbabilityStrategy",
    "SmaCrossoverStrategy",
    "StatefulExitStrategy",
    "TargetExposureStrategy",
    "UndeclaredOutputStrategy",
]
