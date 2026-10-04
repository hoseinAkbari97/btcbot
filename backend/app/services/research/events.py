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
from bisect import bisect_left, insort
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

    def to_payload(self) -> dict:
        """A JSON-safe dict that :meth:`from_payload` turns back into an event.

        Distinct from :meth:`as_row` on purpose: a row is flattened for a table
        and is lossy about types, while this is what a checkpoint stores and must
        round-trip *exactly*. ``Decimal`` is kept as a string rather than a float
        because a sweep's price is compared against later bars -- at float
        precision a level and the price that swept it can stop being equal, and
        the level then looks perpetually unswept.
        """
        return {
            "kind": self.kind,
            "detector": self.detector,
            "event_index": self.event_index,
            "event_time": self.event_time.isoformat(),
            "confirmation_index": self.confirmation_index,
            "confirmation_time": (
                self.confirmation_time.isoformat() if self.confirmation_time else None
            ),
            "price": str(self.price),
            "features": {key: str(value) for key, value in self.features.items()},
            "context": self.context,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> ResearchEvent:
        return cls(
            kind=payload["kind"],
            detector=payload["detector"],
            event_index=int(payload["event_index"]),
            event_time=datetime.fromisoformat(payload["event_time"]),
            confirmation_index=int(payload["confirmation_index"]),
            confirmation_time=(
                datetime.fromisoformat(payload["confirmation_time"])
                if payload.get("confirmation_time")
                else None
            ),
            price=Decimal(payload["price"]),
            features={
                key: Decimal(value) for key, value in payload.get("features", {}).items()
            },
            context=dict(payload.get("context", {})),
        )


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


#: Level kinds a bar can sweep from above. A sweep of a high is a wick above
#: it; a sweep of a low is a wick below. Kept as module constants rather than
#: inline literals so the two candidate-selection sides cannot drift apart.
HIGH_LEVEL_TYPES = ("swing_high", "equal_highs", "range_high")
LOW_LEVEL_TYPES = ("swing_low", "equal_lows", "range_low")


@dataclass
class SweepCarried:
    """Sweep-detector state that must survive a window boundary.

    The swept set is the one piece of this detector that is not a function of
    the current window, and it is what makes a sweep a *crossing* rather than a
    condition. Without it, every level price has already left is re-armed at
    each boundary and swept again, so a segmented run reports the same level
    once per segment the price spent beyond it.

    Keys are ``(creation_index, level_type, price)`` rather than ``id(level)``,
    because ``id`` is not stable across a checkpoint -- a resumed process
    allocates its level objects at different addresses, and a state keyed by
    address would silently match nothing. A structural key survives the round
    trip, and a price collision is harmless: two levels at the same price are
    swept under the same rule anyway.
    """

    #: level key -> absolute bar index the sweep was recorded on. The bar index
    #: is kept because it is the useful fact when auditing -- "how long ago was
    #: this level swept" -- but nothing in the detector branches on its value.
    #: What matters is membership: a level is swept once, on the first bar it is
    #: found beyond after having been back inside.
    swept: dict[tuple[int, str, str], int] = field(default_factory=dict)

    #: Sweeps found on a window's last bar, whose confirmation bar has not
    #: printed yet. A sweep is confirmed by the *next* bar's open, so a sweep on
    #: the last bar of a window cannot be reported until the next window supplies
    #: that bar. Emitting it immediately pins ``confirmation_index`` to the
    #: window's own last bar, and every boundary in a segmented run then reports
    #: its last sweep one bar early -- which is exactly the kind of difference
    #: that makes a segmented event log disagree with a continuous one while
    #: every individual event still looks right.
    pending: list[dict] = field(default_factory=list)

    #: The window's own first bar needs the bar *before* it to build its
    #: candidate band, and at ``candles[0]`` there is none in hand -- indexing
    #: ``candles[-1]`` would silently read the window's *last* bar instead and
    #: band every bar between the two. Only ``high`` and ``low`` are kept,
    #: because those are all the band needs; carrying the whole bar would mean
    #: carrying a slice of history across every boundary.
    previous_bar: tuple[str, str] | None = None

    @staticmethod
    def key(level: LiquidityLevel) -> tuple[int, str, str]:
        return (level.creation_index, level.level_type, str(level.price))

    def to_payload(self) -> dict:
        return {
            "swept": [[list(key), bar] for key, bar in sorted(self.swept.items())],
            "pending": list(self.pending),
            "previous_bar": (
                list(self.previous_bar) if self.previous_bar is not None else None
            ),
        }

    @classmethod
    def from_payload(cls, payload: dict | None) -> SweepCarried:
        if not payload:
            return cls()
        return cls(
            swept={
                (int(key[0]), str(key[1]), str(key[2])): int(bar)
                for key, bar in payload["swept"]
            },
            pending=[dict(item) for item in payload.get("pending", [])],
            previous_bar=(
                tuple(payload["previous_bar"])  # type: ignore[arg-type]
                if payload.get("previous_bar") is not None
                else None
            ),
        )


def detect_liquidity_sweeps(
    candles: Sequence[CandleData],
    *,
    levels: Sequence[LiquidityLevel] | None = None,
    result: MarketStructureResult | None = None,
    min_penetration: Decimal = Decimal("0"),
    level_tolerance: Decimal = Decimal("0.001"),
    offset: int = 0,
    carried: SweepCarried | None = None,
    final: bool = True,
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
    :param offset: the absolute bar index of ``candles[0]``, when the caller is
        passing a *window* of a longer series rather than the whole thing. Every
        event's indices are absolute. Zero for the batch path.
    :param carried: sweep state from the previous window, mutated in place. The
        "already swept" set spans arbitrary bar distances -- a level crossed in
        January and revisited in June is the same level -- so it cannot be
        rebuilt from a window and must be handed over explicitly. It also carries
        the previous window's *unconfirmed* last-bar sweeps, which this window
        resolves against its own first bar.
    :param final: whether this window ends the series. Only the final window may
        report a sweep on its own last bar, whose confirmation bar the dataset no
        longer contains; every other window defers it. See :attr:`SweepCarried.pending`.
    """
    if levels is None:
        if result is None:
            raise ValueError("detect_liquidity_sweeps needs either levels or a result")
        levels = result.liquidity_levels

    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    by_index = sorted(
        # ``< offset + len(candles)``: a bar can only be swept by a level that
        # existed when it opened. With a window, that bound is absolute.
        (level for level in levels if level.creation_index < offset + len(candles)),
        key=lambda level: (level.creation_index, level.price),
    )
    if not by_index:
        return []

    events: list[ResearchEvent] = []
    state = carried if carried is not None else SweepCarried()

    # Resolve what the previous window left pending. Its last bar is this
    # window's bar ``offset``, so the confirmation price and time are available
    # now and were not available then.
    if state.pending:
        first = candles[0]
        for payload in state.pending:
            events.append(
                ResearchEvent.from_payload(
                    {
                        **payload,
                        "confirmation_index": offset,
                        # Close of the confirmation bar, matching what
                        # ``_sweep_event`` reads on the batch path. Using the open
                        # here would make every deferred event differ from its
                        # whole-series counterpart by the bar's own range -- a
                        # small number that silently breaks equality.
                        "confirmation_time": first.close_time.isoformat(),
                        "price": str(first.close),
                    }
                )
            )
        state.pending.clear()
    # Levels are walked in creation order and a bar can only be swept by levels
    # that already existed when it opened — otherwise the "sweep" is the level
    # being created, which is a different phenomenon and is recorded as such by
    # the structure module.
    active: list[LiquidityLevel] = []
    #: Active levels in ascending price order, per side. This structure is why
    #: the detector is usable on 5m data at all -- see :func:`_sweep_candidates`
    #: for why selecting by price band yields *exactly* the same events as
    #: scanning every level. ``active`` is retained only for the emptiness test.
    highs: list[tuple[Decimal, int, LiquidityLevel]] = []
    lows: list[tuple[Decimal, int, LiquidityLevel]] = []
    #: The last bar on which each level was found to be trading *beyond* it.
    #: A sweep is a **crossing**, not a persistent condition: once price has
    #: closed back through a level, that level has already been swept, and
    #: trading above it again on some bar fifty candles later is not a new
    #: sweep of the same level. Without this, a single level that price crossed
    #: once generates an event on every subsequent bar -- which on six thousand
    #: 1h bars produced over a million events instead of a few hundred, and made
    #: the detector both useless as a measurement and impossible to run.
    swept = state.swept
    cursor = 0
    # The sweep on the final bar has no bar after it to be confirmed on, so it
    # is not an event this detector can report. A truncated series must not look
    # as though it could confirm something its own data ends before.
    #
    # Only the *final* window stops short. An intermediate window runs to its own
    # last bar and stashes that bar's sweeps in ``state.pending`` for the next
    # window to confirm -- the alternative, reporting them now against this
    # window's last bar, is the bug that made a segmented run disagree with a
    # continuous one by exactly one bar at every boundary.
    stop = len(candles) - 1 if final else len(candles)
    last_index = len(candles) - 1
    # A window's first bar is a real bar and must be swept. The batch path
    # cannot reach it either (``index`` starts at 1, because it has no previous
    # bar), so both paths agree to leave it to whatever precedes the series --
    # except in a segmented run, where the previous window supplies that bar and
    # this one must evaluate it, or a whole segment's leading sweeps vanish
    # silently at every boundary.
    start_index = 0 if state.previous_bar is not None else 1
    if offset == 0:
        # The dataset's own first bar is skipped by the batch path, so a windowed
        # run must skip it too or it would report events the batch path cannot.
        start_index = 1
    previous_high = Decimal(state.previous_bar[0]) if state.previous_bar else None
    previous_low = Decimal(state.previous_bar[1]) if state.previous_bar else None

    def emit(event: ResearchEvent) -> None:
        """Report a sweep, or park it if its confirmation bar is not here yet.

        A sweep on the window's own last bar is real -- the pierce and the close
        back through the level are both on that bar -- but its confirmation is
        the *next* bar's open, which this window does not contain. Parking it
        keeps the event in the log with the right bar and lets the next window
        fill in the price a decision could actually have acted on.
        """
        if not final and event.event_index == offset + last_index:
            state.pending.append(event.to_payload())
        else:
            events.append(event)
    for index in range(start_index, stop):
        absolute = offset + index
        while cursor < len(by_index) and by_index[cursor].creation_index < absolute:
            level = by_index[cursor]
            active.append(level)
            if level.level_type in HIGH_LEVEL_TYPES:
                insort(highs, (level.price, cursor, level))
            elif level.level_type in LOW_LEVEL_TYPES:
                insort(lows, (level.price, cursor, level))
            cursor += 1
        if not active:
            continue
        candle = candles[index]
        # ``_previous_cut_from`` looks one bar back, which is unavailable on the very
        # first bar and *is* available at a window's first bar -- the previous
        # window supplied it. Handing it ``None`` there would widen the band to
        # "exclude nothing", evaluating every level and re-sweeping ones the
        # previous window had already priced.
        previous_cut_high = (
            None
            if absolute == 0
            else (
                previous_high / (Decimal(1) + level_tolerance)
                if index == 0
                else _previous_cut_from(candles[index - 1], level_tolerance, high=True)
            )
        )
        previous_cut_low = (
            None
            if absolute == 0
            else (
                previous_low / (Decimal(1) - level_tolerance)
                if index == 0
                else _previous_cut_from(candles[index - 1], level_tolerance, high=False)
            )
        )

        # Re-arm first, and over *every* active level rather than the
        # candidate band. A level is swept once per excursion: it becomes
        # sweepable again only once price has traded back through it. That test
        # is about the level's own price against the bar's range, which is
        # exactly as expensive to evaluate as before -- so it is kept correct and
        # cheap by ordering the levels by price and cutting at the price the bar
        # actually reached.
        #
        # It cannot be folded into the candidate band below. The band selects
        # levels that are *beyond* the level, and a level that price has left
        # far behind is inside the range of neither the previous nor the current
        # cut -- so it never appears as a candidate, and the reset branch that
        # used to live there was unreachable for exactly those levels. A level
        # swept once and then abandoned stayed armed off forever: it was
        # suppressed for the rest of the run, and every later sweep of it was
        # silently lost.
        rearm_high = candle.high / (Decimal(1) + level_tolerance)
        rearm_low = candle.low / (Decimal(1) - level_tolerance)
        # Re-arming and sweeping are the *negations* of one another: a high level
        # is beyond the bar when ``high > price * (1 + tol)`` and armed again
        # when it is not. So the re-arm band is the complement of the sweep band
        # and the two are disjoint by construction. Selecting the complement
        # explicitly -- ``> rearm_high`` for highs, ``< rearm_low`` for lows --
        # is what keeps a level from re-arming and being swept on the same bar,
        # which would invent an excursion that never happened.
        inside: set[tuple[int, str, str]] = set()
        for level in highs[_cut(highs, rearm_high) :]:
            key = SweepCarried.key(level[2])
            swept.pop(key, None)
            inside.add(key)
        for level in lows[: _cut(lows, rearm_low)]:
            key = SweepCarried.key(level[2])
            swept.pop(key, None)
            inside.add(key)

        # A sweep of highs is a wick above; of lows, a wick below.
        for level in _sweep_candidates(
            highs,
            previous_cut_high,
            candle.high / (Decimal(1) + level_tolerance),
        ):
            key = SweepCarried.key(level)
            if key in swept or key in inside:
                continue
            swept[key] = absolute
            swing_count = level.swing_count_at(absolute)
            penetration = (candle.high - level.price) / level.price
            if penetration < min_penetration:
                continue
            close_back = candle.close < level.price
            emit(
                _sweep_event(
                    candles,
                    index,
                    level,
                    "above",
                    penetration,
                    close_back,
                    "swing_high",
                    swing_count,
                    offset=offset,
                )
            )
        for level in _sweep_candidates(
            lows,
            previous_cut_low,
            candle.low / (Decimal(1) - level_tolerance),
        ):
            key = SweepCarried.key(level)
            if key in swept or key in inside:
                continue
            swept[key] = absolute
            swing_count = level.swing_count_at(absolute)
            penetration = (level.price - candle.low) / level.price
            if penetration < min_penetration:
                continue
            close_back = candle.close > level.price
            emit(
                _sweep_event(
                    candles,
                    index,
                    level,
                    "below",
                    penetration,
                    close_back,
                    "swing_low",
                    swing_count,
                    offset=offset,
                )
            )
    # Hand the next window the bar it cannot see. Recorded unconditionally,
    # including for the final window: a checkpoint taken at the end of the run
    # should still describe the data it consumed, and the cost is two Decimals.
    state.previous_bar = (str(candles[last_index].high), str(candles[last_index].low))
    return events


def _previous_cut_from(
    candle: CandleData, tolerance: Decimal, *, high: bool
) -> Decimal | None:
    """The previous bar's boundary for the candidate band.

    Takes the *bar*, not the series and an index, because in windowed mode the
    previous bar is not in the window at all: at ``candles[0]`` of the second
    window the previous bar is the last bar of the first. Passing the previous
    bar explicitly is what lets the same code serve both, and it is why the
    detector's band is identical across a boundary instead of widening to
    "exclude nothing" there.

    ``None`` means "exclude nothing", and is only correct on the very first bar
    of the *dataset* -- where there genuinely is no previous bar to have been
    inside every level, so every level is a candidate.
    """
    field = candle.high if high else candle.low
    return field / (Decimal(1) + tolerance if high else Decimal(1) - tolerance)


def _sweep_candidates(
    levels: list[tuple[Decimal, int, LiquidityLevel]],
    lower: Decimal | None,
    upper: Decimal,
) -> list[LiquidityLevel]:
    """Levels a bar could have changed its beyond/inside state against.

    This is the correctness argument for the entire optimisation, so it is
    stated exactly. For the high side a level becomes *newly* beyond at bar
    ``i`` only if

    * it was not beyond at bar ``i - 1``, which means
      ``high[i-1] <= level.price * (1 + tol)``, hence
      ``level.price >= high[i-1] / (1 + tol)``; and
    * it is beyond at bar ``i``, which means
      ``level.price < high[i] / (1 + tol)``.

    Together those put the price in ``[previous_cut, current_cut)`` -- a band
    delimited by *the previous and current bar\'s own highs*, and by nothing
    about the level. A level outside the band cannot have changed state on this
    bar, so skipping it cannot change the output. The scan therefore costs the
    number of levels inside one bar\'s price range rather than the number of
    levels in existence: on 5m data that is a handful instead of 25,000.

    This selects *candidates for evaluation*, not events. A candidate can still
    be inside the level (and hit the reset branch), already swept, or under
    ``min_penetration``. Every original branch is preserved; only the set of
    levels offered to it has shrunk to the set that could possibly reach it.

    On the low side the caller passes the previous bar\'s low as ``upper`` and
    the current bar\'s as ``lower``, so the band is built from whichever of the
    two is smaller -- hence the swap when the series moved against us.
    """
    if lower is None:
        # First processed bar: no previous bar exists to have been inside every
        # level, so the band runs from the bottom of the price range upward.
        band = levels[: _cut(levels, upper)]
    else:
        # The band is the half-open price range ``[min, max)``. The bounds must
        # be ordered by *price* before they are cut, not afterwards by
        # position: `bisect` returns two positions whose order depends on the
        # bounds, and swapping positions when the prices were inverted keeps a
        # cut at a bound that is no longer in range. On the low side the
        # inverted case is the ordinary one -- price moving up puts the current
        # bar's low above the previous bar's -- and it silently dropped the
        # level between the two bounds, which is precisely the level the bar
        # swept.
        low, high = (lower, upper) if lower <= upper else (upper, lower)
        band = levels[_cut(levels, low) : _cut(levels, high)]
    # Re-sorted into creation order before returning. The band is found by
    # price, but the original detector emitted the levels of one bar in
    # creation order, and the event list's order is part of its output -- a
    # report that lists two sweeps of one bar the other way round is a
    # different report. Sorting the band (a handful of entries) rather than
    # iterating `active` (tens of thousands) is where the speedup survives.
    return [level for _, _, level in sorted(band, key=lambda entry: entry[1])]


def _cut(levels: list[tuple[Decimal, int, LiquidityLevel]], price: Decimal) -> int:
    """Index of the first level at or above ``price``.

    The middle element is the level's creation order, and it is what makes this
    a total order. Two levels can share a price exactly -- equal highs are
    clustered onto one price on purpose -- so a comparator that fell through to
    the level object would raise on exactly the case equal highs create. Two
    levels at the same price in creation order is a tie the caller's branch
    logic already handles identically either way, so the choice here only has
    to be *stable*, not meaningful.
    """
    return bisect_left(levels, (price, -1, None))  # type: ignore[list-item]



def _sweep_event(
    candles: Sequence[CandleData],
    index: int,
    level: LiquidityLevel,
    side: str,
    penetration: Decimal,
    close_back: bool,
    level_kind: str,
    swing_count: int = 1,
    offset: int = 0,
) -> ResearchEvent:
    """One sweep, with the event bar and the confirmation bar kept distinct.

    ``index`` and ``confirmation_index`` inside the event are *absolute*, so the
    windowed caller passes its own offset and every event lands on the same bar
    index it would have if the whole series had been passed at once. An index
    that resets at each segment would make a segmented event log and a
    continuous one describe different markets.
    """
    candle = candles[index]
    # The pierce happened on this bar. Whether it turned out to be a sweep
    # rather than a breakout is only settled by the close of this same bar, so
    # the confirmation is this bar's close and the confirmation index is the
    # next one: at the close of bar `index` a trader knows the sweep happened,
    # and can act at the open of bar `index + 1`.
    # The confirmation bar is the next one. When the window ends before it
    # arrives the confirmation falls back to the last bar present -- the sweep is
    # real, only its confirmation has not printed yet, and the caller resolves it
    # on the next window. An index past the end of the data would be a claim
    # about a bar nobody has seen.
    local_confirmation = min(index + 1, len(candles) - 1)
    absolute = offset + index
    confirmation_index = min(absolute + 1, offset + len(candles) - 1)
    swept_side = "high" if side == "above" else "low"
    return ResearchEvent(
        kind="liquidity_sweep",
        detector=f"sweep:{level_kind}",
        event_index=absolute,
        event_time=candle.open_time,
        confirmation_index=confirmation_index,
        confirmation_time=candles[local_confirmation].close_time,
        price=candles[local_confirmation].close,
        features={
            "level_price": level.price,
            "penetration": penetration,
            "swept_side": Decimal(0 if swept_side == "low" else 1),
            "level_age_bars": Decimal(absolute - level.creation_index),
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
