"""What actually happened after each event — measured, not assumed.

This module is the one that decides whether any of the detected phenomena are
worth researching. It does that *before* any strategy is written, which is the
entire point: a strategy fitted to a phenomenon that carries no information
will produce an equity curve regardless, and the curve is the least reliable
evidence available. Measuring the event's forward distribution first means the
question "does this contain information?" is answerable without having
committed to a direction, an entry, a stop or a target.

What gets measured
------------------
For every event, for both directions:

``forward_return`` at 1, 3, 6 and 12 bars after the *confirmation* bar. These
  are the raw question — "after this thing happened, did price go up or down?"
``mfe`` / ``mae``  the most favourable and most adverse excursion over the same
  horizon, in price and in R.
``r_barrier_hit``  whether ``+1R`` was reached before ``-1R``.

The R barriers need a stop distance, and that is the most consequential
assumption in the whole research pipeline. A +1R/-1R hit rate is a statement
about a *specific* stop placement, not about the event. So the stop is a
declared parameter, it is recorded on every labelled row, and the two
conventions that actually differ — a structural stop at the event's own swing
low, and a volatility-based stop at a multiple of trailing ATR — are separate
configurations rather than one silently chosen default.

Why the confirmation bar
------------------------
Outcomes are measured from ``confirmation_index``, not ``event_index``. A sweep
on bar 10 is not known to be a sweep until bar 10 closes, so the earliest price
anyone could act on is bar 11's open. Measuring from bar 10's close would credit
the event with a move that happened before it could have been acted on, and
across a whole event log that inflates every result it touches.

The cost of that honesty is recorded, not hidden: ``confirmation_delay_bars``
is a column in the output, so a reader can see how much of the sample sits at
the edge of the data and how many events have truncated forward windows.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from app.schemas.market_data import CandleData
from app.services.research.events import ResearchEvent

#: Forward horizons, in bars. One, three, six and twelve span from "the next
#: candle" to "roughly a session" on a 5m series. Horizons are not tuned here;
#: they are fixed so that two event kinds are compared on the same ones.
FORWARD_HORIZONS = (1, 3, 6, 12)

#: The bar an outcome is measured from: the bar *after* confirmation, since the
#: confirming bar's close is the first price that could be acted upon.
ENTRY_OFFSET = 1


@dataclass(frozen=True)
class StopModel:
    """How the R unit is defined for one labelling run.

    R is meaningless without it. Two strategies that both "stop out at 1R" on
    the same events are measuring different things if one uses the swing low and
    the other uses 1.5x ATR, and a report that omits this is not comparable to
    one that includes it.
    """

    name: str
    #: "swing" places the stop at the event's own structural extreme; "atr" at a
    #: multiple of trailing volatility; "fixed_percent" at a flat distance.
    kind: str
    atr_multiplier: Decimal = Decimal("1.5")
    atr_window: int = 20
    fixed_percent: Decimal = Decimal("0.005")

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "atr_multiplier": str(self.atr_multiplier),
            "atr_window": self.atr_window,
            "fixed_percent": str(self.fixed_percent),
        }


#: The two conventions, side by side. Reporting an event's edge under both is
#: not indecision — it is the cheapest available check on whether the result
#: depends on the analyst's choice of stop.
SWING_STOP = StopModel(name="swing_extreme", kind="swing")
ATR_STOP = StopModel(name="atr_1.5", kind="atr", atr_multiplier=Decimal("1.5"))
DEFAULT_STOP_MODELS = (SWING_STOP, ATR_STOP)


@dataclass(frozen=True)
class EventOutcome:
    """The measured forward behaviour of one event, in one direction.

    Every field that could not be measured is ``None``, never zero. A truncated
    forward window is missing data, and writing it as zero would pull a mean
    return toward the middle of the distribution in a way nothing in the output
    could reveal.
    """

    event_index: int
    confirmation_index: int
    confirmation_delay_bars: int
    kind: str
    detector: str
    side: str
    #: Price at the bar the outcome is measured from.
    entry_price: Decimal
    #: Price of the R unit, and the number of bars it spans. ``None`` where the
    #: stop could not be placed — no swing low, or no data for ATR.
    stop_price: Decimal | None = None
    stop_distance: Decimal | None = None
    forward_return: dict[int, Decimal] = field(default_factory=dict)
    forward_return_r: dict[int, Decimal] = field(default_factory=dict)
    mfe: Decimal | None = None
    mae: Decimal | None = None
    mfe_r: Decimal | None = None
    mae_r: Decimal | None = None
    #: Horizon over which the excursions were measured.
    excursion_horizon: int = 12
    #: Whether +1R printed before -1R within the barrier horizon. ``None`` when
    #: the R unit is undefined, since the question is then unanswerable rather
    #: than false.
    r_barrier_hit: bool | None = None
    bars_to_barrier: int | None = None
    stop_model: str = ""
    #: True when the forward window ran off the end of the data, so the longest
    #: horizons are genuinely unknown rather than merely small.
    truncated: bool = False

    def as_row(self) -> dict[str, object]:
        row: dict[str, object] = {
            "event_index": self.event_index,
            "confirmation_index": self.confirmation_index,
            "confirmation_delay_bars": self.confirmation_delay_bars,
            "kind": self.kind,
            "detector": self.detector,
            "side": self.side,
            "entry_price": str(self.entry_price),
            "stop_price": None if self.stop_price is None else str(self.stop_price),
            "stop_distance": None if self.stop_distance is None else str(self.stop_distance),
            "stop_model": self.stop_model,
            "truncated": self.truncated,
            "mfe": None if self.mfe is None else str(self.mfe),
            "mae": None if self.mae is None else str(self.mae),
            "mfe_r": None if self.mfe_r is None else str(self.mfe_r),
            "mae_r": None if self.mae_r is None else str(self.mae_r),
            "r_barrier_hit": self.r_barrier_hit,
            "bars_to_barrier": self.bars_to_barrier,
        }
        for horizon in FORWARD_HORIZONS:
            value = self.forward_return.get(horizon)
            row[f"fwd_{horizon}"] = None if value is None else str(value)
            value_r = self.forward_return_r.get(horizon)
            row[f"fwd_{horizon}r"] = None if value_r is None else str(value_r)
        return row


def _true_range(candles: Sequence[CandleData], index: int) -> Decimal:
    """Wilder's true range for one bar, needing only that bar and the last close."""
    candle = candles[index]
    if index == 0:
        return candle.high - candle.low
    previous_close = candles[index - 1].close
    return max(
        candle.high - candle.low,
        abs(candle.high - previous_close),
        abs(candle.low - previous_close),
    )


