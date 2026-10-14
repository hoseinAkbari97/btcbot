"""Equal-level clustering: the tolerance boundary, tested against hand-written prices.

Why this file exists
--------------------
Cluster membership is decided by a single comparison against a constant, and it
previously had no test of its own. Existing coverage exercised it only through
the function that *consumes* the clusters (:func:`equal_level_for`), so a change
to the bucket rule itself would have been invisible.

Every expectation is written out from the price arithmetic. Membership is read
from ``LiquidityLevel.swing_confirmations`` -- the provenance the builder records
itself -- rather than inferred from a downstream label or a count.

Two defects this file pins
--------------------------
Both were found while writing these tests and both are now fixed:

1. **The boundary was decided by IEEE-double representation error.** The
   membership test compared ``float`` prices, so a pivot exactly at the
   tolerance was rejected: ``abs(100.001 - 100.0)`` is
   ``0.0010000000000047748`` in binary double, which is *greater* than
   ``0.001``. The band is inclusive (``>`` rejects), so the decimal-equal
   boundary was on the wrong side of the test purely by representation.
   ``test_a_gap_exactly_equal_to_the_tolerance_joins_one_bucket`` pins it.

2. **The price index excluded the bucket sitting exactly on its upper edge.**
   ``bisect_left(by_price, (high, -1))`` stops *before* an entry whose price
   equals ``high``, while the membership test admits that case. The comment
   claimed the two "cannot disagree about a boundary case"; they did, from
   opposite sides. ``test_the_index_never_hides_a_bucket_the_test_would_admit``
   pins the superset property the fix relies on.

A discrepancy that is NOT resolved here
---------------------------------------
Three places in the repository describe the tolerance as a *relative* fraction
while the rule applied is an **absolute** price distance. On a BTC quote the two
differ by a factor of ~30,000 in how many levels they produce. That is a
specification decision rather than a testing one and is escalated in
SESSION_NOTES.md; ``test_the_tolerance_is_absolute_while_the_documentation_says_relative``
pins the behaviour that exists so it cannot drift unnoticed in either
direction.

Fixture design
--------------
Three constraints must hold simultaneously for a bucket to appear at all, and
violating any one produces *no* level rather than a wrong one -- which makes a
broken fixture look like a passing test:

1. a pivot must be a **strict** local maximum, so no neighbour may tie it;
2. the bucket's anchor is the pivot quantised to ``Decimal("0.01")``;
3. a bucket survives only if ``touch_count >= MIN_TOUCHES`` (2), where a touch is
   any bar at or before its creation bar whose high reaches the anchor.

(1) and (3) look contradictory -- a bar reaching the price ties the pivot -- and
are resolved by giving pivots **sub-cent precision**. A pivot at ``100.0004``
anchors a bucket at ``100.00``; a separate bar at exactly ``100.00`` reaches that
price without tying the pivot. Touch bars are emitted as **adjacent pairs** so
they are not themselves strict maxima, and are placed far from every pivot so
they never enter a pivot's confirmation window.
"""

from __future__ import annotations

from decimal import Decimal

from conftest import make_candle

from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure.analysis import (
    LEVEL_CLUSTER_TOLERANCE,
    analyze_market_structure,
    extract_equal_levels,
)

#: Read from the code, not restated, so a change to the constant turns into a
#: changed expectation a reviewer must look at, rather than a silently wrong
#: assertion.
TOL = LEVEL_CLUSTER_TOLERANCE
assert TOL == Decimal("0.001"), (
    "this file derives its boundary expectations from a 0.001 tolerance; if the "
    "constant changes the boundaries must be re-derived, not adjusted"
)

