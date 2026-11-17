# Strategy interface, decisions and registry

This document describes how to add a strategy to the research pipeline. It is an engineering
contract only: registering a strategy does **not** authorize data access, open a research gate,
or assert that the strategy has an edge. See `docs/briefings/STAGE2ZJ_OWNER_DECISION_BRIEFING.md`
for the standing authorization boundaries. No code here places an order or contacts an exchange.

Two contracts are supported, and both go through the same engine:

- the **decision contract** (preferred) — a strategy implements `decide()` and returns
  `StrategyDecision` values;
- the **callable contract** (Stage 3B, kept for compatibility) — a strategy is callable with a
  legacy `StrategyContext` and returns a `Signal`.

The decision contract is the one to write new strategies against. The callable contract is not
deprecated and existing baselines keep it, but it can only express a fixed-size directional bet,
which is exactly the limitation the decision contract removes.

## The callable contract (Stage 3B, compatibility)

A strategy is any object callable with a `StrategyContext` that returns a `Signal`:

```python
from app.services.backtest.engine import HOLD, OPEN_LONG, Signal, StrategyContext


class MyStrategy:
    def __call__(self, context: StrategyContext) -> Signal:
        if context.position is not None:
            return Signal(kind=HOLD, reason="already in a position")
        return Signal(
            kind=OPEN_LONG,
            risk_fraction=Decimal("0.01"),
            reason="my rule",
        )
```

The formal type is `app.services.backtest.registry.Strategy`, a runtime-checkable `Protocol`.
`Signal` accepts `OPEN_LONG`, `OPEN_SHORT`, `CLOSE` or `HOLD`, optional protective `stop_price` /
`target_price`, a `risk_fraction`, and a `reason` that is carried into the trade ledger.

`StrategyContext` is **read-only** and contains `symbol`, `timeframe`, `index`, `equity`, the
current `position`, and `history`. The engine truncates `history` to bars `0..index` before the
call, so a strategy cannot accidentally read the future even if it tries. The engine, not the
strategy, owns latency, fills, sizing, costs, realized/unrealized PnL and risk enforcement.

### Stateful callables

The engine calls the **same instance** once per signal bar in chronological order. Keep state on
the instance:

```python
@dataclass
class MyStatefulStrategy:
    lookback: int = 20
    _last_signal_index: int = -1  # private: run state, not configuration

    def __call__(self, context: StrategyContext) -> Signal:
        ...
```

Attributes beginning with `_` are treated as run state and excluded from the recorded
parameters. The runner constructs a fresh instance for every run, so a stateful strategy stays
repeatable. A plain function can be a strategy too: register a no-argument factory that returns
it, and the function's keyword defaults become the recorded parameters. Decision strategies get
explicit lifecycle hooks instead; see *Lifecycle and state*.

## The decision contract (Stage 3C)

A decision strategy implements `decide()` and reads a read-only `DecisionContext`:

```python
from dataclasses import dataclass

from app.services.strategy.capabilities import StrategyCapabilities
from app.services.strategy.contract import DecisionContext, DecisionKind, StrategyDecision


@dataclass
class MyStrategy:
    name: str = "my_strategy"

    capabilities = StrategyCapabilities(name="my_strategy")

    def decide(self, context: DecisionContext) -> StrategyDecision:
        if context.position is not None:
            return StrategyDecision(DecisionKind.HOLD, reason="already positioned")
        return StrategyDecision(DecisionKind.ENTER_LONG, confidence=0.7, reason="my rule")
```

`decide()` may return a single `StrategyDecision` or a non-empty sequence of them. Anything else
— a string, a mapping, an empty list, a list containing a non-decision — is rejected with a
`ValueError` instead of being coerced. Return `HOLD` explicitly when there is nothing to do.

### Decision kinds

| kind | meaning |
| --- | --- |
| `HOLD` | no change requested |
| `ENTER_LONG` | want a long position |
| `ENTER_SHORT` | want a short position |
| `EXIT_LONG` | want the long position closed |
| `EXIT_SHORT` | want the short position closed |
| `SET_TARGET_EXPOSURE` | want a specific signed exposure (requires `target_exposure`) |

`StrategyDecision` carries only intent and provenance: `kind`, optional `instrument`, `group_id`,
`confidence` (0–1), `valid_until`, `stop_price`, `target_price`, `reason`, and an immutable
`metadata` mapping. Confidence is descriptive; it is never a position size.

## Decisions, targets and instructions are separate

Three types exist because the three questions are different:

