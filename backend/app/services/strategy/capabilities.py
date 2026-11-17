"""Capability declarations and pre-run validation.

A strategy states what it needs; the environment states what it can provide.
The check happens before a run starts, so a strategy that needs order-book or
event data can never silently receive only OHLCV bars, and a multi-instrument
strategy can never be mistaken for a single-instrument one.

Capabilities are optional interfaces, not a single mandatory mega-interface:
a plain callable from Stage 3B declares nothing and keeps working unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any

from .contract import DecisionKind, StrategyDecision

DEFAULT_OUTPUTS = frozenset(
    {
        DecisionKind.HOLD,
        DecisionKind.ENTER_LONG,
        DecisionKind.ENTER_SHORT,
        DecisionKind.EXIT_LONG,
        DecisionKind.EXIT_SHORT,
        DecisionKind.SET_TARGET_EXPOSURE,
    }
)


class CapabilityError(ValueError):
    """A strategy's declared requirements are not met by the run environment."""


class ConfigError(ValueError):
    """A strategy's configuration violates its declared schema."""


@dataclass(frozen=True)
class ConfigField:
    """One configuration key's type and, optionally, its numeric bounds."""

    expected: type | tuple[type, ...]
    required: bool = True
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True)
class StrategyCapabilities:
    """What a strategy consumes and produces.

    Empty ``timeframes`` means any timeframe. ``instruments`` is ``"single"``
    or ``"multi"``. ``outputs`` must be a non-empty set of decision kinds.
    """

    name: str
    version: str = "1"
    input_data: frozenset[str] = frozenset({"ohlcv"})
    timeframes: frozenset[str] = frozenset()
    instruments: str = "single"
    stateful: bool = False
    warmup_bars: int = 0
    outputs: frozenset[DecisionKind] = DEFAULT_OUTPUTS
    event_types: frozenset[str] = frozenset()
    config_schema: Mapping[str, ConfigField] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("capability name must be non-empty")
        if not self.version.strip():
            raise ValueError("capability version must be non-empty")
        if self.instruments not in ("single", "multi"):
            raise ValueError("instruments capability must be 'single' or 'multi'")
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars cannot be negative")
        if not self.input_data:
            raise ValueError("a strategy must declare at least one input data type")
        if not self.outputs or not all(isinstance(kind, DecisionKind) for kind in self.outputs):
            raise ValueError("outputs must be a non-empty set of DecisionKind values")
        object.__setattr__(self, "config_schema", MappingProxyType(dict(self.config_schema)))


@dataclass(frozen=True)
class StrategyEnvironment:
    """What the current run can actually provide to a strategy."""

    symbol: str
    timeframe: str
    instruments: tuple[str, ...]
    input_data: frozenset[str] = frozenset({"ohlcv"})
    event_types: frozenset[str] = frozenset()
    available_bars: int = 0
    now: datetime | None = None

    def __post_init__(self) -> None:
        if not self.instruments:
            raise ValueError("an environment must have at least one instrument")
        if self.available_bars < 0:
            raise ValueError("available_bars cannot be negative")


def validate_capabilities(
    capabilities: StrategyCapabilities, environment: StrategyEnvironment
) -> None:
    """Refuse a run whose environment cannot satisfy a declared requirement."""
    missing_data = sorted(capabilities.input_data - environment.input_data)
    if missing_data:
        raise CapabilityError(
            f"strategy {capabilities.name!r} requires input data {missing_data} "
            f"not provided by this environment (available: {sorted(environment.input_data)})"
        )
    missing_events = sorted(capabilities.event_types - environment.event_types)
    if missing_events:
        raise CapabilityError(
            f"strategy {capabilities.name!r} requires event types {missing_events} "
            f"not provided by this environment (available: {sorted(environment.event_types)})"
        )
    if capabilities.timeframes and environment.timeframe not in capabilities.timeframes:
        raise CapabilityError(
            f"strategy {capabilities.name!r} supports timeframes "
            f"{sorted(capabilities.timeframes)}, not {environment.timeframe!r}"
        )
    if capabilities.instruments == "multi" and len(environment.instruments) < 2:
        raise CapabilityError(
            f"strategy {capabilities.name!r} requires multiple instruments, but this "
            f"environment provides {list(environment.instruments)}"
        )
    if capabilities.instruments == "single" and len(environment.instruments) != 1:
        raise CapabilityError(
            f"strategy {capabilities.name!r} is single-instrument, but this environment "
            f"provides {len(environment.instruments)} instruments"
        )
    if capabilities.warmup_bars >= environment.available_bars:
        raise CapabilityError(
            f"strategy {capabilities.name!r} requires {capabilities.warmup_bars} warm-up bars "
            f"with at least one signal bar, but only {environment.available_bars} are available"
        )


def validate_config(capabilities: StrategyCapabilities, config: Mapping[str, Any]) -> None:
    """Validate explicit configuration against the declared schema."""
    schema = capabilities.config_schema
    if not schema:
        return
    unknown = sorted(set(config) - set(schema))
    if unknown:
        raise ConfigError(
            f"strategy {capabilities.name!r} has unknown configuration keys {unknown}; "
            f"allowed: {sorted(schema)}"
        )
    for key, spec in schema.items():
        if key not in config:
            if spec.required:
                raise ConfigError(
                    f"strategy {capabilities.name!r} requires configuration key {key!r}"
                )
            continue
        value = config[key]
        # bool is an int subclass, but accepting it where a number is expected
        # would let a config typo pass as a valid numeric setting.
        if isinstance(value, bool) or not isinstance(value, spec.expected):
            raise ConfigError(
                f"configuration {key!r} for {capabilities.name!r} must be "
                f"{spec.expected}, got {type(value).__name__}"
            )
        if spec.minimum is not None and value < spec.minimum:
            raise ConfigError(f"configuration {key!r} must be >= {spec.minimum}")
        if spec.maximum is not None and value > spec.maximum:
            raise ConfigError(f"configuration {key!r} must be <= {spec.maximum}")


def validate_outputs(
    decisions: Sequence[StrategyDecision],
    capabilities: StrategyCapabilities,
    environment: StrategyEnvironment,
) -> None:
    """Reject decisions the strategy did not declare or cannot address."""
    known_instruments = set(environment.instruments)
    for decision in decisions:
        if decision.kind not in capabilities.outputs:
            declared = sorted(kind.value for kind in capabilities.outputs)
            raise CapabilityError(
                f"strategy {capabilities.name!r} emitted undeclared output "
                f"{decision.kind.value!r}; declared: {declared}"
            )
        if decision.instrument is not None and decision.instrument not in known_instruments:
            raise CapabilityError(
                f"strategy {capabilities.name!r} emitted a decision for unknown instrument "
                f"{decision.instrument!r}; available: {sorted(known_instruments)}"
            )


def infer_capabilities(strategy: object) -> StrategyCapabilities | None:
    """Read optional declarations from a strategy instance.

    Legacy callables return ``None`` and keep the unconstrained Stage 3B path.
    """
    declared = getattr(strategy, "capabilities", None)
    if isinstance(declared, StrategyCapabilities):
        return declared
    if callable(getattr(strategy, "decide", None)):
        return StrategyCapabilities(name=type(strategy).__name__)
    return None


__all__ = [
    "DEFAULT_OUTPUTS",
    "CapabilityError",
    "ConfigError",
    "ConfigField",
    "StrategyCapabilities",
    "StrategyEnvironment",
    "infer_capabilities",
    "validate_capabilities",
    "validate_config",
    "validate_outputs",
]