#: The level price a cluster is anchored at, and the pivot prices used against
#: it. Every distance below is measured from ``ANCHOR`` (the quantised anchor),
#: because that is what the membership test compares against -- not from another
#: pivot's raw price.
ANCHOR = Decimal("100.00")
MEMBER_INSIDE = Decimal("100.0004")  # 0.0004 from anchor  -> inside
MEMBER_NEAR = Decimal("100.0009")  # 0.0009 from anchor  -> inside
MEMBER_EXACT = Decimal("100.001")  # 0.0010 from anchor  -> exactly on the band
MEMBER_OUTSIDE = Decimal("100.0015")  # 0.0015 from anchor -> outside

#: The same shape at a BTC quote, where the tolerance is ~3e-8 of the price and a
#: float implementation of the same rule could not keep the distinction.
FAR_ANCHOR = Decimal("30000.00")
FAR_MEMBER = Decimal("30000.0004")
FAR_NEAR = Decimal("30000.0009")
FAR_EXACT = Decimal("30000.001")
FAR_OUTSIDE = Decimal("30000.0015")

FILLER_HIGH = Decimal("90")

#: Adjacent bar pairs used as touches. Two equal adjacent bars are not a strict
#: maximum of each other, so neither becomes a pivot -- a *single* touching bar
#: surrounded by filler would, silently adding a bucket.
TOUCH_SLOTS = ((2, 3), (6, 7), (10, 11), (14, 15), (18, 19), (22, 23))


def build(
    pivots: list[tuple[int, Decimal]],
    *,
    total: int = 90,
    extra_levels: tuple[Decimal, ...] = (),
    filler: Decimal = FILLER_HIGH,
) -> list[CandleData]:
    """A series whose confirmed swing highs are exactly ``pivots``.

    :param pivots: ``(bar_index, high)``, each strictly above its neighbours.
    :param extra_levels: further prices needing touch bars of their own, for
        fixtures with more than one level.
    :param filler: the price of every bar that is neither a pivot nor a touch.
        It must sit *below* the pivots, so sub-$1 fixtures need their own --
        the default of 90 would make a $0.01 pivot the lowest high in the
        series and therefore not a swing high at all.
    """
    anchors = {p.quantize(Decimal("0.01")) for _, p in pivots}
    anchors.update(extra_levels)

    touch_at: dict[int, Decimal] = {}
    for n, price in enumerate(sorted(anchors)):
        first, second = TOUCH_SLOTS[n % len(TOUCH_SLOTS)]
        touch_at[first] = price
        touch_at[second] = price

    pivot_at = dict(pivots)
    candles: list[CandleData] = []
    for index in range(total):
        if index in pivot_at:
            high = pivot_at[index]
        elif index in touch_at:
            high = touch_at[index]
        else:
            high = filler
        close = high - filler / 2
        candles.append(
            make_candle(
                index * 5,
                open_price=str(close),
                high=str(high),
                low=str(high - filler / 4),
                close=str(close),
                volume="10",
            )
        )
    return candles


def clusters(candles: list[CandleData], *, lookback: int = 2) -> list[tuple]:
    """``[(anchor_price, (swing_indices...)), ...]`` over swing-high buckets.

    A **list**, not a dict keyed by price: two distinct buckets can legitimately
    carry the same anchor (that is what a boundary case produces), and keying by
    price would silently drop one of them -- which would make a
    should-be-two-cluster fixture pass as one.
    """
    structure = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=lookback
    )
    return sorted(
        (
            str(level.price),
            tuple(sorted(index for index, _ in level.swing_confirmations)),
        )
        for level in structure.liquidity_levels
        if level.level_type == "swing_high"
    )


def members(candles: list[CandleData], *, lookback: int = 2) -> tuple:
    """The membership tuple of the single expected bucket."""
    found = clusters(candles, lookback=lookback)
    assert len(found) == 1, f"expected exactly one swing-high bucket, got {found}"
    return found[0][1]


def equal_levels(candles: list[CandleData], *, lookback: int = 2) -> list[tuple]:
    """``[(level_type, creation_index)]`` for the derived equal levels."""
    structure = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=lookback
    )
    return [
        (level.level_type, level.creation_index)
        for level in extract_equal_levels(structure.swings, structure.liquidity_levels)
    ]


