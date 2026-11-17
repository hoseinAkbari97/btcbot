"""Strategy contract and registry for the research pipeline.

A strategy is a callable that receives a :class:`~app.services.backtest.engine.StrategyContext`
and returns a :class:`~app.services.backtest.engine.Signal`. That is the whole contract.
The engine owns data truncation, fills, costs, sizing and accounting; a strategy owns
only the decision. Keeping that boundary sharp is what lets a new strategy be added
without touching the engine, and what lets the same strategy later be reused in a
paper-trading simulation instead of being rewritten around order submission.

Registries are explicit and isolated. Nothing is discovered by scanning the filesystem:
a strategy becomes available when a module registers it, which makes an experiment's
strategy name meaningful and reproducible rather than an accident of imports.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast, overload, runtime_checkable

from .engine import Signal, StrategyContext

StrategyFactory = Callable[..., "Strategy"]


@runtime_checkable
class Strategy(Protocol):
    """The contract implemented by every research strategy.

    The engine calls the *same instance* once per signal bar, in chronological
    order, so instance attributes are the supported way to hold state across
    bars (a moving average's last value, a random generator, an event memory).
    The runner builds a fresh instance for every run, which is why a stateful
    strategy stays repeatable. Private attributes (leading underscore) are run
    state, not configuration, and are excluded from recorded parameters.

    This contract deliberately says nothing about orders, venues or accounts.
    A strategy asks for a position; the engine and the risk layer decide what
    is actually allowed to happen. No implementation here can place an order.
    """

    def __call__(self, context: StrategyContext) -> Signal: ...


def _declared_parameters(instance: object) -> dict[str, object]:
    """Explicit configuration of an instance, never its private state.

    Dataclasses expose their fields on the instance, which is the common case.
    Plain callables are supported too by reading keyword defaults from the
    signature, so a strategy need not be a class to participate in research.
    """
    if hasattr(instance, "__dict__"):
        fields = {
            key: value
            for key, value in vars(instance).items()
            if not key.startswith("_")
        }
        if fields:
            return fields
    try:
        signature = inspect.signature(cast(Callable[..., object], instance))
    except (TypeError, ValueError):
        return {}
    return {
        key: parameter.default
        for key, parameter in signature.parameters.items()
        if parameter.default is not inspect.Parameter.empty
    }


@dataclass(frozen=True)
class StrategyDefinition:
    """One registration: how to build a strategy and how to describe it."""

    name: str
    factory: StrategyFactory
    description: str = ""

    def create(self, **parameters: object) -> Strategy:
        """Build a fresh instance and verify it honours the contract."""
        instance = self.factory(**parameters)
        if not isinstance(instance, Strategy):
            raise TypeError(
                f"strategy {self.name!r} factory returned {type(instance).__name__}, "
                "which is not callable with a StrategyContext"
            )
        return instance

    def default_parameters(self) -> dict[str, object]:
        """The parameters a fresh instance uses, for experiment records."""
        return _declared_parameters(self.factory())


class StrategyRegistry(Mapping[str, StrategyFactory]):
    """An isolated collection of named strategies.

    Registries do not share state: registering in one never changes another.
    ``default_registry`` is the collection the research pipeline uses. Duplicate
    names are refused unless ``replace=True`` is explicit, so a typo cannot
    silently shadow a baseline and make a stored experiment irreproducible.
    """

    def __init__(self) -> None:
        self._definitions: dict[str, StrategyDefinition] = {}

    def register(
        self,
        name: str,
        factory: StrategyFactory,
        *,
        description: str = "",
        replace: bool = False,
    ) -> StrategyDefinition:
        """Register ``factory`` under ``name``.

        ``name`` becomes part of a persisted run and an API request, so it must
        be a clean slug rather than something that needs normalising later.
        """
        if not isinstance(name, str) or not name or any(char.isspace() for char in name):
            raise ValueError("strategy name must be a non-empty string without whitespace")
        if not callable(factory):
            raise TypeError(f"strategy {name!r} factory must be callable")
        if name in self._definitions and not replace:
            raise ValueError(
                f"strategy {name!r} is already registered; pass replace=True to override"
            )
        definition = StrategyDefinition(name=name, factory=factory, description=description)
        self._definitions[name] = definition
        return definition

    def unregister(self, name: str) -> None:
        """Remove a registration. Useful for plugin teardown and test isolation."""
        self._definitions.pop(name, None)

    def definition(self, name: str) -> StrategyDefinition:
        """Look up a definition, raising a helpful error for an unknown name."""
        try:
            return self._definitions[name]
        except KeyError:
            available = ", ".join(sorted(self._definitions))
            raise ValueError(f"unknown strategy {name!r}; available: {available}") from None

    def create(self, name: str, /, **parameters: object) -> Strategy:
        """Build a fresh instance of ``name`` with explicit parameter overrides."""
        return self.definition(name).create(**parameters)

    def default_parameters(self, name: str) -> dict[str, object]:
        return self.definition(name).default_parameters()

    def names(self) -> tuple[str, ...]:
        """Registered names in stable order, suitable for API and CLI listings."""
        return tuple(sorted(self._definitions))

    # -- Mapping protocol --------------------------------------------------

    def __getitem__(self, name: str) -> StrategyFactory:
        # Mapping membership relies on a KeyError for a missing key, so this
        # stays a plain lookup; ``definition`` is the friendly-error path.
        return self._definitions[name].factory

    def __iter__(self) -> Iterator[str]:
        return iter(self._definitions)

    def __len__(self) -> int:
        return len(self._definitions)

    def __repr__(self) -> str:
        return f"StrategyRegistry({', '.join(self.names())})"


class StrategyNames(Sequence[str]):
    """A live, read-only view of a registry's names.

    A view rather than a snapshot matters: a strategy registered at runtime is
    immediately visible to the request validator, the CLI and the HTTP route
    without any of them being edited or restarted.
    """

    def __init__(self, registry: StrategyRegistry) -> None:
        self._registry = registry

    def __len__(self) -> int:
        return len(self._registry)

    @overload
    def __getitem__(self, index: int) -> str: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[str]: ...

    def __getitem__(self, index: int | slice) -> str | Sequence[str]:
        names = self._registry.names()
        return names[index]

    def __iter__(self) -> Iterator[str]:
        return iter(self._registry.names())

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._registry

    def __repr__(self) -> str:
        return repr(self._registry.names())


default_registry = StrategyRegistry()

# Backward-compatible names. Both are live views over ``default_registry``:
# ``STRATEGIES`` is the name-to-factory mapping, ``STRATEGY_NAMES`` the ordered
# names. Existing callers keep working, and newly registered strategies appear
# to all of them without a code change.
STRATEGIES: StrategyRegistry = default_registry
STRATEGY_NAMES: StrategyNames = StrategyNames(default_registry)


def register_strategy(
    name: str,
    factory: StrategyFactory,
    *,
    description: str = "",
    replace: bool = False,
) -> StrategyDefinition:
    """Register a strategy in the pipeline's default registry."""
    return default_registry.register(
        name, factory, description=description, replace=replace
    )


def build_strategy(name: str, /, **parameters: object) -> Strategy:
    """Instantiate a registered strategy by name.

    ``name`` is positional-only so a strategy's own ``name`` field can be
    splatted back in as an override, as the runner does.
    """
    return default_registry.create(name, **parameters)


def default_parameters(name: str) -> dict[str, object]:
    """The explicit configuration a fresh instance of ``name`` uses."""
    return default_registry.default_parameters(name)
