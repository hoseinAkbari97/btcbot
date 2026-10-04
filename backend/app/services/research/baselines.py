"""The null hypothesis, made concrete.

An event log that is not compared to something is not a result. A "liquidity
sweep followed by 3.2% mean upside" sounds like an edge, and it is exactly what
you would also see if you took a random bar, or simply took *every* bar — an
event that fires in a bull market will report a positive mean forward return no
matter what the event means, because the drift is in the sample, not in the
signal.

So every measurement in :mod:`app.services.research.outcomes` is reported
against these controls:

``buy_and_hold``   the drift of the underlying. Any strategy on a trending
                   sample will "beat" a random entry point.
``all_bars``       the unconditional forward distribution at every bar in the
                   sample. The strictest control: it absorbs drift, volatility
                   and regime all at once, so beating it means the event's
                   *timing* carried information.
``random_events``  events drawn uniformly at random, in number and in timing,
                   matched to each real event's own horizons. Isolates the
                   event's timing from the fact that events cluster.

The last one is the one usually skipped and the one that most often changes a
conclusion, because real events cluster in volatile stretches where forward
returns are wide but not asymmetric. Without it, "the event has information"
can just mean "the event happened during a big move".
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.schemas.market_data import CandleData
from app.services.research.outcomes import FORWARD_HORIZONS, EventOutcome

#: Below this many samples a mean is not reported, mirroring the trade-level
#: rule in :mod:`app.services.backtest.distributions`. The threshold is a
#: statement about what a handful of observations can support, not a tuned
#: threshold; the two are deliberately the same number so a reader who has seen
#: one does not have to learn another.
MIN_SAMPLES_FOR_MEAN = 30


@dataclass(frozen=True)
class Baseline:
    """One control's forward distribution over the same horizons as the events."""

    name: str
    #: Horizon -> mean forward return, or ``None`` where too few samples exist.
    mean_forward: dict[int, float | None]
    #: Horizon -> fraction of samples with a positive return.
    win_rate: dict[int, float | None]
    count: int
    sufficient_sample: bool
    #: Buy-and-hold total return over the sample, for a size reference.
    total_return: float | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "count": self.count,
            "sufficient_sample": self.sufficient_sample,
            "total_return": self.total_return,
            "mean_forward": {str(k): v for k, v in self.mean_forward.items()},
            "win_rate": {str(k): v for k, v in self.win_rate.items()},
        }


def _summarize(
    name: str, values: dict[int, list[Decimal]], *, total_return: float | None = None
) -> Baseline:
    """Turn a horizon -> returns mapping into means and win rates."""
    counts = [len(v) for v in values.values()]
    count = max(counts) if counts else 0
    enough = count >= MIN_SAMPLES_FOR_MEAN
    means: dict[int, float | None] = {}
    rates: dict[int, float | None] = {}
    for horizon, samples in values.items():
        if not enough:
            means[horizon] = None
            rates[horizon] = None
        else:
            means[horizon] = float(sum(samples) / Decimal(len(samples)))
            rates[horizon] = sum(1 for s in samples if s > 0) / len(samples)
    return Baseline(
        name=name,
        mean_forward=means,
        win_rate=rates,
        count=count,
        sufficient_sample=enough,
        total_return=total_return,
    )


def buy_and_hold(candles: Sequence[CandleData]) -> Baseline:
    """The drift of the underlying, measured over the whole sample.

    A small number here is not a control on an event log, it is the single
    number any long-only result must be read against: a strategy that returned
    less than this over the same period added risk and produced nothing.
    """
    if len(candles) < 2:
        return _summarize("buy_and_hold", {})
    first, last = candles[0].close, candles[-1].close
    return _summarize(
        "buy_and_hold",
        {},
        total_return=float((last - first) / first) if first else None,
    )


def all_bars(
    candles: Sequence[CandleData],
    *,
    horizons: Sequence[int] = FORWARD_HORIZONS,
) -> Baseline:
    """The unconditional forward distribution at every bar.

    This is the honest denominator. Comparing an event's mean to the sample's
    overall mean asks the right question — *did the event's timing add
    anything* — and is not fooled by drift, because drift is in both.
    """
    values: dict[int, list[Decimal]] = {h: [] for h in horizons}
    for index in range(len(candles)):
        for horizon in horizons:
            target = index + horizon
            if target < len(candles):
                values[horizon].append(candles[target].close - candles[index].close)
    return _summarize("all_bars", values)


def random_events(
    candles: Sequence[CandleData],
    n_events: int,
    *,
    seed: int = 0,
    horizons: Sequence[int] = FORWARD_HORIZONS,
) -> Baseline:
    """A matched random control: the same number of draws, at random bars.

    The seed is a parameter rather than a constant because a single random draw
    is itself a sample with wide error bars, and a control that happened to be
    unlucky would either manufacture or destroy an apparent effect. The caller
    should run this several times and look at the spread; one call is not a
    control, it is a coin toss with extra steps.
    """
    rng = random.Random(seed)
    if len(candles) < 2 or n_events <= 0:
        return _summarize("random_events", {})
    # Drawn without replacement, so a control cannot put two events on one bar
    # and claim a count the real event log could not have had either.
    indices = rng.sample(range(len(candles)), min(n_events, len(candles)))
    values: dict[int, list[Decimal]] = {h: [] for h in horizons}
    for index in indices:
        for horizon in horizons:
            target = index + horizon
            if target < len(candles):
                values[horizon].append(candles[target].close - candles[index].close)
    return _summarize("random_events", values)


def compare_to_baseline(
    outcomes: Sequence[EventOutcome],
    baseline: Baseline,
    *,
    side: str | None = None,
    horizons: Sequence[int] = FORWARD_HORIZONS,
) -> dict[int, float | None]:
    """The event's mean minus the baseline's, per horizon.

    ``None`` wherever either side is too small to mean anything, and ``None`` is
    never rendered as a difference of "no difference": an absent edge and a real
    zero are different claims.

    :param side: restrict to one direction. The default of ``None`` averages the
        two, which is only meaningful when the event was labelled both ways and
        the two halves are being pooled deliberately.
    """
    deltas: dict[int, float | None] = {}
    for horizon in horizons:
        event_mean = baseline.mean_forward.get(horizon)
        if not baseline.sufficient_sample or event_mean is None:
            deltas[horizon] = None
            continue
        samples = [
            o.forward_return[horizon]
            for o in outcomes
            if horizon in o.forward_return and (side is None or o.side == side)
        ]
        if len(samples) < MIN_SAMPLES_FOR_MEAN:
            deltas[horizon] = None
            continue
        measured = float(sum(samples) / Decimal(len(samples)))
        deltas[horizon] = measured - float(event_mean)
    return deltas
