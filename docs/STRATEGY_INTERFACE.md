# Strategy interface and registry

This document describes how to add a strategy to the research pipeline. It is an engineering
contract only: registering a strategy does **not** authorize data access, open a research gate,
or assert that the strategy has an edge. See `docs/briefings/STAGE2ZJ_OWNER_DECISION_BRIEFING.md`
for the standing authorization boundaries. No code here places an order or contacts an exchange.

## The contract

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

### Stateful and event-driven strategies

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
it, and the function's keyword defaults become the recorded parameters.

## Registering a strategy

```python
from app.services.backtest.registry import register_strategy

register_strategy("my_strategy", MyStrategy, description="what the rule does")
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
