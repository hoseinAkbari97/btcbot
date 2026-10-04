"""Incremental market-structure state: one implementation, two entry points.

Why this module exists
----------------------
:func:`analyze_market_structure` historically took a whole ``list[CandleData]`` and
recomputed everything from it. That is fine at 1h and 49k bars. At 5m and 595k
bars it is the wrong *shape*, not just slow: the caller must hold the whole
history in RAM to ask a question about the last bar of a segment.

So the pipeline is rewritten as a state machine. :class:`StructureState` consumes
candles one at a time and retains only what a later bar cannot reconstruct.
Feeding it a whole series in one call and feeding it that series in forty
segments are then the *same computation* -- there is one implementation of each
rule, so the two cannot drift.

What crosses a segment boundary
-------------------------------
Retained: swings, structure events, liquidity buckets, the cumulative touch
index, running range extremes, the 20 trailing closes, and the trailing
``2 * lookback + 1`` bars that confirm the next swing.

Not retained: the candles. That is the point -- 595k ``CandleData`` is hundreds
of megabytes and the pipeline needs a 70-bar window, not the sample.

Levels are materialised at the end, not at creation
---------------------------------------------------
``LiquidityLevel.swing_confirmations`` holds *every* swing that has confirmed on
the level's price, and the batch implementation fills it with all of them --
including swings months after the level was published. That field is therefore
not causal on its own.

It does not need to be. Its only production consumer is
:meth:`LiquidityLevel.swing_count_at`, which takes a bar index and counts the
swings confirmed at or before it -- the causal question -- and is read that way at
``events.py:293`` and ``events.py:321``.

So an incremental state cannot emit a level at creation and keep it correct
without rewriting it later, which is not possible for a frozen dataclass and is
bad practice regardless: a level that changes underneath an event that already
cited it is precisely the defect this module's package docstring is about.

Instead the state keeps a :class:`_Bucket` per distinct level price and
materialises :class:`LiquidityLevel` objects in :meth:`finalize`. The quantities
that must be frozen at creation -- ``touch_count`` and ``strength`` -- are read
off the touch index when the bucket is created and stored there, so they are the
same numbers the batch path computes. Bounding: one bucket per distinct level
price (~13k per year of 5m), and the swing references inside them are a subset of
the swing list already retained.
"""

from __future__ import annotations

import json
from bisect import bisect_left, insort
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence

from app.schemas.market_data import CandleData, Timeframe

from . import (
    LiquidityLevel,
    MarketStructureResult,
    StructureEvent,
    SwingPoint,
)
from .analysis import (
    LEVEL_CLUSTER_TOLERANCE,
    MIN_TOUCHES,
    SWING_LOOKBACK_DEFAULT,
    _label_for,
    _sequence_state,
    _swing_state,
    regime_from_closes,
)

#: Trailing closes the regime classifier reads. Matches the ``window`` default of
#: :func:`classify_candles_as_regime`; carried so a segment boundary cannot
#: change the label.
REGIME_WINDOW = 20

#: Bumped when the *shape* of a checkpoint changes such that an older one cannot
#: be read. Carried in every payload so a resume against a stale checkpoint fails
#: loudly rather than silently misreading it.
STATE_SCHEMA_VERSION = 1

#: Fixed decimal places a level price is quantised to, matching the batch
#: implementation's bucket key. A cent grid is what makes the clustering key a
#: real dict key rather than a search over a tolerance band.
PRICE_QUANT = Decimal("0.01")


# ---------------------------------------------------------------------------
# Cumulative touch index
# ---------------------------------------------------------------------------


