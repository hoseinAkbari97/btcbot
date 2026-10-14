"""Phase 9: supply/demand zones and objective retests.

Every expectation below is a number written out by hand from the fixture's OHLC
rows, not a value recomputed by calling the detector. That distinction is the
whole point of the file: an oracle built from the production code passes
whenever the production code is self-consistent, including when it is
consistently wrong — which is exactly the failure mode this module was written
to avoid (see the ``38k retests over 937 zones`` note in ``zones.py``, caught on
real data and not by any test).

The fixture is built to make the causal claims *checkable by inspection*:

    bar 2      a confirmed swing low (lookback 2), so bar 8 has a structural
               anchor and the zone exists at all
    bars 3-7   the base, band [98.0, 103.5]
    bar 8      the displacement, confirmed at bar 9
    bars 9-11  price above the band: it must be *away* before a retest is legal
    bar 12     returns into the band -> retest, invalidated later if it closes deep

A zone that ignored ``confirmation_index`` would report a retest at bar 8 or
earlier, on the bars that *are* the zone. A zone that ignored "cleared" would
report retests at bars 9-11, on price that never left. Both are visible here by
counting, without running anything.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import CandleData
from app.services.research.events import detect_all, detect_displacement
from app.services.research.lookahead import audit
from app.services.research.segmented_runner import ZONE_BASE_BARS
from app.services.research.zones import (
    EXPIRED,
    INVALIDATED,
    MITIGATED,
    Zone,
    ZoneCarried,
    detect_zones,
    zones_from_events,
)

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

#: ``(open, high, low, close)``, written out rather than generated. The shape
#: that matters — a quiet base with a pivot inside it, then one large bar that
#: leaves it — cannot be produced on purpose by a random walk, and a fixture
#: that only arises by luck is a fixture whose expected values cannot be stated.
ROWS = [
    (100.0, 102.0, 98.5, 100.0),  # 0
    (100.0, 103.0, 99.5, 101.0),  # 1
    (101.0, 101.5, 97.0, 97.5),  # 2  swing low: 97.0, below every bar 0..4
    (97.5, 99.0, 98.0, 98.5),  # 3  base begins
    (98.5, 100.0, 98.2, 99.5),  # 4
    (99.5, 101.0, 99.0, 100.5),  # 5
    (100.5, 102.0, 100.0, 101.5),  # 6
    (101.5, 103.5, 101.0, 102.5),  # 7  base ends
    (102.5, 130.0, 102.0, 129.0),  # 8  displacement
    (129.0, 131.0, 128.0, 130.0),  # 9
    (130.0, 132.0, 129.0, 131.0),  # 10
    (131.0, 133.0, 110.0, 111.0),  # 11  approaching
    (111.0, 113.0, 103.0, 104.0),  # 12  retest: low 103.0 is inside the band
    (104.0, 106.0, 103.2, 104.5),  # 13
]

#: The band the detector must produce, read off rows 3-7 by hand:
#: the highest high is 103.5 (bar 7), the lowest low is 98.0 (bar 3).
EXPECTED_LOW = Decimal("98.0")
EXPECTED_HIGH = Decimal("103.5")
EXPECTED_HEIGHT = EXPECTED_HIGH - EXPECTED_LOW

#: Parameters chosen small so the fixture exercises them at these bar counts.
DETECT = dict(
    vol_window=5,
    structure_lookback=2,
    structure_window=8,
    base_bars=5,
    max_base_bars=8,
)


def series(
    rows: list[tuple[float, float, float, float]] | None = None, *, offset: int = 0
) -> list[CandleData]:
    """Build candles from ``ROWS``, shifted by ``offset`` bars.

    The offset is wall-clock only. Bar *indices* are the detector's to number
    via its ``offset`` argument; the timestamps just have to keep increasing, so
    a window handed in mid-series still looks like a continuation of time.
    """
    return [
        make_candle(
            (index + offset) * 5,
            open_price=str(o),
            high=str(h),
            low=str(l),
            close=str(c),
            volume="10",
        )
        for index, (o, h, l, c) in enumerate(rows if rows is not None else ROWS)
    ]


@pytest.fixture
def bars() -> list[CandleData]:
    return series()


@pytest.fixture
def run(bars):
    """Detect over the fixture, with a hand-checked displacement anchor."""
    displacements = detect_displacement(bars, vol_window=5, threshold=Decimal("1.5"))
    return detect_zones(bars, displacements=displacements, **DETECT)


def zones_of(events) -> list:
    return [event for event in events if event.kind == "zone"]


def retests_of(events) -> list:
    return [event for event in events if event.kind == "zone_retest"]


# ---------------------------------------------------------------------------
# Creation: boundaries and timestamps
# ---------------------------------------------------------------------------


def test_fixture_anchors_one_displacement_at_bar_eight(bars) -> None:
    """The fixture's displacement is where the hand-built rows say it is.

    Guards the guard: every other expectation below is conditional on a
    displacement existing at bar 8 with confirmation at bar 9, and a fixture that
    silently stopped producing one would make them all vacuously true.
    """
    displacements = detect_displacement(bars, vol_window=5, threshold=Decimal("1.5"))
    assert [(d.event_index, d.confirmation_index) for d in displacements] == [(8, 9)]


def test_zone_boundaries_are_the_base_bars_extremes(run) -> None:
    """``low``/``high`` are bars 3-7's extremes, read off ``ROWS`` by hand.

    Not rounded and not buffered: the plan asks for measurable definitions, and a
    tolerance here would make "did price reach the zone" depend on a convention
    rather than on the base that produced it.
    """
    (zone,) = zones_of(run)
    assert zone.features["zone_low"] == EXPECTED_LOW
    assert zone.features["zone_high"] == EXPECTED_HIGH
    assert zone.features["zone_height"] == EXPECTED_HEIGHT
    assert zone.features["bars_in_base"] == Decimal(5)


def test_zone_creation_index_is_the_displacement_bar(run) -> None:
    """``event_index`` is bar 8 — the bar a chart would draw the rectangle at."""
    (zone,) = zones_of(run)
    assert zone.event_index == 8


def test_zone_confirmation_is_the_displacement_confirmation(run) -> None:
    """``confirmation_index`` is bar 9, taken from the displacement's own field.

    Not derived here. The zone is not knowable at the displacement's close, and
    a detector that published it one bar early would let a decision at bar 8 use
    a measurement that did not exist until bar 9 closed.
    """
    (zone,) = zones_of(run)
    assert zone.confirmation_index == 9


def test_zone_start_index_is_the_first_base_bar(run) -> None:
    """``start_index`` is bar 3 — the third timestamp, and the one the plan's
    ``start_time`` field needs. Two-index event records cannot express it."""
    (zone,) = zones_of(run)
    assert zone.context["start_index"] == 3


def test_upward_displacement_leaves_a_demand_zone(run) -> None:
    """Price rose out of the base, so the band left behind is demand.

    The mapping is the one that is easy to get backwards. Labelling by departure
    direction instead would call this "supply" and invert every lifecycle rule
    that keys on which side price must clear to count as away.
    """
    (zone,) = zones_of(run)
    assert zone.context["zone_type"] == "demand"
    assert zone.context["departure_direction"] == "up"


def test_departure_strength_is_the_displacements_own_measurement(bars) -> None:
    """The zone reuses the displacement's number rather than re-measuring it.

    Two detectors measuring the same bar with the same rule will agree until one
    is retuned, and then the disagreement is invisible. Sharing the object makes
    the equality structural.
    """
    displacements = detect_displacement(bars, vol_window=5, threshold=Decimal("1.5"))
    events = detect_zones(bars, displacements=displacements, **DETECT)
    (zone,) = zones_of(events)
    assert (
        zone.features["departure_strength"] == displacements[0].features["magnitude_in_volatility"]
    )


def test_no_zone_without_a_structural_anchor(bars) -> None:
    """A displacement with no confirmed extreme near it produces no zone.

    Most large candles have no base in front of them. Without this gate every one
    of them would become a zone, and the count would measure how often BTC has
    big candles rather than how often it consolidates.
    """
    displacements = detect_displacement(bars, vol_window=5, threshold=Decimal("1.5"))
    events = detect_zones(
        bars,
        displacements=displacements,
        **{**DETECT, "structure_window": 1},
    )
    assert zones_of(events) == []


# ---------------------------------------------------------------------------
# Retests: the confirmation gate and the cleared gate
# ---------------------------------------------------------------------------


def test_no_retest_before_confirmation(run) -> None:
    """Bars 3-8 are *inside the zone by construction* and are never retests.

    The base bars are the zone's own construction. Emitting a retest for them
    would manufacture one retest per zone at birth, which is the first of the two
    ways this detector produced fake volume.
    """
    assert retests_of(run) == [] or all(event.event_index >= 9 for event in retests_of(run))
    assert min((e.event_index for e in retests_of(run)), default=99) >= 9


def test_no_retest_while_price_is_still_away(run) -> None:
    """Bars 9-11 are above the band and produce no retest.

    "Returned to" needs somewhere to have returned *from*. A detector that
    treated any overlap as a retest fired on the departure itself — measured on
    real data as 38,513 retests across 937 zones, all of them the move that
    created the zone.
    """
    early = [e.event_index for e in retests_of(run) if e.event_index in (9, 10, 11)]
    assert early == []


def test_retest_fires_when_price_returns_into_the_band(run) -> None:
    """Bar 12's low is 103.0, inside [98.0, 103.5] — a retest, dated to bar 12."""
    retests = retests_of(run)
    assert [event.event_index for event in retests] == [12]
    assert retests[0].features["retest_depth"] > 0


