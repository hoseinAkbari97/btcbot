"""The single boundary where new-style strategies enter the existing engine.

The engine is not duplicated or edited per strategy. It still calls a callable
with a legacy ``StrategyContext`` and receives a legacy ``Signal``. The adapter
builds the richer, read-only decision context, runs the decision → target →
instruction pipeline, and collapses the result into the one instruction the
single-instrument engine can act on. Risk enforcement, fills, costs and
accounting stay inside the engine and remain the authority.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from app.services.backtest.engine import (
    CLOSE,
    HOLD,
    OPEN_LONG,
    OPEN_SHORT,
    Signal,
)
from app.services.backtest.engine import (
    StrategyContext as LegacyStrategyContext,
)
from app.services.backtest.registry import StrategyRegistry, default_registry

from .capabilities import (
    CapabilityError,
    StrategyCapabilities,
    StrategyEnvironment,
    infer_capabilities,
    validate_capabilities,
    validate_config,
    validate_outputs,
)
from .construction import ExposurePortfolioConstructor, PortfolioConstructor
from .contract import (
    DecisionContext,
    ExecutionAction,
    ExecutionInstruction,
    Finalizable,
    Initializable,
    PortfolioTarget,
    PortfolioView,
    PositionView,
    Stateful,
    normalize_decisions,
)
from .execution import ExecutionPlanner, NextBarMarketPlanner


@dataclass
class PreparedStrategy:
    """A strategy ready for the unchanged backtest engine."""

    logic: Callable[[LegacyStrategyContext], Signal]
    strategy: object
    finalize: Callable[[], None]
    capabilities: StrategyCapabilities | None
    state: Callable[[], dict[str, Any] | None]


class StrategyAdapter:
    """Adapt a decision-producing strategy to the engine's callable contract."""

    def __init__(
        self,
        strategy: object,
        capabilities: StrategyCapabilities | None,
        environment: StrategyEnvironment,
        config: Mapping[str, Any],
        name: str,
        *,
        constructor: PortfolioConstructor | None = None,
        planner: ExecutionPlanner | None = None,
        features: Mapping[str, Any] | None = None,
    ) -> None:
        self.strategy = strategy
        self.capabilities = capabilities
        self.environment = environment
        self.config = MappingProxyType(dict(config))
        self.name = name
        self._constructor = constructor or ExposurePortfolioConstructor()
        self._planner = planner or NextBarMarketPlanner()
        self._features = MappingProxyType(dict(features or {}))
        self._initialized = False
        self._last_context: DecisionContext | None = None

    def _context(self, legacy: LegacyStrategyContext) -> DecisionContext:
        history = legacy.history
        bar = history[-1]
        position: PositionView | None = None
        if legacy.position is not None:
            open_position = legacy.position
            position = PositionView(
                side=open_position.side,
                size=open_position.size,
                entry_price=open_position.entry_price,
                unrealized_pnl=open_position.unrealized(bar.close),
                stop_price=open_position.stop_price,
                target_price=open_position.target_price,
            )
        portfolio = PortfolioView(
            equity=legacy.equity,
            instruments=self.environment.instruments,
            open_position_count=1 if position is not None else 0,
        )
        return DecisionContext(
            instrument=legacy.symbol,
            timeframe=legacy.timeframe,
            index=legacy.index,
            timestamp=bar.close_time,
            bar=bar,
            history=history,
            equity=legacy.equity,
            position=position,
            portfolio=portfolio,
            config=self.config,
            features=self._features,
            events=(),
            instruments=self.environment.instruments,
        )

    @staticmethod
    def _select(
        instructions: tuple[ExecutionInstruction, ...], instrument: str
    ) -> ExecutionInstruction | None:
        for instruction in instructions:
            if instruction.instrument == instrument:
                return instruction
        return instructions[0] if instructions else None

    @staticmethod
    def _signal(instruction: ExecutionInstruction | None) -> Signal:
        if instruction is None or instruction.action is ExecutionAction.NONE:
            return Signal(kind=HOLD, reason="no execution instruction")
        if instruction.action is ExecutionAction.CLOSE:
            return Signal(kind=CLOSE, reason="portfolio target is flat")
        # A bare directional decision supplies no brackets. Let the engine apply
        # its default brackets (as it does for Stage 3B signals) rather than
        # opening a stopless position; explicit brackets from the decision are
        # kept because the engine only fills in the missing side.
        kind = OPEN_LONG if instruction.action is ExecutionAction.OPEN_LONG else OPEN_SHORT
        return Signal(
            kind=kind,
            stop_price=instruction.stop_price,
            target_price=instruction.target_price,
            risk_fraction=instruction.sizing_fraction,
            use_default_brackets=True,
            reason=str(instruction.metadata.get("strategy_reason", "")),
        )

    def __call__(self, legacy: LegacyStrategyContext) -> Signal:
        context = self._context(legacy)
        self._last_context = context
        if not self._initialized:
            if isinstance(self.strategy, Initializable):
                self.strategy.initialize(context)
            self._initialized = True

        decide = getattr(self.strategy, "decide", None)
        if not callable(decide):
            # Stage 3B callable: unchanged behaviour through the same pipeline.
            return self.strategy(legacy)  # type: ignore[operator, no-any-return]

        decisions = normalize_decisions(decide(context))
        if self.capabilities is not None:
            validate_outputs(decisions, self.capabilities, self.environment)
        targets: tuple[PortfolioTarget, ...] = self._constructor.build(decisions, context)
        instructions = self._planner.plan(targets, context)
        return self._signal(self._select(instructions, context.instrument))

    def finish(self) -> None:
        """Run the optional finaliser once, after the engine has finished."""
        if self._last_context is not None and isinstance(self.strategy, Finalizable):
            self.strategy.finalize(self._last_context)

    def state(self) -> dict[str, Any] | None:
        if isinstance(self.strategy, Stateful):
            return self.strategy.state()
        return None