| type | question | owner |
| --- | --- | --- |
| `StrategyDecision` | what does the strategy want? | strategy |
| `PortfolioTarget` | what should the account hold? | portfolio construction |
| `ExecutionInstruction` | how will execution try to get there? | execution planning |

A directional decision carries **no size**. `ExposurePortfolioConstructor` (in
`app/services/strategy/construction.py`) turns it into a signed fraction of equity using a policy
it owns — `default_exposure`, `allow_shorts`, `max_abs_exposure`, `max_targets`. `NextBarMarketPlanner`
then plans a market attempt at the next bar's open, and the engine remains the sole authority on
fills, costs, stops, risk limits and accounting. `ExecutionInstruction` has no venue, order id or
fill price, because none of those belong to the strategy layer.

Grouped decisions (`group_id`) are merged per instrument and group, so a coordinated two-leg
intent becomes one target per leg rather than a duplicated position.

## The decision context

`DecisionContext` is what a strategy is authorized to read, and nothing more:

| field | content |
| --- | --- |
| `instrument`, `timeframe`, `index`, `timestamp` | where in the series this decision is made |
| `bar` | the current candle |
| `history` | the engine's own truncated slice, bars `0..index` |
| `equity` | current account equity |
| `position` | read-only `PositionView`, or `None` when flat |
| `portfolio` | read-only `PortfolioView` (equity, instruments, open position count) |
| `config` | immutable mapping of the merged configuration |
| `features` | immutable mapping of pre-computed features supplied by the run |
| `events` | event stream, empty for bar-driven environments |
| `instruments` | the instruments this run authorizes |

`history` is the engine's slice, not a copy, so a strategy cannot force a large additional
allocation by asking for it; treat it as read-only. The context deliberately has no session,
account, broker, order-entry or engine handle, so there is no object through which a strategy
could submit an order or mutate a balance.

## Lifecycle and state

Lifecycle hooks are optional interfaces, not methods every strategy must implement:

| hook | protocol | when it runs |
| --- | --- | --- |
| `initialize(context)` | `Initializable` | once, before the first `decide()` |
| `decide(context)` | `DecisionStrategy` | once per signal bar, chronologically |
| `finalize(context)` | `Finalizable` | once, after the engine finishes |
| `state()` / `restore_state(state)` | `Stateful` | on demand, for inspection and resumption |

The runner constructs a fresh instance for every run, so a stateful strategy cannot leak state
into a later run; `initialize` is the place to reset anything a reused instance might carry.
`state()` is exposed on the prepared strategy for inspection, and `restore_state` is the hook a
future paper-trading session would use. Nothing today persists or restores state across
processes, and no distributed execution exists.

A `decide()` strategy that raises, or that returns a malformed value, fails the run. Errors are
never swallowed, because a silently skipped decision would corrupt the experiment record.

## Capabilities and pre-run validation

A strategy declares what it needs; the run environment declares what it can provide. The check
happens **before** strategy code runs, so a strategy requiring order-book or event data can
never silently receive only OHLCV bars.

```python
from app.services.strategy.capabilities import StrategyCapabilities

capabilities = StrategyCapabilities(
    name="my_strategy",
    version="1",
    input_data=frozenset({"ohlcv"}),
    timeframes=frozenset(),          # empty means any timeframe
    instruments="single",            # "single" or "multi"
    stateful=False,
    warmup_bars=20,
    outputs=frozenset({DecisionKind.HOLD, DecisionKind.ENTER_LONG}),
    event_types=frozenset(),
    config_schema={},
)
```

`StrategyEnvironment` describes the run: `symbol`, `timeframe`, `instruments`, `input_data`,
`event_types`, `available_bars`. `validate_capabilities` raises `CapabilityError` when a
declaration cannot be met:

- required `input_data` is unavailable (for example `{"order_book"}` in an OHLCV run);
- required `event_types` are unavailable;
- the timeframe is not in a non-empty `timeframes` set;
- `instruments="multi"` but fewer than two instruments are available, or `"single"` with more;
- `warmup_bars` leaves no signal bar (`warmup_bars >= available_bars`).

Declarations are read from the registration when given there, otherwise from a `capabilities`
class attribute. A Stage 3B callable that declares nothing keeps the unconstrained path; one that
declares non-OHLCV inputs is rejected, because a compatibility callable cannot consume them.

Output validation runs on every bar: a strategy that emits a kind it did not declare, or a
decision for an instrument the run does not include, is rejected rather than ignored.

