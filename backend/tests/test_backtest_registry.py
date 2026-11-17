"""Strategy contract and registry.

The point of these tests is not that another container exists, but that a
strategy defined outside ``baselines.py`` becomes usable through the runner,
the persisted run record and the HTTP API without the engine being edited.
Nothing here asserts profitability: a stateful entry on a flat series is a
plumbing probe, not a trading idea.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal

import httpx
import pytest
from test_backtest_engine import flat_candles

from app.core.database import get_db_session
from app.main import create_app
from app.schemas.backtest import BacktestRequest
from app.schemas.market_data import Timeframe
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import HOLD, OPEN_LONG, Signal, StrategyContext
from app.services.backtest.registry import (
    STRATEGY_NAMES,
    Strategy,
    StrategyRegistry,
    build_strategy,
    default_parameters,
    default_registry,
    register_strategy,
)
from app.services.backtest.runner import run_backtest

PLUGIN_NAME = "test_plugin_once"


@dataclass
class StatefulOnce:
    """Enter once on the first signal bar, then remember that decision."""

    name: str = PLUGIN_NAME
    period: int = 3
    risk_fraction: Decimal = Decimal("0.01")
    _entered: bool = False

    def __call__(self, context: StrategyContext) -> Signal:
        if self._entered or context.position is not None:
            return Signal(kind=HOLD, reason="already decided")
        self._entered = True
        return Signal(kind=OPEN_LONG, risk_fraction=self.risk_fraction, reason="first bar")


@pytest.fixture
def plugin_strategy():
    register_strategy(PLUGIN_NAME, StatefulOnce, description="registry plumbing probe")
    yield PLUGIN_NAME
    default_registry.unregister(PLUGIN_NAME)


# -- the contract -----------------------------------------------------------


def test_protocol_matches_a_callable_strategy() -> None:
    assert isinstance(StatefulOnce(), Strategy)


def test_protocol_rejects_an_object_without_a_call() -> None:
    assert not isinstance(object(), Strategy)


def test_a_factory_must_return_a_strategy() -> None:
    registry = StrategyRegistry()
    registry.register("not_a_strategy", lambda: object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="not callable with a StrategyContext"):
        registry.create("not_a_strategy")


# -- registry behaviour -----------------------------------------------------


def test_registries_are_isolated() -> None:
    local = StrategyRegistry()
    assert local.names() == ()
    local.register("local_only", StatefulOnce)
    assert "local_only" in local
    assert "local_only" not in default_registry


def test_duplicate_name_requires_an_explicit_replace(plugin_strategy) -> None:
    with pytest.raises(ValueError, match="already registered"):
        register_strategy(plugin_strategy, StatefulOnce)
    register_strategy(plugin_strategy, StatefulOnce, replace=True)


@pytest.mark.parametrize("bad_name", ["", "  ", "has spaces", None])
def test_names_must_be_clean_slugs(bad_name) -> None:
    with pytest.raises((ValueError, TypeError)):
        StrategyRegistry().register(bad_name, StatefulOnce)  # type: ignore[arg-type]


def test_unknown_name_error_lists_the_available_names(plugin_strategy) -> None:
    with pytest.raises(ValueError, match="unknown strategy 'nope'"):
        build_strategy("nope")
    assert PLUGIN_NAME in str(pytest.raises(ValueError, build_strategy, "nope").value)


def test_private_state_is_not_a_parameter(plugin_strategy) -> None:
    parameters = default_parameters(plugin_strategy)
    assert parameters["period"] == 3
    assert parameters["risk_fraction"] == Decimal("0.01")
    assert not any(key.startswith("_") for key in parameters)


def test_plain_callable_strategies_can_declare_defaults() -> None:
    def make_strategy(period: int = 3):
        def strategy(context: StrategyContext, lookback: int = period) -> Signal:
            return Signal(kind=HOLD, reason=f"lookback={lookback}")

        return strategy

    registry = StrategyRegistry()
    registry.register("function_strategy", make_strategy)
    assert registry.default_parameters("function_strategy") == {"lookback": 3}
    assert isinstance(registry.create("function_strategy"), Strategy)


def test_live_name_view_sees_a_runtime_registration(plugin_strategy) -> None:
    assert PLUGIN_NAME in STRATEGY_NAMES
    assert BacktestRequest(strategy=PLUGIN_NAME).strategy == PLUGIN_NAME


# -- working behaviour through the existing pipeline ------------------------


def test_a_registered_strategy_runs_through_the_runner(plugin_strategy) -> None:
    candles = flat_candles([100] * 60)

    result = run_backtest(
        candles,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name=plugin_strategy,
        costs=BacktestCosts(),
        initial_capital=Decimal("10000"),
    )

    assert result.run.strategy_name == plugin_strategy
    assert result.run.parameters["period"] == 3
    assert result.run.trades, "the stateful entry must produce a real, settled trade"
    assert result.metrics.trade_count == len(result.run.trades)
    assert result.dataset_version


@pytest.mark.asyncio
async def test_a_registered_strategy_is_reachable_over_http(plugin_strategy, db_session) -> None:
    async def override_session() -> AsyncIterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        listed = await client.get("/api/v1/backtests/strategies")
        assert listed.status_code == 200
        assert plugin_strategy in listed.json()

        request = {
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "strategy": plugin_strategy,
            "max_candles": 100,
        }
        rejected = await client.post("/api/v1/backtests/run", json=request)
        # No candles are seeded in this test, so the run is refused for lack of
        # data — never for being an unregistered strategy.
        assert rejected.status_code == 422
        assert "not enough candles" in rejected.json()["detail"]


def test_registration_freed_by_fixture_teardown() -> None:
    """A failed plugin must not leak into unrelated experiments."""
    assert PLUGIN_NAME not in STRATEGY_NAMES
    with pytest.raises(ValueError, match="unknown strategy"):
        build_strategy(PLUGIN_NAME)