def prepare_strategy(
    strategy_name: str,
    parameters: Mapping[str, Any],
    environment: StrategyEnvironment,
    *,
    registry: StrategyRegistry | None = None,
    constructor: PortfolioConstructor | None = None,
    planner: ExecutionPlanner | None = None,
    features: Mapping[str, Any] | None = None,
) -> PreparedStrategy:
    """Validate, build and adapt a registered strategy for one run."""
    active = registry or default_registry
    definition = active.definition(strategy_name)
    config = {**definition.default_parameters(), **parameters}

    # A declaration attached at registration time is known before construction,
    # so the environment and config are checked before any strategy code runs.
    declared = definition.capabilities
    if declared is not None:
        validate_capabilities(declared, environment)
        validate_config(declared, config)

    instance = definition.create(**config)
    capabilities = declared or infer_capabilities(instance)

    # Capabilities declared on the instance itself are only visible after it is
    # built, but are still validated before the strategy is used in a run.
    if capabilities is not None and declared is None:
        validate_capabilities(capabilities, environment)
        validate_config(capabilities, config)

    uses_new_contract = callable(getattr(instance, "decide", None))
    if not uses_new_contract:
        if capabilities is not None and capabilities.input_data != frozenset({"ohlcv"}):
            raise CapabilityError(
                f"strategy {strategy_name!r} declares non-OHLCV inputs but has no decide() "
                "method; a compatibility strategy cannot consume them"
            )
        return PreparedStrategy(
            logic=instance,
            strategy=instance,
            finalize=lambda: None,
            capabilities=capabilities,
            state=lambda: None,
        )

    adapter = StrategyAdapter(
        instance,
        capabilities,
        environment,
        config,
        strategy_name,
        constructor=constructor,
        planner=planner,
        features=features,
    )
    return PreparedStrategy(
        logic=adapter,
        strategy=instance,
        finalize=adapter.finish,
        capabilities=capabilities,
        state=adapter.state,
    )


__all__ = ["PreparedStrategy", "StrategyAdapter", "prepare_strategy"]