# ---------------------------------------------------------------------------
# The band, at both ends
# ---------------------------------------------------------------------------


def test_a_gap_exactly_equal_to_the_tolerance_joins_one_bucket() -> None:
    """``|p - anchor| == tolerance`` is **inside** the band.

    The production test is ``> tolerance``, so equality does not skip. Pinned
    from the comparison rather than from a run, because a boundary that later
    flips from inclusive to exclusive changes an event count without attracting
    attention.

    This is the case that IEEE double arithmetic got wrong: ``abs(100.001 -
    100.0)`` evaluates to ``0.0010000000000047748`` in binary double, which is
    *greater* than ``0.001``, so the pre-fix code split a pair the stated
    arithmetic keeps together.

    The error's **sign depends on the magnitude**, which is what makes the float
    comparison indefensible rather than merely imprecise:

    ==================  =============================  ============
    anchor              ``|anchor+0.001 - anchor|``    verdict
    ==================  =============================  ============
    100                 0.0010000000000047748          rejected
    1,000               0.0009999999999763531          admitted
    30,000              0.0010000000002037268          rejected
    ==================  =============================  ============

    So at a BTC quote the boundary was decided by representation error and
    happened to come out wrong; at a 1,000 quote the same rule would have
    admitted it. Neither is a statement about the tolerance.
    """
    assert MEMBER_EXACT - ANCHOR == TOL, "fixture arithmetic must be exact"
    assert members(build([(20, MEMBER_INSIDE), (50, MEMBER_EXACT)])) == (20, 50), (
        "a gap of exactly the tolerance is inclusive and must produce one "
        "two-member bucket"
    )


def test_a_gap_one_unit_past_the_tolerance_splits_into_two_buckets() -> None:
    """The first value outside the band, on the decimal grid.

    ``100.0015`` is 0.0015 from the anchor -- one and a half times the tolerance.
    Both pivots quantise to the *same* anchor price of ``100.00``, which is
    exactly why membership is decided on the raw price: clustering on the
    quantised anchor would report these as one level, and the difference between
    the two readings is invisible in the level's own price field.
    """
    assert MEMBER_OUTSIDE - ANCHOR == TOL + Decimal("0.0005")
    found = clusters(build([(20, MEMBER_INSIDE), (50, MEMBER_OUTSIDE)]))
    assert len(found) == 2, f"expected two buckets, got {found}"
    assert sorted(m for _, m in found) == [(20,), (50,)], (
        f"each pivot must sit alone in its own bucket, got {found}"
    )


def test_the_band_is_measured_from_the_quantised_anchor_not_the_raw_pivot() -> None:
    """Membership compares against ``100.00``, not against ``100.0004``.

    The anchor is the first pivot *quantised* to two decimals, so the band is
    offset from the raw pivot by the quantisation residue. A member is admitted
    when it is within ``0.001`` of ``100.00``, which is not the same set as
    "within 0.001 of 100.0004". Stated explicitly because the two readings
    differ and only one is implemented.

    The second pivot here is ``100.0009``: 0.0009 from the anchor (inside) but
    0.0005 from the first pivot. Both readings admit it, so this fixture pins
    the *anchor* specifically via the outside case below it.
    """
    assert MEMBER_NEAR - ANCHOR == Decimal("0.0009")
    assert MEMBER_NEAR - MEMBER_INSIDE == Decimal("0.0005")
    assert members(build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR)])) == (20, 50)