## Configuration

Configuration is explicit and validated against a declared schema:

```python
from app.services.strategy.capabilities import ConfigField

config_schema={
    "name": ConfigField(str),
    "buy_threshold": ConfigField(float, minimum=0.0, maximum=1.0),
}
```

`ConfigField(expected, required=True, minimum=None, maximum=None)`. Validation rejects unknown
keys, a missing required key, a value of the wrong type, and a value outside the declared bounds.
A boolean is never accepted where a number is expected, so a config typo cannot pass as a valid
numeric setting. A strategy with an empty schema is unvalidated by design — declare a schema when
the parameters have real bounds.

Configuration is merged from the instance defaults and the request overrides, and the merged
values are recorded with the run.

## Registering a strategy

```python
from app.services.backtest.registry import register_strategy

register_strategy("my_strategy", MyStrategy, description="what the rule does")
```

A strategy that declares capabilities should also accept the declaration at registration, which
lets the environment be checked before any strategy code runs:

```python
register_strategy(
    "my_strategy",
    MyStrategy,
    description="what the rule does",
    capabilities=MyStrategy.capabilities,
)
```

The name is a persisted experiment identifier, so it must be a non-empty string with no
whitespace. Duplicate names are refused unless `replace=True` is explicit, which prevents a typo
from silently shadowing an existing strategy and making stored runs irreproducible. Registries
are isolated; `default_registry` is the one the research pipeline uses, and test code can use a
fresh `StrategyRegistry()` without affecting it.

The four existing baselines (`buy_and_hold`, `random`, `sma_trend`, `donchian_breakout`) register
themselves in `baselines.py`. They are scientific controls, not recommended strategies.

## Running it

Once registered, the strategy is available everywhere without further changes:

```python
from app.services.backtest.runner import run_backtest

result = run_backtest(
    candles,
    symbol="BTCUSDT",
    timeframe=Timeframe.M5,
    strategy_name="my_strategy",
    costs=BacktestCosts(),
    initial_capital=Decimal("10000"),
)
```

- `GET /api/v1/backtests/strategies` lists registered names, including ones registered at runtime.
- `POST /api/v1/backtests/run` accepts the name in its `strategy` field.
- `python -m app.cli backtest --strategies my_strategy` runs it over stored candles.

`STRATEGIES` and `STRATEGY_NAMES` remain available as live views for existing callers. The
request schema, CLI and API route read from the same registry, so no consumer needs editing when a
strategy is added.

### How a run reaches your strategy

1. The runner builds a `StrategyEnvironment` from the actual candle series.
2. `prepare_strategy` validates the declared capabilities and configuration.
3. The registered factory builds a fresh instance.
4. The adapter builds a `DecisionContext` for each bar and calls `decide()`.
5. Outputs are normalized and checked against the declaration.
6. Portfolio construction maps decisions to `PortfolioTarget` values.
7. Execution planning maps targets to `ExecutionInstruction` plans.
8. The adapter selects the instruction for the engine's instrument and hands the engine a legacy
   `Signal`; the engine alone fills, charges costs, applies risk limits and books the result.
9. The optional `finalize()` hook runs once.

No engine or runner code changes when a strategy is added; the adapter is the only boundary.

## Two complete examples

Both examples are self-contained: register them, then run them with `run_backtest` exactly as in*Running it*. They are architecture demonstrations, not trading hypotheses.

### 1. Simple directional strategy

```python
from dataclasses import dataclass
from decimal import Decimal

from app.services.strategy.capabilities import ConfigField, StrategyCapabilities
from app.services.strategy.contract import DecisionContext, DecisionKind, StrategyDecision


@dataclass
class SmaReversalStrategy:
    name: str = "sma_reversal_example"
    period: int = 10

    capabilities = StrategyCapabilities(
        name="sma_reversal_example",
        version="1",
        warmup_bars=10,
        outputs=frozenset(
            {DecisionKind.HOLD, DecisionKind.ENTER_LONG, DecisionKind.EXIT_LONG}
        ),
        config_schema={"name": ConfigField(str), "period": ConfigField(int, minimum=2)},
    )

    def decide(self, context: DecisionContext) -> StrategyDecision:
        if len(context.history) < self.period:
            return StrategyDecision(DecisionKind.HOLD, reason="warming up")
        window = context.history[-self.period:]
        average = sum((candle.close for candle in window), Decimal(0)) / Decimal(self.period)
        if context.position is None:
            if context.bar.close < average:
                return StrategyDecision(DecisionKind.ENTER_LONG, reason="close below average")
            return StrategyDecision(DecisionKind.HOLD, reason="no setup")
        if context.bar.close >= average:
            return StrategyDecision(DecisionKind.EXIT_LONG, reason="close back above average")
        return StrategyDecision(DecisionKind.HOLD, reason="still below average")


register_strategy(
    "sma_reversal_example",
    SmaReversalStrategy,
    capabilities=SmaReversalStrategy.capabilities,
)
```

