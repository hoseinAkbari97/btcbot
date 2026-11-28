"""Recorded identity of a registered research strategy.

This module records facts available at execution time. It never uses the
current Git HEAD as a stand-in for strategy code: an implementation is
identified only by its declared version plus, when Python can expose it, its
module, qualified name and source hash. A missing source hash stays null.
"""

from __future__ import annotations

import hashlib
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from app.services.backtest.registry import StrategyRegistry, default_registry
from app.services.strategy.capabilities import ConfigField, StrategyCapabilities

#: Explicit version of the recorded strategy-contract shape introduced here.
#: It describes this provenance record, not the strategy implementation.
STRATEGY_CONTRACT_VERSION = "3c.0"


@dataclass(frozen=True)
class StrategyIdentity:
    """Immutable description of the strategy registration used by a run."""

    name: str
    version: str
    contract_version: str
    capabilities: dict[str, Any]
    module: str | None
    qualname: str | None
    source_sha256: str | None
    source_unavailable_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "contract_version": self.contract_version,
            "capabilities": self.capabilities,
            "module": self.module,
            "qualname": self.qualname,
            "source_sha256": self.source_sha256,
            "source_unavailable_reason": self.source_unavailable_reason,
        }


def _type_names(expected: type | tuple[type, ...]) -> list[str]:
    if isinstance(expected, tuple):
        return [item.__name__ for item in expected]
    return [expected.__name__]


def _capabilities_dict(capabilities: StrategyCapabilities | None) -> dict[str, Any]:
    if capabilities is None:
        return {
            "declared": False,
            "name": None,
            "version": None,
            "input_data": [],
            "timeframes": [],
            "instruments": None,
            "stateful": None,
            "warmup_bars": None,
            "outputs": [],
            "event_types": [],
            "config_schema": [],
        }
    schema: list[dict[str, Any]] = []
    for key, spec in sorted(capabilities.config_schema.items()):
        field: ConfigField = spec
        schema.append(
            {
                "key": key,
                "expected": _type_names(field.expected),
                "required": field.required,
                "minimum": field.minimum,
                "maximum": field.maximum,
            }
        )
    return {
        "declared": True,
        "name": capabilities.name,
        "version": capabilities.version,
        "input_data": sorted(capabilities.input_data),
        "timeframes": sorted(capabilities.timeframes),
        "instruments": capabilities.instruments,
        "stateful": capabilities.stateful,
        "warmup_bars": capabilities.warmup_bars,
        "outputs": sorted(kind.value for kind in capabilities.outputs),
        "event_types": sorted(capabilities.event_types),
        "config_schema": schema,
    }


def _source_identity(factory: object) -> tuple[str | None, str | None]:
    try:
        source = inspect.getsource(cast(Callable[..., object], factory))
    except (OSError, TypeError) as error:
        return None, f"source unavailable: {type(error).__name__}"
    if not source:
        return None, "source unavailable: empty source"
    return hashlib.sha256(source.encode("utf-8")).hexdigest(), None


def strategy_identity(
    name: str, registry: StrategyRegistry | None = None
) -> StrategyIdentity:
    """Describe the registration currently used for ``name``."""
    definition = (registry or default_registry).definition(name)
    factory = inspect.unwrap(definition.factory)
    capabilities = definition.capabilities
    source_sha256, source_reason = _source_identity(factory)
    return StrategyIdentity(
        name=name,
        version=capabilities.version if capabilities is not None else "1",
        contract_version=STRATEGY_CONTRACT_VERSION,
        capabilities=_capabilities_dict(capabilities),
        module=getattr(factory, "__module__", None),
        qualname=getattr(factory, "__qualname__", None),
        source_sha256=source_sha256,
        source_unavailable_reason=source_reason,
    )