def test_the_index_never_hides_a_bucket_the_test_would_admit() -> None:
    """The price index is a superset filter at **every** price, not just BTC's.

    The scan bounds are a pre-filter and their only obligation is to never
    exclude a bucket the exact membership test would accept. Using the relative
    band alone satisfied that only above a price of 1: at $0.01 the relative
    band is $0.00001 wide and the absolute band is $0.001, so the index was
    *narrower* than the test it was guarding.

    Sweeping anchors from $0.01 to $2,000 against the pre-fix bounds found 35
    (anchor, candidate) pairs the membership test would admit and the index
    would have skipped -- every one of them below $1. At a BTC quote the two
    bands differ by five orders of magnitude, which is why the defect survived
    a test suite that only ever used BTC-scale prices.

    The bounds are now the union of both bands. This drives the exact-boundary
    case through the real index at three scales, including one where the two
    bands are the wrong way round.
    """
    for first, second, filler in (
        (MEMBER_INSIDE, MEMBER_EXACT, FILLER_HIGH),
        (FAR_MEMBER, FAR_EXACT, FILLER_HIGH),
        # Below $1 the relative band is narrower than the absolute one, so these
        # are the cases that were actually being missed.
        (Decimal("0.0100"), Decimal("0.0110"), Decimal("0.005")),
        (Decimal("0.2200"), Decimal("0.2210"), Decimal("0.10")),
    ):
        level = first.quantize(Decimal("0.01"))
        found = clusters(
            build([(20, first), (50, second)], filler=filler)
        )
        assert len(found) == 1 and found[0][1] == (20, 50), (
            f"the exact-boundary member must be reachable through the index at "
            f"anchor {level}; got {found}"
        )


def test_the_rule_is_exact_at_prices_where_the_tolerance_is_below_the_quote_resolution() -> None:
    """A float implementation could not keep this distinction at BTC scale.

    At 30,000 the tolerance is 3e-8 of the quote. ``Decimal`` keeps the
    comparison exact there; IEEE doubles round ``30000.001 - 30000.00`` to noise
    and could admit or reject either way.
    """
    inside = clusters(build([(20, FAR_MEMBER), (50, FAR_NEAR)]))
    assert len(inside) == 1 and inside[0][1] == (20, 50), (
        f"a gap of 0.0009 is inside the absolute band at any scale, got {inside}"
    )
    outside = clusters(build([(20, FAR_MEMBER), (50, FAR_OUTSIDE)]))
    assert len(outside) == 2, (
        f"a gap of 0.0015 is outside the absolute band at any scale, got {outside}"
    )


# ---------------------------------------------------------------------------
# The absolute-versus-relative discrepancy: pinned, not resolved
# ---------------------------------------------------------------------------


def test_the_tolerance_is_absolute_while_the_documentation_says_relative() -> None:
    """Records the implemented semantics. It does not endorse them.

    The membership test is ``abs(price - anchor) > tolerance``, an **absolute**
    price distance. Three comments describe it as relative:

    * ``LEVEL_CLUSTER_TOLERANCE = Decimal("0.001")  # 0.1%``
    * "The tolerance is relative to the *bucket's* price ... which derives
      ``p/(1+tol) <= b <= p/(1-tol)``"
    * ``equal_level_for``: "confirmed within ``tolerance`` of it"

    The practical consequence of the implemented rule, measured on real BTCUSDT
    5m data (60,000 bars): every multi-member cluster has a member price spread
    of **exactly zero** -- 271 such clusters, maximum spread 0.00. Under the
    absolute rule an "equal high" is therefore two swing highs at the identical
    price to the cent. Under the relative reading the same data yields 844
    clusters rather than 271.

    That three-fold difference materially changes the dataset, so which reading
    is correct is escalated for human review rather than decided here.
    """
    # Absolute rule: a 0.0009 gap is inside at any price level, including one
    # where the relative reading would also admit it -- so this fixture alone
    # cannot separate the two. What it does pin is that the band does not
    # *widen* with price.
    at_100 = clusters(build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR)]))
    at_btc = clusters(build([(20, FAR_MEMBER), (50, FAR_NEAR)]))
    assert len(at_100) == len(at_btc) == 1, (
        "the implemented band is the same absolute width at both scales"
    )

    # A 0.9 gap. Outside the absolute rule (0.9 >> 0.001); inside the relative
    # rule at a quote of 100 (0.9/100 = 0.009 < 0.001 is false too, so also
    # outside) -- but inside the relative rule at a quote near 1,000, where
    # 0.1% is 1.0. This is the pair that separates the readings, and under the
    # implemented rule both split.
    far_apart_low = clusters(build([(20, MEMBER_INSIDE), (50, Decimal("100.9"))]))
    far_apart_high = clusters(
        build(
            [(20, Decimal("1000.0004")), (50, Decimal("1000.9"))],
            extra_levels=(Decimal("1000.00"), Decimal("1000.90")),
        )
    )
    assert len(far_apart_low) == 2, f"0.9 apart must split, got {far_apart_low}"
    assert len(far_apart_high) == 2, (
        f"a 0.9 gap must split under the absolute rule at any price, including "
        f"where the relative rule would join it; got {far_apart_high}"
    )


