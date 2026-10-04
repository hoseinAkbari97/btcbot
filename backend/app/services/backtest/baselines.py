"""Baseline strategies (Phase 3).

These are scientific controls, not production strategies. Their purpose is to
establish what the market and the cost model do on their own, so that any
later price-action strategy can be judged against them under identical
assumptions (same fees, same slippage, same latency, same sizing).

Baseline A  buy and hold
Baseline B  random entries, identical risk/execution assumptions
Baseline C  simple moving-average trend
Baseline D  Donchian-channel breakout

Randomness is injected as an explicit seed so every run is reproducible.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from app.schemas.market_data import CandleData

from .engine import CLOSE, HOLD, OPEN_LONG, OPEN_SHORT, Signal, StrategyContext

TWO = Decimal(2)


def _closes(history: list[CandleData]) -> list[Decimal]:
    return [candle.close for candle in history]


def _sma(values: list[Decimal], period: int) -> Decimal | None:
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / Decimal(len(window))


# ---------------------------------------------------------------------------
# Baseline A — buy and hold
# ---------------------------------------------------------------------------


@dataclass
class BuyAndHoldStrategy:
    """Buy on the first tradable bar, hold to the end of the data.

    It runs with **no stop and no target** — an artificial bracket would
    convert this baseline into a different strategy. The engine liquidates the
    position at the final close, so exactly two fills are charged: the entry
    and that exit.

    ``allocation_fraction`` is the share of capital committed, and is labelled as
    such: with no stop there is no monetary risk per unit, so this baseline has
    no R multiple. Reporting one would be an artefact of calling capital
    allocation "risk". Its trades are recorded with
    ``sizing_model == capital_allocation`` and ``net_r is None``.
    """

    name: str = "buy_and_hold"
    allocation_fraction: Decimal = Decimal("1")

    def __call__(self, context: StrategyContext) -> Signal:
        if context.position is not None:
            return Signal(kind=HOLD, reason="already long")
        return Signal(
            kind=OPEN_LONG,
            risk_fraction=self.allocation_fraction,
            use_default_brackets=False,
            reason="buy and hold entry at first available bar",
        )


# ---------------------------------------------------------------------------
# Baseline B — random
# ---------------------------------------------------------------------------


@dataclass
class RandomStrategy:
    """Random entries under exactly the same risk and execution assumptions.

    This is the null hypothesis. If a candidate strategy does not beat this
    after costs, its apparent edge is likely luck or an artefact of the sample.
    """

    name: str = "random"
    seed: int = 42
    entry_probability: float = 0.02
    risk_fraction: Decimal = Decimal("0.01")
    allow_short: bool = True

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def __call__(self, context: StrategyContext) -> Signal:
        if context.position is not None:
            return Signal(kind=HOLD, reason="already in a position")
        if self._rng.random() >= self.entry_probability:
            return Signal(kind=HOLD, reason="no random entry this bar")
        long = self._rng.random() >= 0.5
        kind = OPEN_LONG if long else OPEN_SHORT
        if not long and not self.allow_short:
            kind = OPEN_LONG
        return Signal(
            kind=kind,
            risk_fraction=self.risk_fraction,
            reason=f"random entry (seed={self.seed})",
        )


# ---------------------------------------------------------------------------
# Baseline C — moving-average trend
# ---------------------------------------------------------------------------


@dataclass
class SmaTrendStrategy:
    """Long-only trend follower: fast SMA above slow SMA is 'in'."""

    name: str = "sma_trend"
    fast_period: int = 20
    slow_period: int = 50
    risk_fraction: Decimal = Decimal("0.01")
    atr_stop_multiple: Decimal = Decimal("1.5")
    atr_target_multiple: Decimal = Decimal("3.0")

    def __call__(self, context: StrategyContext) -> Signal:
        history = list(context.history)
        closes = _closes(history)
        fast = _sma(closes, self.fast_period)
        slow = _sma(closes, self.slow_period)
        if fast is None or slow is None:
            return Signal(kind=HOLD, reason="warming up")

        in_position = context.position is not None and context.position.side == "long"

        if fast > slow and not in_position:
            return Signal(
                kind=OPEN_LONG,
                stop_price=self._stop(history[-1], history, long=True),
                target_price=self._target(history[-1], history, long=True),
                risk_fraction=self.risk_fraction,
                reason=f"SMA{self.fast_period} above SMA{self.slow_period}",
            )
        if fast < slow and in_position:
            return Signal(kind=CLOSE, reason=f"SMA{self.fast_period} below SMA{self.slow_period}")
        return Signal(kind=HOLD, reason="no crossover")

    def _atr(self, history: list[CandleData], period: int = 14) -> Decimal | None:
        if len(history) < period + 1:
            return None
        ranges = [
            max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close))
            for c, p in zip(history[-period:], history[-period - 1 : -1], strict=False)
        ]
        return sum(ranges) / Decimal(len(ranges))

    def _stop(
        self, candle: CandleData, history: list[CandleData], *, long: bool
    ) -> Decimal | None:
        atr = self._atr(history)
        if atr is None or atr <= 0:
            return None
        return candle.close - atr * self.atr_stop_multiple if long else candle.close + atr * self.atr_stop_multiple

    def _target(
        self, candle: CandleData, history: list[CandleData], *, long: bool
    ) -> Decimal | None:
        atr = self._atr(history)
        if atr is None or atr <= 0:
            return None
        return candle.close + atr * self.atr_target_multiple if long else candle.close - atr * self.atr_target_multiple


# ---------------------------------------------------------------------------
# Baseline D — Donchian breakout
# ---------------------------------------------------------------------------


@dataclass
class DonchianBreakoutStrategy:
    """Long-only breakout of the highest high of the previous N bars."""

    name: str = "donchian_breakout"
    lookback: int = 20
    risk_fraction: Decimal = Decimal("0.01")
    exit_lookback: int = 10
    stop_fraction: Decimal = Decimal("0.02")
    target_multiple: Decimal = TWO

    def __call__(self, context: StrategyContext) -> Signal:
        history = list(context.history)
        if len(history) < self.lookback + 1:
            return Signal(kind=HOLD, reason="warming up")

        # The channel excludes the current bar so the comparison is causal.
        window = history[-(self.lookback + 1) : -1]
        channel_high = max(c.high for c in window)
        channel_low = min(c.low for c in window)
        candle = history[-1]

        in_position = context.position is not None and context.position.side == "long"

        if candle.close > channel_high and not in_position:
            stop = candle.low * (Decimal(1) - self.stop_fraction)
            risk_per_unit = candle.close - stop
            target = (
                candle.close + risk_per_unit * self.target_multiple if risk_per_unit > 0 else None
            )
            return Signal(
                kind=OPEN_LONG,
                stop_price=stop,
                target_price=target,
                risk_fraction=self.risk_fraction,
                reason=f"closed above {self.lookback}-bar high ({channel_high})",
            )

        exit_window = history[-(self.exit_lookback + 1) : -1]
        if len(exit_window) == self.exit_lookback and in_position:
            exit_low = min(c.low for c in exit_window)
            if candle.close < exit_low:
                return Signal(
                    kind=CLOSE, reason=f"closed below {self.exit_lookback}-bar low ({exit_low})"
                )

        return Signal(kind=HOLD, reason="inside channel")


STRATEGIES: dict[str, Callable[[], object]] = {
    "buy_and_hold": BuyAndHoldStrategy,
    "random": RandomStrategy,
    "sma_trend": SmaTrendStrategy,
    "donchian_breakout": DonchianBreakoutStrategy,
}

STRATEGY_NAMES = tuple(STRATEGIES)


def build_strategy(name: str, /, **parameters: object) -> Callable[[StrategyContext], Signal]:
    """Instantiate a registered baseline strategy by name.

    ``name`` is positional-only so that ``default_parameters()`` — which
    includes each strategy's own ``name`` field — can be splatted straight
    back in as overrides.

    Unknown names raise rather than falling back silently — a typo in an
    experiment name would otherwise corrupt reproducibility.
    """
    try:
        factory = STRATEGIES[name]
    except KeyError:
        raise ValueError(
            f"unknown strategy {name!r}; available: {', '.join(sorted(STRATEGIES))}"
        ) from None
    return factory(**parameters)  # type: ignore[operator]


def default_parameters(name: str) -> dict[str, object]:
    """The parameters a fresh instance uses, for experiment records."""
    return {
        key: value
        for key, value in vars(build_strategy(name)).items()
        if not key.startswith("_")
    }