The strategy never chooses a size: `ENTER_LONG` becomes a portfolio target using the constructor's
configured exposure, and a missing `stop_price`/`target_price` lets the engine apply its default
brackets.

### 2. Stateful strategy with a lifecycle

```python
from dataclasses import dataclass

from app.services.strategy.capabilities import ConfigField, StrategyCapabilities
from app.services.strategy.contract import (
    DecisionContext,
    DecisionKind,
    Finalizable,
    Initializable,
    Stateful,
    StrategyDecision,
)


@dataclass
class HoldNStrategy(Initializable, Finalizable, Stateful):
    name: str = "hold_n_example"
    hold_bars: int = 5

    capabilities = StrategyCapabilities(
        name="hold_n_example",
        version="1",
        stateful=True,
        outputs=frozenset(
            {DecisionKind.HOLD, DecisionKind.ENTER_LONG, DecisionKind.EXIT_LONG}
        ),
        config_schema={"name": ConfigField(str), "hold_bars": ConfigField(int, minimum=1)},
    )

    def __post_init__(self) -> None:
        self._entry_index: int | None = None

    def initialize(self, context: DecisionContext) -> None:
        self._entry_index = None

    def decide(self, context: DecisionContext) -> StrategyDecision:
        if context.position is None:
            if self._entry_index is None:
                self._entry_index = context.index
                return StrategyDecision(DecisionKind.ENTER_LONG, reason="enter once")
            return StrategyDecision(DecisionKind.HOLD, reason="waiting for fill")
        entry = self._entry_index if self._entry_index is not None else context.index
        if context.index - entry >= self.hold_bars:
            return StrategyDecision(DecisionKind.EXIT_LONG, reason="hold period elapsed")
        return StrategyDecision(DecisionKind.HOLD, reason="still holding")

    def finalize(self, context: DecisionContext) -> None:
        pass

    def state(self) -> dict[str, object]:
        return {"entry_index": self._entry_index}

    def restore_state(self, state) -> None:
        self._entry_index = state["entry_index"]


register_strategy(
    "hold_n_example",
    HoldNStrategy,
    capabilities=HoldNStrategy.capabilities,
)
```

Private attributes are run state, not configuration, so they stay out of the recorded parameters.
The runner builds a fresh instance per run, which is what keeps the result repeatable; `initialize`
resets the state explicitly as a second line of defence.

## Extending the architecture

Specialized behavior is added through optional interfaces and injected collaborators, never by an
engine branch per strategy:

- **A new decision kind** — add the enum member, a construction case in
  `ExposurePortfolioConstructor`, and (if it survives execution) a planning case. Unknown kinds
  fail loudly instead of being skipped.
- **A different sizing policy** — implement the `PortfolioConstructor` protocol and pass an
  instance to `prepare_strategy(..., constructor=...)`; the strategy is untouched.
- **A different execution style** — implement `ExecutionPlanner` and pass `planner=...`.
- **Extra inputs** — declare them in `input_data`/`event_types` and supply them in the
  environment and context; an undeclared or unsatisfiable input refuses the run.
- **Multi-instrument and target-weight strategies** — already expressible as decisions with
  `instrument`/`group_id`/`target_exposure`. A multi-instrument *environment* is not implemented
  yet, so such a strategy is validated and then correctly rejected rather than run with one leg.

## Parameters and reproducibility

`default_parameters(name)` returns the explicit configuration of a fresh instance. The runner
merges it with any `parameters` overrides, records the merged values, the dataset fingerprint,
git commit, library version, costs and risk assumptions with the run, and persists trades as an
append-only record. A stored run identifies exactly which strategy instance would reproduce it.

## What an addition must not do

- Do not embed exchange order submission in signal generation; that belongs to the separate
  execution layer.
- Do not read reserved, validation or out-of-sample datasets without existing authorization.
- Do not treat a passing test, a backtest result, or a registry entry as evidence of profitability.
- Do not add new risk limits or relax existing gates; the risk engine remains a separate layer.
