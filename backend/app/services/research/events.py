"""Direction-neutral research events, and the detectors that produce them.

The separation this package exists to enforce
---------------------------------------------
Section 3 of the research plan asks for a hard split between *detecting that
something happened* and *deciding what to do about it*. Almost every backtest
that gets quietly wrong fuses the two: a "liquidity sweep" becomes a short
signal, the short signal is backtested, and the backtest is reported as
evidence that sweeps are predictive — when what was actually measured is that
one particular response to one particular sweep was predictive, on one market,
over one period.

So a :class:`ResearchEvent` here has no direction, no entry, no stop and no
target. It says *this happened, here, and these are the numbers that were
knowable when it happened*. Whether to go long, go short, or not trade is a
decision made downstream in a module that is allowed to be wrong, and — this is
the part that matters for research — evaluated on both sides at once. See
:mod:`app.services.research.outcomes`, which labels every event for both
directions so the comparison against a baseline is honest by construction.

Causality
---------
Every event carries two indices, and the distinction is load-bearing:

``event_index``        the bar the phenomenon happened on.
``confirmation_index`` the first bar at which it could be *known*.

For a liquidity sweep — price pierces a previously-established level — the bar
of the pierce is the event, but a trader cannot know it is a sweep rather than
a breakout until the bar closes back inside. Those are different bars, and
labelling outcomes from the pierce bar measures something no participant could
have traded. Outcome labelling therefore always starts at the *confirmation*
bar, and every detector here is expected to differ from a naive implementation
on exactly this point.

Each detector is a pure function of a candle sequence, which is what lets
:mod:`app.services.research.lookahead` test it for causality without any
cooperation from the detector itself.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure import LiquidityLevel, MarketStructureResult
from app.services.market_structure.analysis import analyze_market_structure

#: Event kinds. These are *names for phenomena*, not strategies. Nothing here
#: says what to do about one.
EventKind = Literal[
    "structure",  # BOS / structure shift / swing sequence labels
    "liquidity_sweep",  # a level was pierced then closed back through
    "displacement",  # an unusually large, directional candle
    "volatility",  # realised volatility crosses a threshold
    "regime",  # the market state label changed
]


@dataclass(frozen=True)
class ResearchEvent:
    """Something that happened in the market, described without a position.

    ``features`` holds the numbers that were knowable at ``confirmation_index``
    and nothing else. A feature that can only be computed by looking forward —
    "distance to the next high", "how far this run eventually went" — does not
    belong in this dict, however useful it would be as a label. Labels live in
    :mod:`app.services.research.outcomes`.
    """

    kind: EventKind
    #: Which detector produced it, so a finding can be traced to a rule and a
    #: rule can be changed without invalidating the event log.
    detector: str
    event_index: int
    event_time: datetime
    confirmation_index: int
    confirmation_time: datetime | None
    #: Price at the confirmation bar — the price a decision could act on.
    price: Decimal
    features: dict[str, Decimal] = field(default_factory=dict)
    #: Free-form provenance, e.g. the swing indices a level came from.
    context: dict[str, object] = field(default_factory=dict)

    @property
    def confirmation_delay_bars(self) -> int:
        return self.confirmation_index - self.event_index

    def is_known_at(self, index: int) -> bool:
        """Whether a decision made at bar ``index`` could have used this event."""
        return self.confirmation_index <= index

    def as_row(self) -> dict[str, object]:
        """A flat dict for a dataframe or a CSV, timestamps as ISO strings."""
        return {
            "kind": self.kind,
            "detector": self.detector,
            "event_index": self.event_index,
            "event_time": self.event_time.isoformat(),
            "confirmation_index": self.confirmation_index,
            "confirmation_time": (
                self.confirmation_time.isoformat() if self.confirmation_time else None
            ),
            "confirmation_delay_bars": self.confirmation_delay_bars,
            "price": str(self.price),
            **{key: str(value) for key, value in self.features.items()},
        }


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------
#
# Each detector is a pure function of a candle sequence, reading only backwards
# from the current bar. Two shared conventions keep them comparable:
#
#   * "the reference value" is a rolling statistic over a *trailing* window,
#     never over the whole series. A global average makes every event's features
#     depend on the future.
#   * thresholds are *relative* (a multiple of trailing volatility) rather than
#     absolute, so a detector does not silently encode the price level or the
#     volatility regime of the sample it was written against.


def _close(candles: Sequence[CandleData], index: int) -> Decimal:
    return candles[index].close


def _realized_volatility(candles: Sequence[CandleData], index: int, window: int) -> Decimal | None:
    """Standard deviation of trailing log-style returns, in price units.

    Returned as a price-denominated volatility rather than a percentage so that
    every downstream distance — stop placement, excursion, displacement — is in
    the same units as the price itself and cannot be mixed up with a fraction.
    """
    if index < window:
        return None
    returns = [
        _close(candles, i) - _close(candles, i - 1)
        for i in range(index - window + 1, index + 1)
    ]
    if len(returns) < 2:
        return None
    mean = sum(returns) / Decimal(len(returns))
    variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns) - 1)
    return variance.sqrt()


def detect_structure_events(result: MarketStructureResult) -> list[ResearchEvent]:
    """Re-emit the market-structure pipeline's events as research events.

    This is a projection, not a reimplementation. The structure module already
    carries the swing/confirmation split and has been audited for causality;
    duplicating its logic here would be one more thing to keep in step, and one
    more chance for the two to disagree about what a swing is.
    """
    events: list[ResearchEvent] = []
    for item in result.events:
        events.append(
            ResearchEvent(
                kind="structure",
                detector=f"structure:{item.event_type}",
                event_index=item.index,
                event_time=item.timestamp,
                confirmation_index=item.confirmation_index,
                confirmation_time=item.confirmation_time,
                # The *confirmation* close, not the event-bar close: the event
                # bar's price was not knowable until the confirming bar closed,
                # and using it is the same error as labelling from a pivot.
                price=item.price,
                features={"event_price": item.price},
                context={
                    "event_type": item.event_type,
                    "broken_level": item.broken_level,
                    "penetration": item.penetration,
                    "previous_state": item.previous_state,
                    "new_state": item.new_state,
                    # Recorded, deliberately not acted on here. The direction is
                    # carried through so a downstream analysis can slice by it,
                    # but it grants the event no authority to be a signal.
                    "structure_direction": item.direction,
                },
            )
        )
    return events


def detect_liquidity_sweeps(
    candles: Sequence[CandleData],
    *,
    levels: Sequence[LiquidityLevel] | None = None,
    result: MarketStructureResult | None = None,
    min_penetration: Decimal = Decimal("0"),
    level_tolerance: Decimal = Decimal("0.001"),
) -> list[ResearchEvent]:
    """A level was pierced intrabar but the bar closed back through it.

    The definition is deliberately the *two-bar* one: a sweep is not merely
    "price went below the level", it is "price went below the level and then
    did not". Detecting that needs the bar's close, so ``event_index`` is the
    bar of the pierce and ``confirmation_index`` is the following bar. A
    detector that collapsed these into one index would look three to five bars
    more profitable than it is, which is precisely the illusion Section 2 exists
    to remove.

    :param min_penetration: how far past the level, as a fraction of its price,
        the wick must reach for this to count as a sweep rather than a graze.
        Zero means any penetration at all, which on real data is mostly noise.
    :param level_tolerance: how close a level's price must match a swing extreme
        for the swing to be treated as *that* level, as a fraction. Real markets
        produce clusters of near-equal highs; without a tolerance, equal highs
        are missed and every level is trivially unique.
    """
    if levels is None:
        if result is None:
            raise ValueError("detect_liquidity_sweeps needs either levels or a result")
        levels = result.liquidity_levels

    by_index = sorted(
        (level for level in levels if level.creation_index < len(candles)),
        key=lambda level: (level.creation_index, level.price),
    )
    if not by_index:
        return []

    events: list[ResearchEvent] = []
    # Levels are walked in creation order and a bar can only be swept by levels
    # that already existed when it opened — otherwise the "sweep" is the level
    # being created, which is a different phenomenon and is recorded as such by
    # the structure module.
    active: list[LiquidityLevel] = []
    #: The last bar on which each level was found to be trading *beyond* it.
    #: A sweep is a **crossing**, not a persistent condition: once price has
    #: closed back through a level, that level has already been swept, and
    #: trading above it again on some bar fifty candles later is not a new
    #: sweep of the same level. Without this, a single level that price crossed
    #: once generates an event on every subsequent bar — which on six thousand
    #: 1h bars produced over a million events instead of a few hundred, and made
    #: the detector both useless as a measurement and impossible to run.
    beyond_since: dict[int, int] = {}
    cursor = 0
    # The sweep on the final bar has no bar after it to be confirmed on, so it
    # is not an event this detector can report. A truncated series must not look
    # as though it could confirm something its own data ends before.
    for index in range(1, len(candles) - 1):
        while cursor < len(by_index) and by_index[cursor].creation_index < index:
            active.append(by_index[cursor])
            cursor += 1
        if not active:
            continue
        candle = candles[index]
        # A sweep of highs is a wick above; of lows, a wick below.
        for level in active:
            if level.level_type not in ("swing_high", "equal_highs", "range_high"):
                continue
            if candle.high <= level.price * (Decimal(1) + level_tolerance):
                # Price is back inside the level: any prior excursion is over,
                # so this level is eligible to be swept again next time.
                beyond_since.pop(id(level), None)
                continue
            # The level must be swept on the *first* bar it is found beyond.
            # Recording it as beyond and returning is what stops the rest of the
            # excursion from being counted as further sweeps of the same level.
            if id(level) in beyond_since:
                continue
            beyond_since[id(level)] = index
            swing_count = level.swing_count_at(index)
            penetration = (candle.high - level.price) / level.price
            if penetration < min_penetration:
                continue
            close_back = candle.close < level.price
            events.append(
                _sweep_event(
                    candles,
                    index,
                    level,
                    "above",
                    penetration,
                    close_back,
                    "swing_high",
                    swing_count,
                )
            )
        for level in active:
            if level.level_type not in ("swing_low", "equal_lows", "range_low"):
                continue
            if candle.low >= level.price * (Decimal(1) - level_tolerance):
                beyond_since.pop(id(level), None)
                continue
            if id(level) in beyond_since:
                continue
            beyond_since[id(level)] = index
            swing_count = level.swing_count_at(index)
            penetration = (level.price - candle.low) / level.price
            if penetration < min_penetration:
                continue
            close_back = candle.close > level.price
            events.append(
                _sweep_event(
                    candles,
                    index,
                    level,
                    "below",
                    penetration,
                    close_back,
                    "swing_low",
                    swing_count,
                )
            )
    return events


def _sweep_event(
    candles: Sequence[CandleData],
    index: int,
    level: LiquidityLevel,
    side: str,
    penetration: Decimal,
    close_back: bool,
    level_kind: str,
    swing_count: int = 1,
) -> ResearchEvent:
    """One sweep, with the event bar and the confirmation bar kept distinct."""
    candle = candles[index]
    # The pierce happened on this bar. Whether it turned out to be a sweep
    # rather than a breakout is only settled by the close of this same bar, so
    # the confirmation is this bar's close and the confirmation index is the
    # next one: at the close of bar `index` a trader knows the sweep happened,
    # and can act at the open of bar `index + 1`.
    confirmation_index = min(index + 1, len(candles) - 1)
    swept_side = "high" if side == "above" else "low"
    return ResearchEvent(
        kind="liquidity_sweep",
        detector=f"sweep:{level_kind}",
        event_index=index,
        event_time=candle.open_time,
        confirmation_index=confirmation_index,
        confirmation_time=candles[confirmation_index].close_time,
        price=candles[confirmation_index].close,
        features={
            "level_price": level.price,
            "penetration": penetration,
            "swept_side": Decimal(0 if swept_side == "low" else 1),
            "level_age_bars": Decimal(index - level.creation_index),
            "level_touch_count": Decimal(level.touch_count),
            "level_strength": Decimal(str(level.strength)),
            # How many swings had confirmed on this price *by this bar*. A level
            # formed from one swing and one formed from four are different
            # phenomena, but that difference has to be read at the time of the
            # sweep, not from a level object that has since absorbed the rest.
            "level_swing_count": Decimal(swing_count),
        },
        context={
            "swept_side": swept_side,
            "close_back_through_level": close_back,
            # Whether the bar closed back is a *known* fact at confirmation
            # time, but it is a feature, not a filter: a sweep that did not
            # close back is still a sweep of that level, and whether the
            # phenomenon only works when it does is a question the outcome
            # analysis is there to answer.
            "sweep_side": side,
            "level_type": level.level_type,
            "level_creation_index": level.creation_index,
            "level_is_equal": swing_count > 1,
        },
    )


def detect_displacement(
    candles: Sequence[CandleData],
    *,
    vol_window: int = 20,
    threshold: Decimal = Decimal("2"),
    min_body_ratio: Decimal = Decimal("0.5"),
) -> list[ResearchEvent]:
    """A candle whose body is large relative to recent volatility.

    Displacement is the price leaving a level *fast*, and the interesting
    property is usually the size relative to what the market has been doing
    recently — a 200-point candle means one thing when the last twenty moved 5
    and quite another when they moved 200. An absolute threshold would encode
    the sample it was written against; this one is a multiple of trailing
    volatility, so it means the same thing on any instrument at any price.

    :param threshold: body length, in units of trailing volatility, for a candle
        to qualify.
    :param min_body_ratio: body as a fraction of the full bar range. A candle
        with a huge wick and a small body is rejection, not displacement, and
        conflating the two would make the event log describe neither.
    """
    events: list[ResearchEvent] = []
    for index in range(1, len(candles)):
        volatility = _realized_volatility(candles, index, vol_window)
        if volatility is None or volatility == 0:
            continue
        candle = candles[index]
        body = abs(candle.close - candle.open)
        bar_range = candle.high - candle.low
        if bar_range == 0:
            continue
        body_ratio = body / bar_range
        if body_ratio < min_body_ratio:
            continue
        magnitude = body / volatility
        if magnitude < threshold:
            continue
        confirmation_index = min(index + 1, len(candles) - 1)
        events.append(
            ResearchEvent(
                kind="displacement",
                detector="displacement:volatility_multiple",
                event_index=index,
                event_time=candle.open_time,
                # A candle's magnitude is only final at its close, so the
                # earliest anyone can act on it is the next bar's open.
                confirmation_index=confirmation_index,
                confirmation_time=candles[confirmation_index].close_time,
                price=candles[confirmation_index].close,
                features={
                    "body": body,
                    "magnitude_in_volatility": magnitude,
                    "body_ratio": body_ratio,
                    "close_location": _close_location(candle),
                    "bar_range": bar_range,
                },
                context={
                    "direction_of_move": "up" if candle.close > candle.open else "down",
                    "vol_window": vol_window,
                    "threshold": threshold,
                },
            )
        )
    return events


def _close_location(candle: CandleData) -> Decimal:
    """Where the close sits in the bar's range: 0 at the low, 1 at the high.

    Used to tell a closing-bar (continuation) from a rejection (reversal), both
    of which can have the same body and range. A zero-range bar would divide by
    zero, so it is reported as the midpoint rather than raising.
    """
    bar_range = candle.high - candle.low
    if bar_range == 0:
        return Decimal("0.5")
    return (candle.close - candle.low) / bar_range


def detect_volatility_expansions(
    candles: Sequence[CandleData],
    *,
    vol_window: int = 20,
    ratio: Decimal = Decimal("2"),
) -> list[ResearchEvent]:
    """Realised volatility jumps relative to its own recent history.

    This is a volatility event, not a direction event: it says the market got
    more restless, and nothing about which way. Labelling it would be exactly
    the conflation Section 3 forbids.
    """
    events: list[ResearchEvent] = []
    # Stop one bar short: a level on the last bar has no next bar to confirm it,
    # and emitting one anyway would make a truncated prefix look as though it
    # could confirm an event it has not finished measuring.
    for index in range(vol_window, len(candles) - 1):
        current = _realized_volatility(candles, index, vol_window)
        if current is None or current == 0:
            continue
        # The comparison window sits entirely *before* the current one. Using
        # an overlapping window would compare volatility with itself.
        previous = _realized_volatility(candles, index - vol_window, vol_window)
        if previous is None or previous == 0:
            continue
        expansion = current / previous
        if expansion < ratio:
            continue
        confirmation_index = min(index + 1, len(candles) - 1)
        events.append(
            ResearchEvent(
                kind="volatility",
                detector="volatility:expansion",
                event_index=index,
                event_time=candles[index].open_time,
                confirmation_index=confirmation_index,
                confirmation_time=candles[confirmation_index].close_time,
                price=candles[confirmation_index].close,
                features={
                    "volatility": current,
                    "prior_volatility": previous,
                    "expansion_ratio": expansion,
                },
                context={"vol_window": vol_window, "ratio": ratio},
            )
        )
    return events


def detect_regime_changes(
    candles: Sequence[CandleData],
    *,
    vol_window: int = 20,
    trend_window: int = 50,
    vol_quantile: Decimal = Decimal("0.5"),
) -> list[ResearchEvent]:
    """Regime *transitions*, classified from trailing data only.

    Section 3 lists a regime event as one of the event kinds, and ``EventKind``
    declared one, but no detector ever produced any. That is not cosmetic: a
    research report that breaks results down "by regime" needs the regime label
    to be derivable, and without a detector the only honest answer is the word
    "unavailable".

    Two axes, both backward-looking:

    - **Trend** — sign of the trailing ``trend_window`` change in close, with a
      flat band so that a market drifting sideways does not alternate between
      "up" and "down" on noise.
    - **Volatility** — realised volatility against its own trailing
      distribution, thresholded at ``vol_quantile``. Percentile rather than an
      absolute cut, because an absolute cut is a parameter fitted to whatever
      volatility regime this sample happens to contain; a percentile re-derives
      itself and stays comparable across the five-year dataset and the next one.

    Only transitions are emitted, not every bar. A regime that holds for 400
    bars is one finding, not 400, and emitting it 400 times would inflate every
    downstream sample size by the number of bars in the longest regime.

    ``vol_quantile`` is computed over the window ending at the *current* bar and
    nothing after it, so the label on bar ``i`` is reachable from bar ``i``'s
    own close. The event is therefore confirmed at the bar it is detected on —
    ``confirmation_index == event_index`` — and there is no right-hand
    confirmation bar to leak from.
    """
    events: list[ResearchEvent] = []
    previous: str | None = None
    for index in range(max(vol_window, trend_window), len(candles)):
        candle = candles[index]

        change = _close(candles, index) - _close(candles, index - trend_window)
        # The flat band is a fraction of the trailing volatility, so it scales
        # with the market instead of being a fixed price amount that would be
        # trivially small in a quiet market and unreachable in a violent one.
        vol = _realized_volatility(candles, index, vol_window)
        band = vol if vol is not None else Decimal(0)
        if change > band:
            trend = "up"
        elif change < -band:
            trend = "down"
        else:
            trend = "flat"

        if vol is None or vol == 0:
            # A window with no measurable movement is *low* volatility, not an
            # absence of one. Calling it "unknown" would park a dead-flat
            # market in a category that is excluded from every breakdown, and
            # it also makes the percentile cut below undefined — there is no
            # distribution to take a median of when every value is zero.
            volatility = "low"
        else:
            history = [
                _realized_volatility(candles, i, vol_window)
                for i in range(index - vol_window + 1, index + 1)
            ]
            usable = sorted(v for v in history if v is not None)
            if not usable:
                volatility = "low"
            else:
                cut = usable[min(len(usable) - 1, int(len(usable) * vol_quantile))]
                volatility = "high" if vol >= cut else "low"

        state = f"{trend}:{volatility}"
        if previous is not None and state != previous:
            events.append(
                ResearchEvent(
                    kind="regime",
                    detector="regime:transition",
                    event_index=index,
                    event_time=candle.open_time,
                    confirmation_index=index,
                    confirmation_time=candle.close_time,
                    price=candle.close,
                    features={
                        "trend_change": change,
                        "volatility": vol if vol is not None else Decimal(0),
                        "flat_band": band,
                    },
                    context={
                        "trend": trend,
                        "volatility_state": volatility,
                        "previous_regime": previous,
                        "new_regime": state,
                    },
                )
            )
        previous = state
    return events


def detect_all(
    candles: Sequence[CandleData],
    *,
    symbol: str = "BTCUSDT",
    lookback: int = 3,
    vol_window: int = 20,
    trend_window: int = 50,
    #: Quoted and imported inside the body: ``Timeframe`` is resolved locally
    #: there so this module's detectors stay importable without pulling in the
    #: schema layer's enum at module scope.
    timeframe: Timeframe | None = None,
) -> list[ResearchEvent]:
    """Every detector's events over one series, in bar order.

    The structure pipeline is run once and shared: the sweep detector needs the
    same liquidity levels the structure events came from, and running the
    analysis twice would be both slower and a chance for the two runs to differ.

    ``timeframe`` must describe the series actually being analysed. It is a
    label on the events, and a wrong one does not change a single number — which
    is exactly why it is easy to get wrong and why a report that says "5m" while
    measuring 15m bars is worse than no report at all. It defaults to the first
    candle's own timeframe rather than a hardcoded guess.
    """
    if timeframe is None:
        timeframe = candles[0].timeframe if candles else Timeframe.M5

    result = analyze_market_structure(
        list(candles), symbol=symbol, timeframe=timeframe, lookback=lookback
    )
    events: list[ResearchEvent] = []
    events.extend(detect_structure_events(result))
    events.extend(detect_liquidity_sweeps(candles, result=result))
    events.extend(detect_displacement(candles, vol_window=vol_window))
    events.extend(detect_volatility_expansions(candles, vol_window=vol_window))
    events.extend(
        detect_regime_changes(
            candles, vol_window=vol_window, trend_window=trend_window
        )
    )
    events.sort(key=lambda event: (event.confirmation_index, event.kind, event.detector))
    return events