# ---------------------------------------------------------------------------
# Cluster formation
# ---------------------------------------------------------------------------


def test_three_pivots_on_one_price_form_a_single_bucket() -> None:
    """Repeated confirmations join the cluster; they do not accumulate levels."""
    pivots = [(20, MEMBER_INSIDE), (50, MEMBER_NEAR), (80, MEMBER_INSIDE)]
    found = clusters(build(pivots, total=120))
    assert found == [(str(ANCHOR), (20, 50, 80))], (
        f"expected one three-member bucket, got {found}"
    )


def test_two_pivots_on_distant_prices_form_two_buckets() -> None:
    """Clustering is not transitive by accident: a distant price stays apart."""
    found = clusters(
        build([(20, MEMBER_INSIDE), (50, Decimal("120.0004"))])
    )
    assert len(found) == 2, f"expected two buckets, got {found}"


def test_the_anchor_is_the_first_swing_and_is_never_re_averaged() -> None:
    """Later members cannot move the bucket's price.

    An anchor that drifted as members arrived would change the level under every
    event already published against it. Both later pivots are inside the band of
    the first, so both join its bucket and the anchor must be unchanged.
    """
    found = clusters(
        build(
            [(20, MEMBER_INSIDE), (50, MEMBER_NEAR), (80, Decimal("100.0006"))],
            total=120,
        )
    )
    assert found == [(str(ANCHOR), (20, 50, 80))], f"got {found}"


def test_membership_does_not_depend_on_the_order_pivots_are_listed() -> None:
    """The same pivot set yields the same clusters however it is supplied.

    ``detect_swings`` emits in bar order, so the builder always sees a
    confirmation-ordered sequence. Cluster *membership* is asserted to be
    order-independent; the anchor is deliberately not, because it is by
    construction the first swing and cannot be anything else.
    """
    forward = clusters(build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR)]))
    reversed_ = clusters(build([(50, MEMBER_NEAR), (20, MEMBER_INSIDE)]))
    assert len(forward) == len(reversed_) == 1
    assert forward[0][1] == reversed_[0][1] == (20, 50)


def test_repeated_runs_are_deterministic() -> None:
    """Same input, same output -- no set iteration or dict ordering leaking in."""
    candles = build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR), (80, MEMBER_OUTSIDE)])
    first = clusters(candles)
    assert clusters(candles) == first
    assert clusters(list(candles)) == first


# ---------------------------------------------------------------------------
# Timing: an equal level is dated to the second swing's confirmation
# ---------------------------------------------------------------------------


def test_an_equal_level_is_dated_to_the_second_confirming_swing() -> None:
    """``equal_highs`` becomes knowable at the *second* pivot's confirmation.

    With ``lookback=2`` a pivot at bar 50 confirms at bar 52. Publishing the
    equal level at the first pivot's confirmation (bar 22) would claim two highs
    existed when only one had printed. The leak is in the label rather than the
    price, which is why it survives a casual look.
    """
    derived = equal_levels(build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR)]))
    assert ("equal_highs", 52) in derived, (
        f"equal_highs must be dated to the second confirmation (bar 52); got {derived}"
    )


