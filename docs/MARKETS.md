# Research Market vs. Execution Market

This is the one document that should be read before any backtest result is
believed, and again before any result is allowed to influence a real order.

## The short version

```text
Research market:    BTC/USDT, Binance historical klines
Execution market:   BTC/USDT, Nobitex
```

**They are not assumed to be the same market.** Every backtest in this project
was produced on Binance data and models Binance cost behaviour. Nothing in the
backtester is currently validated against Nobitex. That is stated here so no
reader infers Nobitex execution quality from a Binance backtest.

## What differs, and why it matters

| Property | Why a Binance number does not transfer |
|---|---|
| **Fees** | Taker/maker schedules are set per venue. The research default in `costs.py` encodes the Binance schedule. |
| **Spread** | BTC/USDT is among the most liquid instruments in existence on Binance. Nobitex spread on BTC/USDT will differ, especially off-peak. Every result in this repo is, optimistically, a low-spread result. |
| **Depth / market impact** | The research cost model is a flat rate, not a depth model. At the sizes a risk-framed strategy trades, this is probably fine on Binance and is an open question on Nobitex. |
| **Slippage** | Empirically a function of venue depth *and* order size. Flat-rate slippage is a modelling assumption, not a measurement. |
| **Candle construction** | Binance klines are exchange-native. Nobitex trades may consolidate differently. Research features derived from Binance candles need not exist identically on Nobitex. |
| **Data history** | Binance has years of 5m BTC/USDT. Nobitex may not. This is the practical reason research and execution venues differ at all here. |
| **Latency** | A research latency of `latency_bars >= 1` is a *lower bound* chosen to be conservative on a 5m chart. It is not a model of a real venue round trip. |

## The consequence for reading results

A backtest result from this project answers:

> *Would this strategy have worked on Binance BTC/USDT, under the modelled
> costs, on this dataset?*

It does **not** yet answer:

> *Would this strategy make money on Nobitex?*

The honest reading is that a Nobitex-relevant result requires re-running with
Nobitex cost parameters. The infrastructure for that is in place (see below);
the parameters are not yet gathered.

## Design commitment: cost parameters are pluggable

`app/services/backtest/costs.py` holds fees, spread, slippage and latency as
**four separate named rates**, not one opaque number. That is not stylistic
preference — it is the reason venue migration does not require rewriting the
strategy or the backtester:

```python
from app.services.backtest.costs import CostModel

binance = CostModel(fee_rate=..., spread_rate=..., slippage_rate=..., latency_bars=1)
nobitex = CostModel(fee_rate=..., spread_rate=..., slippage_rate=..., latency_bars=1)
```

Later, `NobitexCostModel` should be a constructor of `CostModel` from measured
Nobitex characteristics — not a new backtester, and not a subclass that
re-implements fill logic. If adding Nobitex ever requires touching
`engine.py`'s fill path, that constraint has been violated.

## Open work (deliberately deferred, not forgotten)

- Measure Nobitex BTC/USDT fee schedule (maker/taker) and store it as a config
  default, not a hardcoded literal.
- Measure Nobitex spread distribution over a full BTC cycle; the flat-rate
  assumption should be replaced with at least a time-of-day profile.
- Measure Nobitex fill behaviour at the order sizes this system generates.
- Re-run the cost-sensitivity sweep (`costs.py::scaled`) under Nobitex
  parameters and confirm the strategy's edge survives the wider cost band.

Until those are done, **no result in this repository should be described as a
Nobitex result.**
