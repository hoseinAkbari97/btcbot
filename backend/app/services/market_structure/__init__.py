"""Market structure primitives.

Causality contract
------------------
Every object here separates two times:

``timestamp``            when the phenomenon *happened* (the bar of the swing
                         itself, the bar that broke the level, the bar that swept).
``confirmation_index`` / ``confirmation_time``
                         the first bar at which a participant could *know* it
                         happened.

For a swing found with ``lookback = k`` the two differ by ``k`` bars: the pivot at
bar *i* is only known once bar ``i + k`` has closed. Nothing may consume a swing
before its confirmation index. ``is_known_at(index)`` is the single accessor that
enforces this, and every consumer in this package goes through it.

Two related rules follow from the same idea:

* Derived quantities (a level's touch count, a swing's strength) are only defined
  ``as of`` some bar. ``analyze_market_structure(..., as_of_index=n)`` truncates its
  inputs to ``candles[: n + 1]``, so a caller asking "what did I know at bar *n*"
  gets an answer that cannot contain bar *n+1*'s data.
* Labels are descriptive, never directional. A BOS records *that* a level broke and
  in which direction; it does not claim to be a buy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from app.schemas.market_data import CandleData, Timeframe

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

SwingKind = Literal["high", "low"]

EventType = Literal["HH", "HL", "LH", "LL", "BOS", "structure_shift"]

LevelType = Literal[
    "swing_high",
    "swing_low",
    "equal_highs",
    "equal_lows",
    "range_high",
    "range_low",
    "session_high",
    "session_low",
    "previous_day_high",
    "previous_day_low",
]

#: The ten liquidity levels the specification (Section 14) names. Kept as one
#: tuple so a report, a test and the sweep detector all enumerate the same set and
#: a level type cannot be added to one place and forgotten in another -- which is
#: exactly how "equal highs" sat declared in the enum and derived by nothing.
LIQUIDITY_LEVEL_TYPES: tuple[LevelType, ...] = (
    "swing_high",
    "swing_low",
    "equal_highs",
    "equal_lows",
    "range_high",
    "range_low",
    "session_high",
    "session_low",
    "previous_day_high",
    "previous_day_low",
)

RegimeLabel = Literal["TREND_UP", "TREND_DOWN", "RANGE", "UNKNOWN"]


def confirmation_time_for(
    candles: list[CandleData], confirmation_index: int
) -> datetime | None:
    """Close time of the bar at which knowledge became available.

    Knowledge arrives when the confirming bar *closes*, so a swing confirmed at
    index ``c`` is usable from ``candles[c].close_time`` onwards — not from its
    open. Returning ``None`` for an out-of-range index keeps a truncated series
    from claiming knowledge it cannot justify.
    """
    if 0 <= confirmation_index < len(candles):
        return candles[confirmation_index].close_time
    return None


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SwingPoint:
    """A local extremum, with the moment it became knowable.

    ``index``/``timestamp`` locate the pivot bar. ``confirmation_index``/
    ``confirmation_time`` locate the bar that proved it. For a lookback-``k``
    detector, ``confirmation_index == index + k``.
    """

    index: int
    timestamp: datetime
    price: Decimal
    kind: SwingKind
    confirmation_index: int = 0
    confirmation_time: datetime | None = None

    def is_known_at(self, index: int) -> bool:
        """Whether this swing may be used by a decision made at bar ``index``."""
        return self.confirmation_index <= index

    @property
    def confirmation_delay_bars(self) -> int:
        return self.confirmation_index - self.index


@dataclass(frozen=True)
class StructureEvent:
    """A market-structure observation. Descriptive, not a trade instruction.

    ``source_swing_idx`` and ``broken_level`` record what the event refers to so
    that a researcher can join back to the swing that caused it.
    """

    timestamp: datetime
    price: Decimal
    event_type: EventType
    confirmation_index: int = 0
    confirmation_time: datetime | None = None
    index: int = 0
    # BOS: the price of the level that was broken, and the swing that made it.
    broken_level: Decimal | None = None
    penetration: Decimal | None = None
    source_swing_idx: int | None = None
    # Structure shift: the swing state before and after.
    previous_state: str | None = None
    new_state: str | None = None
    # Set once a direction is defined, always one of the two trade sides or "".
    # BOS is directional; HH/HL/LL/LH are labels on swings, not signals.
    direction: Literal["long", "short", "neutral"] = "neutral"

    def is_known_at(self, index: int) -> bool:
        return self.confirmation_index <= index


@dataclass(frozen=True)
class LiquidityLevel:
    """A price level derived from swings, with age and touch count as of a bar.

    ``touch_count`` and ``strength`` are computed over candles up to the level's
    ``creation_index`` only. They are therefore a function of history, not of the
    full series — the non-causality this replaces was the level's strongest
    looking-ahead feature.
    """

    price: Decimal
    level_type: LevelType
    first_seen: datetime
    last_seen: datetime
    creation_index: int = 0
    creation_time: datetime | None = None
    touch_count: int = 0
    strength: float = 0.0
    origin: str = "swing"
    # Indices of the swings that produced the level, so it can be traced.
    source_swing_indices: tuple[int, ...] = ()
    #: ``(swing_index, confirmation_index)`` for every swing that has confirmed
    #: on this price, in time order. Kept as a list of *times* rather than a
    #: count precisely so that a consumer can ask how mature the level was at a
    #: given bar — a level formed from one swing and one formed from four are
    #: different phenomena, and a single frozen count could only ever answer
    #: that question for the last bar of the sample.
    swing_confirmations: tuple[tuple[int, int], ...] = ()

    def is_known_at(self, index: int) -> bool:
        return self.creation_index <= index

    def swing_count_at(self, index: int) -> int:
        """How many swings had confirmed on this level by bar ``index``.

        ``swing_count_at(t)`` is monotonic in ``t`` and independent of any bar
        after ``t``, so it is safe to read at the time of a decision. The total
        number of swings ever to confirm on the level is *not* safe to read,
        because it is a fact about the end of the sample.
        """
        return sum(1 for _, confirmed in self.swing_confirmations if confirmed <= index)


@dataclass
class MarketStructureResult:
    """Aggregated output of a single structure analysis pass.

    ``as_of_index`` records the last bar this result is allowed to depend on, so a
    consumer can verify it was built causally.
    """

    symbol: str
    timeframe: Timeframe
    swings: list[SwingPoint] = field(default_factory=list)
    events: list[StructureEvent] = field(default_factory=list)
    liquidity_levels: list[LiquidityLevel] = field(default_factory=list)
    recent_range: tuple[Decimal, Decimal] | None = None
    current_regime: RegimeLabel = "UNKNOWN"
    as_of_index: int | None = None

    def swings_known_at(self, index: int) -> list[SwingPoint]:
        return [s for s in self.swings if s.is_known_at(index)]

    def events_known_at(self, index: int) -> list[StructureEvent]:
        return [e for e in self.events if e.is_known_at(index)]

    def levels_known_at(self, index: int) -> list[LiquidityLevel]:
        return [level for level in self.liquidity_levels if level.is_known_at(index)]
