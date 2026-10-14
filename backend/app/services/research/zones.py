"""Phase 9: supply/demand zones and objective retests.

What this is and is not
-----------------------
Section 16 of the research plan asks for measurable zone definitions rather than
subjective rectangles, and asks that the system "be able to test whether these
zones have predictive value". It does *not* assert that they do. So nothing in
this module takes a side, places an entry, or assumes a zone holds. A zone here
is a rectangular band of price, stamped with the measurements that were knowable
when it was published, and a retest is a bar that came back into that band. That
is the whole claim. Whether returning to a band is worth anything is a Phase 11
question, and this module is built so that answering it does not require
rewriting anything here.

The causal problem, stated precisely
------------------------------------
A zone is drawn from three pieces of history: a base (consolidation), a
displacement (departure), and structural significance (a swing or break in the
direction of the move). Each of those is final only *after* the fact:

* the base is the bars immediately **before** the displacement bar -- including
  the displacement bar itself would place the zone partly inside the move, which
  is how a rectangle ends up drawn over the departure it is supposed to explain;
* the displacement is final at its close, so it is knowable one bar later, which
  is exactly what ``detect_displacement`` already records as its
  ``confirmation_index``. This module uses *that* index and never derives its own;
* structural significance needs a swing, and a swing needs ``lookback`` bars
  *after* the pivot to prove it -- the same property
  :class:`~app.services.market_structure.SwingPoint` exposes as ``confirmation_index``.

So a zone's ``confirmation_index`` is the latest of those three, and the zone is
not published before it. The zone's boundaries are fixed at creation and never
revised: a zone that widened to accommodate later bars would be a measurement of
the future, and one that narrowed would retroactively change the price of every
retest already recorded against it.

Three timestamps, deliberately not two
--------------------------------------
``ResearchEvent`` carries ``event_index`` and ``confirmation_index``. A zone needs
a third, and it is the one that is easy to get wrong:

``start_index``   the first bar of the base.
``creation_index`` the displacement bar -- the bar price left the base. This is
                  the bar a chart would draw the rectangle ending at.
``confirmation_index`` the first bar at which the zone exists as a known object.

The retest rule depends on that third index rather than the second. Price is
inside the base by construction on the bars from ``start_index`` to
``creation_index`` -- those bars *are* the zone -- and calling any of them a
retest would manufacture one retest per zone at birth. The first bar that can be
a retest is the first bar at or after ``confirmation_index``.

Lifecycle
---------
``fresh`` -> ``mitigated`` (touched, but price did not close far enough into the
band to invalidate) -> ``invalidated`` (a close more than ``max_touch_depth`` of
the band width inside it), or ``expired`` (older than ``max_age_bars`` at
``confirmation_index``). A retest increments ``retest_count`` and moves the zone
to ``mitigated``; it never returns it to ``fresh``, because a zone price has
already been through once is not the same object as one that has not.

Touch depth and invalidation are measured from different parts of the bar on
purpose: depth from the bar's *range*, invalidation from its *close*. A wick deep
into a zone that closed back out is the rejection the concept is named for, and
treating it as invalidation would record the zone's best evidence as its death.

Both terminal states are *terminal*: once a zone is invalidated or expired it
stops being updated and can no longer emit retests. A zone that trades back and
forth across its boundary must therefore produce exactly one invalidation, not
one per crossing -- the duplicate-suppression case the lifecycle exists to make
deterministic.

Overlapping zones
-----------------
Two zones from different displacements may overlap, and this is left permitted
rather than merged. Merging would require deciding, retrospectively, that they
are one object, and a retest of the merged band could not be attributed to either
source. A retest is therefore emitted per zone, and a bar that enters two
overlapping zones produces two retest events with different ``zone_id`` values.
Both are kept -- the downstream aggregation already clusters by detector, so two
retests on one bar land in the same family and are not mistaken for two
independent observations.

Ambiguous bars
--------------
A single bar whose range spans two zone boundaries touches both. The bar is
recorded as touching each zone it intersects, independently, and no ordering
between them is invented: which one price reached first is not knowable from OHLC
and guessing would be reading an intrabar sequence the data does not contain.

Carried state
-------------
Zones are long-lived, so :class:`ZoneCarried` survives a segment boundary the way
:class:`~app.services.research.events.SweepCarried` does -- keyed by structural
values rather than ``id()``, because an ``id`` does not survive a checkpoint round
trip and a resumed process would match nothing. The open-zone set is bounded by
``max_age_bars``, so the carried state is bounded by that and not by the length of
the run.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal

from app.schemas.market_data import CandleData
from app.services.research.events import ResearchEvent, detect_displacement

#: Lifecycle states, in the order they can be reached.
ZoneState = str

FRESH: ZoneState = "fresh"
MITIGATED: ZoneState = "mitigated"
INVALIDATED: ZoneState = "invalidated"
EXPIRED: ZoneState = "expired"

#: States in which a zone still accepts retests.
OPEN_STATES = (FRESH, MITIGATED)

#: Terminal states. A zone in one of these is frozen -- it keeps its numbers but
#: is never updated and never emits again. This is what makes "one invalidation
#: per zone" true by construction rather than by a flag check inside the
#: retest loop.
TERMINAL_STATES = (INVALIDATED, EXPIRED)


@dataclass(frozen=True)
class Zone:
    """A rectangular price band left behind by a displacement.

    Boundaries are fixed at creation. ``high``/``low`` are the exact extremes of
    the base bars -- not rounded, not buffered -- because a retest is tested
    against these numbers and a tolerance would make "did price reach the zone"
    a matter of a rounding convention.
    """

    #: Stable, structural identifier. See :meth:`key` for how it is formed.
    zone_id: str
    #: ``supply`` when the base sits *below* the departure and price rose out of
    #: it; ``demand`` when the base sits *above* the departure and price fell out
    #: of it. This is the vocabulary the research plan uses, and it is the field
    #: every lifecycle rule keys on: what makes a retest a retest is price
    #: returning from the *departure side*, and for a supply zone that is below
    #: the band, for a demand zone above it.
    zone_type: str
    #: ``up`` or ``down`` -- which way price left. Kept separate from
    #: ``zone_type`` because the two are easy to conflate and conflating them
    #: silently inverts the retest rule: a zone labelled by its departure
    #: direction reads "supply" for an upward move, when the price that matter is
    #: above it.
    departure_direction: str
    #: First bar of the base. Absolute bar index, so a segmented run and a
    #: whole-series run name the same bar.
    start_index: int
    start_time: datetime
    #: The displacement bar -- the last bar of the zone's price range and the
    #: bar the departure began on.
    creation_index: int
    creation_time: datetime
    #: First bar at which this zone was a known object and could be acted on.
    confirmation_index: int
    confirmation_time: datetime | None
    high: Decimal
    low: Decimal
    creation_reason: str
    #: The displacement's body in units of trailing volatility -- the same
    #: measure ``detect_displacement`` publishes as ``magnitude_in_volatility``,
    #: so a zone's departure strength is comparable to any other displacement.
    departure_strength: Decimal | None
    #: Base volume over the base bars.
    volume: Decimal
    bars_in_base: int
    #: How far through the base window the displacement began, in bars from its
    #: first bar: 0 is a base extended as far back as allowed.
    base_offset_bars: int
    # -- mutable lifecycle, applied in bar order -----------------------------
    state: ZoneState = FRESH
    touch_count: int = 0
    retest_count: int = 0
    #: Bar of the first touch after confirmation, and of the most recent one.
    first_touch_index: int | None = None
    last_touch_index: int | None = None
    #: Deepest penetration into the zone from the outside, as a fraction of zone
    #: height. For a demand zone, how far up into it price came; for supply, how
    #: far down. This is the "retest_depth" the plan's feature list names.
    max_touch_depth: Decimal | None = None
    #: Bar at which the zone left the open set, and the state it left in.
    terminal_index: int | None = None
    #: Last bar this zone's lifecycle has been advanced over.
    #:
    #: This exists for one reason: a segmented caller re-supplies a *prefix* of
    #: bars from the previous segment so the detectors have history, and that
    #: prefix has already been applied to every carried zone. Without a
    #: watermark, replaying it applies the same bars twice, and ``touch_count``,
    #: ``first_touch_index`` and ``last_touch_index`` are all *increments* -- so
    #: a segmented run silently reports a zone as touched more often than the
    #: continuous run does. Measured on a hand-built fixture: ``touch_count`` 4
    #: where the whole series says 3, with the retest count coincidentally
    #: matching because ``min_retest_separation_bars`` happened to suppress the
    #: replayed retest. A match on the count that a reader would check, caused
    #: by luck rather than by correctness, is the worst kind.
    #:
    #: It is lifecycle state rather than an immutable property, so it lives here
    #: with ``touch_count`` and not on the frozen band.
    applied_through: int | None = None

    @property
    def height(self) -> Decimal:
        return self.high - self.low

    @property
    def is_open(self) -> bool:
        return self.state in OPEN_STATES

    @property
    def age_bars(self) -> int:
        """Bars between creation and confirmation.

        Frozen at creation, unlike the plan's ``age`` field: a zone's age at
        *confirmation* is a fact about when it became knowable, while its age at
        the last bar depends on which bar you ask about and so belongs in the
        lifecycle, not on the immutable object.
        """
        return self.confirmation_index - self.creation_index

    def key(self) -> tuple[int, str, str, str]:
        """The structural identity used for checkpointing and de-duplication.

        ``(creation_index, zone_type, low, high)``. Not ``id(self)``: object
        identity is not stable across a checkpoint round trip, so a resumed
        process would re-arm every carried zone and re-emit its retests. Not
        ``zone_id`` computed from the bar index alone, because two displacements
        can share a bar in a future detector and the zone's *price band* is what
        distinguishes the objects a retest could refer to.
        """
        return (self.creation_index, self.zone_type, str(self.low), str(self.high))

    def distance_to_price(self, price: Decimal) -> Decimal:
        """Signed distance from ``price`` to the zone: positive above, negative below.

        Zero inside the band. A *signed* distance rather than an absolute one, so
        a consumer can tell which side price is on -- the sign is the whole
        information an absolute distance throws away.
        """
        if price > self.high:
            return price - self.high
        if price < self.low:
            return price - self.low
        return Decimal(0)

    def with_lifecycle(
        self,
        *,
        state: ZoneState,
        touch_count: int | None = None,
        retest_count: int | None = None,
        first_touch_index: int | None = None,
        last_touch_index: int | None = None,
        max_touch_depth: Decimal | None = None,
        terminal_index: int | None = None,
        applied_through: int | None = None,
    ) -> Zone:
        """A copy with lifecycle fields replaced. The zone itself is frozen."""
        return Zone(
            **{
                **{field: getattr(self, field) for field in _ZONE_FIELDS},
                "state": state,
                "touch_count": touch_count if touch_count is not None else self.touch_count,
                "retest_count": (retest_count if retest_count is not None else self.retest_count),
                "first_touch_index": (
                    first_touch_index if first_touch_index is not None else self.first_touch_index
                ),
                "last_touch_index": (
                    last_touch_index if last_touch_index is not None else self.last_touch_index
                ),
                "max_touch_depth": (
                    max_touch_depth if max_touch_depth is not None else self.max_touch_depth
                ),
                "terminal_index": (
                    terminal_index if terminal_index is not None else self.terminal_index
                ),
                # ``None`` here means "leave as-is", which is what every other
                # lifecycle field does -- except that ``applied_through`` has a
                # legitimate advance-from-unset state on a zone published
                # mid-window. Callers that need to set it back to ``None``
                # cannot, and none does: the watermark only ever moves forward.
                "applied_through": (
                    applied_through if applied_through is not None else self.applied_through
                ),
            }
        )


#: Every constructor field, so :meth:`Zone.with_lifecycle` can rebuild without
#: hand-listing twenty names and silently dropping one.
_ZONE_FIELDS = (
    "zone_id",
    "zone_type",
    "departure_direction",
    "start_index",
    "start_time",
    "creation_index",
    "creation_time",
    "confirmation_index",
    "confirmation_time",
    "high",
    "low",
    "creation_reason",
    "departure_strength",
    "volume",
    "bars_in_base",
    "base_offset_bars",
)


@dataclass
class ZoneCarried:
    """Zone state that must survive a window boundary.

    Same shape and same reasoning as
    :class:`~app.services.research.events.SweepCarried`: a segmented run has to
    produce the same retests a continuous one does, and a zone created before a
    boundary is still open after it.

    ``pending`` holds a zone whose confirmation bar has not printed yet. A zone's
    confirmation index is not simply its creation index plus a fixed delay -- it
    is the max of the displacement's confirmation and the structural significance
    bar, which is a per-zone number. So a zone whose confirmation index falls past
    the last bar of this window cannot be published yet, and publishing it anyway
    would pin its confirmation to a bar that does not exist.
    """

    zones: dict[tuple[int, str, str, str], Zone] = field(default_factory=dict)
    pending: list[Zone] = field(default_factory=list)
    #: Bar index of the most recent retest already emitted per zone key, so a
    #: zone price oscillating along its boundary cannot emit a retest on every
    #: bar. ``min_retest_separation_bars`` is the rule; this is the memory of it.
    last_retest_index: dict[tuple[int, str, str, str], int] = field(default_factory=dict)
    #: Whether price has been *clear of* each zone since it was published.
    #:
    #: This is what makes a retest a return rather than a continuation. The base
    #: bars are inside the band by construction, and the departure bar usually
    #: still overlaps it, so without this gate a zone emits a retest on every bar
    #: from the moment price drifts back into its own construction range — which
    #: is not a retest of the zone, it is the zone still being formed. On the
    #: first real-data pass this was worth 38,513 retests over 937 zones, ~41
    #: each, all with a retest depth of zero because price had never left.
    #:
    #: Deliberately *not* a field on :class:`Zone`. It describes the market's
    #: relationship to the zone, which changes over the zone's life, and folding
    #: it into the frozen zone object would make "the zone" a record of how
    #: price behaved afterwards — the exact retrospective rewriting this module
    #: exists to avoid.
    cleared: set[tuple[int, str, str, str]] = field(default_factory=set)

    def open_zones(self) -> list[Zone]:
        return [zone for zone in self.zones.values() if zone.is_open]

    def prune(self, *, before_index: int) -> int:
        """Drop terminal zones that are older than the retention horizon.

        A zone in a terminal state can never emit again and can never be
        updated again -- :func:`_advance_lifecycle` skips anything not in
        ``OPEN_STATES`` before it can do anything. So a terminal zone is dead
        weight in the checkpoint, and keeping every one of them makes the
        carried state grow with the *length of the run* rather than with the
        number of *live* zones.

        That matters concretely rather than theoretically. Measured on real
        BTCUSDT 5m data: after 6,000 bars the carried state held 255 zones of
        which **3 were open** -- and 212 KB of checkpoint to describe a run
        whose live working set was a few kilobytes. Extrapolated to a multi-year
        run that is a checkpoint that grows without limit, written at every
        segment boundary, which is precisely the resource profile this project
        is not allowed to have.

        The horizon is ``max_age_bars`` past the terminal bar rather than zero,
        for two reasons: a checkpoint written *just* after a zone terminates
        should still be able to report that terminal state (a resume that lost
        it would report the zone as merely absent, which is a different claim),
        and the same horizon keeps the bound a constant times the live set
        instead of a cliff.

        Returns the number of zones dropped, so a caller or a test can see that
        pruning happened rather than inferring it from a smaller dict.
        """
        dropped = [
            key
            for key, zone in self.zones.items()
            if zone.state in TERMINAL_STATES
            and zone.terminal_index is not None
            and zone.terminal_index < before_index
        ]
        if not dropped:
            return 0
        for key in dropped:
            del self.zones[key]
            # The auxiliary maps are keyed by the same structural key, so they
            # would otherwise leak one entry per retired zone -- the same
            # unbounded growth wearing a different hat.
            self.last_retest_index.pop(key, None)
            self.cleared.discard(key)
        return len(dropped)

    def to_payload(self) -> dict:
        return {
            "zones": [
                _zone_to_payload(zone)
                for zone in sorted(self.zones.values(), key=lambda z: z.creation_index)
            ],
            "pending": [_zone_to_payload(zone) for zone in self.pending],
            "last_retest_index": [
                [list(key), index] for key, index in sorted(self.last_retest_index.items())
            ],
            "cleared": [list(key) for key in sorted(self.cleared)],
        }

    @classmethod
    def from_payload(cls, payload: dict | None) -> ZoneCarried:
        if not payload:
            return cls()
        return cls(
            zones={
                _zone_key_from_payload(item): _zone_from_payload(item) for item in payload["zones"]
            },
            pending=[_zone_from_payload(item) for item in payload.get("pending", [])],
            last_retest_index={
                (int(key[0]), str(key[1]), str(key[2]), str(key[3])): int(index)
                for key, index in payload.get("last_retest_index", [])
            },
            cleared={
                (int(key[0]), str(key[1]), str(key[2]), str(key[3]))
                for key in payload.get("cleared", [])
            },
        )


def _zone_key_from_payload(item: dict) -> tuple[int, str, str, str]:
    return (
        int(item["creation_index"]),
        str(item["zone_type"]),
        str(item["low"]),
        str(item["high"]),
    )


def _zone_to_payload(zone: Zone) -> dict:
    """A zone as JSON. ``Decimal`` as text, for the same reason events do it."""
    return {
        "zone_id": zone.zone_id,
        "zone_type": zone.zone_type,
        "departure_direction": zone.departure_direction,
        "start_index": zone.start_index,
        "start_time": zone.start_time.isoformat(),
        "creation_index": zone.creation_index,
        "creation_time": zone.creation_time.isoformat(),
        "confirmation_index": zone.confirmation_index,
        "confirmation_time": (
            zone.confirmation_time.isoformat() if zone.confirmation_time else None
        ),
        "high": str(zone.high),
        "low": str(zone.low),
        "creation_reason": zone.creation_reason,
        "departure_strength": (
            str(zone.departure_strength) if zone.departure_strength is not None else None
        ),
        "volume": str(zone.volume),
        "bars_in_base": zone.bars_in_base,
        "base_offset_bars": zone.base_offset_bars,
        "state": zone.state,
        "touch_count": zone.touch_count,
        "retest_count": zone.retest_count,
        "first_touch_index": zone.first_touch_index,
        "last_touch_index": zone.last_touch_index,
        "max_touch_depth": (
            str(zone.max_touch_depth) if zone.max_touch_depth is not None else None
        ),
        "terminal_index": zone.terminal_index,
        "applied_through": zone.applied_through,
    }


def _zone_from_payload(item: dict) -> Zone:
    return Zone(
        zone_id=item["zone_id"],
        zone_type=item["zone_type"],
        departure_direction=item["departure_direction"],
        start_index=int(item["start_index"]),
        start_time=datetime.fromisoformat(item["start_time"]),
        creation_index=int(item["creation_index"]),
        creation_time=datetime.fromisoformat(item["creation_time"]),
        confirmation_index=int(item["confirmation_index"]),
        confirmation_time=(
            datetime.fromisoformat(item["confirmation_time"])
            if item.get("confirmation_time")
            else None
        ),
        high=Decimal(item["high"]),
        low=Decimal(item["low"]),
        creation_reason=item["creation_reason"],
        departure_strength=(
            Decimal(item["departure_strength"])
            if item.get("departure_strength") is not None
            else None
        ),
        volume=Decimal(item["volume"]),
        bars_in_base=int(item["bars_in_base"]),
        base_offset_bars=int(item["base_offset_bars"]),
        state=item["state"],
        touch_count=int(item.get("touch_count", 0)),
        retest_count=int(item.get("retest_count", 0)),
        first_touch_index=item.get("first_touch_index"),
        last_touch_index=item.get("last_touch_index"),
        max_touch_depth=(
            Decimal(item["max_touch_depth"]) if item.get("max_touch_depth") is not None else None
        ),
        terminal_index=item.get("terminal_index"),
        applied_through=item.get("applied_through"),
    )


# ---------------------------------------------------------------------------
# Zone construction
# ---------------------------------------------------------------------------


def _confirmed_extreme(candles: Sequence[CandleData], index: int, kind: str, lookback: int) -> bool:
    """Whether bar ``index`` is a confirmed swing extreme of the given ``kind``.

    Confirmed *without* reading past the window it is asked about: a pivot at
    ``index`` is proved by the ``lookback`` bars that follow it, so the answer is
    only meaningful if the caller already holds those bars and is at least
    ``lookback`` bars past ``index``. This function does not check that, because it
    cannot -- it is the *caller's* job, and the callers below all pass an index
    that is at least ``lookback`` bars before the bar they are scoring. Writing the
    check here would make the function look safe in a context where it is not.

    This is deliberately not built on
    :func:`~app.services.market_structure.analysis.detect_swings`, whose swings are
    confirmed relative to the *end* of the series. That is correct for the chart
    and wrong here: asking it "was this bar a swing?" while scanning forward would
    import the future into a boundary question.
    """
    if index - lookback < 0 or index + lookback >= len(candles):
        return False
    window = candles[index - lookback : index + lookback + 1]
    price = candles[index].high if kind == "high" else candles[index].low
    if kind == "high":
        return all(price > other.high for other in window if other is not candles[index])
    return all(price < other.low for other in window if other is not candles[index])


def detect_zones(
    candles: Sequence[CandleData],
    *,
    displacements: Sequence[ResearchEvent] | None = None,
    vol_window: int = 20,
    displacement_threshold: Decimal = Decimal("2"),
    min_body_ratio: Decimal = Decimal("0.5"),
    base_bars: int = 5,
    max_base_bars: int = 20,
    structure_lookback: int = 3,
    structure_window: int = 10,
    max_touch_depth: Decimal = Decimal("0.5"),
    max_age_bars: int = 500,
    min_retest_separation_bars: int = 3,
    offset: int = 0,
    carried: ZoneCarried | None = None,
    final: bool = False,
) -> list[ResearchEvent]:
    """Zones and their retests over one window, in bar order.

    Returns ``zone`` events and ``zone_retest`` events interleaved by
    confirmation bar, so a caller can fold the two families together the way the
    runner folds sweeps and compression.

    :param displacements: reuse an existing displacement list. Passing one in is
        not an optimisation only -- it guarantees the zone is anchored to the
        *same* displacement measurement a separate ``detect_displacement`` call
        would produce, rather than to a second, possibly-differing measurement of
        the same bar.
    :param base_bars: how many bars before the displacement to include in the base
        when one is available.
    :param max_base_bars: the furthest back the base may be extended to find
        structural significance. The base is *shortened* by a nearby pivot and
        lengthened only as far as needed, so the reported ``base_offset_bars``
        says how far it actually reached.
    :param max_touch_depth: penetration past the far edge, as a fraction of zone
        height, at which the zone is invalidated rather than mitigated.
    :param offset: absolute index of ``candles[0]``. Prefix bars before it
        participate in history and never emit.
    :param carried: zone state across a window boundary.
    :param final: whether this is the last window. Zones still open are reported
        with ``is_final_bar_seen`` rather than being closed, because the run
        ending is not the same fact as the zone ending.
    """
    state = carried if carried is not None else ZoneCarried()
    if displacements is None:
        displacements = detect_displacement(
            candles,
            vol_window=vol_window,
            threshold=displacement_threshold,
            min_body_ratio=min_body_ratio,
        )
    displacement_by_index = {event.event_index: event for event in displacements}
    events: list[ResearchEvent] = []

    # 1. Zones carried in from a previous window whose confirmation bar printed
    #    here. Published *before* the lifecycle walk so a zone that comes due at
    #    bar k of this window can be touched at bar k rather than only from bar
    #    k+1 -- which would make a windowed run and a continuous one disagree
    #    about the first retest after every boundary.
    still_pending: list[Zone] = []
    for zone in state.pending:
        if zone.confirmation_index - offset >= len(candles):
            still_pending.append(zone)
            continue
        key = zone.key()
        if key not in state.zones:
            # A pending zone was built in an earlier window, so its confirmation
            # bar was not in range and its ``confirmation_time`` is unset. The bar
            # is in *this* window -- that is what "pending" meant -- so the time
            # is filled in now rather than left null in a stored event.
            if zone.confirmation_time is None:
                zone = replace(
                    zone,
                    confirmation_time=candles[zone.confirmation_index - offset].close_time,
                )
            state.zones[key] = zone
            events.append(_zone_event(candles, zone, offset=offset))
    state.pending = still_pending if not final else []

    # 2. Creation, at bars where a displacement printed.
    #
    #    The window is scanned in full, including the prefix a segmented caller
    #    supplied as history. An earlier revision filtered on
    #    ``offset <= index < len(candles)``, which compares a *window-local*
    #    index against the *absolute* offset of the window's first bar. At
    #    ``offset == 0`` that is a no-op, so every unit test passed; at
    #    ``offset > 0`` -- every segment after the first -- it rejects every bar
    #    whose local index is below the offset, so a segment of 288 bars paired
    #    with a 64-bar tail silently emits **no zones at all**. The failure is
    #    total rather than partial, which is the only reason it was caught at
    #    all: the segmented run produced a plausible-looking, zone-free event
    #    log rather than an exception.
    #
    #    Suppressing the prefix is therefore a question of *identity*, not of
    #    index arithmetic, and is handled by the two key checks below: a zone
    #    already published is in ``state.zones``, and one whose confirmation bar
    #    has not printed is in ``state.pending``. Re-deriving it here is cheap,
    #    matches on its structural key, and is dropped. Getting it right by
    #    index instead would require knowing how many leading bars are prefix --
    #    information this function does not have and cannot infer.
    for index, displacement in sorted(displacement_by_index.items()):
        if not (0 <= index < len(candles)):
            continue
        zone = _build_zone(
            candles,
            index,
            displacement,
            base_bars=base_bars,
            max_base_bars=max_base_bars,
            structure_lookback=structure_lookback,
            structure_window=structure_window,
            offset=offset,
        )
        if zone is None:
            continue
        # A zone whose confirmation bar has not printed yet cannot be published.
        # Publishing it would date it to a bar that does not exist and let a
        # later window retest a zone before it was knowable.
        if zone.confirmation_index - offset >= len(candles):
            if not final:
                state.pending.append(zone)
            continue
        key = zone.key()
        if key in state.zones:
            # Same displacement seen twice -- a duplicated window boundary, or a
            # caller passing the same list twice. One zone, not two.
            continue
        state.zones[key] = zone
        events.append(_zone_event(candles, zone, offset=offset))

    # 3. Lifecycle, over the whole window, against the zone set as it stood.
    #
    #    This runs *after* creation, so a zone created at bar k is touched by
    #    bars from its confirmation onward within this same window. Running it
    #    first -- which reads better, because "advance the state, then add to it"
    #    -- leaves every zone created in this window untested until the next one,
    #    and on a whole-series run with no next window, untested forever.
    #
    #    The ordering does not let the future reach back: ``_advance_lifecycle``
    #    skips any bar at or before a zone's ``confirmation_index``, so a zone
    #    created at bar k cannot be touched by bars k-5 through k-1, which are
    #    before it existed.
    events.extend(
        _advance_lifecycle(
            candles,
            state,
            offset=offset,
            max_touch_depth=max_touch_depth,
            max_age_bars=max_age_bars,
            min_retest_separation_bars=min_retest_separation_bars,
        )
    )

    # Retire zones that can no longer emit or change, so the carried state is
    # bounded by the *live* set rather than by the length of the run. See
    # :meth:`ZoneCarried.prune`. The horizon matches the zone's own maximum
    # life, so "how long might this zone still have mattered" and "how long do
    # we remember it" are the same number rather than two that can disagree.
    state.prune(before_index=offset + len(candles) - max_age_bars)

    events.sort(key=lambda event: (event.confirmation_index, event.kind, event.detector))
    return events


def _build_zone(
    candles: Sequence[CandleData],
    index: int,
    displacement: ResearchEvent,
    *,
    base_bars: int,
    max_base_bars: int,
    structure_lookback: int,
    structure_window: int,
    offset: int,
) -> Zone | None:
    """The zone left by the displacement on bar ``index``, or ``None``.

    ``None`` means the three ingredients the plan names are not all present: a
    base to leave, a displacement to leave it with, and a structural extreme in
    that direction near enough to be what the base built around. Absence is not
    an error -- most displacement bars have no base in front of them, and
    inventing a zone for those would produce a zone from every large candle.

    ``index`` is window-local; the returned Zone's indices are absolute
    (``index + offset`` and likewise for the base), because those are the
    numbers the lifecycle walk and every stored event are keyed on.
    """
    direction = displacement.context.get("direction_of_move")
    if direction not in ("up", "down"):
        return None
    # An upward displacement leaves a *demand* zone behind it: price rose out of
    # the base, so the base is below and becomes demand. A downward displacement
    # leaves supply. The base's structural anchor is correspondingly a swing low
    # for an upward move, a swing high for a downward one.
    zone_type = "demand" if direction == "up" else "supply"
    kind = "low" if direction == "up" else "high"

    # The base ends at the bar *before* the displacement. Including the
    # displacement bar would drag the zone's far edge out to the top of the
    # departure, which is the move itself.
    base_end = index - 1
    if base_end < 0:
        return None

    # How far back is the nearest confirmed pivot in this direction? Its age is
    # the zone's structural significance: a base that grew out of a swing low
    # four bars ago is a different object from one that grew out of nowhere.
    nearest = None
    for back in range(1, max_base_bars + 1):
        candidate = base_end - back + 1
        if candidate - structure_lookback < 0:
            break
        if _confirmed_extreme(candles, candidate, kind, structure_lookback):
            nearest = candidate
            break
    if nearest is None:
        return None
    if base_end - nearest > structure_window:
        return None

    length = min(base_bars, base_end - nearest + 1)
    if length < 1:
        return None
    start = base_end - length + 1
    base = candles[start : base_end + 1]
    if not base:
        return None

    high = max(candle.high for candle in base)
    low = min(candle.low for candle in base)
    if high <= low:
        # A zero-height band cannot be tested against and cannot be invalidated;
        # a one-bar base with high == low is a real shape, not a zone.
        return None

    # ------------------------------------------------------------------
    # Two index spaces meet here, and mixing them is the single easiest way
    # to get this silently wrong.
    #
    # *Every* index used to read ``candles`` is **window-local**: ``index``,
    # ``start``, ``base_end`` and ``nearest`` all index this call's own
    # ``candles`` sequence, which is a window and not the series.
    #
    # *Every* index stored on the Zone is **absolute**, because the lifecycle
    # walk steps through absolute bar numbers and a Zone carried into the next
    # window must be compared against the same bars the next window will walk.
    #
    # So the conversion happens here, at the boundary, in one place -- and
    # nothing after this line reads ``candles``. Adding ``offset`` to a
    # variable and then indexing ``candles`` with it is exactly the bug this
    # comment exists to prevent: with ``offset == 0`` it is invisible (every
    # unit test runs at offset zero), and with ``offset > 0`` it either raises
    # ``IndexError`` on the first segment that has history in front of it or,
    # when the absolute index happens to land inside the window, reads a
    # perfectly plausible *wrong* candle.
    #
    # ``displacement.confirmation_index`` is window-local too -- it was produced
    # by ``detect_displacement`` over this same window -- so it is converted
    # with the rest rather than compared against an absolute number.
    # ------------------------------------------------------------------
    absolute_start = start + offset
    absolute_creation = index + offset
    confirmation_index = max(displacement.confirmation_index + offset, absolute_creation + 1)
    confirmation_local = confirmation_index - offset
    confirmation_time = (
        candles[confirmation_local].close_time if 0 <= confirmation_local < len(candles) else None
    )

    return Zone(
        zone_id=_zone_id(
            candles[index],
            zone_type=zone_type,
            start=absolute_start,
            high=high,
            low=low,
        ),
        zone_type=zone_type,
        departure_direction=direction,
        start_index=absolute_start,
        start_time=candles[start].open_time,
        creation_index=absolute_creation,
        creation_time=candles[index].open_time,
        confirmation_index=confirmation_index,
        confirmation_time=confirmation_time,
        high=high,
        low=low,
        creation_reason="base+displacement+structure",
        departure_strength=displacement.features.get("magnitude_in_volatility"),
        volume=sum((candle.volume for candle in base), Decimal(0)),
        bars_in_base=length,
        base_offset_bars=base_end - nearest + 1,
    )


def _zone_id(candle: CandleData, *, zone_type: str, start: int, high: Decimal, low: Decimal) -> str:
    """A readable, stable id.

    Built from values that do not change over the zone's life, so two runs of the
    same data produce the same ids and a stored event log can be joined to a
    re-derived one without a positional match.
    """
    stamp = candle.open_time.strftime("%Y%m%dT%H%M")
    return f"{zone_type}:{stamp}:{start}:{high}:{low}"


# ---------------------------------------------------------------------------
# Lifecycle and retests
# ---------------------------------------------------------------------------


def _advance_lifecycle(
    candles: Sequence[CandleData],
    state: ZoneCarried,
    *,
    offset: int,
    max_touch_depth: Decimal,
    max_age_bars: int,
    min_retest_separation_bars: int,
) -> list[ResearchEvent]:
    """Walk the window bar by bar, updating open zones and emitting retests.

    Bars are stepped one at a time in order, and each zone is gated on its own
    ``confirmation_index``, so a zone is never touched by a bar that printed
    before it was knowable. That gate is the whole reason this is a bar-ordered
    walk rather than a per-zone scan: a per-zone scan over the whole window would
    have to ask "was this zone confirmed before *that* bar?" for every pair, and
    the answer changes as zones are published mid-window.

    Zones are replaced in ``state.zones`` rather than mutated -- the dataclass is
    frozen so a checkpoint can never capture a half-updated zone.
    """
    events: list[ResearchEvent] = []
    for index, candle in enumerate(candles, start=offset):
        # ``offset`` is carried explicitly rather than baked into the Zone's
        # indices because the walk has to start at an absolute number; the two
        # must be the same number or every gate below compares a zone against a
        # different bar.
        for key, zone in list(state.zones.items()):
            if not zone.is_open:
                continue
            if index <= zone.creation_index:
                # The bar the zone was created on is part of the departure, not a
                # return to it. The base bars before it are the zone's own
                # construction and were never retests.
                continue
            if index < zone.confirmation_index:
                # Price may already be inside the band here -- the zone's own
                # bars are -- but nobody knew the zone existed. Touching it would
                # manufacture a retest for every zone at birth.
                continue
            if zone.applied_through is not None and index <= zone.applied_through:
                # A prefix bar a previous segment already applied to this zone.
                # See :attr:`Zone.applied_through` -- replaying it double-counts
                # the touches, and the damage is invisible in the event stream.
                continue

            updated = _update_zone(
                zone,
                index,
                candle,
                max_touch_depth=max_touch_depth,
                max_age_bars=max_age_bars,
            )
            if updated is None:
                # Age limit reached: terminal, and never updated again.
                state.zones[key] = zone.with_lifecycle(
                    state=EXPIRED, terminal_index=index, applied_through=index
                )
                continue
            # The watermark is advanced *before* any of the branches below can
            # ``continue`` out of the loop, so a bar is applied to a zone at most
            # once no matter which path it takes. Setting it only on the paths
            # that emit would leave the terminal paths unmarked, and the next
            # segment's prefix would then replay them.
            state.zones[key] = updated.with_lifecycle(state=updated.state, applied_through=index)
            updated = state.zones[key]

            if updated.state in TERMINAL_STATES:
                # A bar that both entered and invalidated is not a retest -- it is
                # the end of the zone. Emitting both would count a zone's death
                # as a use of it.
                continue

            # A retest needs all three, and each is doing separate work:
            #   * price has been *away* since confirmation (``cleared``), so this
            #     is a return rather than the zone still forming;
            #   * this bar reaches *into* the band (``_touches``), from the
            #     departure side, which is what distinguishes a touch from the
            #     bars merely sitting nearby;
            #   * enough bars have passed since the last one, so a price
            #     oscillating along the boundary does not emit every bar.
            #
            # The `cleared` update is deliberately *not* inside that branch: a
            # zone that price walks away from must be re-armed even on a bar that
            # is itself too soon to count as a retest, or a zone approached in a
            # steady drift would never re-arm at all.
            if key in state.cleared and _touches(updated, candle):
                last = state.last_retest_index.get(key)
                if last is None or index - last >= min_retest_separation_bars:
                    state.last_retest_index[key] = index
                    # The count is advanced on the zone itself, not derived from
                    # the event log. It is one of the fields the plan names, and
                    # it has to survive on the zone because a consumer reading a
                    # checkpoint has no other place to find it -- an event log is
                    # a separate file and may be truncated or resumed away.
                    counted = updated.with_lifecycle(
                        state=MITIGATED, retest_count=updated.retest_count + 1
                    )
                    state.zones[key] = counted
                    events.append(_retest_event(counted, candle, index, counted.retest_count))
            if _clears(updated, candle):
                state.cleared.add(key)
    return events


def _clears(zone: Zone, candle: CandleData) -> bool:
    """Whether this bar closed clear of the band *on the departure side*.

    Direction-aware, and that is the whole point. A supply zone was left when
    price fell *below* it; a demand zone was left when price rose *above* it.
    Only that side counts as "away" — price on the other side of the band never
    went anywhere, it is still inside the zone's story.

    Getting this wrong is invisible on a fixture and enormous on real data: with
    a direction-agnostic test, a supply zone's very first bar after confirmation
    already reads as "cleared" (price is below it — that is the departure), so
    every zone immediately earns a retest on the next overlapping bar, and
    "retest" stops meaning a return at all. It showed up as 38k retests over 937
    zones, every one of them measuring the departure rather than a return to it.

    Close-based, not range-based, for the same reason invalidation is: a wick
    clipping the boundary is contact, not a departure from it.
    """
    if zone.zone_type == "supply":
        return candle.close < zone.low
    return candle.close > zone.high


def _touches(zone: Zone, candle: CandleData) -> bool:
    """Whether this bar's range intersects the zone's band.

    Direction-aware in the same way as :func:`_clears`, for the same reason: a
    touch is a *return from the departure side*. Price overlapping the band while
    sitting on the departure side is the zone still forming, not a retest of it.

    Inclusive on both boundaries: a bar that reaches exactly ``zone.high`` has
    reached the zone, and treating the boundary as exclusive would make the
    answer depend on a bar that happens to land on an exact price.
    """
    if zone.zone_type == "supply":
        return candle.high >= zone.low
    return candle.low <= zone.high


def _update_zone(
    zone: Zone,
    index: int,
    candle: CandleData,
    *,
    max_touch_depth: Decimal,
    max_age_bars: int,
) -> Zone | None:
    """Apply one bar to one zone. ``None`` means it expired at this bar.

    Two separate measurements, and keeping them separate is the point:

    ``depth``       how far into the band the bar's *range* reached. Recorded as
                    ``max_touch_depth`` because a wick into a zone is the
                    rejection the concept is usually cited for, and throwing it
                    away would discard the most interesting bar that touches it.
    ``close_depth`` how far the bar's *close* ended up into the band, which is
                    what decides invalidation.

    They differ exactly on the bar that matters most — a long wick into a zone
    that closed back out of it. That bar is the zone's best evidence of working
    order and must not also be recorded as the zone's death. Invalidation is
    therefore tested on the close, and never on the range: a level invalidated by
    a wick would record every rejection as a failure and the retest count would
    end up measuring the opposite of what it is for.
    """
    if index - zone.confirmation_index > max_age_bars:
        return None

    depth = _penetration(zone, candle)
    if depth is None:
        return zone

    new_depth = depth if zone.max_touch_depth is None else max(zone.max_touch_depth, depth)
    updated = zone.with_lifecycle(
        state=MITIGATED,
        touch_count=zone.touch_count + 1,
        first_touch_index=(zone.first_touch_index if zone.first_touch_index is not None else index),
        last_touch_index=index,
        max_touch_depth=new_depth,
    )

    close_depth = _close_penetration(zone, candle)
    if max_touch_depth is not None and close_depth > max_touch_depth:
        return updated.with_lifecycle(state=INVALIDATED, terminal_index=index)
    return updated


def _close_penetration(zone: Zone, candle: CandleData) -> Decimal:
    """How far the bar's *close* sits inside the band, as a fraction of height.

    Zero when the close is outside it. Measured with the same edge as
    :func:`_penetration` so the two are comparable — one is how far the bar came,
    the other how far it stayed.
    """
    height = zone.height
    if height <= 0 or not (zone.low <= candle.close <= zone.high):
        return Decimal(0)
    if zone.zone_type == "supply":
        return (zone.high - candle.close) / height
    return (candle.close - zone.low) / height


def _penetration(zone: Zone, candle: CandleData) -> Decimal | None:
    """How far into the zone price came on this bar, as a fraction of its height.

    ``None`` when the bar does not return to the band from the departure side.

    Measured from the edge price returns across: a supply zone is entered from
    below at ``zone.low``, a demand zone from above at ``zone.high``. So depth 0
    is a graze of the boundary and depth 1 is the full width to the far edge, and
    a bar that overshoots past the far edge clamps at 1 rather than reporting more
    than the whole zone is deep — an overshoot is a fact about the *market*, and
    it is already observable from the bar's own high/low; folding it into the
    zone's depth would make zones of different widths incomparable.
    """
    height = zone.height
    if height <= 0:
        return None
    if zone.zone_type == "supply":
        if candle.high < zone.low:
            return None
        reached = min(candle.high, zone.high)
        return (zone.high - reached) / height
    if candle.low > zone.high:
        return None
    reached = max(candle.low, zone.low)
    return (reached - zone.low) / height


def _zone_event(candles: Sequence[CandleData], zone: Zone, *, offset: int = 0) -> ResearchEvent:
    """The zone itself, as a research event.

    ``price`` is the close at the zone's *confirmation* bar -- the bar the zone
    becomes knowable at, and therefore the only price a decision taken at that
    moment could have used.

    ``candles`` is a *window*, so a Zone's absolute confirmation index has
    ``offset`` subtracted off it before indexing. Reading the absolute number
    straight into a window array is not a small slip: it silently returns a real
    candle from the wrong place, and the event it produces looks entirely
    plausible -- which is exactly how a boundary-crossing zone came to report the
    price of a bar several bars after the one that confirmed it.
    """
    price = candles[zone.confirmation_index - offset].close
    return ResearchEvent(
        kind="zone",
        detector="zone:base_displacement_structure",
        event_index=zone.creation_index,
        event_time=zone.creation_time,
        confirmation_index=zone.confirmation_index,
        confirmation_time=zone.confirmation_time,
        price=price,
        features={
            "zone_high": zone.high,
            "zone_low": zone.low,
            "zone_height": zone.height,
            "distance_to_price": zone.distance_to_price(price),
            "departure_strength": zone.departure_strength,
            "volume": zone.volume,
            "freshness": Decimal(0),
            "retest_depth": zone.max_touch_depth,
            "retest_count": Decimal(zone.retest_count),
            "age": Decimal(zone.age_bars),
            "bars_in_base": Decimal(zone.bars_in_base),
        },
        context={
            "zone_id": zone.zone_id,
            "zone_type": zone.zone_type,
            "departure_direction": zone.departure_direction,
            "zone_key": list(zone.key()),
            "creation_reason": zone.creation_reason,
            "start_index": zone.start_index,
            "creation_index": zone.creation_index,
            "start_time": zone.start_time.isoformat(),
            "confirmation_index": zone.confirmation_index,
            "state": zone.state,
        },
    )


def _retest_event(zone: Zone, candle: CandleData, index: int, touch_count: int) -> ResearchEvent:
    """One return into one zone, as a research event.

    Dated to the bar that touched the zone, with ``confirmation_index`` the same
    bar: a touch is knowable at its own close, unlike a sweep, which needs the
    next bar to prove price came back. ``event_index`` and ``confirmation_index``
    being equal here is the honest answer rather than a special case -- and it is
    why the retest rule is anchored on ``confirmation_index`` and not on
    ``creation_index``.

    ``retest_depth`` is this bar's own penetration, not the zone's running
    maximum: a retest is a measurement of a moment, and reporting the deepest
    previous approach would make every retest of a deep-touched zone look like it
    reached the same depth again.
    """
    depth = _penetration(zone, candle) or Decimal(0)
    age = Decimal(index - zone.creation_index)
    return ResearchEvent(
        kind="zone_retest",
        detector="zone_retest:touch",
        event_index=index,
        event_time=candle.open_time,
        confirmation_index=index,
        confirmation_time=candle.close_time,
        price=candle.close,
        features={
            "retest_depth": depth,
            "retest_count": Decimal(touch_count),
            "freshness": age,
            "zone_height": zone.height,
            "departure_strength": zone.departure_strength,
            "age": age,
        },
        context={
            "zone_id": zone.zone_id,
            "zone_type": zone.zone_type,
            "departure_direction": zone.departure_direction,
            "zone_key": list(zone.key()),
            "creation_index": zone.creation_index,
        },
    )


def zones_from_events(events: Iterable[ResearchEvent]) -> list[Zone]:
    """Rebuild zone objects from a stored event log.

    Exists so a researcher can re-derive a zone's band from a persisted run
    without re-reading the candles -- the boundaries and the zone id are both in
    the event's context, which is what makes them part of the stored contract
    rather than something only this session's objects knew.
    """
    return [
        Zone(
            zone_id=str(event.context["zone_id"]),
            zone_type=str(event.context["zone_type"]),
            departure_direction=str(event.context["departure_direction"]),
            start_index=int(event.context["start_index"]),
            start_time=datetime.fromisoformat(str(event.context["start_time"])),
            creation_index=int(event.context["creation_index"]),
            creation_time=event.event_time,
            confirmation_index=int(event.context["confirmation_index"]),
            confirmation_time=event.confirmation_time,
            high=event.features["zone_high"],
            low=event.features["zone_low"],
            creation_reason=str(event.context["creation_reason"]),
            departure_strength=event.features.get("departure_strength"),
            volume=event.features["volume"],
            bars_in_base=int(event.features["bars_in_base"]),
            base_offset_bars=0,
        )
        for event in events
        if event.kind == "zone"
    ]
