"""Stage 3C strategy-contract architecture acceptance tests.

These are plumbing probes, not profitability experiments. They prove that a
strategy produces decisions, that portfolio construction and execution planning
are separate layers, that capabilities gate a run before strategy code executes,
and that Stage 3B callables still work through the same engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest
from test_backtest_engine import flat_candles

from app.schemas.market_data import Timeframe
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import HOLD, OPEN_LONG, Signal, StrategyContext
from app.services.backtest.registry import (
    StrategyRegistry,
    default_registry,
    register_strategy,
)
from app.services.backtest.runner import run_backtest
from app.services.strategy.adapter import StrategyAdapter, prepare_strategy
from app.services.strategy.capabilities import (
    CapabilityError,
    ConfigError,
    ConfigField,
    StrategyCapabilities,
    StrategyEnvironment,
    validate_capabilities,
    validate_config,
    validate_outputs,
)
from app.services.strategy.construction import (
    ExposureConstructorConfig,
    ExposurePortfolioConstructor,
)
from app.services.strategy.contract import (
    DecisionContext,
    DecisionKind,
    PortfolioView,
    StrategyDecision,
    normalize_decisions,
)
from app.services.strategy.examples import (
    EventDrivenStrategy,
    GroupedPairsStrategy,
    MalformedOutputStrategy,
    OrderBookStrategy,
    ProbabilityStrategy,
    SmaCrossoverStrategy,
    StatefulExitStrategy,
    TargetExposureStrategy,
    UndeclaredOutputStrategy,
)
from app.services.strategy.execution import NextBarMarketPlanner


def _environment(
    bars: int = 30,
    *,
    symbol: str = "BTCUSDT",
    instruments: tuple[str, ...] | None = None,
) -> StrategyEnvironment:
    return StrategyEnvironment(
        symbol=symbol,
        timeframe="5m",
        instruments=instruments or (symbol,),
        available_bars=bars,
    )


def _context(
    bars: int = 30,
    *,
    instruments: tuple[str, ...] | None = None,
) -> DecisionContext:
    candles = flat_candles([100 + i for i in range(bars)])
    names = instruments or ("BTCUSDT",)
    return DecisionContext(
        instrument="BTCUSDT",
        timeframe=Timeframe.M5,
        index=bars - 1,
        timestamp=candles[-1].close_time,
        bar=candles[-1],
        history=candles,
        equity=Decimal("10000"),
        position=None,
        portfolio=PortfolioView(equity=Decimal("10000"), instruments=names, open_position_count=0),
        instruments=names,
    )


# -- contract and context ---------------------------------------------------


def test_decision_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="confidence"):
        StrategyDecision(DecisionKind.HOLD, confidence=1.5)
    with pytest.raises(ValueError, match="target_exposure"):
        StrategyDecision(DecisionKind.HOLD, target_exposure=Decimal("2"))
    with pytest.raises(ValueError, match="requires a target_exposure"):
        StrategyDecision(DecisionKind.SET_TARGET_EXPOSURE)
    with pytest.raises(ValueError, match="must be a DecisionKind"):
        StrategyDecision("enter_long")  # type: ignore[arg-type]


def test_decision_metadata_is_immutable() -> None:
    decision = StrategyDecision(DecisionKind.HOLD, metadata={"source": "x"})
    with pytest.raises(TypeError):
        decision.metadata["source"] = "y"  # type: ignore[index]


def test_normalize_decisions_rejects_malformed_results() -> None:
    with pytest.raises(ValueError, match="must return"):
        normalize_decisions("not a decision")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no decisions"):
        normalize_decisions([])
    with pytest.raises(ValueError, match="not a StrategyDecision"):
        normalize_decisions([StrategyDecision(DecisionKind.HOLD), "bad"])  # type: ignore[list-item]
    assert len(normalize_decisions(StrategyDecision(DecisionKind.HOLD))) == 1


def test_context_has_no_execution_handles_and_does_not_copy_history() -> None:
    candles = flat_candles([100, 101, 102])
    context = DecisionContext(
        instrument="BTCUSDT",
        timeframe=Timeframe.M5,
        index=2,
        timestamp=candles[-1].close_time,
        bar=candles[-1],
        history=candles,
        equity=Decimal("10000"),
        position=None,
        portfolio=PortfolioView(
            equity=Decimal("10000"),
            instruments=("BTCUSDT",),
            open_position_count=0,
        ),
        config={"fast": 3},
    )
    assert context.history is candles, "history must be the engine's slice, not a copy"
    with pytest.raises(TypeError):
        context.config["fast"] = 5  # type: ignore[index]
    for forbidden in ("session", "account", "broker", "submit_order", "engine"):
        assert not hasattr(context, forbidden)


# -- capability validation --------------------------------------------------


def test_order_book_requirement_is_rejected_in_ohlcv_environment() -> None:
    with pytest.raises(CapabilityError, match="order_book"):
        validate_capabilities(OrderBookStrategy.capabilities, _environment())


def test_multi_instrument_requirement_is_rejected_in_single_environment() -> None:
    with pytest.raises(CapabilityError, match="multiple instruments"):
        validate_capabilities(GroupedPairsStrategy.capabilities, _environment())


def test_event_requirement_is_rejected_when_environment_has_no_events() -> None:
    with pytest.raises(CapabilityError, match="event types"):
        validate_capabilities(EventDrivenStrategy.capabilities, _environment())


def test_warmup_requirement_is_rejected_on_short_history() -> None:
    with pytest.raises(CapabilityError, match="warm-up"):
        validate_capabilities(SmaCrossoverStrategy.capabilities, _environment(bars=2))


def test_config_schema_rejects_unknown_missing_wrong_type_and_bad_range() -> None:
    schema = ProbabilityStrategy.capabilities
    with pytest.raises(ConfigError, match="unknown configuration keys"):
        validate_config(schema, {"name": "x", "buy_threshold": 0.6, "bogus": 1})
    with pytest.raises(ConfigError, match="requires configuration key"):
        validate_config(
            StrategyCapabilities(
                name="needs-key",
                config_schema={"threshold": ConfigField(float)},
            ),
            {},
        )
    with pytest.raises(ConfigError, match="must be"):
        validate_config(schema, {"name": "x", "buy_threshold": "high"})
    with pytest.raises(ConfigError, match="<= 1.0"):
        validate_config(schema, {"name": "x", "buy_threshold": 1.5})


def test_output_validation_rejects_undeclared_kind_and_unknown_instrument() -> None:
    with pytest.raises(CapabilityError, match="undeclared output"):
        validate_outputs(
            [StrategyDecision(DecisionKind.ENTER_LONG)],
            UndeclaredOutputStrategy.capabilities,
            _environment(),
        )
    with pytest.raises(CapabilityError, match="unknown instrument"):
        validate_outputs(
            [StrategyDecision(DecisionKind.HOLD, instrument="ETHUSDT")],
            SmaCrossoverStrategy.capabilities,
            _environment(),
        )


# -- portfolio construction -------------------------------------------------


def test_directional_decision_has_no_size_and_constructor_assigns_default() -> None:
    decision = StrategyDecision(DecisionKind.ENTER_LONG, reason="long")
    assert decision.target_exposure is None
    target = ExposurePortfolioConstructor().build([decision], _context())[0]
    assert target.desired_exposure == Decimal("0.01")
    assert target.decision is decision


def test_short_target_is_rejected_when_shorts_are_disabled() -> None:
    constructor = ExposurePortfolioConstructor(
        ExposureConstructorConfig(allow_shorts=False)
    )
    with pytest.raises(ValueError, match="shorts are disabled"):
        constructor.build([StrategyDecision(DecisionKind.ENTER_SHORT)], _context())


def test_grouped_decisions_are_merged_per_instrument_and_group() -> None:
    decisions = [
        StrategyDecision(DecisionKind.ENTER_LONG, instrument="A", group_id="g"),
        StrategyDecision(DecisionKind.EXIT_LONG, instrument="A", group_id="g"),
        StrategyDecision(DecisionKind.ENTER_SHORT, instrument="B", group_id="g"),
    ]
    targets = ExposurePortfolioConstructor().build(decisions, _context(instruments=("A", "B")))
    assert len(targets) == 2
    assert {target.instrument: target.desired_exposure for target in targets} == {
        "A": Decimal(0),
        "B": Decimal("-0.01"),
    }
    assert {target.group_id for target in targets} == {"g"}


def test_expired_decision_is_dropped() -> None:
    expired = StrategyDecision(
        DecisionKind.ENTER_LONG,
        valid_until=flat_candles([100])[0].close_time,
    )
    assert ExposurePortfolioConstructor().build([expired], _context()) == ()


def test_exposure_limit_and_target_cap_are_enforced() -> None:
    limited = ExposurePortfolioConstructor(
        ExposureConstructorConfig(max_abs_exposure=Decimal("0.1"))
    )
    with pytest.raises(ValueError, match="exceeds portfolio limit"):
        limited.build(
            [StrategyDecision(DecisionKind.SET_TARGET_EXPOSURE, target_exposure=Decimal("0.5"))],
            _context(),
        )
    capped = ExposurePortfolioConstructor(ExposureConstructorConfig(max_targets=1))
    with pytest.raises(ValueError, match="too many portfolio targets"):
        capped.build(
            [
                StrategyDecision(DecisionKind.ENTER_LONG, instrument="A"),
                StrategyDecision(DecisionKind.ENTER_LONG, instrument="B"),
            ],
            _context(instruments=("A", "B")),
        )


# -- execution planning -----------------------------------------------------


def test_planner_emits_plans_not_orders() -> None:
    target = ExposurePortfolioConstructor().build(
        [StrategyDecision(DecisionKind.ENTER_LONG, reason="probe")], _context()
    )[0]
    instruction = NextBarMarketPlanner().plan([target], _context())[0]
    assert instruction.order_type == "market_at_next_open"
    assert instruction.sizing_fraction == Decimal("0.01")
    assert instruction.action.value == "open_long"
    assert not hasattr(instruction, "order_id")
    assert not hasattr(instruction, "fill_price")


# -- adapter lifecycle ------------------------------------------------------


def test_adapter_maps_a_decision_and_runs_initialize_and_finalize_once() -> None:
    registry = StrategyRegistry()
    registry.register("stateful", StatefulExitStrategy)
    prepared = prepare_strategy("stateful", {}, _environment(), registry=registry)
    candles = flat_candles([100 + i for i in range(30)])
    engine_logic = StrategyAdapter(
        StatefulExitStrategy(),
        StatefulExitStrategy.capabilities,
        _environment(),
        {},
        "stateful",
    )
    legacy = StrategyContext(
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        index=0,
        history=candles[:1],
        equity=Decimal("10000"),
        position=None,
    )
    assert engine_logic(legacy).kind == OPEN_LONG
    engine_logic(legacy)
    engine_logic.finish()
    assert engine_logic.finish() is None  # finalisation is safe to call again
    assert prepared.state() is not None


def test_legacy_callable_passes_through_the_adapter_unchanged() -> None:
    @dataclass
    class Legacy:
        name: str = "legacy"

        def __call__(self, context: StrategyContext) -> Signal:
            return Signal(kind=HOLD, reason="legacy")

    registry = StrategyRegistry()
    registry.register("legacy", Legacy)
    prepared = prepare_strategy("legacy", {}, _environment(), registry=registry)
    assert prepared.logic is prepared.strategy
    assert prepared.capabilities is None
    assert prepared.state() is None


# -- end-to-end through the unchanged engine --------------------------------


DEMO_REGISTRATIONS: dict[str, type[Any]] = {
    "arch_sma": SmaCrossoverStrategy,
    "arch_stateful": StatefulExitStrategy,
    "arch_target": TargetExposureStrategy,
    "arch_probability": ProbabilityStrategy,
    "arch_orderbook": OrderBookStrategy,
    "arch_pairs": GroupedPairsStrategy,
    "arch_event": EventDrivenStrategy,
    "arch_malformed": MalformedOutputStrategy,
    "arch_undeclared": UndeclaredOutputStrategy,
}


@pytest.fixture
def demos():
    for name, factory in DEMO_REGISTRATIONS.items():
        register_strategy(name, factory, replace=True)
    yield DEMO_REGISTRATIONS
    for name in DEMO_REGISTRATIONS:
        default_registry.unregister(name)


def _run(name: str, prices: list[int], **parameters: Any):
    return run_backtest(
        flat_candles(prices),
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name=name,
        costs=BacktestCosts(),
        initial_capital=Decimal("10000"),
        parameters=parameters,
        allow_short=True,
    )


@pytest.mark.parametrize("name", ["arch_sma", "arch_stateful", "arch_target", "arch_probability"])
def test_distinct_strategy_styles_share_the_same_engine(demos, name) -> None:
    prices = [100 + i for i in range(30)] + [130 - i for i in range(15)]
    result = _run(name, prices)
    assert result.run.strategy_name == name
    assert result.dataset_version
    assert result.run.parameters["name"] == DEMO_REGISTRATIONS[name]().name


@pytest.mark.parametrize("name", ["arch_orderbook", "arch_pairs", "arch_event"])
def test_missing_capability_is_rejected_before_the_run(demos, name) -> None:
    with pytest.raises(CapabilityError):
        _run(name, [100] * 30)


def test_invalid_outputs_are_rejected(demos) -> None:
    with pytest.raises(ValueError, match="must return"):
        _run("arch_malformed", [100] * 30)
    with pytest.raises(CapabilityError, match="undeclared output"):
        _run("arch_undeclared", [100] * 30)


def test_invalid_config_is_rejected(demos) -> None:
    with pytest.raises(ConfigError, match="<= 1.0"):
        _run("arch_probability", [100] * 30, buy_threshold=1.5)


def test_stateful_strategy_is_deterministic_and_isolated(demos) -> None:
    prices = [100 + i for i in range(30)] + [130 - i for i in range(15)]
    first = _run("arch_stateful", prices)
    second = _run("arch_stateful", prices)
    def signature(run):
        return (
            run.final_equity,
            [(trade.side, trade.net_pnl, trade.exit_reason) for trade in run.trades],
        )

    assert signature(first.run) == signature(second.run), "a fresh run must not inherit state"
    assert first.run.trades, "the stateful demo must still produce a settled trade"


def test_stage3b_baseline_still_runs_through_the_new_pipeline() -> None:
    result = _run("buy_and_hold", [100] * 30)
    assert result.run.strategy_name == "buy_and_hold"
    assert result.run.trades, "the baseline must remain functional"


def test_demo_registrations_are_removed_after_each_test() -> None:
    for name in DEMO_REGISTRATIONS:
        assert name not in default_registry