class TouchIndex:
    """Running count of bars that reached a price, foldable across segments.

    Answers, for a price ``P``, how many of the bars added so far *reached* it --
    ``high >= P`` when ``above=True``, ``low <= P`` when ``False``. Exact
    :class:`~decimal.Decimal` arithmetic: a float would miscount on the cent-grid
    boundaries that level prices sit on, and a miscounted touch count is a
    miscounted level.

    A sorted list of distinct prices seen so far, plus a Fenwick tree of counts
    over it. :meth:`add_many` folds in one segment's bars by merging them into
    that sorted set, which is what makes the index incremental without retaining
    a single bar.
    """

    __slots__ = ("_above", "_values", "_counts", "_tree", "_total")

    def __init__(self, *, above: bool) -> None:
        self._above = above
        self._values: list[Decimal] = []
        self._counts: list[int] = []
        self._tree: list[int] = []
        self._total = 0

    # -- queries ------------------------------------------------------------

    def reached(self, price: Decimal) -> int:
        """Bars added so far that reached ``price`` in this index's direction."""
        if not self._values:
            return 0
        at = bisect_left(self._values, price)
        if self._above:
            # Prices at or above ``price``: everything less the bars strictly
            # below it, and ``at`` is exactly how many values are below.
            return self._total - self._prefix_sum(at)
        # Mirrored: at or below ``price`` is the prefix ending just past the last
        # value that is <= price.
        if at < len(self._values) and self._values[at] == price:
            at += 1
        return self._prefix_sum(at)

    # -- updates ------------------------------------------------------------

    def add_many(self, prices: Iterable[Decimal]) -> None:
        """Fold one segment's bar prices into the index.

        Merged as a batch rather than incremented one bar at a time because the
        coordinate set is sorted: a new price can land anywhere in it, and a
        Fenwick tree indexed by value would need every node from there upward
        adjusted. Rebuilding once per segment is linear in the number of
        *distinct* prices -- bounded by the cent grid, not by the bar count.
        """
        incoming: dict[Decimal, int] = {}
        total = self._total
        for price in prices:
            incoming[price] = incoming.get(price, 0) + 1
            total += 1
        if not incoming:
            return

        additions = sorted(incoming.items())
        old_values = self._values
        old_counts = self._counts
        old_len = len(old_values)

        values: list[Decimal] = []
        counts: list[int] = []
        # A plain two-pointer merge of the two sorted sequences. Written out
        # step by step rather than as a fused "walk and maybe merge" loop:
        # the fused version has three branches that each have to advance
        # *both* lists, and getting one of them to advance only one desynchronises
        # the key/count pairing -- which is silent, because a misaligned Fenwick
        # tree still answers queries, just the wrong ones.
        a = 0  # cursor into old_values
        b = 0  # cursor into additions
        while a < old_len and b < len(additions):
            existing = old_values[a]
            fresh, count = additions[b]
            if existing < fresh:
                values.append(existing)
                counts.append(old_counts[a])
                a += 1
            elif fresh < existing:
                values.append(fresh)
                counts.append(count)
                b += 1
            else:
                values.append(existing)
                counts.append(old_counts[a] + count)
                a += 1
                b += 1
        while a < old_len:
            values.append(old_values[a])
            counts.append(old_counts[a])
            a += 1
        while b < len(additions):
            fresh, count = additions[b]
            values.append(fresh)
            counts.append(count)
            b += 1

        self._values = values
        self._counts = counts
        self._total = total
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        """Fenwick tree over ``_counts``, built in linear time.

        The standard build: seed the node, then push it up to its parent. Building
        by repeated ``add`` instead would be O(n log n) and, at a few thousand
        distinct prices per segment across a year of 5m, that difference is the
        whole running time of this class.
        """
        counts = self._counts
        size = len(counts)
        tree = [0] * (size + 1)
        for position in range(1, size + 1):
            tree[position] += counts[position - 1]
            parent = position + (position & -position)
            if parent <= size:
                tree[parent] += tree[position]
        self._tree = tree

    def _prefix_sum(self, count: int) -> int:
        """Total over the first ``count`` values."""
        tree = self._tree
        total = 0
        while count > 0:
            total += tree[count]
            count -= count & -count
        return total

    # -- persistence --------------------------------------------------------

    def to_payload(self) -> dict:
        return {
            "above": self._above,
            "values": [str(value) for value in self._values],
            "counts": list(self._counts),
            "total": self._total,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> TouchIndex:
        index = cls(above=bool(payload["above"]))
        index._values = [Decimal(text) for text in payload["values"]]
        index._counts = [int(value) for value in payload["counts"]]
        index._total = int(payload["total"])
        index._rebuild_tree()
        return index

    # -- diagnostics --------------------------------------------------------

    @property
    def distinct_prices(self) -> int:
        return len(self._values)

    @property
    def total_bars(self) -> int:
        return self._total


# ---------------------------------------------------------------------------
# Liquidity buckets
# ---------------------------------------------------------------------------


@dataclass
class _Bucket:
    """One level price and the swings confirmed on it.

    ``price`` is fixed by the first swing, permanently. ``touches`` and
    ``strength`` are read off the touch index when the bucket is *created* and
    never recomputed: they are quantities at the creation bar, and a running
    total would rank levels by how long the sample is rather than how strong
    they are.
    """

    kind: str
    price: Decimal
    swings: list[SwingPoint]
    touches: int
    strength: float

    @property
    def creation_index(self) -> int:
        return self.swings[0].confirmation_index

    @property
    def level_type(self) -> str:
        return "swing_high" if self.kind == "high" else "swing_low"


# ---------------------------------------------------------------------------
# Structure state
# ---------------------------------------------------------------------------


class StructureState:
    """Causal market-structure state that survives a segment boundary.

    Call :meth:`observe` with candles in ascending, contiguous bar order. A
    segment boundary is a memory-management boundary and nothing else.

    There is deliberately no ``reset``. A reset that callers can reach for is a
    reset that eventually gets called at the start of every segment, at which
    point the segmented run quietly stops matching the whole-series run while both
    still produce plausible-looking output. :meth:`observe` instead *requires*
    contiguity: a segment that does not begin where the last one ended is a data
    gap, and accepting one would put a hole in the carried state that nothing
    downstream could detect.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: Timeframe,
        lookback: int = SWING_LOOKBACK_DEFAULT,
        *,
        search_window: int = 5,
        shift_window: int = 2,
    ) -> None:
        if lookback < 1:
            raise ValueError(f"lookback must be >= 1, got {lookback}")
        self.symbol = symbol
        self.timeframe = timeframe
        self.lookback = lookback
        self.search_window = search_window
        self.shift_window = shift_window

        self.swings: list[SwingPoint] = []
        self.events: list[StructureEvent] = []
        self._buckets: list[_Bucket] = []
        #: ``(kind, quantised price) -> bucket position``. A swing joins the
        #: earliest-created bucket whose price is in range, which is what the
        #: batch path's "first match in creation order" scan resolves to.
        self._bucket_by_key: dict[tuple[str, Decimal], int] = {}
        #: The same prices as ``_bucket_by_key`` keys, sorted, per swing kind, so
        #: the tolerance window is a range lookup rather than a scan of every
        #: bucket created so far. ``insort`` rather than a rebuild per swing:
        #: one memmove of ~13k pointers is cheaper than the scan it replaces.
        self._bucket_prices: dict[str, list[Decimal]] = {"high": [], "low": []}

        self._highs = TouchIndex(above=True)
        self._lows = TouchIndex(above=False)

        #: Bars needed to confirm a swing: ``2 * lookback + 1``, and no more.
        self._window: list[CandleData] = []
        self._next_index = 0

        self._range_low: Decimal | None = None
        self._range_high: Decimal | None = None
        self._closes: list[float] = []

        #: Open time of the last bar consumed, so a gap between segments is
        #: rejected rather than silently producing a state with a hole in it.
        self._last_open_time: datetime | None = None
        self._base: datetime | None = None

        self._pending_events: list[StructureEvent] = []

    # -- ingestion ----------------------------------------------------------

    def observe(self, candles: Sequence[CandleData]) -> list[StructureEvent]:
        """Consume ``candles`` and return the structure events they confirmed.

        The returned events are also retained, because
        :func:`analyze_market_structure` returns the whole set. Callers wanting
        only the incremental output can ignore the retained list.
        """
        if not candles:
            return []
        if self._last_open_time is None:
            self._base = candles[0].open_time
        elif candles[0].open_time <= self._last_open_time:
            # Overlapping or reordered, not merely a gap: a repeated bar would be
            # observed twice and double-counted against the touch index.
            raise ValueError(
                f"segment starts at {candles[0].open_time}, at or before the previous "
                f"segment's last bar ({self._last_open_time}); segments must be "
                f"contiguous and strictly ascending"
            )
        for candle in candles:
            self._observe_one(candle)
            self._last_open_time = candle.open_time
        fresh = self._pending_events
        self._pending_events = []
        # The batch path generates labels, then BOS, then structure shifts in
        # three separate passes and finally sorts the concatenation by
        # ``(confirmation_index, index)`` with a *stable* sort. Reproducing that
        # global sort incrementally means ordering each drain by the same key --
        # and Python's sort is stable, so events emitted in the order
        # labels -> BOS -> shifts keep that relative order on a tie, exactly as
        # the batch concatenation does.
        #
        # Without this, a structure shift -- which is knowable only once the swing
        # *after* its `curr` confirms -- is emitted several bars after events whose
        # confirmation index is larger, and the two paths' event lists diverge in
        # order while containing identical events.
        fresh.sort(key=lambda event: (event.confirmation_index, event.index))
        self.events.extend(fresh)
        return fresh

    def _observe_one(self, candle: CandleData) -> None:
        index = self._next_index

        if self._range_low is None or candle.low < self._range_low:
            self._range_low = candle.low
        if self._range_high is None or candle.high > self._range_high:
            self._range_high = candle.high

        # One bar, one insert. `add_many` on a single-element list is the same
        # call the merge uses, so there is no second code path to keep correct.
        self._highs.add_many((candle.high,))
        self._lows.add_many((candle.low,))

        self._window.append(candle)
        if len(self._window) > 2 * self.lookback + 1:
            del self._window[0 : len(self._window) - (2 * self.lookback + 1)]

        self._closes.append(float(candle.close))
        if len(self._closes) > REGIME_WINDOW:
            del self._closes[0 : len(self._closes) - REGIME_WINDOW]

        self._confirm_swings(index, candle)
        self._next_index = index + 1

    def _confirm_swings(self, index: int, confirming: CandleData) -> None:
        """Emit the swings whose right-hand side the bar just completed.

        A pivot at ``i`` needs bars ``i - lookback .. i + lookback``; bar ``index``
        completes the window for ``i = index - lookback``. The carried window
        holds ``2 * lookback + 1`` bars, so the window is complete by
        construction.

        The lower bound ``i >= lookback`` is *absolute*, not relative to the
        segment. That mirrors the batch detector's ``range(lookback, ...)`` and
        is what stops the first bars of the dataset producing pivots with no
        left-hand context -- including at the very first segment, where a
        segment-relative bound would wrongly begin producing swings immediately.

        ``confirmation_time`` is the *confirming* bar's close: knowledge arrives
        when the bar that proves the pivot closes, which is ``index``, not the
        pivot's own bar.
        """
        lookback = self.lookback
        pivot_index = index - lookback
        if pivot_index < lookback:
            return
        window = self._window
        if len(window) < 2 * lookback + 1:
            return
        pivot = window[lookback]
        previous = window[:lookback]
        following = window[lookback + 1 :]

        if pivot.high > max(c.high for c in previous) and pivot.high > max(
            c.high for c in following
        ):
            self._add_swing(
                SwingPoint(
                    index=pivot_index,
                    timestamp=pivot.open_time,
                    price=pivot.high,
                    kind="high",
                    confirmation_index=index,
                    confirmation_time=confirming.close_time,
                )
            )
        if pivot.low < min(c.low for c in previous) and pivot.low < min(
            c.low for c in following
        ):
            self._add_swing(
                SwingPoint(
                    index=pivot_index,
                    timestamp=pivot.open_time,
                    price=pivot.low,
                    kind="low",
                    confirmation_index=index,
                    confirmation_time=confirming.close_time,
                )
            )

    def _add_swing(self, swing: SwingPoint) -> None:
        """Record a confirmed swing and everything that becomes true because of it.

        The emission order is load-bearing. The batch path generates all HH/HL
        labels, then all BOS, then all structure shifts, and finally sorts by
        ``(confirmation_index, index)`` with a *stable* sort -- so for a given
        confirmation bar the order is labels, then BOS, then shifts, each in
        swing order. Reproducing it is what makes the segmented event list equal
        to the batch one element for element rather than as a set, and the order
        is observable output: a report that lists two events of one bar the other
        way round is a different report.
        """
        position = len(self.swings)
        self.swings.append(swing)

        labels: list[StructureEvent] = []
        bos: list[StructureEvent] = []
        shifts: list[StructureEvent] = []

        if position >= 1:
            previous = self.swings[position - 1]
            if previous.kind == swing.kind:
                state = _swing_state(swing, previous)
                labels.append(
                    StructureEvent(
                        index=swing.index,
                        timestamp=swing.timestamp,
                        price=swing.price,
                        event_type=state,  # type: ignore[arg-type]
                        confirmation_index=swing.confirmation_index,
                        source_swing_idx=swing.index,
                        previous_state=(
                            _swing_state(previous, self.swings[position - 2])
                            if position >= 2
                            else None
                        ),
                        new_state=state,
                        direction="neutral",
                    )
                )

        if position >= 2:
            event = self._detect_bos_at(position)
            if event is not None:
                bos.append(event)

        # The batch loop's `i` is the position of the swing that confirms the
        # reversal, so `i` is the position just appended -- one ahead of `curr`.
        if position >= self.shift_window + 1:
            event = self._detect_shift_at(position)
            if event is not None:
                shifts.append(event)

        self._pending_events.extend(labels)
        self._pending_events.extend(bos)
        self._pending_events.extend(shifts)

        self._cluster(swing)

    def _detect_bos_at(self, position: int) -> StructureEvent | None:
        """The batch ``_detect_bos`` loop body, for one swing position.

        Scans backwards over at most ``search_window`` swings and stops at the
        *first* qualifying one. Scanning forward, or keeping the deepest breach,
        would cite a different level whenever two are in range -- and
        ``broken_level`` is part of the event's output.
        """
        current = self.swings[position]
        for candidate in range(max(0, position - self.search_window), position):
            reference = self.swings[candidate]
            if reference.kind == current.kind:
                continue
            breached = (current.kind == "high" and current.price > reference.price) or (
                current.kind == "low" and current.price < reference.price
            )
            if not breached:
                continue
            penetration = (
                current.price - reference.price
                if current.kind == "high"
                else reference.price - current.price
            )
            return StructureEvent(
                index=current.index,
                timestamp=current.timestamp,
                price=current.price,
                event_type="BOS",
                # A high breaking a prior high is bullish in description only;
                # the label carries no trading instruction.
                direction="long" if current.kind == "high" else "short",
                confirmation_index=max(
                    current.confirmation_index, reference.confirmation_index
                ),
                broken_level=reference.price,
                penetration=penetration,
                source_swing_idx=reference.index,
            )
        return None

    def _detect_shift_at(self, position: int) -> StructureEvent | None:
        """The batch ``_detect_structure_shift`` loop body, for one ``curr``.

        Mirrors the batch loop's indices exactly: for its ``i``, ``prior`` is
        ``swings[i - window - 1 : i - 1]`` and ``curr`` is ``swings[i - 1]``. This
        is called with the batch loop's ``i`` -- the position of the swing that
        *followed* ``curr``, since a shift is only knowable once the reversing
        swing has confirmed.
        """
        window = self.shift_window
        i = position
        if i < window + 1:
            return None
        start = i - window - 1
        prior = self.swings[start : i - 1]
        curr_position = i - 1
        if len(prior) < window or any(s.kind != prior[0].kind for s in prior):
            return None
        current = self.swings[curr_position]
        prior_state = _sequence_state(prior)
        current_state = (
            _sequence_state(prior[1:] + [current])
            if window > 1
            else _label_for(current, prior[0])
        )
        if current_state is None or prior_state is None or current_state == prior_state:
            return None
        return StructureEvent(
            index=current.index,
            timestamp=current.timestamp,
            price=current.price,
            event_type="structure_shift",
            direction="long" if current_state == "up" else "short",
            confirmation_index=current.confirmation_index,
            previous_state=prior_state,
            new_state=current_state,
            source_swing_idx=self.swings[start].index,
        )

    # -- liquidity ----------------------------------------------------------

    def _cluster(self, swing: SwingPoint) -> None:
        """Attach a confirmed swing to its level, creating a bucket if none matches.

        The match test is ``abs(p - b) <= tolerance * b``, relative to the
        *bucket's* price, so the window of bucket prices a swing ``p`` may join is
        ``p / (1 + tol) .. p / (1 - tol)`` -- derived, not symmetric around the
        swing, and not ``p +/- tol * p``.

        The bucket's own price is *not* the window's centre and using
        ``p * (1 +/- tol)`` would silently shift which swings cluster together at
        the boundary. Both candidate lists below are therefore bisected against
        the derived bounds and each candidate re-checked with the original
        comparison, so the index only ever decides which candidates are
        considered.
        """
        quantised = swing.price.quantize(PRICE_QUANT)
        position = self._find_bucket(swing)
        if position is None:
            self._create_bucket(swing, quantised)
        else:
            # A swing joining an existing level. The level's price, touch count
            # and strength were fixed at its creation and are not recomputed; only
            # its provenance grows, which `swing_count_at` reads causally.
            self._buckets[position].swings.append(swing)

    def _find_bucket(self, swing: SwingPoint) -> int | None:
        """Index of the bucket ``swing`` joins, or ``None``.

        "First match wins", which the batch path's linear scan resolves as the
        *earliest created* bucket in range. Buckets are appended in swing order,
        so the lowest position among matches is the earliest -- which is the
        correct rule whether or not two candidates share a price.

        Selection is by price window, not by scanning every bucket: at 72k
        confirmed swings per year of 5m against ~13k buckets, a full scan is
        ~9e8 comparisons, and it is the same quadratic the batch path was
        measured paying before its bucket lookup was indexed.
        """
        prices = self._bucket_prices.get(swing.kind)
        if not prices:
            return None
        tolerance = float(LEVEL_CLUSTER_TOLERANCE)
        price = float(swing.price)
        low = Decimal(repr(price / (1.0 + tolerance)))
        high = Decimal(repr(price / (1.0 - tolerance)))
        first = bisect_left(prices, low)
        last = bisect_left(prices, high)
        best: int | None = None
        for slot in range(first, last):
            candidate = prices[slot]
            # Re-checked with the original comparison so the index only ever
            # decides *which* candidates are considered; the two cannot then
            # disagree about a boundary case.
            if abs(price - float(candidate)) > tolerance:
                continue
            position = self._bucket_by_key[(swing.kind, candidate)]
            if best is None or position < best:
                best = position
        return best

    def _create_bucket(self, swing: SwingPoint, quantised: Decimal) -> None:
        """Start a level at ``swing``, freezing its creation-bar quantities."""
        creation_index = swing.confirmation_index
        touches = (
            self._highs.reached(quantised)
            if swing.kind == "high"
            else self._lows.reached(quantised)
        )
        # Normalised against the history available at creation, so the
        # denominator grows with the sample rather than with the whole series.
        strength = min(
            1.0, touches / max(MIN_TOUCHES, (creation_index + 1) // 10)
        )
        self._bucket_by_key[(swing.kind, quantised)] = len(self._buckets)
        insort(self._bucket_prices[swing.kind], quantised)
        self._buckets.append(
            _Bucket(
                kind=swing.kind,
                price=quantised,
                swings=[swing],
                touches=touches,
                strength=strength,
            )
        )

    # -- output -------------------------------------------------------------

    def regime(self) -> str:
        """Regime from the carried trailing closes.

        Delegates to the batch classifier so the thresholds cannot drift between
        the two paths. The window it needs is at most ``REGIME_WINDOW`` closes,
        which is why that many are carried.
        """
        if not self._closes:
            return "UNKNOWN"
        return regime_from_closes(self._closes)

    def levels(self) -> list[LiquidityLevel]:
        """Materialise the levels, in creation order.

        The batch path filters on ``MIN_TOUCHES`` and sorts by creation index;
        both happen here so that a bucket which never reached the threshold is
        retained in state (a later swing may raise it) but never published.
        """
        out: list[LiquidityLevel] = []
        for bucket in self._buckets:
            if bucket.touches < MIN_TOUCHES:
                continue
            members = bucket.swings
            first = members[0]
            out.append(
                LiquidityLevel(
                    price=bucket.price,
                    level_type=bucket.level_type,  # type: ignore[arg-type]
                    origin="swing",
                    first_seen=first.timestamp,
                    last_seen=first.timestamp,
                    creation_index=first.confirmation_index,
                    creation_time=first.confirmation_time,
                    touch_count=bucket.touches,
                    strength=bucket.strength,
                    source_swing_indices=(first.index,),
                    swing_confirmations=tuple(
                        (swing.index, swing.confirmation_index) for swing in members
                    ),
                )
            )
        out.sort(key=lambda level: level.creation_index)
        return out

    def result(self) -> MarketStructureResult:
        """The whole-sample view, matching ``analyze_market_structure``'s output."""
        return MarketStructureResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            swings=list(self.swings),
            events=list(self.events),
            liquidity_levels=self.levels(),
            recent_range=(self._range_low, self._range_high)
            if self._range_low is not None and self._range_high is not None
            else None,
            current_regime=self.regime(),
            as_of_index=self._next_index - 1 if self._next_index else None,
        )