def _atr(candles: Sequence[CandleData], index: int, window: int) -> Decimal | None:
    """Trailing ATR, using only bars at or before ``index``."""
    if index < window:
        return None
    total = sum(_true_range(candles, i) for i in range(index - window + 1, index + 1))
    return total / Decimal(window)


def _structural_stop(
    candles: Sequence[CandleData], event: ResearchEvent, side: str
) -> Decimal | None:
    """The stop implied by the event's own structure.

    For a long the stop goes below the most recent bar's low before entry; for a
    short, above its high. Entry happens one bar *after* confirmation, so the
    reference is the confirmation bar, not the event bar: a stop taken from a
    level the market already left would be a distance to the wrong place.

    When the confirming bar itself made a new extreme in the trade's favour the
    distance collapses to zero, and ``None`` is returned rather than a guess —
    a stop placed somewhere arbitrary would produce an R that looks measured but
    is not.
    """
    reference = min(event.confirmation_index, len(candles) - 1)
    if reference < 0:
        return None
    candle = candles[reference]
    if side == "long":
        return candle.low
    return candle.high


def _stop_for(
    candles: Sequence[CandleData],
    event: ResearchEvent,
    side: str,
    entry_price: Decimal,
    model: StopModel,
) -> tuple[Decimal, Decimal] | None:
    """The stop price and its distance from entry, or ``None`` if undefined."""
    if model.kind == "swing":
        stop = _structural_stop(candles, event, side)
        if stop is None:
            return None
        distance = abs(entry_price - stop)
    elif model.kind == "atr":
        # ATR at the *entry* bar and earlier, never later: the volatility a
        # trader could see when sizing is the volatility behind them.
        atr = _atr(candles, event.confirmation_index, model.atr_window)
        if atr is None or atr == 0:
            return None
        distance = atr * model.atr_multiplier
        stop = entry_price - distance if side == "long" else entry_price + distance
    elif model.kind == "fixed_percent":
        distance = entry_price * model.fixed_percent
        stop = entry_price - distance if side == "long" else entry_price + distance
    else:
        raise ValueError(f"unknown stop model kind: {model.kind!r}")
    # A zero-distance stop would divide by zero in every R calculation below, and
    # it means the entry is already at the stop, so there is no trade to size.
    if distance <= 0:
        return None
    return stop, distance


