import pytest

from app.services.backtest.registry import StrategyRegistry
from app.services.provenance.strategy import (
    STRATEGY_CONTRACT_VERSION,
    strategy_identity,
)
from app.services.strategy.capabilities import DecisionKind, StrategyCapabilities


def factory(context):  # pragma: no cover - never called in this test
    return None


def test_identity_records_module_qualname_and_source_hash() -> None:
    registry = StrategyRegistry()
    registry.register("identity_test", factory)

    identity = strategy_identity("identity_test", registry)

    assert identity.name == "identity_test"
    assert identity.version == "1"
    assert identity.contract_version == STRATEGY_CONTRACT_VERSION
    assert identity.module == factory.__module__
    assert identity.qualname == factory.__qualname__
    assert identity.source_sha256 is not None
    assert len(identity.source_sha256) == 64
    assert identity.source_unavailable_reason is None
    assert identity.capabilities["declared"] is False


def test_declared_capabilities_are_recorded_in_stable_order() -> None:
    registry = StrategyRegistry()
    capabilities = StrategyCapabilities(
        name="declared",
        version="2",
        input_data=frozenset({"ohlcv", "order_book"}),
        timeframes=frozenset({"1h", "5m"}),
        outputs=frozenset({DecisionKind.HOLD, DecisionKind.ENTER_LONG}),
    )
    registry.register("declared", factory, capabilities=capabilities)

    identity = strategy_identity("declared", registry)

    assert identity.version == "2"
    assert identity.capabilities["input_data"] == ["ohlcv", "order_book"]
    assert identity.capabilities["timeframes"] == ["1h", "5m"]
    assert identity.capabilities["outputs"] == ["enter_long", "hold"]


def test_missing_source_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(_factory: object) -> str:
        raise OSError("no source")

    monkeypatch.setattr("app.services.provenance.strategy.inspect.getsource", unavailable)
    registry = StrategyRegistry()
    registry.register("no_source", factory)

    identity = strategy_identity("no_source", registry)

    assert identity.source_sha256 is None
    assert identity.source_unavailable_reason == "source unavailable: OSError"


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown strategy"):
        strategy_identity("missing", StrategyRegistry())
