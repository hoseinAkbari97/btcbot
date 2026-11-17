"""Portfolio construction: decisions become desired exposures, not orders.

This layer owns the default size a directional signal implies. A signal that
says "long" carries no size; the configured exposure does. That separation is
what lets the same signal be reused with a different sizing policy without
editing the strategy.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from .contract import DecisionContext, DecisionKind, PortfolioTarget, StrategyDecision


@runtime_checkable
class PortfolioConstructor(Protocol):
    def build(
        self, decisions: Sequence[StrategyDecision], context: DecisionContext
    ) -> tuple[PortfolioTarget, ...]: ...


@dataclass(frozen=True)
class ExposureConstructorConfig:
    """Policy inputs owned by portfolio construction, never by a strategy."""

    default_exposure: Decimal = Decimal("0.01")
    allow_shorts: bool = True
    max_abs_exposure: Decimal = Decimal("1")
    max_targets: int = 8

    def __post_init__(self) -> None:
        if not Decimal(0) < self.default_exposure <= self.max_abs_exposure:
            raise ValueError("default_exposure must be positive and within max_abs_exposure")
        if not Decimal(0) < self.max_abs_exposure <= Decimal(1):
            raise ValueError("max_abs_exposure must be within (0, 1]")
        if self.max_targets < 1:
            raise ValueError("max_targets must be at least 1")


class ExposurePortfolioConstructor:
    """Map intents to signed exposure targets, merging grouped decisions."""

    def __init__(self, config: ExposureConstructorConfig | None = None) -> None:
        self.config = config or ExposureConstructorConfig()

    def _exposure_for(self, decision: StrategyDecision) -> Decimal | None:
        if decision.kind is DecisionKind.HOLD:
            return None
        if decision.kind is DecisionKind.ENTER_LONG:
            return self.config.default_exposure
        if decision.kind is DecisionKind.ENTER_SHORT:
            if not self.config.allow_shorts:
                raise ValueError("strategy requested a short while shorts are disabled")
            return -self.config.default_exposure
        if decision.kind in (DecisionKind.EXIT_LONG, DecisionKind.EXIT_SHORT):
            return Decimal(0)
        if decision.kind is DecisionKind.SET_TARGET_EXPOSURE:
            exposure = decision.target_exposure
            if exposure is None:  # construction guards the contract too
                raise ValueError("SET_TARGET_EXPOSURE requires a target_exposure")
            if abs(exposure) > self.config.max_abs_exposure:
                raise ValueError(f"target exposure {exposure} exceeds portfolio limit")
            if exposure < 0 and not self.config.allow_shorts:
                raise ValueError("strategy requested a short while shorts are disabled")
            return exposure
        raise ValueError(f"unsupported decision kind {decision.kind!r}; add a construction case")

    def build(
        self, decisions: Sequence[StrategyDecision], context: DecisionContext
    ) -> tuple[PortfolioTarget, ...]:
        by_key: dict[tuple[str, str | None], tuple[StrategyDecision, Decimal]] = {}
        known = set(context.instruments)
        for decision in decisions:
            if decision.valid_until is not None and decision.valid_until < context.timestamp:
                continue
            instrument = decision.instrument or context.instrument
            if instrument not in known:
                raise ValueError(
                    f"decision targets unknown instrument {instrument!r}; "
                    f"available: {sorted(known)}"
                )
            exposure = self._exposure_for(decision)
            if exposure is None:
                continue
            key = (instrument, decision.group_id)
            by_key[key] = (decision, exposure)

        if len(by_key) > self.config.max_targets:
            raise ValueError(f"too many portfolio targets: {len(by_key)}")

        targets: list[PortfolioTarget] = []
        for (instrument, group_id), (decision, exposure) in by_key.items():
            targets.append(
                PortfolioTarget(
                    instrument=instrument,
                    desired_exposure=exposure,
                    decision=decision,
                    group_id=group_id,
                    metadata={
                        "strategy_reason": decision.reason,
                        "confidence": decision.confidence,
                    },
                )
            )
        return tuple(targets)


__all__ = [
    "ExposureConstructorConfig",
    "ExposurePortfolioConstructor",
    "PortfolioConstructor",
]
