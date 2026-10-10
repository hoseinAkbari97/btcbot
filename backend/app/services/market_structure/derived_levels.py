"""Time-anchored liquidity levels: rolling range, sessions, and previous days.

Why this is a separate module
-----------------------------
A swing level is derived from *price structure*: a pivot prints, a later bar
confirms it, and swings that land on the same price cluster into a level. Every
level it produces therefore has a confirmation delay measured in bars, and its
availability timestamp is the bar that proved the pivot.

The four level types added here are derived from *wall-clock time* instead. A
previous day's high exists because a day ended, not because a pivot printed, and
it is knowable at the close of that day's last bar — not several bars later. So
they need their own state. :class:`~app.services.market_structure.segmented.StructureState`
is a sliding window over bars and knows nothing about where a day ended; bolting
day-boundary bookkeeping onto it would make one class responsible for two
unrelated kinds of knowledge.

Availability, stated once
-------------------------
Every level this module produces is dated to **the bar at which its defining
information became complete**, and never earlier. The two families differ on
what "complete" means, and the difference is not cosmetic:

===========================  ================================================
Level type                   Available from
===========================  ================================================
``range_high`` / ``range_low``   close of the last bar of the trailing window
``session_high`` / ``_low``      the bar that *opens* the next occurrence of
                            that same session slot
``previous_day_high`` / ``_low`` the bar that opens the next UTC day
===========================  ================================================

A rolling window's extreme is complete as soon as its last bar closes, so the
rolling range is dated to that close. A session's or day's extreme is **not**
complete then: at its own last bar it is only a high *so far*, and nothing
distinguishes it from one price goes on to exceed. It becomes a session high when
the session closes, which is when the next session opens. So those levels are
dated forward to the boundary, and a level's own period is never available to be
swept by the bars that formed it.

``equal_highs`` / ``equal_lows`` are the fourth family the specification names,
and they are not here because they are not time-anchored: an equal high is a
fact about *two swings on one price*, so it is produced by the swing bucket
machinery. See :func:`equal_level_for` in this module, which builds one
causally from a bucket's confirmations, and
:func:`app.services.market_structure.segmented.StructureState.equal_levels` /
:func:`app.services.market_structure.analysis.extract_equal_levels` for the two
entry points that call it.

The invariant every one of them shares
--------------------------------------
``creation_index < i`` for every bar ``i`` that could sweep the level. The sweep
detector's existing bound is ``level.creation_index < bar_index``, so this
guarantee is all that is needed to make "a level is never swept by information
that produced it" structural rather than a property someone has to remember.
:func:`assert_no_self_sweep` is the executable form of that claim, and the tests
run it over every level the state publishes.

Definitions, in full
--------------------
The specification (Section 14) lists these level types without defining them.
Where it is silent, this module fixes the definition rather than leaving a reader
to guess. Each choice is a *definition*, not a parameter: none was chosen by
looking at what BTC did, and none is fitted to a backtest.

**Sessions** are fixed six-hour UTC partitions of the day: ``00-06``, ``06-12``,
``12-18``, ``18-24``, named ``session_00`` / ``session_06`` / ``session_12`` /
``session_18``. The specification says "session high" without saying what a
session is, and the named venues that "session" usually refers to (Asia / London
/ New York) are not defined anywhere in this repository. Six equal UTC hours is
the choice that needs no external convention: it tiles the day with no gap and
no overlap, so every bar belongs to exactly one session and every day has exactly
four of them. A named-venue scheme would make a level type depend on a
trading-hours table this codebase does not carry, and would silently change
every level if that table were ever revised.

A session level is the extreme of the **previous occurrence of the same slot** —
not the session immediately before it. Comparing Wednesday's 12:00 session to
Wednesday's 12:00 session is the only comparison not confounded by the fact that
different slots trade differently; the session immediately preceding a given slot
is always a *different* slot, so its extreme is not a "same-session" extreme at
all. The lookup by name in :meth:`DerivedLevelState._publish_session` is what
makes that distinction, and dropping it would leave a level type that meant
"the high of six hours that happen to precede this one".

**Previous day** is the calendar day in UTC, matching the UTC convention used
throughout the research pipeline — a local-midnight boundary would move with
daylight saving and stop corresponding to a fixed bar index.

**Range** is a rolling window of ``range_window`` bars, and the level is the
extreme of the window *strictly before* the current bar. Including the current
bar would make the level the current bar's own extreme; a level whose window
ends on the bar that sweeps it is only ever sweepable by a later bar, which is
the same fact arrived at later and more expensively. Excluding it also makes the
level knowable at the current bar's *open* — strictly earlier than a
self-inclusive version would be.

Because a rolling maximum is not a fixed price, a range level is *superseded*
whenever the trailing extreme changes. The old level is not re-published or
moved: an already-emitted sweep of it stands, and the new level is a distinct
object at a distinct creation bar. This is the append-only discipline the swing
buckets already use — a level a participant has seen never changes price — and it
is why this module publishes on *change* rather than on every bar. A range that
holds its high for forty bars therefore produces one level, not forty.
"""

from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable, Sequence