def label_event(
    candles: Sequence[CandleData],
    event: ResearchEvent,
    *,
    side: str,
    stop_model: StopModel,
    horizons: Sequence[int] = FORWARD_HORIZONS,
    barrier_r: Decimal = Decimal("1"),
    barrier_horizon: int = 12,
) -> EventOutcome:
    """Measure one event's forward behaviour in one direction.

    ``side`` is ``"long"`` or ``"short"``. Both are always computed: a
    phenomenon that only "works" in one direction is still a phenomenon, and
    labelling only the flattering side is how a research log becomes a
    backtest in disguise.
    """
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side!r}")
    direction = Decimal(1) if side == "long" else Decimal(-1)

    # The earliest bar anyone could transact on. Entering at the confirmation
    # bar's close is a *limit* of what is achievable — it assumes an order
    # placed the instant that close prints, with no latency. Adding a bar is a
    # cost, not a refinement; the honest default is the optimistic one and the
    # assumption is stated here.
    entry_index = min(event.confirmation_index + ENTRY_OFFSET, len(candles) - 1)
    entry_price = _close(candles, entry_index)

    stop = _stop_for(candles, event, side, entry_price, stop_model)
    stop_price = stop[0] if stop else None
    stop_distance = stop[1] if stop else None

    forward: dict[int, Decimal] = {}
    forward_r: dict[int, Decimal] = {}
    for horizon in horizons:
        target = entry_index + horizon
        if target < len(candles):
            move = (_close(candles, target) - entry_price) * direction
            forward[horizon] = move
            if stop_distance is not None:
                forward_r[horizon] = move / stop_distance
        # A horizon past the end of the data is left *absent* from the dict
        # rather than filled with zero: the difference between "the move was
        # zero" and "we do not know" is the whole reason this dict is sparse.

    last = min(entry_index + max(horizons), len(candles) - 1)
    horizon_bars = last - entry_index
    mfe = mae = mfe_r = mae_r = None
    if horizon_bars > 0:
        best = worst = None
        for index in range(entry_index + 1, last + 1):
            candle = candles[index]
            # A long's favourable excursion is the highest high reached, its
            # adverse one the lowest low — intrabar, not close-to-close, so a
            # spike that reversed inside the bar still counts. That is the
            # conservative direction for MFE and the honest one for MAE.
            for extreme, favourable in ((candle.high, True), (candle.low, False)):
                move = (extreme - entry_price) * direction
                if favourable:
                    best = move if best is None else max(best, move)
                else:
                    worst = move if worst is None else min(worst, move)
        mfe, mae = best, worst
        if stop_distance is not None:
            mfe_r, mae_r = best / stop_distance, worst / stop_distance

    barrier_hit: bool | None = None
    bars_to_barrier: int | None = None
    if stop_distance is not None:
        barrier_price = entry_price + direction * barrier_r * stop_distance
        last_barrier = min(entry_index + barrier_horizon, len(candles) - 1)
        for index in range(entry_index + 1, last_barrier + 1):
            candle = candles[index]
            if side == "long":
                hit_high, hit_low = candle.high >= barrier_price, candle.low <= stop_price
            else:
                hit_high, hit_low = candle.low <= barrier_price, candle.high >= stop_price
            if hit_high and hit_low:
                # Both barriers inside one bar: which printed first is not
                # knowable from OHLC data. Recording "hit" would assume the
                # favourable one, and recording "miss" would assume the
                # adverse one, so neither is claimed.
                barrier_hit = None
                bars_to_barrier = None
                break
            if hit_high or hit_low:
                barrier_hit = hit_high
                bars_to_barrier = index - entry_index
                break

    return EventOutcome(
        event_index=event.event_index,
        confirmation_index=event.confirmation_index,
        confirmation_delay_bars=event.confirmation_delay_bars,
        kind=event.kind,
        detector=event.detector,
        side=side,
        entry_price=entry_price,
        stop_price=stop_price,
        stop_distance=stop_distance,
        forward_return=forward,
        forward_return_r=forward_r,
        mfe=mfe,
        mae=mae,
        mfe_r=mfe_r,
        mae_r=mae_r,
        excursion_horizon=horizon_bars,
        r_barrier_hit=barrier_hit,
        bars_to_barrier=bars_to_barrier,
        stop_model=stop_model.name,
        truncated=entry_index + max(horizons) >= len(candles),
    )


def label_events(
    candles: Sequence[CandleData],
    events: Sequence[ResearchEvent],
    *,
    stop_models: Sequence[StopModel] = DEFAULT_STOP_MODELS,
    sides: Sequence[str] = ("long", "short"),
) -> list[EventOutcome]:
    """Label every event on every stop model and both sides.

    The full cross-product is produced deliberately. One stop model is a choice
    the analyst made; showing the result under several is how you find out
    whether the finding was the event's or yours.
    """
    outcomes: list[EventOutcome] = []
    for event in events:
        for model in stop_models:
            for side in sides:
                outcomes.append(
                    label_event(candles, event, side=side, stop_model=model)
                )
    return outcomes


def _close(candles: Sequence[CandleData], index: int) -> Decimal:
    return candles[index].close