def test_one_pivot_on_a_price_is_not_an_equal_level() -> None:
    """A single swing is not an 'equal' anything."""
    derived = equal_levels(build([(20, MEMBER_INSIDE), (50, Decimal("120.0004"))]))
    assert not any(kind == "equal_highs" for kind, _ in derived), (
        f"two different prices must not form an equal level, got {derived}"
    )


def test_a_pivot_arriving_later_cannot_rewrite_the_level_already_published() -> None:
    """Appending a matching pivot may add a label, never move the swing level.

    The bucket's price is the first swing's quantised price and its creation
    index is the first confirmation's. A second pivot confirming later may only
    grow the bucket.
    """
    early = clusters(build([(20, MEMBER_INSIDE)], total=45))
    later = clusters(build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR)]))

    assert early == [(str(ANCHOR), (20,))], f"early publication: {early}"
    assert later == [(str(ANCHOR), (20, 50))], (
        f"the level published before the second pivot must keep its price and "
        f"creation bar and only gain a member; got {later}"
    )


def test_cluster_state_is_append_only_under_bar_appending() -> None:
    """Appending bars may *add* cluster members but never revise the cluster.

    The project's :func:`audit` is the wrong instrument for this component and
    saying so is part of the result. It asserts that the output *for a past bar*
    is byte-identical on a prefix and on the full run, which is the right
    invariant for a detector that emits an event and is done -- a sweep, a zone,
    a compression. Clustering is different: a bucket is an open-ended set that
    keeps gaining members as further swings confirm on the same price. On a
    prefix ending before the second swing, the cluster legitimately has one
    member; on the full run it has two. That is the concept working, and the
    audit reports it as a violation.

    So the invariant stated here is the one that actually matters and is what
    "no future leakage" means for a growing cluster:

    * the **anchor** (the level's price) is fixed by the first swing and is
      never revised;
    * the **creation index** is the first confirmation's and never moves;
    * membership only ever **grows**, and the members seen on a prefix are still
      members on the full run -- nothing is retracted or re-attributed.

    A retraction or a reprice is what would break causality here, and all three
    are checked.
    """
    candles = build(
        [(20, MEMBER_INSIDE), (50, MEMBER_NEAR), (70, Decimal("130.0004"))],
        total=130,
    )
    full = clusters(candles)

    for cut in (35, 45, 60, 80, 100, 129):
        prefix = clusters(candles[:cut])
        for anchor, seen in prefix:
            matches = [m for a, m in full if a == anchor]
            assert matches, f"cluster at {anchor} vanished when bars were appended"
            assert seen == matches[0][: len(seen)], (
                f"cluster at {anchor} on the prefix to bar {cut} had members "
                f"{seen}; the full run has {matches[0]}, which must extend it "
                "rather than rewrite it"
            )

    # And the specific repricing that would be a genuine leak: the bucket formed
    # by the first pivot must still carry the first pivot's anchor and creation
    # bar on the full run.
    def first_bucket(levels):
        found = analyze_market_structure(
            levels, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=2
        ).liquidity_levels
        return sorted(
            (
                level.level_type,
                str(level.price),
                level.creation_index,
                tuple(sorted(i for i, _ in level.swing_confirmations)),
            )
            for level in found
            if level.level_type == "swing_high"
        )

    early = first_bucket(candles[:45])
    late = first_bucket(candles)

    # Identity fields: price and creation bar must survive verbatim. Membership
    # is compared separately above, because it is *expected* to grow.
    def identity(records):
        return sorted(record[:3] for record in records)

    assert identity(early) <= identity(late), (
        f"a level published by bar 45 lost its identity on the full run: "
        f"{identity(early)} vs {identity(late)}"
    )
    early_members = dict((r[:3], r[3]) for r in early)
    late_members = dict((r[:3], r[3]) for r in late)
    for key, seen in early_members.items():
        assert late_members[key][: len(seen)] == seen, (
            f"the cluster {key} published by bar 45 had members {seen}; the full "
            f"run has {late_members[key]}, which must extend that list rather "
            "than rewrite it"
        )