from app.schemas.market_data import CandleData, Timeframe

from . import LevelType, LiquidityLevel

#: Length of one session partition, in hours. Six hours tiles a UTC day into four
#: equal parts with no gap and no overlap; see the module docstring for why named
#: venues were not used.
SESSION_HOURS = 6

#: The session slots as ``(name, start_hour)``, in day order.
SESSION_SLOTS: tuple[tuple[str, int], ...] = tuple(
    (f"session_{hour:02d}", hour) for hour in range(0, 24, SESSION_HOURS)
)

#: Default trailing window for ``range_high`` / ``range_low``, in bars. Matches
#: ``REGIME_WINDOW`` and the default ``vol_window`` used elsewhere in the research
#: package, so the three trailing statistics a reader might compare describe the
#: same span by default. It defines what the word "range" *means* here; it is not
#: a look-back that was searched for anything.
DEFAULT_RANGE_WINDOW = 20

#: Level price quantisation, matching the swing bucket key. A level's price is
#: compared against bar highs and lows for many bars afterwards, so it is frozen
#: on a fixed grid rather than left at whatever precision the source bar had.
PRICE_QUANT = Decimal("0.01")

#: Swings that must have confirmed on a price before it is an *equal* level
#: rather than a single swing. Two is the minimum that makes "equal" mean
#: anything at all; see :func:`equal_level_for` for why it is two and not three.
EQUAL_MIN_SWINGS = 2


def session_slot_for(moment: datetime) -> str:
    """The session slot a timestamp falls in.

    Total and deterministic: every UTC instant maps to exactly one of the four
    slots. The instant is converted to UTC first, so a bar carrying a UTC offset
    lands in the session its *instant* belongs to rather than the one its printed
    hour suggests.
    """
    utc = moment.astimezone(UTC)
    hour = utc.hour
    return f"session_{hour - hour % SESSION_HOURS:02d}"