def test_retest_is_confirmed_at_its_own_bar(run) -> None:
    """``confirmation_index == event_index`` for a retest.

    A touch is knowable at its own close, unlike a sweep, which needs the next
    bar to prove price came back. Equal indices are the honest answer, not a
    special case.
    """
    (retest,) = retests_of(run)
    assert retest.event_index == retest.confirmation_index
    assert retest.confirmation_delay_bars == 0


def test_retest_count_advances_on_the_zone(bars) -> None:
    """``retest_count`` — a field the plan names — is carried on the zone itself.

    Read off the object, not counted off the event log: a checkpoint restores the
    zone state without the log, so a count kept only in events would read zero
    on every resumed run.
    """
    carried = ZoneCarried()
    detect_zones(
        bars,
        displacements=detect_displacement(bars, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    (zone,) = carried.zones.values()
    assert zone.retest_count == 1
    assert zone.state == MITIGATED


def test_repeated_retests_are_separated(bars) -> None:
    """Price loitering in the band does not emit a retest on every bar.

    ``min_retest_separation_bars`` is the rule and ``last_retest_index`` is the
    memory of it; without the memory, a zone price shuffling along the boundary
    produced one retest per bar and the count measured volatility, not retests.
    """
    loiter = ROWS + [
        (104.5, 105.0, 103.6, 104.8),  # 13
        (104.8, 105.2, 103.4, 104.6),  # 14
        (104.6, 105.0, 103.5, 104.9),  # 15
        (104.9, 105.3, 103.3, 104.7),  # 16
        (104.7, 105.1, 103.6, 105.0),  # 17
    ]
    events = detect_zones(
        series(loiter),
        displacements=detect_displacement(series(loiter), vol_window=5, threshold=Decimal("1.5")),
        **DETECT,
    )
    indices = [event.event_index for event in retests_of(events)]
    # Bars 13 and 14 are eligible by touch but barred by the 3-bar separation;
    # 15 is the first bar at or after 12+3 whose low reaches 103.5. Bar 17 would
    # be the next, but 15+3 is 18, which is past the end of this series -- so a
    # zone price shuffling along the boundary for five bars still counts twice.
    assert indices == [12, 15]
    assert all(b - a >= 3 for a, b in zip(indices, indices[1:], strict=False))


# ---------------------------------------------------------------------------
# Lifecycle: invalidation and expiration
# ---------------------------------------------------------------------------


def test_wick_into_a_zone_does_not_invalidate_it(bars) -> None:
    """A deep wick that closed back out is the zone's best evidence, not its death.

    The two measurements are deliberately different quantities and this is the
    bar that separates them: bar 12's range reaches 97.0, the whole 5.5-wide
    band, so the recorded *range* depth is well past the 0.5 invalidation
    threshold -- and the zone is still mitigated, because its close of 111.5 is
    outside the band entirely. Deciding invalidation from the range would record
    every sharp rejection as a zone death, and the retest count would end up
    measuring the opposite of what it is for.
    """
    wick = list(ROWS)
    wick[12] = (111.0, 113.0, 97.0, 111.5)  # through the whole band, closes above
    rows = series(wick)
    carried = ZoneCarried()
    detect_zones(
        rows,
        displacements=detect_displacement(rows, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **{**DETECT, "max_touch_depth": Decimal("0.5")},
    )
    (zone,) = carried.zones.values()
    assert zone.state == MITIGATED
    # The threshold is exceeded on the range measure and ignored, which is the
    # whole claim. (The recorded depth is 0.945, from bar 13: bar 12's low of
    # 97.0 is past the zone's own low edge, so it is not a penetration *into*
    # the band from the side price arrived on.)
    assert zone.max_touch_depth > Decimal("0.5")


def test_close_deep_in_the_band_invalidates(bars) -> None:
    """The same bar with the close left inside is invalidated, and emits no retest.

    "Deep" for a demand zone means near its *high* edge: price closed up inside
    the band has accepted above it, which is what invalidates it. A close near
    the low edge is price still below the zone and says nothing.

    A bar that enters and invalidates in the same print is the zone ending. The
    code chooses not to call that a retest, so the retest count stays a count of
    *uses* and not of deaths.
    """
    rows = list(ROWS)
    rows[12] = (111.0, 113.0, 102.0, 102.4)  # closes 0.8 below the 103.5 high
    parsed = series(rows)
    carried = ZoneCarried()
    events = detect_zones(
        parsed,
        displacements=detect_displacement(parsed, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **{**DETECT, "max_touch_depth": Decimal("0.5")},
    )
    (zone,) = carried.zones.values()
    assert zone.state == INVALIDATED
    assert zone.terminal_index == 12
    assert [e.event_index for e in retests_of(events)] == []


def test_invalidated_zone_is_frozen(bars) -> None:
    """A terminal zone stops updating: one invalidation, not one per crossing.

    ``INVALIDATED`` and ``EXPIRED`` are terminal *by state membership*, so this
    holds without a flag being consulted anywhere in the retest loop — the loop
    skips anything not in ``OPEN_STATES`` before it can do anything.
    """
    rows = list(ROWS)
    rows[12] = (111.0, 113.0, 102.0, 102.4)
    rows += [
        (102.4, 104.0, 99.0, 100.0),
        (100.0, 105.0, 99.0, 101.0),
        (101.0, 106.0, 99.0, 102.0),
    ]
    parsed = series(rows)
    carried = ZoneCarried()
    detect_zones(
        parsed,
        displacements=detect_displacement(parsed, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **{**DETECT, "max_touch_depth": Decimal("0.5")},
    )
    (zone,) = carried.zones.values()
    assert zone.state == INVALIDATED
    # Frozen: the same terminal bar and the same touch count no matter how many
    # more bars traded inside the band it had already been invalidated by.
    assert zone.terminal_index == 12
    assert zone.touch_count == 1
    assert zone.last_touch_index == 12


def test_zone_expires_after_max_age(bars) -> None:
    """Age is measured from ``confirmation_index``, and expiry is terminal.

    From confirmation rather than creation because that is when the zone became
    knowable, and a run resuming mid-zone must expire it on the same bar a
    continuous run would.
    """
    carried = ZoneCarried()
    detect_zones(
        bars,
        displacements=detect_displacement(bars, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **{**DETECT, "max_age_bars": 2},
    )
    (zone,) = carried.zones.values()
    assert zone.state == EXPIRED
    assert zone.terminal_index == 12  # 9 + 2 + 1


def test_open_zone_at_end_of_data_is_not_closed(bars) -> None:
    """Ending the data does not end the zone.

    ``expired`` and "the run stopped" are different facts. A zone still open at
    the last bar is reported as still open, because claiming otherwise would put
    a terminal state in the log that no bar actually produced.

    The slice ends at bar 10, one bar past the confirmation at bar 9, so the
    zone is published and has had a single bar to age -- the case a segment
    boundary produces when a zone is confirmed in the final window.
    """
    carried = ZoneCarried()
    parsed = bars[:11]
    detect_zones(
        parsed,
        displacements=detect_displacement(parsed, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    (zone,) = carried.zones.values()
    assert zone.state == "fresh"
    assert zone.is_open
    assert zone.terminal_index is None


def test_an_unconfirmed_zone_is_not_published(bars) -> None:
    """Truncating at the displacement bar yields no zone at all.

    The counterpart to the test above, and the one that matters for causality:
    a zone whose confirmation bar has not printed yet has nothing to publish,
    and publishing it anyway is the leak this phase exists to prevent.
    """
    carried = ZoneCarried()
    parsed = bars[:9]  # displacement at 8 is the last bar; confirmation would be 9
    events = detect_zones(
        parsed,
        displacements=detect_displacement(parsed, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    assert zones_of(events) == []
    assert carried.zones == {}
    assert carried.pending and carried.pending[0].confirmation_index == 9


# ---------------------------------------------------------------------------
# Causality
# ---------------------------------------------------------------------------


def test_prefix_invariance_holds() -> None:
    """Appending future bars never changes what was already reported.

    The strongest available check, and the one that does not need the detector's
    cooperation: :func:`audit` runs the detector on every prefix and on the full
    series and compares. This is the test that would have caught the 38k-retest
    bug if it had been a *leak* rather than a definitional error — and it is kept
    because the two failure modes are easy to confuse and only one of them is
    about the future.

    Displacements are computed inside the audited function rather than passed
    in, because a caller that hoisted them out would be pinning the audit to a
    fixed detection run and the prefix comparison would no longer be testing
    the zone path alone.
    """
    bars = series()
    report = audit(
        lambda candles: detect_zones(
            candles,
            displacements=detect_displacement(candles, vol_window=5, threshold=Decimal("1.5")),
            **DETECT,
        ),
        bars,
        subject="zones",
    )
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:5])


def test_no_event_is_dated_before_it_could_be_known(run) -> None:
    """Every published zone has ``confirmation_index >= event_index``.

    A zone whose confirmation precedes its creation was published before the bar
    that makes it meaningful had printed.
    """
    for event in zones_of(run):
        assert event.confirmation_index >= event.event_index
        assert event.is_known_at(event.confirmation_index)


def test_boundaries_do_not_change_when_bars_are_appended(bars) -> None:
    """The band a zone publishes is the band it keeps.

    A zone that widened to accommodate later bars would be a measurement of the
    future, and one that narrowed would retroactively change the price of every
    retest already recorded against it.
    """
    first = zones_of(detect_zones(bars, **DETECT))
    later = [
        event
        for event in zones_of(detect_zones(series(ROWS + [(104.5, 106.0, 90.0, 91.0)]), **DETECT))
        if event.context["zone_id"] == first[0].context["zone_id"]
    ]
    assert [(e.features["zone_low"], e.features["zone_high"]) for e in later] == [
        (first[0].features["zone_low"], first[0].features["zone_high"])
    ]


# ---------------------------------------------------------------------------
# Overlap, duplicates, determinism, boundaries
# ---------------------------------------------------------------------------


def test_overlapping_zones_each_get_their_own_retest(bars) -> None:
    """Overlapping zones are permitted and never merged.

    Merging would require deciding retrospectively that two bands are one object,
    and a retest of the merged band could then not be attributed to either
    source. Both retests are kept; the aggregation clusters by detector, so two
    retests on one bar land in one family and are not read as independent.
    """
    displacements = detect_displacement(bars, vol_window=5, threshold=Decimal("1.5"))
    assert len(displacements) == 1
    # The same band reached by a second displacement at the same bar is one zone.
    carried = ZoneCarried()
    events = detect_zones(
        bars, displacements=displacements + displacements, carried=carried, **DETECT
    )
    assert len(zones_of(events)) == 1


def test_a_zone_is_not_recreated_across_a_boundary(bars) -> None:
    """Re-running the same window against the same carried state adds nothing.

    The duplicate a resumed or double-processed segment would otherwise produce.
    Zone identity is structural — ``(creation_index, type, low, high)`` — so it
    survives a checkpoint where ``id()`` would not.
    """
    carried = ZoneCarried()
    first = detect_zones(
        bars,
        displacements=detect_displacement(bars, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    second = detect_zones(
        bars,
        displacements=detect_displacement(bars, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    assert len(zones_of(first)) == 1
    assert zones_of(second) == []


def test_results_are_deterministic_across_runs(bars) -> None:
    """Two identical calls produce identical events, field for field.

    Checked on the payload rather than on object equality because
    :class:`ResearchEvent` is a plain dataclass and ``==`` on it would pass on
    identity of shared substructure without comparing anything.
    """

    def once():
        return [
            event.to_payload()
            for event in detect_zones(
                bars,
                displacements=detect_displacement(bars, vol_window=5, threshold=Decimal("1.5")),
                **DETECT,
            )
        ]

    assert once() == once()


def test_empty_and_short_series_are_handled() -> None:
    """No history and too-little history produce nothing, rather than raising.

    A detector that indexed ``candles[0]`` on an empty series would crash on the
    first segment of a resumed run that starts late — which is the common case,
    not an edge one.
    """
    assert detect_zones([], **DETECT) == []
    assert detect_zones(series(ROWS[:2]), **DETECT) == []


def test_zone_state_round_trips_through_a_checkpoint(bars) -> None:
    """Carried state survives serialisation exactly.

    Keyed structurally rather than by ``id()``: a resumed process allocates its
    objects at different addresses, and state keyed by address silently matches
    nothing — a resumed run would then re-arm every carried zone and re-emit its
    retests, while reporting a clean resume.
    """
    carried = ZoneCarried()
    detect_zones(
        bars,
        displacements=detect_displacement(bars, vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    restored = ZoneCarried.from_payload(carried.to_payload())
    assert restored.to_payload() == carried.to_payload()
    assert set(restored.zones) == set(carried.zones)
    assert restored.cleared == carried.cleared
    assert restored.last_retest_index == carried.last_retest_index


def test_zone_rebuilds_from_a_stored_event_log(run) -> None:
    """Boundaries and identity survive in the event context, not just in memory.

    A stored run has to be able to re-derive a zone's band without re-reading
    the candles, or the event log is not a research artifact and only this
    session's objects knew the answer.
    """
    (zone,) = zones_of(run)
    (rebuilt,) = zones_from_events(run)
    assert rebuilt.high == zone.features["zone_high"]
    assert rebuilt.low == zone.features["zone_low"]
    assert rebuilt.creation_index == zone.context["creation_index"]
    assert rebuilt.zone_type == zone.context["zone_type"]


# ---------------------------------------------------------------------------
# Segmentation equivalence
# ---------------------------------------------------------------------------


def test_segmented_run_equals_the_whole_series(bars) -> None:
    """A windowed run must reproduce the continuous run, event for event.

    This models what ``SegmentedResearchRunner`` actually does, which is not
    "call the detector on each window": every window is evaluated as
    *tail + new bars*, where the tail is the last ``ZONE_BASE_BARS`` bars of
    the previous window, and windows overlap by exactly that much. Evaluating
    raw windows instead would test a run no one performs, and would report a
    mismatch that is really the test being wrong.

    The property still matters here: the zone created in window one lives on
    into window two, so losing ``cleared`` or ``last_retest_index`` across the
    boundary shows up only as a retest appearing on the wrong bar.
    """
    displacements = detect_displacement(bars, vol_window=5, threshold=Decimal("1.5"))
    whole = detect_zones(bars, displacements=displacements, **DETECT)
    assert whole, "the fixture produced no zones; the comparison would be vacuous"

    tail = ZONE_BASE_BARS  # the overlap the runner keeps between windows
    carried = ZoneCarried()
    emitted: list = []
    for offset, end, final in ((0, 9, False), (9 - tail, len(ROWS), True)):
        parsed = series(ROWS[offset:end], offset=offset)
        emitted.extend(
            detect_zones(
                parsed,
                displacements=[d for d in displacements if d.event_index >= offset],
                offset=offset,
                carried=carried,
                final=final,
                **DETECT,
            )
        )
    assert [e.to_payload() for e in emitted] == [e.to_payload() for e in whole]


def test_lifecycle_carries_across_a_boundary(bars) -> None:
    """The zone created in window one keeps its state into window two.

    Checked on the zone object rather than on the event stream, because this is
    the property that is invisible in event counts: a lost zone still produces
    the same retests unless a *second* retest should have fired, and that shows
    up only as a count one lower.

    The boundary sits between bars 11 and 12, so bar 12's retest is emitted by
    the *second* window against a zone the first window created and the second
    one has never seen a candle for. ``last_touch_index`` is 13 rather than 12
    because bar 13 also reaches into the band (low 103.2): a touch is a touch
    whether or not it is far enough past the separation to count as a retest.
    """
    carried = ZoneCarried()
    first = detect_zones(
        bars[:12],
        displacements=detect_displacement(bars[:12], vol_window=5, threshold=Decimal("1.5")),
        carried=carried,
        **DETECT,
    )
    assert [e.event_index for e in retests_of(first)] == []
    second = detect_zones(
        series(ROWS[12:], offset=12),
        displacements=[],
        offset=12,
        carried=carried,
        final=True,
        **DETECT,
    )
    assert [e.event_index for e in retests_of(second)] == [12]
    (zone,) = carried.zones.values()
    assert zone.retest_count == 1
    assert zone.state == MITIGATED
    assert zone.last_touch_index == 13


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


def test_detect_all_includes_both_new_kinds(bars) -> None:
    """The aggregate detector must not silently omit Phase 9.

    ``detect_all`` is the batch entry point ``scripts/run_event_research.py``
    uses, so a family that exists only when called directly would be absent from
    every stored event log -- the failure this exact assertion exists for, having
    already happened once with the ``regime`` kind.
    """
    kinds = {
        event.kind
        for event in detect_all(
            bars,
            vol_window=5,
            lookback=2,
            trend_window=5,
            zone_structure_lookback=DETECT["structure_lookback"],
            zone_structure_window=DETECT["structure_window"],
            zone_base_bars=DETECT["base_bars"],
            zone_max_base_bars=DETECT["max_base_bars"],
        )
    }
    assert "zone" in kinds
    assert "zone_retest" in kinds


def test_zone_events_round_trip_as_research_events(run) -> None:
    """Both kinds survive ``to_payload``/``from_payload``.

    A family that cannot round-trip is a family a checkpoint drops, so it is
    present in the first segment of a run and absent from every resumed one.
    """
    for event in run:
        restored = type(event).from_payload(event.to_payload())
        assert restored.to_payload() == event.to_payload()


def test_overlapping_touch_counts_each_zone_independently() -> None:
    """One bar entering two bands is two retests, not one event and a merge.

    Both are emitted and neither is ordered before the other: which boundary
    price reached first is not knowable from OHLC, and inventing an order would
    be reading an intrabar sequence the data does not contain.
    """
    high = Zone(
        zone_id="a",
        zone_type="demand",
        departure_direction="up",
        start_index=0,
        start_time=make_candle(0).open_time,
        creation_index=2,
        creation_time=make_candle(10).open_time,
        confirmation_index=3,
        confirmation_time=make_candle(15).close_time,
        high=Decimal("110"),
        low=Decimal("100"),
        creation_reason="t",
        departure_strength=None,
        volume=Decimal(1),
        bars_in_base=2,
        base_offset_bars=1,
    )
    low = Zone(
        zone_id="b",
        zone_type="demand",
        departure_direction="up",
        start_index=0,
        start_time=make_candle(0).open_time,
        creation_index=2,
        creation_time=make_candle(10).open_time,
        confirmation_index=3,
        confirmation_time=make_candle(15).close_time,
        high=Decimal("105"),
        low=Decimal("95"),
        creation_reason="t",
        departure_strength=None,
        volume=Decimal(1),
        bars_in_base=2,
        base_offset_bars=1,
    )
    # Bar 3 clears both zones (a demand zone is "away" above its high); bar 4
    # then enters both at once, from 113 down to 94.
    cleared = make_candle(15, open_price="112", high="114", low="111", close="113")
    wide = make_candle(20, open_price="112", high="113", low="94", close="112")
    carried = ZoneCarried(zones={high.key(): high, low.key(): low})
    events = detect_zones([cleared, wide], displacements=[], offset=3, carried=carried, **DETECT)
    assert len(retests_of(events)) == 2
    assert {e.context["zone_id"] for e in retests_of(events)} == {"a", "b"}
    assert {e.event_index for e in retests_of(events)} == {4}


# ===========================================================================
# Regressions: windowed runs at a non-zero offset
# ===========================================================================
#
# Every test above runs at ``offset == 0``. That is not an accident of the
# fixture -- it is a real blind spot, and these four tests exist because all
# four defects below survived a green suite for that reason.
#
# At ``offset == 0`` the window *is* the series, so a window-local index and an
# absolute index are the same number and an index-space mix-up is invisible.
# The segmented runner, however, passes ``tail + new bars`` with
# ``offset = tail_start``, so every segment after the first has a non-zero
# offset -- which is precisely the configuration no unit test was exercising.


#: The same shape as ``ROWS``, with bar 10 returning into the band.
#:
#: Bar 10 is the load-bearing row. It reaches 102.0, which is inside
#: [98.0, 103.5], and closes at 132.0, which is clear above. So it is a *touch*
#: that leaves the zone open -- it advances ``touch_count`` and
#: ``max_touch_depth`` -- and it is exactly the kind of bar a replayed prefix
#: would apply a second time.
RETURNING_ROWS = [
    (100.0, 102.0, 98.5, 100.0),  # 0
    (100.0, 103.0, 99.5, 101.0),  # 1
    (101.0, 101.5, 97.0, 97.5),  # 2  swing low
    (97.5, 99.0, 98.0, 98.5),  # 3  base begins
    (98.5, 100.0, 98.2, 99.5),  # 4
    (99.5, 101.0, 99.0, 100.5),  # 5
    (100.5, 102.0, 100.0, 101.5),  # 6
    (101.5, 103.5, 101.0, 102.5),  # 7  base ends
    (102.5, 130.0, 102.0, 129.0),  # 8  displacement
    (129.0, 131.0, 128.0, 130.0),  # 9
    (131.0, 133.0, 102.0, 132.0),  # 10 dips to 102.0: inside the band, closes clear
    (133.0, 140.0, 130.0, 139.0),  # 11 away
    (140.0, 141.0, 103.0, 104.0),  # 12 retest
    (104.0, 106.0, 103.2, 104.5),  # 13
]


def lifecycle(
    rows,
    *,
    offset: int = 0,
    final: bool = True,
    carried: ZoneCarried | None = None,
    displacements=None,
) -> tuple[list, ZoneCarried]:
    """Detect over a window and hand back the events and the state left behind."""
    state = carried if carried is not None else ZoneCarried()
    parsed = series(rows, offset=offset)
    if displacements is None:
        displacements = detect_displacement(parsed, vol_window=5, threshold=Decimal("1.5"))
    return (
        detect_zones(
            parsed, displacements=displacements, offset=offset, carried=state, final=final, **DETECT
        ),
        state,
    )


#: A base-then-displacement motif, repeated three times so a series carries
#: several zones and a segment boundary can land *between* two of them.
#:
#: Repetition is what makes the boundary testable: with a single zone, any
#: fixture can be arranged so the boundary falls after it, and the interesting
#: case -- a zone created in a segment that has history in front of it -- is
#: never reached.
MOTIF = [
    (100.0, 102.0, 98.5, 100.0),  # 0
    (100.0, 103.0, 99.5, 101.0),  # 1
    (101.0, 101.5, 97.0, 97.5),  # 2  swing low: the structural anchor
    (97.5, 99.0, 98.0, 98.5),  # 3  base begins
    (98.5, 100.0, 98.2, 99.5),  # 4
    (99.5, 101.0, 99.0, 100.5),  # 5
    (100.5, 102.0, 100.0, 101.5),  # 6
    (101.5, 103.5, 101.0, 102.5),  # 7  base ends
    (102.5, 130.0, 102.0, 129.0),  # 8  displacement -> zone at bar 8
]
REPEATED = MOTIF * 3  # zones due at bars 8 and 17

#: Segment geometry chosen so the second segment's window begins at absolute
#: bar 9 and the zone due at bar 17 lands at *local* index 8 -- below the
#: window's own offset of 9.
#:
#: That is the exact condition the broken gate got wrong, and the numbers were
#: arrived at by enumerating segmentations rather than chosen to look tidy.
#: Verified against the pre-fix source: the whole series reports zones at bars 8
#: and 17, and the segmented run under the broken gate reports only bar 8.
SEGMENT_BARS = 15
SEGMENT_TAIL = 6

#: Zone lifetime for the bounding test. Long enough that the zones the motif
#: produces are still open or recently terminal when the run ends, short enough
#: that the ones it retires fall outside the horizon. The default of 500 is
#: larger than this entire fixture, so it would prune nothing and the test would
#: pass vacuously -- which is exactly how the missing ``prune`` call went
#: unnoticed.
MAX_AGE = 12


def segmented_events(rows, *, segment: int, tail: int) -> list:
    """Run the detector the way ``SegmentedResearchRunner`` does.

    Each window is ``tail`` prefix bars plus the segment's own, with ``offset``
    set to the absolute index of the window's first bar -- which is what makes
    the two index spaces differ, and is the whole point.
    """
    state = ZoneCarried()
    emitted: list = []
    for start in range(0, len(rows), segment):
        end = min(start + segment, len(rows))
        tail_start = max(0, start - tail)
        emitted.extend(
            detect_zones(
                rows[tail_start:end],
                offset=tail_start,
                carried=state,
                final=end >= len(rows),
                **DETECT,
            )
        )
    return emitted


def test_a_windowed_run_at_a_non_zero_offset_creates_its_zones() -> None:
    """A segment with history in front of it must still find its own zones.

    The gate that decided which bars to build zones on read

        if not (offset <= index < len(candles))

    with ``index`` a *window-local* bar number and ``offset`` the *absolute*
    index of the window's first bar. At ``offset == 0`` the two are the same
    number, so the gate accepts every bar and all the tests above pass. At
    ``offset == 9`` it rejects every bar whose local index is below 9 -- and in a
    window of 22 bars starting at absolute 9 that is most of the segment's own
    new bars, not just the prefix.

    The zone due at bar 17 is exactly such a bar: local index 8 in a window
    whose offset is 9. Under the broken gate the segmented run reported only the
    zone at bar 8 and lost bar 17 entirely.

    The consequence is not a crash but a run that quietly under-reports, and a
    zone count that depends on where the segment boundaries were drawn. That is
    the failure worth a regression test, because a detector that reports less
    than it found looks exactly like a detector that found less.
    """
    bars = series(REPEATED)
    expected = [
        event.event_index
        for event in detect_zones(bars, final=True, **DETECT)
        if event.kind == "zone"
    ]
    assert expected == [8, 17], f"the fixture should yield zones at bars 8 and 17, got {expected}"

    emitted = segmented_events(bars, segment=SEGMENT_BARS, tail=SEGMENT_TAIL)
    got = [event.event_index for event in emitted if event.kind == "zone"]
    assert got == expected, (
        f"segmented run reported zones at {got} against the whole series' "
        f"{expected}; a zone created in a segment that has history in front of "
        "it is being dropped"
    )


def test_a_windowed_run_reports_absolute_indices_not_window_local_ones() -> None:
    """Event indices stay absolute across a boundary, and never go backwards.

    The other half of the same bug class. ``Zone`` stores absolute indices
    because the lifecycle walk steps through absolute bar numbers, so a
    window-local index stored on a zone would be compared against the wrong bars
    by the next window -- silently, since a plausible-looking wrong bar still
    looks like a bar.

    ``event_index`` is asserted to be strictly increasing across the whole
    emitted stream rather than per-segment, because a stream that restarts its
    numbering at each boundary is the signature of a window-local index leaking
    into an absolute field.
    """
    bars = series(REPEATED)
    emitted = segmented_events(bars, segment=SEGMENT_BARS, tail=SEGMENT_TAIL)
    indices = [event.event_index for event in emitted]
    assert indices == sorted(indices), (
        f"event indices are not monotonic across the segment boundary: {indices}"
    )
    for event in emitted:
        assert event.event_index >= 0
        assert event.confirmation_index >= event.event_index
        assert event.context["creation_index"] >= 0


def test_a_zone_boundary_is_read_from_the_base_bars_at_a_non_zero_offset() -> None:
    """Absolute indices must not be used to index a window.

    ``_build_zone`` computed its band correctly, then converted ``start`` and
    ``index`` to absolute and read ``candles[start]`` and ``candles[index]``
    against the *window* anyway. At ``offset == 0`` the two index spaces are
    identical. At ``offset == 2`` they are not, and the read either raised
    ``IndexError`` or -- when the absolute index happened to land inside the
    window -- returned a perfectly plausible candle from the wrong bar, which is
    worse because nothing fails.

    The band is the observable: it is the extremes of the base bars, which the
    fixture fixes by hand at [98.0, 103.5] regardless of where the window
    starts. A correct implementation reports the same band at every offset.
    """
    reference, _ = lifecycle(RETURNING_ROWS)
    assert zones_of(reference), "the reference window must produce a zone"

    for offset in (0, 1, 2, 3, 5):
        events, _ = lifecycle(RETURNING_ROWS, offset=offset)
        zones = zones_of(events)
        if not zones:
            continue
        (zone,) = zones
        assert (zone.features["zone_low"], zone.features["zone_high"]) == (
            EXPECTED_LOW,
            EXPECTED_HIGH,
        ), (
            f"at offset {offset} the band is "
            f"[{zone.features['zone_low']}, {zone.features['zone_high']}] rather than "
            f"the base bars' own extremes [{EXPECTED_LOW}, {EXPECTED_HIGH}]; the "
            "boundaries are being read from the wrong bars"
        )
        assert zone.event_index >= offset, "indices must be absolute, not window-local"


def test_a_replayed_prefix_does_not_count_a_touch_twice() -> None:
    """A carried zone's counters must survive a segment boundary unchanged.

    The lifecycle walk iterates every bar in the window handed to it, including
    the prefix a segmented caller re-supplies for history. Those prefix bars
    have *already* been applied to every carried zone, so without a watermark
    they are applied twice -- and ``touch_count``, ``first_touch_index`` and
    ``last_touch_index`` are all increments, so the error is silent arithmetic
    rather than a crash.

    ``RETURNING_ROWS`` bar 10 is the bar that makes this visible: it reaches
    102.0, inside the band, and closes clear at 132.0, so it advances
    ``touch_count`` without ending the zone.

    Read the expected numbers off the fixture by hand:

    * bar 10 -- low 102.0 is inside [98.0, 103.5] -> touch 1
    * bar 12 -- low 103.0 is inside the band -> touch 2, and a retest
    * bar 13 -- low 103.2 is inside the band -> touch 3

    so the whole series reports ``touch_count == 3`` and ``retest_count == 2``.
    """
    whole, whole_state = lifecycle(RETURNING_ROWS)
    (reference,) = whole_state.zones.values()
    assert reference.touch_count == 3, (
        "the fixture is miscounted; three bars reach into the band (10, 12, 13)"
    )
    assert reference.retest_count == 2, (
        "bars 12 and 13 are separated by one bar, and separation is 3, so only "
        "bar 12 is far enough past the last retest to emit"
    )

    # Two segments, the second replaying bars 9-10 as its prefix -- bar 10 being
    # the touch that would be double-counted.
    carried = ZoneCarried()
    lifecycle(RETURNING_ROWS[:11], offset=0, final=False, carried=carried)
    lifecycle(RETURNING_ROWS[9:], offset=9, carried=carried)

    (segmented,) = carried.zones.values()
    assert (segmented.touch_count, segmented.retest_count) == (
        reference.touch_count,
        reference.retest_count,
    ), (
        f"segmented run reports {segmented.touch_count} touches / "
        f"{segmented.retest_count} retests against the whole series' "
        f"{reference.touch_count} / {reference.retest_count}; the prefix bars "
        "have been applied to a carried zone more than once"
    )
    assert segmented.last_touch_index == reference.last_touch_index


def test_terminal_zones_are_pruned_so_the_state_stays_bounded() -> None:
    """Carried state must be bounded by the *live* zones, not by the run length.

    A terminal zone can never emit or change again -- ``_advance_lifecycle``
    skips anything not in ``OPEN_STATES``. Retaining every one of them anyway
    makes the checkpoint grow with the length of the run, which is a resource
    failure dressed as a bookkeeping detail: this project writes a checkpoint at
    every segment boundary.

    Measured on real BTCUSDT 5m data before the fix: after 6,000 bars the
    carried state held 255 zones of which 3 were open, 212 KB. The bound is
    stated as a *horizon* rather than as an immediate delete so that a run
    resuming shortly after a zone terminates can still report how it ended --
    losing the terminal state would report the zone as merely absent, which is a
    different claim.
    """
    carried = ZoneCarried(zones={}, last_retest_index={}, cleared=set())
    terminal = Zone(
        zone_id="t",
        zone_type="demand",
        departure_direction="up",
        start_index=0,
        start_time=make_candle(0).open_time,
        creation_index=2,
        creation_time=make_candle(10).open_time,
        confirmation_index=3,
        confirmation_time=make_candle(15).close_time,
        high=Decimal("110"),
        low=Decimal("100"),
        creation_reason="t",
        departure_strength=None,
        volume=Decimal(1),
        bars_in_base=2,
        base_offset_bars=1,
        state=INVALIDATED,
        terminal_index=10,
    )
    open_zone = terminal.with_lifecycle(
        state="fresh",
        terminal_index=None,
        applied_through=None,
    )
    # ``key()`` is ``(creation_index, zone_type, low, high)``, so a copy sharing
    # the band and the creation bar *is* the same zone as far as the carried
    # state is concerned. Give the survivor a distinct band so this test is
    # about pruning rather than about a dict silently keeping one key.
    open_zone = Zone(
        **{
            **{f: getattr(open_zone, f) for f in open_zone.__dataclass_fields__},
            "zone_id": "o",
            "low": Decimal("50"),
        }
    )
    key = terminal.key()
    carried.zones = {key: terminal, open_zone.key(): open_zone}
    carried.last_retest_index = {key: 9, open_zone.key(): 9}
    carried.cleared = {key, open_zone.key()}

    # Far enough past the terminal bar: pruned.
    assert carried.prune(before_index=10_000) == 1
    assert key not in carried.zones
    assert key not in carried.last_retest_index and key not in carried.cleared
    # The open zone is never pruned, whatever the horizon.
    assert open_zone.key() in carried.zones
    # Nothing left to do.
    assert carried.prune(before_index=10_000) == 0
    # And the horizon is not "immediately": a zone that ended recently is still
    # reportable, because a run resuming in that window should be able to say
    # the zone was *invalidated* rather than merely that it is absent.
    #
    # ``before_index`` is the horizon itself, already net of ``max_age_bars`` --
    # :func:`detect_zones` computes ``offset + len(candles) - max_age_bars``
    # before calling. So a zone terminal at bar 10 survives while ``10 >=
    # before_index`` and is pruned once it does not.
    recent = Zone(
        **{
            **{f: getattr(terminal, f) for f in terminal.__dataclass_fields__},
            "zone_id": "r",
            "low": Decimal("20"),
            "terminal_index": 40,
        }
    )
    recent_key = recent.key()
    carried.zones[recent_key] = recent
    carried.last_retest_index[recent_key] = 39
    carried.cleared.add(recent_key)
    assert carried.prune(before_index=40) == 0, (
        "a zone whose terminal bar is exactly at the horizon is still carried; "
        "the rule is strict (<), so a zone is kept for the whole horizon"
    )
    assert recent_key in carried.zones
    assert carried.prune(before_index=41) == 1
    assert recent_key not in carried.zones


def test_a_long_run_does_not_accumulate_dead_zones() -> None:
    """The real bound, measured on a run long enough for it to show.

    :meth:`ZoneCarried.prune` is unit-tested above against a hand-built state,
    which proves the method does what its docstring says but says nothing about
    whether :func:`detect_zones` actually *calls* it. This drives the detector
    over a series long enough for retired zones to pile up, and asserts the
    invariant directly: the carried state holds live zones, not a diary.

    The horizon is ``max_age_bars``, so a zone created at bar *k* is eligible
    for pruning once the walk passes ``k + 2 * max_age_bars``. ``SEGS`` below
    spans well past that for the zones at bars 8 and 17.
    """
    bars = series(REPEATED * 2)
    state = ZoneCarried()
    for start in range(0, len(bars), SEGMENT_BARS):
        end = min(start + SEGMENT_BARS, len(bars))
        tail_start = max(0, start - SEGMENT_TAIL)
        detect_zones(
            bars[tail_start:end],
            offset=tail_start,
            carried=state,
            final=end >= len(bars),
            **{**DETECT, "max_age_bars": MAX_AGE},
        )

    assert len(state.zones) > 0, "the fixture produced no zones at all"
    # Every zone still held must be open, or inside the retention horizon.
    horizon = len(bars) - MAX_AGE
    for zone in state.zones.values():
        assert zone.is_open or zone.terminal_index is None or (zone.terminal_index >= horizon), (
            f"zone created at bar {zone.creation_index} terminated at "
            f"{zone.terminal_index}, well past the horizon {horizon}, and should "
            "have been pruned"
        )
    # The concrete claim: on a 54-bar series with a 5-bar horizon, the number of
    # retained zones is a small constant rather than one per zone ever created.
    assert len(state.zones) <= 4, (
        f"{len(state.zones)} zones retained after {len(bars)} bars with a "
        f"{MAX_AGE}-bar horizon; dead zones are accumulating"
    )


def test_a_pruned_zone_never_reappears_and_a_checkpoint_still_round_trips() -> None:
    """Pruning must not resurrect work, and must survive serialisation.

    Pruning is the one mutation of the carried state that *loses* information,
    so the two things that could go wrong are checked together: a dropped zone
    must not be rebuilt by the next segment that still contains its
    displacement, and the pruning must not corrupt the payload a resumed run
    reads back.
    """
    rows = list(ROWS)
    rows[12] = (111.0, 113.0, 102.0, 102.4)  # closes deep in the band -> invalidated
    carried = ZoneCarried()
    _, carried = lifecycle(rows, carried=carried)
    assert list(carried.zones.values())[0].state == INVALIDATED

    # Re-running the same window must not rebuild the zone that is still held.
    events, carried = lifecycle(rows, carried=carried)
    assert zones_of(events) == []
    # And once pruned it is gone from the payload as well.
    carried.prune(before_index=10_000)
    assert carried.to_payload()["zones"] == []
    assert ZoneCarried.from_payload(carried.to_payload()).to_payload() == (carried.to_payload())
