"""The three deliberately separate outputs of the strategy pipeline.

``StrategyDecision`` is what a strategy *wants*. ``PortfolioTarget`` is what
portfolio construction decides the account *should hold*. ``ExecutionInstruction``
is how the execution layer proposes to get there. A directional decision carries
no size: attaching one would couple strategy logic to sizing and risk, which are
owned by later layers.

These types do not fill orders, move cash or touch the engine. The adapter at the
backtest boundary is the only code that translates an instruction into the
engine's legacy ``Signal``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from app.schemas.market_data import CandleData, Timeframe


class DecisionKind(str, Enum):
    """The intents a strategy may express.

    Extensible by adding a member and a corresponding case in portfolio
    construction; unknown intents are rejected rather than silently ignored.
    """

    HOLD = "hold"
    ENTER_LONG = "enter_long"
    ENTER_SHORT = "enter_short"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    SET_TARGET_EXPOSURE = "set_target_exposure"


@dataclass(frozen=True)
class StrategyDecision:
    """One strategy intent, with provenance and optional qualifiers.

    ``confidence``, ``valid_until`` and ``metadata`` are descriptive: the
    adapter neither ranks nor acts on them beyond expiry and construction. A
    signal's confidence is never a position size.
    """

    kind: DecisionKind
    instrument: str | None = None
    confidence: float | None = None
    valid_until: datetime | None = None
    target_exposure: Decimal | None = None
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    group_id: str | None = None
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, DecisionKind):
            raise ValueError(f"decision kind must be a DecisionKind, got {self.kind!r}")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0 and 1, got {self.confidence!r}")
        if self.target_exposure is not None and not (
            Decimal(-1) <= self.target_exposure <= Decimal(1)
        ):
            raise ValueError(
                f"target_exposure must be between -1 and 1, got {self.target_exposure!r}"
            )
        if self.kind is DecisionKind.SET_TARGET_EXPOSURE and self.target_exposure is None:
            raise ValueError("SET_TARGET_EXPOSURE requires a target_exposure")
        if self.instrument is not None and not self.instrument.strip():
            raise ValueError("decision instrument must be a non-empty string")
        if self.group_id is not None and not self.group_id.strip():
            raise ValueError("decision group_id must be a non-empty string")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class PortfolioTarget:
    """The desired exposure after portfolio construction.

    ``desired_exposure`` is a signed fraction of equity: positive long, negative
    short, zero flat. It is an intention at the account level, not an order and
    not a quantity of units.
    """

    instrument: str
    desired_exposure: Decimal
    decision: StrategyDecision
    group_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.instrument.strip():
            raise ValueError("target instrument must be a non-empty string")
        if not Decimal(-1) <= self.desired_exposure <= Decimal(1):
            raise ValueError(f"desired_exposure out of range: {self.desired_exposure!r}")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class ExecutionAction(str, Enum):
    NONE = "none"
    OPEN_LONG = "open_long"
    OPEN_SHORT = "open_short"
    CLOSE = "close"


@dataclass(frozen=True)
class ExecutionInstruction:
    """How execution proposes to pursue one approved target.

    This is a plan, not an order: there is no venue, order id or fill here. The
    engine remains responsible for latency, fills, costs and position updates.
    """

    instrument: str
    action: ExecutionAction
    sizing_fraction: Decimal
    order_type: str = "market_at_next_open"
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    valid_until: datetime | None = None
    group_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.instrument.strip():
            raise ValueError("instruction instrument must be a non-empty string")
        if not Decimal(0) <= self.sizing_fraction <= Decimal(1):
            raise ValueError(f"sizing_fraction out of range: {self.sizing_fraction!r}")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class PositionView:
    """Read-only view of an open position, never the engine's mutable object."""

    side: str
    size: Decimal
    entry_price: Decimal
    unrealized_pnl: Decimal
    stop_price: Decimal | None = None
    target_price: Decimal | None = None


@dataclass(frozen=True)
class PortfolioView:
    """Portfolio state a strategy may inspect but cannot change."""

    equity: Decimal
    instruments: tuple[str, ...]
    open_position_count: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class DecisionContext:
    """All information a decision-making strategy is authorised to read.

    Deliberately absent: any session, account handle, order entry point, venue
    connection or mutable engine state. ``history`` is the engine's own truncated
    slice and is not copied; consumers must treat it as read-only.
    """

    instrument: str
    timeframe: Timeframe
    index: int
    timestamp: datetime
    bar: CandleData
    history: Sequence[CandleData]
    equity: Decimal
    position: PositionView | None
    portfolio: PortfolioView
    config: Mapping[str, Any] = field(default_factory=dict)
    features: Mapping[str, Any] = field(default_factory=dict)
    events: Sequence[Any] = ()
    instruments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("config", "features"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))
        if not self.instruments:
            object.__setattr__(self, "instruments", (self.instrument,))


@runtime_checkable
class DecisionStrategy(Protocol):
    """The new-style contract: decide from a read-only context."""

    def decide(
        self, context: DecisionContext
    ) -> StrategyDecision | Sequence[StrategyDecision]: ...


@runtime_checkable
class Initializable(Protocol):
    def initialize(self, context: DecisionContext) -> None: ...


@runtime_checkable
class Finalizable(Protocol):
    def finalize(self, context: DecisionContext) -> None: ...


@runtime_checkable
class Stateful(Protocol):
    def state(self) -> dict[str, Any]: ...

    def restore_state(self, state: Mapping[str, Any]) -> None: ...


def normalize_decisions(
    result: StrategyDecision | Sequence[StrategyDecision],
) -> tuple[StrategyDecision, ...]:
    """Normalise one decision or a sequence, rejecting malformed outputs."""
    if isinstance(result, StrategyDecision):
        return (result,)
    if isinstance(result, str | bytes | Mapping) or not isinstance(result, Sequence):
        raise ValueError("decide() must return a StrategyDecision or a sequence of them")
    decisions = tuple(result)
    if not decisions:
        raise ValueError("decide() returned no decisions; return HOLD explicitly instead")
    if not all(isinstance(decision, StrategyDecision) for decision in decisions):
        raise ValueError("decide() returned an item that is not a StrategyDecision")
    return decisions
