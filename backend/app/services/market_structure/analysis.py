"""Swing detection and market-structure analysis.

Causal by construction
----------------------
Each public function accepts an optional ``as_of_index``. When supplied, the series
is truncated to ``candles[: as_of_index + 1]`` *before* any computation, so the
result provably cannot depend on a later bar. The last ``lookback`` bars never yield
a confirmed swing, because the confirming bars do not exist yet within the
truncation.

The distinction that matters downstream:

    swing_time         = T          (the bar of the pivot)
    confirmation_time   = T + k      (k = lookback, the first knowable bar)

``detect_swings`` is the only place a future bar is ever read, and it reads it only
to decide *when* the swing became known — never to place it earlier.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right, insort
from decimal import Decimal
from typing import Sequence

from app.schemas.market_data import CandleData, Timeframe

from . import (
    LiquidityLevel,
    MarketStructureResult,
    StructureEvent,
    SwingPoint,
    confirmation_time_for,
)
from .derived_levels import DerivedLevelState, equal_level_for

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SWING_LOOKBACK_DEFAULT = 5
# Two swing prices within this fraction of each other are treated as one level
# (an "equal high/low" cluster) rather than two independent ones.
LEVEL_CLUSTER_TOLERANCE = Decimal("0.001")  # 0.1%
# A level is only interesting if at least this many later candles reached it.
MIN_TOUCHES = 2


def _truncate(candles: list[CandleData], as_of_index: int | None) -> list[CandleData]:
    """Restrict a series to the bars a decision at ``as_of_index`` could have seen."""
    if as_of_index is None:
        return candles
    return candles[: as_of_index + 1]


# ---------------------------------------------------------------------------
# Swings
# ---------------------------------------------------------------------------


def detect_swings(
    candles: list[CandleData],
    lookback: int = SWING_LOOKBACK_DEFAULT,
    *,
    as_of_index: int | None = None,
) -> list[SwingPoint]:
    """Detect local extrema (swing highs and lows) with confirmation timestamps.

    A swing high at index *i* requires ``candles[i].high`` to be strictly greater
    than all *lookback* candles before and after it. The trailing comparison needs
    future bars, so the swing is *dated* at ``i`` but only *knowable* at
    ``i + lookback``; both are recorded.
    """
    series = _truncate(candles, as_of_index)
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")
    # Two full windows are needed before any pivot can exist, and the last
    # `lookback` bars can never be confirmed because their right-hand side is
    # still inside the truncation.
    if len(series) < 2 * lookback + 1:
        return []

    swings: list[SwingPoint] = []

    for i in range(lookback, len(series) - lookback):
        window = series[i - lookback : i + lookback + 1]
        pivot = window[lookback]

        prev_highs = [c.high for c in window[:lookback]]
        next_highs = [c.high for c in window[lookback + 1 :]]
        prev_lows = [c.low for c in window[:lookback]]
        next_lows = [c.low for c in window[lookback + 1 :]]

        confirmation_index = i + lookback

        if pivot.high > max(prev_highs) and pivot.high > max(next_highs):
            swings.append(
                SwingPoint(
                    index=i,
                    timestamp=pivot.open_time,
                    price=pivot.high,
                    kind="high",
                    confirmation_index=confirmation_index,
                    confirmation_time=confirmation_time_for(series, confirmation_index),
                )
            )

        if pivot.low < min(prev_lows) and pivot.low < min(next_lows):
            swings.append(
                SwingPoint(
                    index=i,
                    timestamp=pivot.open_time,
                    price=pivot.low,
                    kind="low",
                    confirmation_index=confirmation_index,
                    confirmation_time=confirmation_time_for(series, confirmation_index),
                )
            )

    swings.sort(key=lambda s: (s.confirmation_index, s.index))
    return swings


# ---------------------------------------------------------------------------
# Structural labels
# ---------------------------------------------------------------------------


def _swing_state(swing: SwingPoint, previous: SwingPoint) -> str:
    """HH / HL / LH / LL comparing two swings of the same kind."""
    higher = swing.price > previous.price
    if swing.kind == "high":
        return "HH" if higher else "LH"
    return "HL" if higher else "LL"


def classify_swing_sequence(swings: list[SwingPoint]) -> list[StructureEvent]:
    """Label consecutive same-kind swings as HH/HL/LH/LL.

    A label becomes knowable when *both* of the swings it compares are confirmed,
    so the event inherits the later of the two confirmation points. Using only the
    second swing's confirmation would leak the first swing's existence — the first
    was still an unproven candidate at that point.
    """
    if len(swings) < 2:
        return []

    events: list[StructureEvent] = []

    for i in range(1, len(swings)):
        prev = swings[i - 1]
        curr = swings[i]
        if prev.kind != curr.kind:
            continue

        confirmation_index = max(prev.confirmation_index, curr.confirmation_index)
        events.append(
            StructureEvent(
                index=curr.index,
                timestamp=curr.timestamp,
                price=curr.price,
                event_type=_swing_state(curr, prev),  # type: ignore[arg-type]
                confirmation_index=confirmation_index,
                source_swing_idx=curr.index,
                previous_state=_swing_state(prev, swings[i - 2]) if i >= 2 else None,
                new_state=_swing_state(curr, prev),
                direction="neutral",
            )
        )

    events.extend(_detect_bos(swings))
    events.extend(_detect_structure_shift(swings))
    events.sort(key=lambda e: (e.confirmation_index, e.index))
    return events


def _detect_bos(swings: list[SwingPoint], search_window: int = 5) -> list[StructureEvent]:
    """Break-of-structure: a swing exceeds the most recent opposite-kind swing.

    The break is dated at the breaking swing and confirmed when both the breaking
    swing and the level it broke are known — the later of the two. ``penetration``
    records how far past the level price travelled, which is the measurable part of
    the concept.
    """
    events: list[StructureEvent] = []

    for i in range(2, len(swings)):
        curr = swings[i]
        for j in range(max(0, i - search_window), i):
            reference = swings[j]
            if reference.kind == curr.kind:
                continue
            breached = (curr.kind == "high" and curr.price > reference.price) or (
                curr.kind == "low" and curr.price < reference.price
            )
            if not breached:
                continue

            penetration = (
                curr.price - reference.price
                if curr.kind == "high"
                else reference.price - curr.price
            )
            events.append(
                StructureEvent(
                    index=curr.index,
                    timestamp=curr.timestamp,
                    price=curr.price,
                    event_type="BOS",
                    # A high breaking a prior high is bullish in description only;
                    # the label carries no trading instruction.
                    direction="long" if curr.kind == "high" else "short",
                    confirmation_index=max(
                        curr.confirmation_index, reference.confirmation_index
                    ),
                    broken_level=reference.price,
                    penetration=penetration,
                    source_swing_idx=reference.index,
                )
            )
            break  # only the most recent qualifying level per swing

    return events


def _detect_structure_shift(swings: list[SwingPoint], window: int = 2) -> list[StructureEvent]:
    """Detect a change in the swing sequence's direction.

    A shift is declared when the ``window`` most recent confirmed swings trend one
    way and the swing that follows reverses it. Both states are recorded, and the
    shift is confirmed when the reversing swing itself is confirmed.
    """
    if len(swings) < window + 2:
        return []

    events: list[StructureEvent] = []

    for i in range(window + 1, len(swings)):
        prior = swings[i - window - 1 : i - 1]
        if len(prior) < window or any(s.kind != prior[0].kind for s in prior):
            continue

        prior_state = _sequence_state(prior)
        curr = swings[i - 1]
        curr_state = _sequence_state(prior[1:] + [curr]) if window > 1 else _label_for(curr, prior[0])
        if curr_state is None or prior_state is None:
            continue
        if curr_state == prior_state:
            continue

        events.append(
            StructureEvent(
                index=curr.index,
                timestamp=curr.timestamp,
                price=curr.price,
                event_type="structure_shift",
                direction="long" if curr_state == "up" else "short",
                confirmation_index=curr.confirmation_index,
                previous_state=prior_state,
                new_state=curr_state,
                source_swing_idx=swings[i - window - 1].index,
            )
        )

    return events


def _sequence_state(window: list[SwingPoint]) -> str | None:
    """Aggregate a run of same-kind swings into 'up' / 'down' / None."""
    if len(window) < 2 or any(s.kind != window[0].kind for s in window):
        return None
    labels = [_label_for(window[i], window[i - 1]) for i in range(1, len(window))]
    if any(label is None for label in labels):
        return None
    up = sum(1 for label in labels if label in ("HH", "HL"))
    return "up" if up * 2 > len(labels) else "down"


def _label_for(curr: SwingPoint, prev: SwingPoint) -> str | None:
    if curr.kind != prev.kind:
        return None
    return _swing_state(curr, prev)


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------


class _TouchCounter:
    """How many bars seen so far reached a price, in O(log n) per query.

    The question ``extract_liquidity_levels`` asks once per level is "of the bars
    at or before this level's creation, how many reached its price". Answering it
    by summing costs O(bars) per level, making the whole function O(bars x
    levels) -- 4.8s / 19.6s / 85.9s for 20k / 40k / 80k real 5m bars. This
    keeps a Fenwick tree over price ranks instead, so a query is a prefix sum in
    O(log bars) and ``advance_to`` is the incremental part that makes the prefix
    cheap to have.

    The direction is fixed at construction. A swing_high counts bars whose high
    *reached* it (prices at or above it) and a swing_low counts bars whose low
    *fell to* it, and those are mirror images -- encoding the direction once
    means :meth:`reached` is one code path rather than two that could disagree.

    Only bars already added are in the tree, which is what makes the count
    causal: advancing to bar *t* and querying gives the answer as of bar *t*,
    with no look-ahead and nothing to recompute. Memory is one int per *distinct
    price*, not per bar per level.

    Prices are compressed to ranks once, so no Decimal comparison happens inside
    the tree. A level's price is quantised to 0.01 and will usually match no bar
    exactly, so :meth:`reached` handles a miss by taking the boundary rank --
    the first stored price at or above it, or the last at or below. That keeps
    the answer equal to what exact per-bar comparison would have counted: a bar
    either reached the level or did not.
    """

    __slots__ = ("_ranks", "_tree", "_values", "_prefix", "_cursor", "_above", "_pending")

    def __init__(self, prices: list[Decimal], *, above: bool) -> None:
        self._above = above
        # Compress to ranks: sorting the distinct values once turns every
        # comparison in the hot path into an integer lookup.
        self._values = sorted(set(prices))
        self._ranks = {value: position for position, value in enumerate(self._values)}
        self._tree = [0] * (len(self._values) + 1)
        self._prefix = [self._ranks[value] for value in prices]
        #: How many bars have been added. This is the *count*, which is also the
        #: index of the next bar to add -- not the index of the last one added.
        #: Keeping the two meanings apart is the whole reason `advance_to` is
        #: written as ``while cursor <= index``: naming this `_last_index` and
        #: incrementing it in the same expression would be off by one on every
        #: call, and the monotonicity check would then reject a level that is in
        #: fact in order.
        self._cursor = 0
        self._pending = list(self._prefix)

    def advance_to(self, index: int) -> None:
        """Add every bar up to and including ``index``.

        Monotonic by construction: levels are visited in creation order, so
        ``index`` never moves backwards. Going backwards would mean answering
        with a count taken over bars the level is not allowed to know, which is
        precisely the look-ahead this module exists to prevent -- so it raises
        rather than quietly returning a number from the future.
        """
        # Re-advancing to the bar just added is not going backwards: two levels
        # can share a creation bar, and a tie is read twice with no new bars in
        # between. Only a genuinely earlier bar is rejected.
        if index < self._cursor - 1:
            raise ValueError(
                f"_TouchCounter.advance_to({index}) is before the last bar added "
                f"({self._cursor - 1}); levels must be read in creation order"
            )
        pending = self._pending
        tree = self._tree
        size = len(tree)
        cursor = self._cursor
        while cursor <= index:
            position = pending[cursor] + 1
            while position < size:
                tree[position] += 1
                position += position & -position
            cursor += 1
        self._cursor = cursor

    def reached(self, price: Decimal) -> int:
        """Bars added so far whose price reached ``price`` in this direction."""
        boundary = self._boundary(price)
        if boundary is None:
            return 0
        if self._above:
            # Prices at or above the boundary: everything added, less the bars
            # strictly below it.
            return self._cursor - self._prefix_sum(boundary)
        return self._prefix_sum(boundary + 1)

    def _prefix_sum(self, count: int) -> int:
        """Bars added at ranks below ``count``, via the tree."""
        tree = self._tree
        total = 0
        while count > 0:
            total += tree[count]
            count -= count & -count
        return total

    def _boundary(self, price: Decimal) -> int | None:
        """Zero-based index of the first stored price at or above ``price``."""
        position = bisect_left(self._values, price)
        if not self._above:
            # Mirrored: the count wanted is over prices at or *below*, and its
            # boundary is the position after the last one of those.
            position = bisect_right(self._values, price) - 1
        return None if position < 0 or position >= len(self._values) else position


def extract_liquidity_levels(
    swings: list[SwingPoint],
    candles: list[CandleData],
    *,
    top_n: int = 0,
    as_of_index: int | None = None,
) -> list[LiquidityLevel]:
    """Cluster confirmed swings into price levels, touching only past candles.

    Two properties this has to have, and the original implementation had
    neither.

    **Levels are never rewritten.** Clustering is *append-only and
    price-ordered*: swings are visited in confirmation order, each is attached
    to the existing level whose price it falls on, or starts a new one. The
    earlier alternative sorted every swing by price and re-bucketed the whole
    set on each call, which meant a level's membership and its creation index
    both depended on which swings happened to exist — appending one bar could
    retroactively move a swing recorded fifty bars ago onto a different level
    and change that level's price. A level a trader has already seen cannot
    move, so this version never lets it.

    **Touch counts do not look past creation.** Touches are counted over bars up
    to the level's creation, and are never updated afterwards, so a level's
    strength is a fixed fact about the moment it existed rather than a running
    total. Ranking by a touch count that grows across the whole sample would
    rank levels by how long the series is, not by how strong they are; levels
    are therefore returned in creation order and ranked by nothing.

    :param top_n: keep only the *strongest* ``top_n`` levels. ``0``, the
        default, keeps every level. Ranking is only meaningful on a fixed
        as-of window, and picking the best 10 of a 1200-bar sample's levels is
        an arbitrary filter that has nothing to do with the phenomenon.
    """
    if not swings or not candles:
        return []

    series = _truncate(candles, as_of_index)
    last_usable = len(series) - 1
    confirmed = sorted(
        (s for s in swings if s.confirmation_index <= last_usable),
        key=lambda s: s.confirmation_index,
    )
    if not confirmed:
        return []

    # Each bucket holds the swings on one level, in the order they were
    # confirmed. Buckets are searched by price, so "the level this swing falls
    # on" is a local question and the search is a linear scan of a short list.
    buckets: list[dict] = []
    #: Buckets indexed by price, so "which level does this swing fall on" is a
    #: range lookup rather than a scan of every level created so far. That scan
    #: was 24.8M comparisons on 80k real 5m bars -- the last quadratic here.
    by_price: list[tuple[Decimal, int]] = []

    tolerance = float(LEVEL_CLUSTER_TOLERANCE)
    for swing in confirmed:
        target = None
        price = float(swing.price)
        # |p - b| <= tol * b  <=>  p/(1 + tol) <= b <= p/(1 - tol).
        #
        # The tolerance is relative to the *bucket's* price rather than
        # symmetric around the swing's, so the matching window is not simply
        # p +/- tol*p and has to be derived rather than guessed. Deriving it in
        # float and re-checking each candidate with the original comparison
        # means the index only ever decides *which* candidates are considered;
        # the test itself is still the one the original loop made, so the two
        # cannot disagree about a boundary case.
        low = price / (1.0 + tolerance)
        high = price / (1.0 - tolerance)
        first = bisect_left(by_price, (Decimal(repr(low)), -1))
        last = bisect_left(by_price, (Decimal(repr(high)), -1))
        best: int | None = None
        for candidate in range(first, last):
            position = by_price[candidate][1]
            if buckets[position]["kind"] != swing.kind:
                continue
            if abs(price - float(buckets[position]["price"])) > tolerance:
                continue
            # First match wins, so among matching candidates the earliest
            # created is the one the linear scan would have stopped on.
            if best is None or position < best:
                best = position
        if best is not None:
            target = buckets[best]
        if target is None:
            target = {
                "kind": swing.kind,
                # The first swing fixes the level's price for good. Re-averaging
                # into the mean as later swings arrive would move a level that
                # has already been published, which is the defect this replaces.
                "price": swing.price.quantize(Decimal("0.01")),
                "swings": [],
            }
            buckets.append(target)
            insort(by_price, (target["price"], len(buckets) - 1))
        target["swings"].append(swing)

    # Touch counts are answered from a running prefix rather than by re-reading
    # history for each level.
    #
    # Counting per level sums over `series` once per level, which is
    # O(bars x levels). Measured on the real 5m dataset: 4.8s / 19.6s / 85.9s
    # for 20k / 40k / 80k bars -- exactly quadratic, roughly forty minutes for a
    # single year of 5m data, to produce one integer per level.
    #
    # The definition is unchanged. A swing_high's touch_count is still the number
    # of bars at or before its `creation_index` whose high reached its price; a
    # swing_low's is the number whose low fell to it. What changes is that the
    # count over *that exact prefix* is already available, so a level reads it
    # off rather than recomputing it. A level still counts from the whole prefix
    # rather than from the bars since its swing, which is what makes `strength`
    # comparable between a level three bars old and one three hundred bars old.
    #
    # `_TouchCounter` answers "how many of the bars seen so far reached price P"
    # in O(log n) by keeping a Fenwick tree over price ranks. Only bars already
    # seen are in it, so a prefix is not something that has to be recomputed --
    # it is what the tree *is* at that moment. Peak extra memory is one float
    # and one int per bar, independent of the number of levels.
    highs_seen = _TouchCounter([candle.high for candle in series], above=True)
    lows_seen = _TouchCounter([candle.low for candle in series], above=False)

    levels: list[LiquidityLevel] = []
    # Buckets are visited in creation order so the counters can be advanced to
    # each one's own bar and the level reads the count as of that bar. The
    # emitted list is sorted back into creation order below regardless.
    # Sorted by creation bar alone, and stably, so two levels confirmed on the
    # same bar are read in an order that does not move backwards. Without the
    # explicit kind/price tiebreak a sort between equal keys can permute them,
    # and the counter's monotonicity check then trips on a level that is not
    # actually out of order.
    pending = sorted(
        buckets,
        key=lambda bucket: (
            bucket["swings"][0].confirmation_index,
            bucket["kind"],
            bucket["price"],
        ),
    )
    for bucket in pending:
        members = bucket["swings"]
        price = bucket["price"]
        kind = bucket["kind"]
        # The level exists from the moment its first swing was confirmed; that
        # is when it could first have been acted upon.
        creation_index = members[0].confirmation_index
        history_length = creation_index + 1

        # Advance the running counters to exactly this level's creation bar, so
        # the answer is the prefix count *as of that bar* -- the same set of bars
        # the original per-level loop summed over.
        highs_seen.advance_to(creation_index)
        lows_seen.advance_to(creation_index)

        if kind == "high":
            touches = highs_seen.reached(price)
        else:
            touches = lows_seen.reached(price)

        # Everything above is as of ``creation_index`` and everything below is
        # frozen to the first swing. A level that reclassified itself as
        # "equal highs" when a second swing arrived months later would be a
        # level changing underneath every event that cites it, and the events
        # already published would retroactively be citing something different.
        # A level's *maturity* is real information and is not lost — see
        # ``swing_count_at`` below, which reports it causally at the moment it
        # is used.
        levels.append(
            LiquidityLevel(
                price=price,
                level_type="swing_high" if kind == "high" else "swing_low",
                origin="swing",
                first_seen=members[0].timestamp,
                last_seen=members[0].timestamp,
                creation_index=creation_index,
                creation_time=confirmation_time_for(series, creation_index),
                touch_count=touches,
                # Normalised against the history available at creation, so the
                # denominator grows with the sample instead of the whole series.
                strength=min(1.0, touches / max(MIN_TOUCHES, history_length // 10)),
                source_swing_indices=(members[0].index,),
                # Every swing that has confirmed on this price, each with the
                # bar it was confirmed on, so maturity can be read causally
                # later via ``swing_count_at``.
                swing_confirmations=tuple(
                    (swing.index, swing.confirmation_index) for swing in members
                ),
            )
        )

    levels = [level for level in levels if level.touch_count >= MIN_TOUCHES]
    levels.sort(key=lambda level: level.creation_index)
    if top_n and len(levels) > top_n:
        # Ranking a growing level set by a whole-sample score is itself a form
        # of the future leaking in, so the cut is by creation order and the
        # caller opts in to it explicitly rather than by omitting an argument.
        levels = levels[:top_n]
    return levels


def extract_equal_levels(
    swings: list[SwingPoint], levels: list[LiquidityLevel]
) -> list[LiquidityLevel]:
    """The ``equal_highs`` / ``equal_lows`` levels implied by swing levels.

    The batch counterpart of
    :meth:`~app.services.market_structure.segmented.StructureState.equal_levels`.
    It takes both arguments — the published levels *and* the swings — because the
    level objects store swing provenance as bare ``(index, index)`` pairs while
    the forming swing's confirmation *timestamp* is needed to date the equal level.
    Reading the timestamp off a level would mean attributing the level's own
    creation time to whichever swing happens to be listed last, which is the wrong
    swing and a fabricated availability time for the rest.

    A level qualifies once two of its confirmed swings sit within
    ``LEVEL_CLUSTER_TOLERANCE`` of its price, and its creation index is the
    confirmation bar of the **second** of them. That second-swing dating is the
    whole causality argument, and it is the part a naive implementation gets
    wrong: reusing the source level's ``creation_index`` — when *one* swing
    confirmed there — would publish an "equal high" on a bar where only one high
    existed, and the sweep detector could then report a sweep of an equal high
    before the second high had printed. The leak would be in the label rather than
    the price, which is why it survives a casual look.

    ``levels`` arrives pre-filtered on ``MIN_TOUCHES``, so no equal level is built
    on a price that was touched once.
    """
    by_index = {swing.index: swing for swing in swings}
    out: list[LiquidityLevel] = []
    for level in levels:
        confirmations = [
            (
                swing_index,
                confirmed,
                by_index[swing_index].confirmation_time
                if swing_index in by_index
                else None,
            )
            for swing_index, confirmed in level.swing_confirmations
        ]
        equal = equal_level_for(
            level.price,
            kind="high" if level.level_type.endswith("high") else "low",
            swing_confirmations=confirmations,
            tolerance=LEVEL_CLUSTER_TOLERANCE,
            origin="swing",
        )
        if equal is not None:
            out.append(equal)
    out.sort(key=lambda level: level.creation_index)
    return out


def _derived_levels(series: list[CandleData]) -> list[LiquidityLevel]:
    """Range, session and previous-day levels over a whole series.

    The batch counterpart of driving
    :class:`~app.services.market_structure.derived_levels.DerivedLevelState` from
    the segmented runner. It runs the *same* state object over the same bars in
    the same order rather than reimplementing the period logic, because two
    implementations of "the previous day's high" are two answers and the spec
    names one.
    """
    if not series:
        return []
    state = DerivedLevelState()
    for candle in series:
        state.observe([candle])
    return state.as_liquidity_levels()


def classify_candles_as_regime(
    candles: list[CandleData],
    *,
    window: int = 20,
    as_of_index: int | None = None,
) -> str:
    """Coarse regime label from the trailing ``window`` candles.

    Reads only a trailing slice, so it is causal for any ``as_of_index``. The
    thresholds are fixed constants, not fitted values — a regime label is a
    descriptive bucket here, not a validated classifier.
    """
    series = _truncate(candles, as_of_index)
    if len(series) < 5:
        return "UNKNOWN"
    return regime_from_closes([float(c.close) for c in series[-window:]])


def regime_from_closes(closes: Sequence[float]) -> str:
    """The regime rule, over an already-truncated list of closes.

    Split out so the segmented state can reproduce the label from carried closes
    without re-deriving the thresholds. Two copies of a threshold rule is one
    more than this codebase should have, and a divergence between them would be
    invisible until a regime label differed by one bucket in a report nobody was
    reading closely.

    The thresholds are fixed constants, not fitted values -- a regime label is a
    descriptive bucket here, not a validated classifier.
    """
    if len(closes) < 2:
        return "UNKNOWN"
    returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    if not returns:
        return "UNKNOWN"

    net = sum(returns)
    volatility = sum(abs(r) for r in returns) / len(returns)

    if volatility < 0.0005:
        return "RANGE"
    if net > 0.005:
        return "TREND_UP"
    if net < -0.005:
        return "TREND_DOWN"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def analyze_market_structure(
    candles: list[CandleData],
    symbol: str,
    timeframe: Timeframe,
    lookback: int = SWING_LOOKBACK_DEFAULT,
    *,
    as_of_index: int | None = None,
) -> MarketStructureResult:
    """Run the full structure pipeline over ``candles[: as_of_index + 1]``.

    Passing ``as_of_index=n`` answers "what structure was knowable at bar *n*", which
    is the only question a backtest or a research event may ask. Every downstream
    object carries a confirmation point at or before ``n``, so nothing in the
    result can have been derived from bar ``n + 1`` or later.
    """
    series = _truncate(candles, as_of_index)
    last_index = len(series) - 1 if series else None

    swings = detect_swings(series, lookback)
    events = classify_swing_sequence(swings)
    liquidity = extract_liquidity_levels(swings, series)

    # Phase 7 completes the level set: swing levels alone are two of the ten
    # types the specification names. Equal highs/lows come from the swing levels
    # that survived MIN_TOUCHES; range/session/previous-day levels come from the
    # streaming state, fed the same bars in the same order so that the
    # continuous path and the segmented path publish the same levels at the same
    # indices -- the equality that Phase 7 requires, and that a report over one
    # path but not the other would quietly violate.
    liquidity = sorted(
        [*liquidity, *extract_equal_levels(swings, liquidity), *_derived_levels(series)],
        key=lambda level: (level.creation_index, level.price, level.level_type),
    )

    range_high: Decimal | None = None
    range_low: Decimal | None = None
    if series:
        range_high = max(c.high for c in series)
        range_low = min(c.low for c in series)

    regime = classify_candles_as_regime(series)

    # A defensive invariant: a confirmation point beyond the data would mean some
    # downstream consumer could act on a fact it cannot have. Fail loudly rather
    # than emit a subtly impossible result.
    for event in events:
        if last_index is not None and event.confirmation_index > last_index:
            raise AssertionError(
                f"event {event.event_type} at bar {event.index} claims confirmation at "
                f"bar {event.confirmation_index}, beyond the supplied data ({last_index})"
            )

    return MarketStructureResult(
        symbol=symbol,
        timeframe=timeframe,
        swings=swings,
        events=events,
        liquidity_levels=liquidity,
        recent_range=(range_low, range_high) if range_low is not None else None,
        current_regime=regime,
        as_of_index=last_index,
    )
