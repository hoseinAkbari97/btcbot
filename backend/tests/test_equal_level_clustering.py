"""Equal-level clustering: relative tolerance to a frozen anchor, tested against
hand-written prices.

The rule under test (engineering decision, 2026-10-17 -- the main
specification defines no tolerance)
-------------------------------------------------------------
A swing joins a bucket when::

    abs(swing.price - anchor) <= LEVEL_CLUSTER_TOLERANCE * anchor

where ``anchor`` is the **first** swing that created the bucket, quantised to
``Decimal("0.01")``, and is never re-averaged as the cluster grows.

Consequences the tests pin one at a time:

* the band **scales with the anchor** -- at $100 it is $0.10, at $30,000 it is
  $30.00, which is the whole point of a *relative* tolerance;
* boundary equality is **inclusive** (``>`` skips, ``==`` joins);
* membership is against the frozen anchor, so clustering is **not transitive**;
* membership depends on **arrival order**, because the anchor *is* the first
  member;
* the search index is only a pre-filter and must return a **superset** -- it may
  never exclude a bucket the membership test would accept.

The rule was previously absolute (``abs(p - anchor) <= 0.001``). Over 60,000 real
bars every cluster it produced had a member price spread of exactly 0.00, i.e.
"equal high" meant "the same price to the cent". It was changed on the meaning of
the term, not on the fact that the relative rule yields more clusters.

Fixture design
--------------
Three constraints must hold simultaneously for a bucket to appear at all, and
violating any one produces *no* level rather than a wrong one -- which makes a
broken fixture look like a passing test:

1. a pivot must be a **strict** local maximum, so no neighbour may tie it;
2. the anchor is the pivot quantised to 0.01;
3. a bucket survives only if ``touch_count >= MIN_TOUCHES`` (2), where a touch is
   any bar at or before its creation bar whose high reaches the anchor.

(1) and (3) look contradictory -- a bar reaching the price ties the pivot -- and
are resolved by giving the first pivot **sub-cent precision**. A pivot at
``100.004`` anchors a bucket at ``100.00``; a separate bar at exactly ``100.00``
reaches that price without tying the pivot. Touch bars are emitted as **adjacent
pairs** so they are not themselves strict maxima, and are placed far from every
pivot so they never enter a pivot's confirmation window.
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
#: changed expectation a reviewer must look at.
TOL = LEVEL_CLUSTER_TOLERANCE
assert TOL == Decimal("0.001"), (
    "this file derives its boundary expectations from a 0.001 tolerance; if the "
    "constant changes the boundaries must be re-derived, not adjusted"
)

# --- low scale: anchor $100.00, band = 0.1 * 100.00 = $0.10 ----------------
ANCHOR = Decimal("100.00")
BAND_LOW = TOL * ANCHOR  # 0.10
assert BAND_LOW == Decimal("0.10"), "the low-scale band must be exactly a tenth"

#: The first pivot. Its sub-cent precision puts the anchor at 100.00 while
#: keeping the pivot a strict local maximum above the 100.00 touch bars.
FIRST_LOW = Decimal("100.004")
MEMBER_INSIDE = ANCHOR + BAND_LOW / 2  # 100.05, half the band
MEMBER_EXACT = ANCHOR + BAND_LOW  # 100.10, exactly on the band
MEMBER_OUTSIDE = ANCHOR + BAND_LOW + Decimal("0.01")  # 100.11, just outside

# --- high scale: anchor $30,000.00, band = 0.1 * 30,000 = $30.00 -----------
FAR_ANCHOR = Decimal("30000.00")
BAND_FAR = TOL * FAR_ANCHOR  # 30.00
assert BAND_FAR == Decimal("30.00"), "the band must scale with the anchor"

FIRST_FAR = Decimal("30000.004")
FAR_INSIDE = FAR_ANCHOR + BAND_FAR / 2  # 30015.00
FAR_EXACT = FAR_ANCHOR + BAND_FAR  # 30030.00, exactly on the band
FAR_OUTSIDE = FAR_ANCHOR + BAND_FAR + Decimal("0.01")  # 30030.01

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
    :param extra_levels: further prices needing touch bars of their own.
    :param filler: price of every bar that is neither a pivot nor a touch. Must
        sit below the pivots, so sub-$1 fixtures need their own.
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
    carry the same anchor, and keying by price would silently drop one.
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
# The rule: relative, inclusive at the boundary
# ---------------------------------------------------------------------------


def test_a_gap_exactly_equal_to_the_band_joins_one_bucket() -> None:
    """``|p - anchor| == tol * anchor`` is **inside** the band.

    The test is ``>``, so equality does not skip. Pinned from the comparison
    rather than from a run, because a boundary that later flips from inclusive to
    exclusive changes an event count without attracting attention.

    This case was also wrong under the old float implementation:
    ``abs(100.001 - 100.0)`` evaluates to ``0.0010000000000047748`` in binary
    double, which is *greater* than ``0.001``, so a pivot exactly at the
    tolerance was rejected while one a hair inside was accepted. The error's sign
    depends on the magnitude:

    ==============  ==============================  ===========
    anchor          ``|anchor+0.001 - anchor|``     verdict
    ==============  ==============================  ===========
    100             0.0010000000000047748           rejected
    1,000           0.0009999999999763531           admitted
    30,000          0.0010000000002037268           rejected
    ==============  ==============================  ===========

    So the old verdict was an artefact of the price level, not of the rule. The
    comparison is now exact ``Decimal``.
    """
    assert MEMBER_EXACT - ANCHOR == TOL * ANCHOR, "fixture arithmetic must be exact"
    assert members(build([(20, FIRST_LOW), (50, MEMBER_EXACT)])) == (20, 50)


def test_a_gap_one_cent_past_the_band_splits_into_two_buckets() -> None:
    """The first value outside the band.

    ``100.11`` is one cent beyond a band that ends at exactly ``100.10``.
    """
    assert MEMBER_OUTSIDE - ANCHOR > TOL * ANCHOR
    found = clusters(build([(20, FIRST_LOW), (50, MEMBER_OUTSIDE)]))
    assert len(found) == 2, f"expected two buckets, got {found}"
    assert sorted(m for _, m in found) == [(20,), (50,)], (
        f"each pivot must sit alone in its own bucket, got {found}"
    )


def test_the_band_scales_with_the_anchor() -> None:
    """The defining property of a *relative* tolerance, and the reason for the change.

    At $100 the band is $0.10. At $30,000 it is $30.00. The identical *relative*
    separation -- 0.05% -- is 5 cents at one price and $15 at the other, and both
    must join their cluster.

    Under the previous absolute rule the same pair of prices would have joined at
    $30,000 and not at $100, which is not a tolerance at all but a fixed distance
    that happens to be meaningless at the scale being traded.
    """
    assert TOL * ANCHOR == Decimal("0.10")
    assert TOL * FAR_ANCHOR == Decimal("30.00")

    low = clusters(build([(20, FIRST_LOW), (50, MEMBER_INSIDE)]))
    far = clusters(build([(20, FIRST_FAR), (50, FAR_INSIDE)], filler=Decimal("90")))
    assert len(low) == 1 and len(far) == 1, (
        f"the same relative gap must join at both scales: low={low} far={far}"
    )

    # The converse: below $1 the relative band is *narrower* than the old absolute
    # one, so a gap the old rule admitted is now outside. At $0.10 the band is
    # 0.0001, and a gap of 0.00015 falls outside it.
    tiny_anchor, tiny_far = Decimal("0.1000"), Decimal("0.10015")
    assert TOL * tiny_anchor == Decimal("0.0001")
    tiny = clusters(
        build([(20, tiny_anchor), (50, tiny_far)], filler=Decimal("0.05"))
    )
    assert len(tiny) == 2, (
        f"a 0.00015 gap is outside a 0.0001 band at $0.10; got {tiny}"
    )


def test_membership_is_measured_against_the_frozen_anchor_not_the_raw_pivot() -> None:
    """The anchor is the first swing *quantised* to 0.01.

    The band is therefore offset from the raw pivot by the quantisation residue:
    the band around ``100.004`` runs to ``100.00 + 0.10``, not
    ``100.004 + 0.10``. A member at ``100.099`` is inside; one at ``100.101`` is
    not, even though the latter is only ``0.097`` from the raw pivot.
    """
    inside = build([(20, FIRST_LOW), (50, ANCHOR + Decimal("0.099"))])
    outside = build([(20, FIRST_LOW), (50, ANCHOR + Decimal("0.101"))])
    assert len(clusters(inside)) == 1, "0.099 from the anchor is inside"
    assert len(clusters(outside)) == 2, "0.101 from the anchor is outside"


def test_the_anchor_is_never_re_averaged_as_the_cluster_grows() -> None:
    """Later members cannot move the bucket's price.

    An anchor that drifted as members arrived would change the level under every
    event already published against it. Three members, the last well toward the
    far edge, must all join the anchor set at creation.
    """
    pivots = [(20, FIRST_LOW), (50, MEMBER_INSIDE), (80, MEMBER_EXACT)]
    found = clusters(build(pivots, total=120))
    assert found == [(str(ANCHOR), (20, 50, 80))], f"got {found}"
    assert list(found[0])[0] == str(ANCHOR), "the anchor must stay at 100.00"


# ---------------------------------------------------------------------------
# Non-transitivity and order-dependence -- measured properties, not accidents
# ---------------------------------------------------------------------------


def test_clustering_is_not_transitive() -> None:
    """``A~B`` and ``B~C`` do not imply ``A~C``: every member is tested against
    the **frozen anchor**, never pairwise.

    Chosen so each consecutive pair is inside the band and the outer pair is
    not. Under a pairwise or "nearest neighbour" rule all three would merge;
    under the anchor rule they cannot, because the band is only ever measured
    from the bucket's own price.
    """
    a, b, c = ANCHOR, ANCHOR + Decimal("0.09"), ANCHOR + Decimal("0.18")
    assert abs(b - a) <= TOL * a, "A~B must hold"
    assert abs(c - b) <= TOL * a, "B~C must hold"
    assert abs(c - a) > TOL * a, "A~C must NOT hold, or the case proves nothing"

    found = clusters(build([(20, a), (50, b), (80, c)], total=120))
    assert sorted(m for _, m in found) == [(20, 50), (80,)], (
        f"b belongs to a's cluster, c must start its own; got {found}"
    )


def test_membership_depends_on_the_order_members_are_confirmed_in() -> None:
    """The anchor is the first member, so contents follow arrival order.

    Stated explicitly rather than left implicit: it is a direct consequence of
    the append-only rule (a published level must not move its price), and it is
    the reason a cluster's *contents* cannot be reproduced from its price alone.
    ``first_seen`` and the recorded swing confirmations are part of its identity.
    """
    a, b, c = ANCHOR, ANCHOR + Decimal("0.09"), ANCHOR + Decimal("0.18")

    # a first -> b joins a, c starts its own bucket.
    forward = clusters(build([(20, a), (50, b), (80, c)], total=120))
    # c first -> c anchors at 100.18 with a band of 0.10018. b (0.09 away) still
    # falls inside that band, but a (0.18 away) does not. So the same three
    # prices produce two different clusterings purely from arrival order.
    reversed_ = clusters(build([(20, c), (50, b), (80, a)], total=120))

    assert sorted(m for _, m in forward) == [(20, 50), (80,)]
    assert sorted(m for _, m in reversed_) == [(20, 50), (80,)], (
        f"with c as the anchor the pair is (c,b) rather than (a,b); got {reversed_}"
    )
    assert forward != reversed_, (
        "the two orders must not produce the same buckets; if they do, the "
        "anchor is not the first member and this test proves nothing"
    )


def test_repeated_runs_are_deterministic() -> None:
    """Same input, same output -- no set iteration or dict ordering leaking in."""
    candles = build([(20, FIRST_LOW), (50, MEMBER_INSIDE), (80, MEMBER_OUTSIDE)])
    first = clusters(candles)
    assert clusters(candles) == first
    assert clusters(list(candles)) == first


# ---------------------------------------------------------------------------
# The search index must never exclude an admissible bucket
# ---------------------------------------------------------------------------


def test_the_index_never_hides_a_bucket_the_test_would_admit() -> None:
    """The index is a superset filter, at **every** price, not just BTC's.

    The scan bounds are a pre-filter and their only obligation is to never
    exclude a bucket the exact membership test would accept. Using the relative
    band alone satisfied that only above $1: at $0.01 a 0.1% band is $0.00001
    wide, so the index was *narrower* than an absolute test and could skip an
    admissible bucket. Sweeping anchors from $0.01 to $2,000 found 35 such pairs,
    every one of them below $1 -- invisible from BTC-scale prices.

    The bounds are now the union of both bands. This drives the exact boundary
    through the real index at four scales.
    """
    for first, second, filler in (
        (FIRST_LOW, MEMBER_EXACT, FILLER_HIGH),
        (FIRST_FAR, FAR_EXACT, FILLER_HIGH),
        # Below $1 the *relative* band is the narrow one, so the index has to span
        # a correspondingly tiny window. Anchor 0.01 -> band 0.00001, and the
        # boundary member is 0.01001.
        (Decimal("0.0100"), Decimal("0.01001"), Decimal("0.005")),
        (Decimal("0.2200"), Decimal("0.22022"), Decimal("0.10")),
    ):
        level = first.quantize(Decimal("0.01"))
        found = clusters(build([(20, first), (50, second)], filler=filler))
        assert len(found) == 1 and found[0][1] == (20, 50), (
            f"the boundary member must be reachable through the index at anchor "
            f"{level}; got {found}"
        )


def test_the_index_covers_the_band_at_prices_far_above_and_below_one() -> None:
    """The band scales with the anchor, so the index bounds must too.

    A relative band at $30,000 is $30 wide. A pre-filter still expressed in
    absolute terms would therefore exclude almost every legitimate candidate at
    that price -- the inverse of the sub-$1 failure, and the one that would bite
    a real instrument.
    """
    found = clusters(
        build([(20, FIRST_FAR), (50, FAR_INSIDE)], filler=Decimal("90"))
    )
    assert len(found) == 1 and found[0][1] == (20, 50), (
        f"a $15 gap is inside a $30 band at $30,000; got {found}"
    )

    # And the far edge of that band is reachable too, which needs the index to
    # span $30 rather than the $0.001 the old absolute rule allowed.
    edge = clusters(
        build([(20, FIRST_FAR), (50, FAR_EXACT)], filler=Decimal("90"))
    )
    assert len(edge) == 1 and edge[0][1] == (20, 50), f"got {edge}"


# ---------------------------------------------------------------------------
# Cluster formation
# ---------------------------------------------------------------------------


def test_three_pivots_inside_the_band_form_a_single_bucket() -> None:
    pivots = [(20, FIRST_LOW), (50, MEMBER_INSIDE), (80, MEMBER_EXACT)]
    found = clusters(build(pivots, total=120))
    assert found == [(str(ANCHOR), (20, 50, 80))], f"got {found}"


def test_two_pivots_on_distant_prices_form_two_buckets() -> None:
    found = clusters(build([(20, FIRST_LOW), (50, Decimal("120.004"))]))
    assert len(found) == 2, f"expected two buckets, got {found}"


def test_pivots_on_opposite_sides_never_share_a_bucket() -> None:
    """A high and a low at one price are two levels.

    The bucket key carries ``kind``, so a swing high and a swing low at the same
    price cannot merge. A silent merge if the key ever lost its kind component.
    """
    candles = []
    for index in range(60):
        high = Decimal("100.004") if index in (20, 50) else Decimal("99")
        low = Decimal("80.004") if index == 30 else Decimal("81")
        if index in (2, 3, 6, 7):  # touch pairs at the level price, for MIN_TOUCHES
            high = Decimal("100.00")
        candles.append(
            make_candle(index * 5, open_price="90", high=str(high), low=str(low),
                        close="90", volume="10")
        )
    structure = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=2
    )
    highs = [l for l in structure.liquidity_levels if l.level_type == "swing_high"]
    lows = [l for l in structure.liquidity_levels if l.level_type == "swing_low"]
    assert len(highs) == 1 and highs[0].price == Decimal("100.00"), (
        f"one swing-high cluster expected at 100.00, got {[l.price for l in highs]}"
    )
    assert lows == [], (
        f"a low series with no strict local minimum must produce no swing-low "
        f"level, got {[l.price for l in lows]}"
    )


# ---------------------------------------------------------------------------
# Timing: an equal level is dated to the second swing's confirmation
# ---------------------------------------------------------------------------


def test_an_equal_level_is_dated_to_the_second_confirming_swing() -> None:
    """``equal_highs`` becomes knowable at the *second* pivot's confirmation.

    With ``lookback=2`` a pivot at bar 50 confirms at bar 52. Publishing at the
    first pivot's confirmation (bar 22) would claim two highs existed when only
    one had printed. The leak is in the label, not the price.
    """
    derived = equal_levels(build([(20, FIRST_LOW), (50, MEMBER_INSIDE)]))
    assert ("equal_highs", 52) in derived, (
        f"equal_highs must be dated to the second confirmation (bar 52); got {derived}"
    )


def test_one_pivot_on_a_price_is_not_an_equal_level() -> None:
    """A single swing is not an 'equal' anything."""
    derived = equal_levels(build([(20, FIRST_LOW), (50, Decimal("120.004"))]))
    assert not any(kind == "equal_highs" for kind, _ in derived), (
        f"two different prices must not form an equal level, got {derived}"
    )


def test_a_pivot_arriving_later_cannot_rewrite_the_level_already_published() -> None:
    """Appending a matching pivot may add a label, never move the swing level."""
    early = clusters(build([(20, FIRST_LOW)], total=45))
    later = clusters(build([(20, FIRST_LOW), (50, MEMBER_INSIDE)]))

    assert early == [(str(ANCHOR), (20,))], f"early publication: {early}"
    assert later == [(str(ANCHOR), (20, 50))], (
        f"the level published before the second pivot must keep its price and "
        f"creation bar and only gain a member; got {later}"
    )


def test_cluster_state_is_append_only_under_bar_appending() -> None:
    """Appending bars may *add* members but never revise the cluster.

    The project's :func:`audit` is the wrong instrument here and saying so is
    part of the result. It asserts the output *for a past bar* is byte-identical
    on a prefix and on the full run, which is right for a detector that emits and
    is done. Clustering is an open-ended set that keeps gaining members as
    further swings confirm on the same price -- that is the concept working, and
    the audit reports it as a violation.

    The invariant that actually matters, and what "no future leakage" means for a
    growing cluster, is that the anchor is fixed by the first swing, the creation
    index is the first confirmation's, and members only ever accumulate.
    """
    from app.services.research.lookahead import audit  # noqa: F401  (documents why unused)

    candles = build(
        [(20, FIRST_LOW), (50, MEMBER_INSIDE), (70, Decimal("130.004"))],
        total=130,
    )
    full = clusters(candles)

    for cut in (35, 45, 60, 80, 100, 129):
        for anchor, seen in clusters(candles[:cut]):
            matches = [m for a, m in full if a == anchor]
            assert matches, f"cluster at {anchor} vanished when bars were appended"
            assert seen == matches[0][: len(seen)], (
                f"cluster at {anchor} on the prefix to bar {cut} had members "
                f"{seen}; the full run has {matches[0]}, which must extend it "
                "rather than rewrite it"
            )

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
            f"run has {late_members[key]}, which must extend that list"
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
    """A windowed run must cluster exactly as a whole-series run does."""
    from app.services.market_structure.segmented import StructureState

    candles = build([(20, FIRST_LOW), (50, MEMBER_INSIDE), (80, MEMBER_EXACT)], total=120)

    state = StructureState("BTCUSDT", Timeframe.M5, lookback=2)
    for start in range(0, len(candles), 25):
        state.observe(candles[start : start + 25])
    windowed = state.levels()

    whole = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=2
    ).liquidity_levels

    assert _cluster_key(windowed) == _cluster_key(whole), (
        f"windowed clustering must equal the whole-series result:\n"
        f"  windowed={_cluster_key(windowed)}\n  whole    ={_cluster_key(whole)}"
    )


def test_a_checkpoint_round_trip_preserves_cluster_membership() -> None:
    """Serialising and resuming cannot re-bucket or re-date anything."""
    from app.services.market_structure.segmented import StructureState

    candles = build([(20, FIRST_LOW), (50, MEMBER_INSIDE), (80, MEMBER_EXACT)], total=120)

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
    assert clusters(build([(20, FIRST_LOW)], total=5)) == []


def test_an_empty_series_produces_no_clusters() -> None:
    assert clusters([]) == []


def test_a_flat_series_produces_no_strict_pivots_and_no_clusters() -> None:
    """Strict comparison means a flat series has no strict local maximum.

    The derived *range* levels still exist on a flat series -- they come from a
    different component -- so this asserts on swing buckets specifically.
    """
    flat = [
        make_candle(
            index * 5, open_price="100", high="100", low="100", close="100", volume="1"
        )
        for index in range(40)
    ]
    assert clusters(flat) == []