def _floor_to_day(moment: datetime) -> datetime:
    utc = moment.astimezone(UTC)
    return utc.replace(hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Equal levels
# ---------------------------------------------------------------------------


def equal_level_for(
    price: Decimal,
    *,
    kind: str,
    swing_confirmations: Sequence[tuple[int, int, datetime | None]],
    tolerance: Decimal,
    origin: str = "swing",
) -> LiquidityLevel | None:
    """The equal-highs / equal-lows level for a price, or ``None``.

    The rule, stated exactly:

        * A price carries an equal level once ``EQUAL_MIN_SWINGS`` (two) swings
          have **confirmed** within ``tolerance`` of it.
        * The level's price is the **quantised price of the first swing that
          formed it** — the same anchor the swing bucket already uses — and it is
          never re-averaged as later swings arrive.
        * The level's ``creation_index`` and ``creation_time`` are those of the
          *second* qualifying swing, because that is the first bar at which the
          word "equal" was true.

    The last two lines are the causality, and they are the part a naive
    implementation gets wrong. A bucket's creation bar is when *one* swing
    confirmed there. Publishing an ``equal_highs`` level at that bar would be a
    claim about a second swing that had not yet printed, and the sweep detector —
    which excludes levels by ``creation_index < bar_index`` — would then be
    willing to sweep an "equal high" on a bar where only one high existed. The
    future leaks in through a *label* rather than through a price, which is
    harder to notice, because the price is right.

    Two rather than three, deliberately. "Equal highs" in the specification names
    a *relationship* between two extremes, so two is the number at which the word
    starts meaning something; a third swing would make the level a measure of how
    often a price was revisited, which is the touch count's job and is already
    measured. Using three would also make the level type unavailable for the large
    majority of levels that are visited exactly twice, which is the case the term
    is actually about.

    ``swing_confirmations`` is the level's own provenance — ``(swing_index,
    confirmation_index, confirmation_time)`` triples in confirmation order.
    Triples rather than the ``(index, index)`` pairs stored in a checkpoint,
    because the confirmation *timestamp* of the forming swing is needed and is not
    recoverable from a pair. Passing the whole list rather than a count is what
    lets the answer be read as of the bars in it: the second qualifying entry is
    the forming swing, and nothing beyond it is read.

    ``tolerance`` is the cluster tolerance the *bucket* was built with, carried
    through so this function's contract names the rule it is part of rather than
    leaving the caller to know that clustering happened elsewhere. It is not
    re-applied per swing, and deliberately so: membership was decided when the
    swings were assigned to the bucket, and re-deciding it here from a price
    that is by construction the bucket's own anchor would compare every swing to
    itself and always succeed. That comparison is what an earlier revision of
    this function performed, which made the tolerance a filter that could not
    reject anything -- the appearance of a check with none of the effect, which
    is worse than no check, because a reader concludes the bucket is being
    re-validated when it is not.

    So the rule is stated once, in the bucket builder
    (:meth:`MarketStructureAnalysis._bucket_price` and its callers in
    ``analysis.py``), and this function consumes the result.
    """
    if kind not in ("high", "low"):
        raise ValueError(f"kind must be 'high' or 'low', got {kind!r}")

    if not tolerance >= 0:
        raise ValueError(f"tolerance must be >= 0, got {tolerance}")

    quantised = price.quantize(PRICE_QUANT)
    qualifying = list(swing_confirmations)
    if len(qualifying) < EQUAL_MIN_SWINGS:
        return None

    _, formation_index, formation_time = qualifying[EQUAL_MIN_SWINGS - 1]
    if formation_time is None:
        # Not defended against. A swing without a confirmation time cannot supply
        # a level's availability timestamp, and the only honest responses are to
        # publish a level with an unknown timestamp or to publish none. Refusing
        # loudly is right here because a swing genuinely lacking that timestamp
        # would be a bug upstream, and a level with an unreconstructable
        # availability time is exactly the thing a checkpoint resume cannot
        # restore.
        raise ValueError(
            f"swing confirming equal level at {quantised} has no confirmation time; "
            f"the level's availability timestamp would not be reconstructable"
        )
    first_seen = qualifying[0][2] or formation_time
    return LiquidityLevel(
        price=quantised,
        level_type="equal_highs" if kind == "high" else "equal_lows",
        origin=origin,
        # Dated to the *first* swing, because that is when the price was first
        # marked as a level — while its own creation index is dated to the
        # second. The two deliberately disagree, and that disagreement is what
        # ``level_age_bars`` on a sweep reports: an equal high is a level that has
        # existed for a while and only recently acquired its second touch.
        first_seen=first_seen,
        last_seen=formation_time,
        creation_index=formation_index,
        creation_time=formation_time,
        # Same reasoning as :class:`DerivedLevel`. Unlike a swing level this one
        # has no pre-existence history to count, because the bucket's touch count
        # is measured to the *bucket's* creation bar, which for an equal level is
        # before the word "equal" was true.
        touch_count=0,
        strength=0.0,
    )


def assert_no_self_sweep(
    levels: Iterable[LiquidityLevel], bars: Sequence[CandleData]
) -> None:
    """Raise if any level claims to be knowable later than its own bar closed.

    The sweep detector excludes levels by ``creation_index < bar_index``, so a
    level's creation bar is never itself sweepable. That bound makes the *index*
    safe on its own. What the bound cannot check is that the level's stated
    availability *timestamp* agrees with its creation bar: a level carrying a
    ``creation_time`` later than its own bar's close describes something a
    participant could not have acted on even though the index filter lets it
    through, and the disagreement between the two is invisible in the event log.

    This is the executable form of the module's availability claim, and the tests
    run it over every level each entry point publishes — including the awkward
    cases where a level is created immediately before a segment boundary.
    """
    for level in levels:
        if level.creation_index < 0:
            raise AssertionError(
                f"level at {level.price} ({level.level_type}) has a negative "
                f"creation index {level.creation_index}"
            )
        if level.creation_index >= len(bars):
            raise AssertionError(
                f"level at {level.price} ({level.level_type}) is dated to bar "
                f"{level.creation_index}, beyond the {len(bars)} bars supplied"
            )
        if level.creation_time is None:
            raise AssertionError(
                f"level at {level.price} ({level.level_type}) has no creation_time; "
                f"its availability timestamp is not reconstructable from the "
                f"checkpoint and must not be guessed"
            )
        level_bar_close = bars[level.creation_index].close_time
        if level.creation_time > level_bar_close:
            raise AssertionError(
                f"level at {level.price} ({level.level_type}) claims to become "
                f"knowable at {level.creation_time.isoformat()}, after its own bar "
                f"{level.creation_index} closed at {level_bar_close.isoformat()}"
            )
        # The self-sweep case the timestamp check above cannot see. A boundary
        # level's own creation time *is* at or before its creation bar's close, so
        # it passes -- while the level it summarises was formed by bars that
        # precede that boundary. The test is therefore structural rather than
        # temporal: the boundary bar's open must not be earlier than the
        # boundary bar itself, which holds for every legitimately dated level and
        # fails the moment a period's last bar is used as the creation index.
        if level.creation_time < bars[level.creation_index].open_time:
            raise AssertionError(
                f"level at {level.price} ({level.level_type}) claims to become "
                f"knowable at {level.creation_time.isoformat()}, before the open of "
                f"bar {level.creation_index} it is dated to"
            )


# ---------------------------------------------------------------------------
# Period accumulators
# ---------------------------------------------------------------------------


@dataclass
class _PeriodExtremes:
    """High and low accumulated over a **completed** period.

    Kept as raw Decimals rather than a built level, because the level these
    produce is not knowable until the period ends: until then the extreme is
    still moving, and a level published from a half-finished period would be
    revised on the next bar. Storing the pair and building the level at the
    boundary is what keeps the creation bar on the correct side of the
    information.

    ``period_start`` and ``period_end_index`` identify *which* period these
    extremes belong to, so a resumed state can tell "this slot has no previous
    occurrence yet" from "it has one", and so a level published at a boundary
    names the period it summarised rather than the period that happened to be in
    progress when it was published.
    """

    high: Decimal | None = None
    low: Decimal | None = None
    period_start: datetime | None = None
    period_end_index: int | None = None
    period_bars: int = 0
    #: Close time of the period's last bar. Carried rather than recomputed from
    #: ``period_end_index + 1``, because the state's window only holds the rolling
    #: range bars and a resumed run cannot reach back to an arbitrary earlier
    #: bar's close time. Deriving it arithmetically from the wall clock would be
    #: a second, subtly different definition of when a period ends.
    period_end_time: datetime | None = None

    def to_payload(self) -> dict:
        return {
            "high": str(self.high) if self.high is not None else None,
            "low": str(self.low) if self.low is not None else None,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end_index": self.period_end_index,
            "period_bars": self.period_bars,
            "period_end_time": (
                self.period_end_time.isoformat() if self.period_end_time else None
            ),
        }

    @classmethod
    def from_payload(cls, payload: dict | None) -> _PeriodExtremes:
        if not payload:
            return cls()
        return cls(
            high=Decimal(payload["high"]) if payload["high"] is not None else None,
            low=Decimal(payload["low"]) if payload["low"] is not None else None,
            period_start=(
                datetime.fromisoformat(payload["period_start"])
                if payload["period_start"]
                else None
            ),
            period_end_index=(
                int(payload["period_end_index"])
                if payload["period_end_index"] is not None
                else None
            ),
            period_bars=int(payload.get("period_bars", 0)),
            period_end_time=(
                datetime.fromisoformat(payload["period_end_time"])
                if payload["period_end_time"]
                else None
            ),
        )


# ---------------------------------------------------------------------------
# Derived levels
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DerivedLevel:
    """A liquidity level defined by wall-clock time rather than by a pivot.

    Kept distinct from :class:`~app.services.market_structure.LiquidityLevel`
    because one quantity differs in kind. A swing level's ``touch_count`` counts
    bars that reached the level *before it existed*, and is meaningful because a
    swing is confirmed with a bar delay. A time-anchored level has no such delay
    — the previous day's high is knowable at the previous day's close, so every
    bar that could count as a touch had already printed. Its ``touch_count`` is
    therefore zero by construction, and reporting a real count would imply a
    history the level does not have.

    The sweep detector consumes :meth:`to_liquidity_level`, so nothing downstream
    has to know these two types apart.
    """

    price: Decimal
    level_type: LevelType
    origin: str
    creation_index: int
    creation_time: datetime
    #: Bars in the summarised period — 288 for a day of 5m bars, 72 for a session,
    #: ``range_window`` for a rolling range. It is what makes a 24-hour day level
    #: distinguishable from a six-hour session level carrying the same type
    #: string, and it is a property of the definition rather than of the sample.
    period_bars: int
    #: The boundary this level summarises: ``"day"``, ``"range"``, or a session
    #: slot name such as ``"session_12"``. Retained separately from
    #: ``level_type`` because the type name does not say which session it came
    #: from.
    boundary: str
    #: Start of the summarised period. Lets a reader join a level back to the
    #: period it came from without re-deriving the boundary.
    period_start: datetime

    def is_known_at(self, index: int) -> bool:
        return self.creation_index <= index

    def to_liquidity_level(self) -> LiquidityLevel:
        """The sweep detector's view of this level."""
        return LiquidityLevel(
            price=self.price,
            level_type=self.level_type,
            origin=self.origin,
            first_seen=self.creation_time,
            last_seen=self.creation_time,
            creation_index=self.creation_index,
            creation_time=self.creation_time,
            # See the class docstring: every candidate touch bar printed before
            # the level was knowable, so the honest count is zero rather than a
            # plausible-looking number.
            touch_count=0,
            strength=0.0,
        )

    def to_payload(self) -> dict:
        return {
            "price": str(self.price),
            "level_type": self.level_type,
            "origin": self.origin,
            "creation_index": self.creation_index,
            "creation_time": self.creation_time.isoformat(),
            "period_bars": self.period_bars,
            "boundary": self.boundary,
            "period_start": self.period_start.isoformat(),
        }

    @classmethod
    def from_payload(cls, payload: dict) -> DerivedLevel:
        return cls(
            price=Decimal(payload["price"]),
            level_type=payload["level_type"],
            origin=payload["origin"],
            creation_index=int(payload["creation_index"]),
            creation_time=datetime.fromisoformat(payload["creation_time"]),
            period_bars=int(payload["period_bars"]),
            boundary=payload["boundary"],
            period_start=datetime.fromisoformat(payload["period_start"]),
        )


@dataclass
class _RollingRange:
    """The trailing ``range_window`` bars, and the extremes last published.

    The window is the state; the two published values exist so a range that
    holds its extreme does not republish it every bar. Holding state across a
    segment boundary is the whole requirement here, and ``range_window`` bars
    is a fixed count rather than a slice of history.
    """

    window: list[CandleData] = field(default_factory=list)
    published_high: Decimal | None = None
    published_low: Decimal | None = None


class DerivedLevelState:
    """Incremental, causal state for the three time-anchored level families.

    Consumes candles in ascending, contiguous bar order and returns the levels
    that became knowable on each bar. Like
    :class:`~app.services.market_structure.segmented.StructureState` it
    deliberately has no ``reset``: a segment boundary is a memory boundary, and a
    reset reachable from a caller is a reset that eventually gets called at the
    start of every segment, at which point the segmented run quietly stops
    matching the continuous one while both still look plausible.

    What crosses a boundary: the trailing ``range_window`` bars, the running
    extremes of the day and session in progress, the completed extremes of the
    last day and of each of the four session slots, and the published levels
    themselves. The candles do not cross — 595k of them is hundreds of megabytes
    and this state needs at most one rolling window plus two extremes.

    The published levels are carried rather than re-derived on resume. Unlike the
    swing buckets, they are cheap to keep and *must* be: a sweep detected in
    segment 11 can be of a level published in segment 1, and a resumed run that
    forgot it would silently stop reporting sweeps of it. They are bounded by the
    number of bars at which an extreme moved, not by the number of bars.
    """

    def __init__(self, *, range_window: int = DEFAULT_RANGE_WINDOW) -> None:
        if range_window < 1:
            raise ValueError(f"range_window must be >= 1, got {range_window}")
        self.range_window = range_window
        self._range = _RollingRange()
        self._next_index = 0

        #: Periods in progress.
        self._day_key: datetime | None = None
        self._day_high: Decimal | None = None
        self._day_low: Decimal | None = None
        self._day_bars = 0
        self._slot: str | None = None
        self._session_high: Decimal | None = None
        self._session_low: Decimal | None = None
        self._session_bars = 0

        #: The most recent *completed* occurrence of each period family.
        self._previous_day = _PeriodExtremes()
        self._previous_sessions: dict[str, _PeriodExtremes] = {
            name: _PeriodExtremes() for name, _ in SESSION_SLOTS
        }

        self._last_open_time: datetime | None = None
        self._last_close_time: datetime | None = None
        #: Close time of the bar *before* the one currently being consumed. This
        #: is the timestamp a day or session level is dated to, and it is carried
        #: explicitly rather than derived from ``_last_close_time`` because inside
        #: a segment the latest close belongs to a bar already consumed, not to
        #: the predecessor of the bar in hand.
        self._previous_close_time: datetime | None = None
        #: Open time of the session in progress, for the level's ``period_start``.
        self._session_start: datetime | None = None
        self._levels: list[DerivedLevel] = []

    @property
    def _bar_close_time(self) -> datetime | None:
        """Alias making the :meth:`_close_period` call site read as intent."""
        return self._previous_close_time

    # -- ingestion ----------------------------------------------------------

    def observe(self, candles: Sequence[CandleData]) -> list[DerivedLevel]:
        """Consume candles and return the levels that became knowable on them.

        The returned levels are also retained and reachable through
        :meth:`levels`, because the sweep detector is given the whole cumulative
        set rather than only the increment: a level derived in segment 3 is still
        sweepable in segment 11.
        """
        if not candles:
            return []
        if (
            self._last_open_time is not None
            and candles[0].open_time <= self._last_open_time
        ):
            raise ValueError(
                f"segment starts at {candles[0].open_time}, at or before the previous "
                f"segment's last bar ({self._last_open_time}); segments must be "
                f"contiguous and strictly ascending"
            )
        fresh: list[DerivedLevel] = []
        for candle in candles:
            # The previous bar's close is what a boundary-published level is dated
            # to, and it must be captured *before* ``_last_close_time`` advances
            # past the bar being consumed.
            self._previous_close_time = self._last_close_time
            fresh.extend(self._observe_one(candle))
            self._last_open_time = candle.open_time
            self._last_close_time = candle.close_time
        self._levels.extend(fresh)
        return fresh

    def _observe_one(self, candle: CandleData) -> list[DerivedLevel]:
        index = self._next_index
        produced: list[DerivedLevel] = []

        # The rolling range is published *before* the bar enters the window: the
        # level describes the previous ``range_window`` bars and is knowable at
        # this bar's open. Appending first would put the bar in its own reference
        # population, which is the self-inclusion the displacement detector's
        # trailing windows go out of their way to avoid.
        produced.extend(self._publish_range())
        window = self._range.window
        window.append(candle)
        if len(window) > self.range_window:
            del window[0 : len(window) - self.range_window]

        # Boundaries are rolled before the bar is folded into the period it opens,
        # so a level published at a boundary summarises the period that *ended*,
        # not the one that began. Folding first would put the first bar of the new
        # day into the previous day's high — a level containing a bar from a
        # period it does not name, and one that would then be re-published
        # differently on the next bar.
        produced.extend(self._roll_boundaries(candle, index))

        self._next_index = index + 1
        return produced

    # -- rolling range ------------------------------------------------------

    def _publish_range(self) -> list[DerivedLevel]:
        """Emit a ``range_high`` / ``range_low`` when the trailing extreme moves."""
        window = self._range.window
        if len(window) < self.range_window:
            return []
        high = max(bar.high for bar in window)
        low = min(bar.low for bar in window)
        published = self._range
        produced: list[DerivedLevel] = []
        # The window's last bar is the one before the bar being consumed, which is
        # exactly the bar at which this level's information completed.
        creation_index = self._next_index - 1
        creation_time = window[-1].close_time
        period_start = window[0].open_time

        if high != published.published_high:
            published.published_high = high
            produced.append(
                DerivedLevel(
                    price=high.quantize(PRICE_QUANT),
                    level_type="range_high",
                    origin="range",
                    creation_index=creation_index,
                    creation_time=creation_time,
                    period_bars=self.range_window,
                    boundary="range",
                    period_start=period_start,
                )
            )
        if low != published.published_low:
            published.published_low = low
            produced.append(
                DerivedLevel(
                    price=low.quantize(PRICE_QUANT),
                    level_type="range_low",
                    origin="range",
                    creation_index=creation_index,
                    creation_time=creation_time,
                    period_bars=self.range_window,
                    boundary="range",
                    period_start=period_start,
                )
            )
        return produced

    # -- calendar boundaries ------------------------------------------------

    def _roll_boundaries(
        self, candle: CandleData, index: int
    ) -> list[DerivedLevel]:
        """Roll the day and session accumulators, publishing at each boundary.

        A bar that opens a new session necessarily opens a new day too, so the
        session boundary is tested first and the day boundary second. Either
        order gives the same levels — the day level's extremes were already
        frozen before the bar was folded into either accumulator — but testing
        the finer boundary first keeps the code's reading order the same as the
        nesting of the periods themselves.
        """
        produced: list[DerivedLevel] = []
        day = _floor_to_day(candle.open_time)
        slot = session_slot_for(candle.open_time)

        if self._slot is None:
            self._slot = slot
            self._session_start = candle.open_time
        elif slot != self._slot:
            produced.extend(self._publish_session(index, candle.open_time))
            self._slot = slot
            self._session_start = candle.open_time
            self._session_high = None
            self._session_low = None
            self._session_bars = 0

        if self._day_key is None:
            self._day_key = day
        elif day != self._day_key:
            produced.extend(self._publish_day(index, candle.open_time))
            self._day_key = day
            self._day_high = None
            self._day_low = None
            self._day_bars = 0

        if self._day_high is None or candle.high > self._day_high:
            self._day_high = candle.high
        if self._day_low is None or candle.low < self._day_low:
            self._day_low = candle.low
        self._day_bars += 1

        if self._session_high is None or candle.high > self._session_high:
            self._session_high = candle.high
        if self._session_low is None or candle.low < self._session_low:
            self._session_low = candle.low
        self._session_bars += 1

        return produced

    def _publish_day(self, index: int, boundary_time: datetime) -> list[DerivedLevel]:
        """Close out the day in progress, dated to its final bar.

        Publishes the *previous* day's extremes, then banks the day that just
        ended for the boundary after next. Publishing nothing on the dataset's
        first day is correct rather than a gap: a "previous day high" built from
        a day that has not ended is exactly the leak the specification names this
        level type to avoid.
        """
        return self._close_period(
            index=index,
            boundary_time=boundary_time,
            high=self._day_high,
            low=self._day_low,
            bars=self._day_bars,
            start=self._day_key,
            level_high="previous_day_high",
            level_low="previous_day_low",
            origin="previous_day",
            boundary="day",
        )

    def _publish_session(self, index: int, boundary_time: datetime) -> list[DerivedLevel]:
        """Close out the session in progress, dated to its final bar.

        Publishes the previous occurrence of *this slot*, not the previous
        session. The lookup by name is the entire distinction: the session
        immediately before this one is a different slot, trades differently, and
        comparing against it would report a "session high" that is mostly a
        statement about which six hours of the day preceded this one.
        """
        assert self._slot is not None
        return self._close_period(
            index=index,
            boundary_time=boundary_time,
            high=self._session_high,
            low=self._session_low,
            bars=self._session_bars,
            start=self._session_start,
            level_high="session_high",
            level_low="session_low",
            origin="session",
            boundary=self._slot,
            slot=self._slot,
        )

    def _close_period(
        self,
        *,
        index: int,
        boundary_time: datetime,
        high: Decimal | None,
        low: Decimal | None,
        bars: int,
        start: datetime | None,
        level_high: LevelType,
        level_low: LevelType,
        origin: str,
        boundary: str,
        slot: str | None = None,
    ) -> list[DerivedLevel]:
        """Publish the previous occurrence's levels, then bank the one that ended.

        The bank is written on *every* call, including the first, because that is
        what makes the second occurrence find a previous one to publish. This is
        the single place both families share, which is the point: they reach it at
        very different cadences — a day closes once in 288 five-minute bars, a
        session once in 72 — and a rule that only banked for the slower family
        would leave sessions permanently unpublished, silently, because sessions
        recur four times a day and would always find an empty slot.

        A published level is dated to the **boundary bar** -- ``index``, the bar
        that opened the new period -- and not to the summarised period's last
        bar. That is the whole difference between "this day's extreme finished
        forming" and "this day's extreme is knowable", and only the second one
        licenses a decision. The extreme finished forming at the period's last
        bar, but nothing at that bar distinguishes it from a high that price
        goes on to exceed: the period has to *close* before its high is a
        session high rather than a high so far, and the period closes when the
        next one opens.

        Dating it to the period's last bar is not a harmless rounding choice. It
        lets a sweep detected inside the level's own period report that period's
        high as the level that was swept -- the level being swept by the very
        period that defines it. The segmented path exposes this immediately as a
        batch/segmented divergence, because there the level genuinely does not
        exist until the boundary; the batch path hides it by carrying the whole
        month and presenting a not-yet-knowable level as available from the bar
        whose extreme it contains.
        """
        # Bank the period that just ended *first*, then publish it. The order is
        # the whole correctness of this function, and the earlier order -- read
        # the bank, publish it, then bank -- was off by one whole period.
        #
        # It read as though it were the safe one: publishing the previous bank
        # means publishing a period that closed at least one period ago, which
        # cannot be lookahead. But "previous day high" is a name, and at the
        # boundary where day D ends the previous day is day D, not day D-1.
        # Reading first published the day before last: on five days of bars the
        # ``previous_day_high`` known at 2024-01-03T00:00 was the high of
        # 2024-01-01, a value the market had already superseded a day earlier.
        # Nothing in the sweep detector could have caught it -- the level's
        # price is real, its timestamp is honest about when it was published,
        # and the leakage is a full 24 hours of the wrong reference day, which
        # is a statement about a different day rather than about a future bar.
        #
        # Banking first is still causal, and the comment on
        # ``creation_index`` below is the reason: the extreme that forms the
        # level is the one belonging to the period that ends *at this
        # boundary*, and this boundary is the first bar at which that period is
        # known to have closed. Publishing it here claims nothing that a later
        # bar would have supplied; publishing the earlier bank claims a level
        # that is simply the wrong day.
        self._bank(slot, high, low, bars, start, index - 1, self._bar_close_time)
        bank = self._previous_day if slot is None else self._previous_sessions[slot]

        produced: list[DerivedLevel] = []
        if (
            bank.high is not None
            and bank.low is not None
            and bank.period_end_index is not None
            and bank.period_end_time is not None
            and bank.period_start is not None
        ):
            shared = {
                "origin": origin,
                # The level is dated to the bar that *opened the next period* --
                # ``index`` -- not to the last bar of the period it summarises.
                # The period's last bar is when its extreme finished forming, but
                # the level is not knowable there: only when the *following*
                # period opens do we know that the period has closed and which
                # slot/day it was. Dating it to ``bank.period_end_index`` would
                # let a sweep at a bar inside the level's own period act on it,
                # which is precisely the lookahead this module exists to
                # prevent, and which the segmented path (where the publication
                # genuinely happens later) would expose as a batch-vs-segmented
                # divergence. ``period_start`` and ``period_bars`` still describe
                # the summarised period; only availability moves.
                "creation_index": index,
                # The boundary bar's *open*, which is the instant the period
                # closed and the level became true. Not the summarised period's
                # last close -- that is one bar of lookahead -- and not the
                # boundary bar's own close, which has not happened yet at the
                # moment the level comes into existence.
                "creation_time": boundary_time,
                "period_bars": bank.period_bars,
                "boundary": boundary,
                "period_start": bank.period_start,
            }
            produced.append(
                DerivedLevel(
                    price=bank.high.quantize(PRICE_QUANT),
                    level_type=level_high,
                    **shared,  # type: ignore[arg-type]
                )
            )
            produced.append(
                DerivedLevel(
                    price=bank.low.quantize(PRICE_QUANT),
                    level_type=level_low,
                    **shared,  # type: ignore[arg-type]
                )
            )
        return produced


    def _bank(
        self,
        slot: str | None,
        high: Decimal | None,
        low: Decimal | None,
        bars: int,
        start: datetime | None,
        end_index: int,
        end_time: datetime | None,
    ) -> None:
        record = _PeriodExtremes(
            high=high,
            low=low,
            period_start=start,
            period_end_index=end_index,
            period_bars=bars,
            period_end_time=end_time,
        )
        if slot is None:
            self._previous_day = record
        else:
            self._previous_sessions[slot] = record

    # -- output -------------------------------------------------------------

    def levels(self) -> list[DerivedLevel]:
        """Every level published so far, in publication order."""
        return list(self._levels)

    def as_of(self, index: int) -> list[DerivedLevel]:
        """The levels knowable at bar ``index`` — the causal read."""
        return [level for level in self._levels if level.is_known_at(index)]

    def as_liquidity_levels(self) -> list[LiquidityLevel]:
        """The cumulative set, in the shape the sweep detector consumes."""
        return [level.to_liquidity_level() for level in self._levels]

    # -- persistence --------------------------------------------------------

    def to_payload(self) -> dict:
        """Serialise the carried state."""
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "range_window": self.range_window,
            "next_index": self._next_index,
            "range": {
                "published_high": (
                    str(self._range.published_high)
                    if self._range.published_high is not None
                    else None
                ),
                "published_low": (
                    str(self._range.published_low)
                    if self._range.published_low is not None
                    else None
                ),
                "window": [_window_bar_payload(candle) for candle in self._range.window],
            },
            "day": {
                "key": self._day_key.isoformat() if self._day_key else None,
                "high": str(self._day_high) if self._day_high is not None else None,
                "low": str(self._day_low) if self._day_low is not None else None,
                "bars": self._day_bars,
            },
            "session": {
                "slot": self._slot,
                "start": (
                    self._session_start.isoformat() if self._session_start else None
                ),
                "high": (
                    str(self._session_high) if self._session_high is not None else None
                ),
                "low": (
                    str(self._session_low) if self._session_low is not None else None
                ),
                "bars": self._session_bars,
            },
            "previous_day": self._previous_day.to_payload(),
            "previous_sessions": {
                name: value.to_payload()
                for name, value in sorted(self._previous_sessions.items())
            },
            "last_open_time": (
                self._last_open_time.isoformat() if self._last_open_time else None
            ),
            "last_close_time": (
                self._last_close_time.isoformat() if self._last_close_time else None
            ),
            "previous_close_time": (
                self._previous_close_time.isoformat()
                if self._previous_close_time
                else None
            ),
            "levels": [level.to_payload() for level in self._levels],
        }

    @classmethod
    def from_payload(cls, payload: dict) -> DerivedLevelState:
        version = payload.get("schema_version")
        if version != STATE_SCHEMA_VERSION:
            raise ValueError(
                f"derived-level checkpoint schema version {version!r} cannot be read "
                f"by this build (expects {STATE_SCHEMA_VERSION})"
            )
        state = cls(range_window=int(payload["range_window"]))
        state._next_index = int(payload["next_index"])
        rolling = payload["range"]
        state._range = _RollingRange(
            window=[_window_bar_from_payload(item) for item in rolling["window"]],
            published_high=(
                Decimal(rolling["published_high"])
                if rolling["published_high"] is not None
                else None
            ),
            published_low=(
                Decimal(rolling["published_low"])
                if rolling["published_low"] is not None
                else None
            ),
        )
        day = payload["day"]
        state._day_key = datetime.fromisoformat(day["key"]) if day["key"] else None
        state._day_high = Decimal(day["high"]) if day["high"] is not None else None
        state._day_low = Decimal(day["low"]) if day["low"] is not None else None
        state._day_bars = int(day["bars"])
        session = payload["session"]
        state._slot = session["slot"]
        state._session_start = (
            datetime.fromisoformat(session["start"]) if session["start"] else None
        )
        state._session_high = (
            Decimal(session["high"]) if session["high"] is not None else None
        )
        state._session_low = (
            Decimal(session["low"]) if session["low"] is not None else None
        )
        state._session_bars = int(session["bars"])
        state._previous_day = _PeriodExtremes.from_payload(payload["previous_day"])
        state._previous_sessions = {
            name: _PeriodExtremes.from_payload(value)
            for name, value in payload["previous_sessions"].items()
        }
        # Any slot the payload predates is initialised rather than assumed absent,
        # so a resumed state and a fresh one have the same table shape.
        for name, _ in SESSION_SLOTS:
            state._previous_sessions.setdefault(name, _PeriodExtremes())
        state._last_open_time = (
            datetime.fromisoformat(payload["last_open_time"])
            if payload["last_open_time"]
            else None
        )
        state._last_close_time = (
            datetime.fromisoformat(payload["last_close_time"])
            if payload["last_close_time"]
            else None
        )
        state._previous_close_time = (
            datetime.fromisoformat(payload["previous_close_time"])
            if payload.get("previous_close_time")
            else None
        )
        state._levels = [DerivedLevel.from_payload(item) for item in payload["levels"]]
        return state