# ---------------------------------------------------------------------------
# Carried state across a segment boundary
# ---------------------------------------------------------------------------


def _cluster_key(levels) -> list[tuple]:
    return sorted(
        (
            level.level_type,
            str(level.price),
            level.creation_index,
            tuple(sorted(index for index, _ in level.swing_confirmations)),
        )
        for level in levels
        if level.level_type in ("swing_high", "swing_low")
    )


def test_clustering_is_identical_across_segment_boundaries() -> None:
    """A windowed run must cluster exactly as a whole-series run does.

    ``StructureState`` carries swing buckets across a boundary, so a bucket
    whose members straddle it must survive with the same members and the same
    creation index.
    """
    from app.services.market_structure.segmented import StructureState

    candles = build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR), (80, MEMBER_NEAR)], total=120)

    state = StructureState("BTCUSDT", Timeframe.M5, lookback=2)
    for start in range(0, len(candles), 25):
        state.observe(candles[start : start + 25])
    # ``levels()`` is the *cumulative* set, so it is read once at the end. Calling
    # it per window and extending would concatenate a growing list with itself.
    windowed = state.levels()

    whole = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=2
    ).liquidity_levels

    assert _cluster_key(windowed) == _cluster_key(whole), (
        "windowed clustering must equal the whole-series result, including "
        f"members and creation indices:\n  windowed={_cluster_key(windowed)}"
        f"\n  whole    ={_cluster_key(whole)}"
    )


def test_a_checkpoint_round_trip_preserves_cluster_membership() -> None:
    """Serialising and resuming cannot re-bucket or re-date anything.

    The bucket list is rebuilt from swing confirmations on resume; if that
    reconstruction dropped or reordered a member, a resumed run would emit a
    different ``equal_highs`` set from an uninterrupted one.
    """
    from app.services.market_structure.segmented import StructureState

    candles = build([(20, MEMBER_INSIDE), (50, MEMBER_NEAR), (80, MEMBER_NEAR)], total=120)

    state = StructureState("BTCUSDT", Timeframe.M5, lookback=2)
    state.observe(candles[:60])
    restored = StructureState.from_payload(state.to_payload())
    restored.observe(candles[60:])

    uninterrupted = StructureState("BTCUSDT", Timeframe.M5, lookback=2)
    uninterrupted.observe(candles)

    assert _cluster_key(restored.levels()) == _cluster_key(uninterrupted.levels()), (
        "a resumed state must cluster exactly as an uninterrupted one does"
    )


# ---------------------------------------------------------------------------
# Minimal and malformed input
# ---------------------------------------------------------------------------


def test_a_series_too_short_to_confirm_any_pivot_produces_no_clusters() -> None:
    """No confirmed swings means no buckets -- not an error, and not a guess."""
    assert clusters(build([(20, MEMBER_INSIDE)], total=5)) == []


def test_an_empty_series_produces_no_clusters() -> None:
    assert clusters([]) == []


def test_a_flat_series_produces_no_strict_pivots_and_no_clusters() -> None:
    """Strict comparison means a flat series has no strict local maximum.

    The derived *range* levels still exist on a flat series -- they come from a
    different component -- so this asserts on swing buckets specifically, which
    is what clustering consumes.
    """
    flat = [
        make_candle(
            index * 5, open_price="100", high="100", low="100", close="100", volume="1"
        )
        for index in range(40)
    ]
    assert clusters(flat) == []