#: Bumped when the *shape* of this state's payload changes such that an older one
#: cannot be read. Kept separate from the swing state's version because the two
#: states are versioned independently and neither can fix the other's payload.
STATE_SCHEMA_VERSION = 1


def _window_bar_payload(candle: CandleData) -> dict:
    """A trailing bar, stored with the fields the range level actually reads.

    Only ``high``, ``low`` and the two timestamps are kept: the rolling range is
    a max/min over those, and carrying ``open``/``close``/``volume`` would grow
    every checkpoint by a third for quantities no reader of this state can use.
    """
    return {
        "open_time": candle.open_time.isoformat(),
        "close_time": candle.close_time.isoformat(),
        "high": str(candle.high),
        "low": str(candle.low),
    }


def _window_bar_from_payload(payload: dict) -> CandleData:
    """Rebuild a window bar.

    Constructed against the smallest schema that satisfies the range
    computation, which is why the returned bar's ``open``/``close`` are both its
    ``high``. The bar is never handed to anything that reads an open or a close —
    :meth:`DerivedLevelState._publish_range` and nothing else touches this
    window — and faking them with real-looking values would be worse than the
    honest zero-range placeholder, because a future reader could not tell.
    """
    high = Decimal(payload["high"])
    return CandleData(
        symbol="",
        timeframe=Timeframe.M5,
        open_time=datetime.fromisoformat(payload["open_time"]),
        close_time=datetime.fromisoformat(payload["close_time"]),
        open=high,
        high=high,
        low=Decimal(payload["low"]),
        close=high,
        volume=Decimal(0),
    )