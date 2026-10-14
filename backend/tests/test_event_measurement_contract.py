"""The event measurement contract: what "equal" means for a segmented run, and
what the existing checks demonstrably cannot see.

Background
----------
An earlier audit found 38 of 268,358 sweep events carrying a wrong
``time_above``, ``time_below`` and ``recovery_ratio`` at segment boundaries,
while **every aggregate matched**. That is the lesson this file encodes: a
research pipeline has two very different notions of equality, and only one of
them is usually checked.

Two notions
-----------
*aggregate* equality
    The outcome accumulator: total rows, truncated count, and a
    ``(detector, kind, side, stop_model)`` cell per family with its ``n``,
    ``mean``, ``variance``. Cheap, and the right check for "did the pipeline
    compute the same statistics".

*content* equality
    Every field of every event row, compared exactly. The only check that can
    see a wrong measurement.

The 38-event bug lived in the gap between them, and the reason is structural
rather than accidental: ``time_above``, ``time_below`` and ``recovery_ratio``
are recorded for downstream research but **never enter the outcome
accumulator at all**. No aggregate could ever have detected their corruption,
at any magnitude, however large. ``test_an_aggregate_check_cannot_see_a_wrong_
measurement`` pins that blindness deliberately, so the next person to trust an
aggregate comparison knows exactly what it does not cover.

Exactness: which fields get a tolerance, and why
-------------------------------------------------
**No field gets a tolerance.** That is a decision, not an oversight.

The one place a tolerance looked defensible was ``recovery_ratio``, where a
deferred sweep re-measures the same bar and 9 of 268,358 rows came back
different in the 28th decimal place -- a relative error of 2e-25. The cause was
real but removable: the excursion denominator was *reconstructed* as
``level * (1 + penetration)``, which is algebraically equal to
``|extreme - level|`` and numerically not. Carrying the value instead of
re-deriving it made the difference exactly zero.

A tolerance would have been the wrong repair. "Equal to within 1e-20" is not
equality, and adopting one would have created a permanent place where a real
difference could hide. It would also have been untestable in the only sense that
matters: a tolerance has to be chosen, and choosing it means choosing how much
corruption to accept. ``Decimal`` fields are exact by construction, prices are
compared as text rather than floats, and the whole point is that this does not
have to be revisited.
"""

from __future__ import annotations

import itertools
import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.core.resources import ResourceLimits
from app.schemas.market_data import Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.aggregate import OutcomeAccumulator, label_events_streaming
from app.services.research.events import (
    detect_compression,
    detect_liquidity_sweeps,
)
from app.services.research.segmented_runner import (
    COMPRESSION_VOL_WINDOW,
    SWEEP_EXCURSION_BARS,
    ZONE_BASE_BARS,
    ZONE_MAX_AGE_BARS,
    ZONE_MAX_BASE_BARS,
    ZONE_MAX_TOUCH_DEPTH,
    ZONE_MIN_RETEST_SEPARATION_BARS,
    ZONE_STRUCTURE_LOOKBACK,
    ZONE_STRUCTURE_WINDOW,
    SegmentedResearchRunner,
)
from app.services.research.streaming import stream_candles
from app.services.research.zones import detect_zones

DATASET = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "datasets"
    / "BTCUSDT-5m-20210101-20260901.json"
)
START = "2021-01-01"
END = "2021-02-01"


#: Every field a sweep row carries, per the specification's nine measurements plus
#: the level provenance and lifecycle attributes around them. Pinned so a future
#: field cannot be added and then left out of the content comparison -- the same
#: discipline ``test_liquidity_causality`` applies to ``features``.
#: A value that is obviously wrong. The point of the canary above is that even a
#: value this far out is invisible to an aggregate comparison.
OBVIOUSLY_WRONG = "999"


def _row_field_names(rows: list[dict]) -> set[str]:
    return {key for row in rows for key in row}


@pytest.fixture(scope="module")
def month() -> list:
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    from datetime import UTC, datetime

    end = datetime(2021, 2, 1, tzinfo=UTC)
    bars = []
    for candle in stream_candles(DATASET):
        if candle.open_time >= end:
            break
        bars.append(candle)
    return bars


def _zone_params() -> dict:
    return {
        "vol_window": COMPRESSION_VOL_WINDOW,
        "base_bars": ZONE_BASE_BARS,
        "max_base_bars": ZONE_MAX_BASE_BARS,
        "structure_lookback": ZONE_STRUCTURE_LOOKBACK,
        "structure_window": ZONE_STRUCTURE_WINDOW,
        "max_touch_depth": ZONE_MAX_TOUCH_DEPTH,
        "max_age_bars": ZONE_MAX_AGE_BARS,
        "min_retest_separation_bars": ZONE_MIN_RETEST_SEPARATION_BARS,
    }


#: Memo for :func:`continuous_events`. Detecting structure over a month of 5m
#: bars takes ~30 s and the segmented runs take ~35 s each; recomputing the
#: whole-series pass once per test added roughly four minutes to the suite for
#: no extra coverage. The result is deterministic and the fixture is
#: module-scoped, so caching it changes nothing about what is asserted.
#:
#: Keyed by ``id(bars)`` **and** holding a reference to ``bars``. Without the
#: reference a freed fixture's address could be reused by a different list and
#: the cache would return another run's events -- a wrong answer that looks
#: exactly like a right one.
_CONTINUOUS_CACHE: dict[int, tuple[list, list]] = {}


def continuous_events(bars: list) -> list:
    """The whole-series event list, in the order the runner emits."""
    key = id(bars)
    cached = _CONTINUOUS_CACHE.get(key)
    if cached is not None:
        return cached[1]
    structure = analyze_market_structure(
        bars, symbol="BTCUSDT", timeframe=Timeframe.M5
    )
    events = sorted(
        itertools.chain(
            detect_liquidity_sweeps(
                bars,
                levels=structure.liquidity_levels,
                excursion_bars=SWEEP_EXCURSION_BARS,
            ),
            detect_compression(bars, vol_window=COMPRESSION_VOL_WINDOW),
            detect_zones(bars, final=True, **_zone_params()),
        ),
        key=lambda e: (e.confirmation_index, e.kind, e.detector),
    )
    _CONTINUOUS_CACHE[key] = (bars, events)
    return events


def segmented_iter(tmp_path: Path, bars: list, *, segment_days: int):
    """Yield the segmented run's event rows one at a time.

    Streaming rather than returning a list: the whole-series side already holds
    ~78k event objects, and materialising a second full set of parsed dicts was
    the largest single allocation in this file. Comparing in lockstep also
    localises a failure to the first differing row instead of reporting a count.
    """
    from datetime import UTC, datetime

    runner = SegmentedResearchRunner(
        dataset=DATASET,
        symbol="BTCUSDT",
        limits=ResourceLimits(segment_days=segment_days),
        start=datetime(2021, 1, 1, tzinfo=UTC),
        end=datetime(2021, 2, 1, tzinfo=UTC),
        out_dir=tmp_path / f"stream{segment_days}",
    )
    runner.run()
    with runner.events_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _content_multiset(rows: list[dict]) -> list[str]:
    """Every row normalised to comparable text, sorted.

    Order-insensitive. Used only by the exactness test below; the
    continuous-versus-segmented content test compares in lockstep instead, which
    both avoids a second full materialisation and names the offending row.
    """
    return sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)


# ---------------------------------------------------------------------------
# The aggregate check's blindness, pinned deliberately
# ---------------------------------------------------------------------------


def test_an_aggregate_check_cannot_see_a_wrong_measurement(month) -> None:
    """Corrupting a measurement leaves every aggregate untouched. On purpose.

    This is the 38-event bug turned into a standing canary. ``recovery_ratio``,
    ``time_above`` and ``time_below`` are recorded on the event for downstream
    research and are *never* read by the outcome labeller -- so rewriting them,
    to any value at all, cannot move a single aggregate number.

    The test asserts the blindness rather than working around it, because the
    blindness *is* the finding. It is what an aggregate-only equivalence check is
    structurally unable to cover, and it is why this repository compares event
    content rather than statistics alone.

    Mutated in place and restored in a ``finally`` rather than deep-copied: a
    month of 5m bars yields ~78k events, and copying them cost roughly a
    gigabyte of peak RSS to change three feature keys.
    """
    events = continuous_events(month)
    assert events, "fixture produced no events"

    honest = OutcomeAccumulator()
    label_events_streaming(month, events, honest)

    saved: list[tuple[dict, object, object, object]] = []
    try:
        for event in events:
            if event.kind != "liquidity_sweep":
                continue
            if event.features.get("recovery_ratio") is None:
                continue
            saved.append(
                (
                    event.features,
                    event.features["recovery_ratio"],
                    event.features.get("time_above"),
                    event.features.get("time_below"),
                )
            )
            event.features["recovery_ratio"] = Decimal(OBVIOUSLY_WRONG)
            event.features["time_above"] = None
            event.features["time_below"] = None

        assert len(saved) > 100, f"expected many sweeps to corrupt, got {len(saved)}"

        dirty = OutcomeAccumulator()
        label_events_streaming(month, events, dirty)
        corrupted_totals = dirty.as_dict()
    finally:
        for features, ratio, above, below in saved:
            features["recovery_ratio"] = ratio
            features["time_above"] = above
            features["time_below"] = below

    assert corrupted_totals == honest.as_dict(), (
        "if this assertion ever fails, the aggregate check has started covering "
        "these fields -- which is good news, and would mean the canary should be "
        "replaced by a real regression test rather than removed"
    )


# ---------------------------------------------------------------------------
# Content equality, at several segment sizes and with offset > 0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("segment_days", [1, 3, 7])
def test_event_content_and_order_are_identical_continuous_versus_segmented(
    tmp_path, month, segment_days: int
) -> None:
    """Every field of every event must match exactly, at three segment sizes.

    ``1`` places a boundary roughly every 288 bars, so many events straddle one;
    ``7`` is the size the validation runs use. Both must agree with a
    whole-series pass field for field.

    **Ordering is checked by this test, not alongside it.** The comparison runs
    in lockstep, so a row appearing at a different position fails immediately --
    an order difference cannot hide behind an order-insensitive multiset. There
    was previously a separate ordering test; it was removed as redundant once the
    content comparison became lockstep, and removing it is the reason this file's
    runtime dropped rather than doubled.

    Lockstep also means the failure names the offending event instead of
    reporting how many differ, and it lets the segmented log be streamed rather
    than materialised -- the whole-series side already holds ~78k event objects,
    and holding a second full set of parsed dicts was the largest single
    allocation here.
    """
    whole = [event.as_row() for event in continuous_events(month)]
    assert whole, "fixture produced no events"

    index = 0
    for index, windowed in enumerate(
        segmented_iter(tmp_path, month, segment_days=segment_days)
    ):
        assert index < len(whole), (
            f"the segmented run emitted more rows than the whole-series pass "
            f"({len(whole)}); first extra row is {index}"
        )
        expected = json.dumps(whole[index], sort_keys=True, default=str)
        actual = json.dumps(windowed, sort_keys=True, default=str)
        assert actual == expected, (
            f"event {index} differs between the whole-series and segmented runs "
            f"(in content or in position).\n"
            f"  whole-series: {expected[:500]}\n"
            f"  segmented   : {actual[:500]}"
        )
    assert index + 1 == len(whole), (
        f"the segmented run emitted {index + 1} rows against the whole-series "
        f"pass' {len(whole)}; the last {len(whole) - index - 1} were dropped"
    )


def test_the_content_comparison_covers_every_field_the_run_emits(
    tmp_path, month
) -> None:
    """A field added to the event and then left out of the check must fail here.

    Same discipline as ``test_each_measured_field_is_individually_covered``: the
    content comparison is only as good as the surface it reads. Rather than
    pinning a hard-coded list -- which would break on every legitimate field
    addition -- this asserts that both runs emit the *same* field set, so a field
    present on one path and absent on the other is caught immediately.
    """
    whole = [event.as_row() for event in continuous_events(month)]
    windowed = list(segmented_iter(tmp_path, month, segment_days=3))

    whole_fields = _row_field_names(whole)
    windowed_fields = _row_field_names(windowed)
    assert whole_fields == windowed_fields, (
        f"field set differs: only in whole-series {sorted(whole_fields - windowed_fields)}, "
        f"only in segmented {sorted(windowed_fields - whole_fields)}"
    )
    assert len(whole_fields) >= 20, (
        f"expected the full measurement surface, saw {sorted(whole_fields)}"
    )


# ---------------------------------------------------------------------------
# Exactness, not tolerance
# ---------------------------------------------------------------------------


def test_measurements_are_compared_exactly_and_no_tolerance_is_silently_in_use(
    month,
) -> None:
    """A field that differs only in its 28th decimal must still count as different.

    This is the 9-row rounding defect pinned as a property of the *comparison*
    rather than of one detector: the content check above uses exact string
    equality, so a value that is correct to 24 significant figures and wrong in
    the 25th is reported as a difference. If a future change introduces a
    tolerance to make a comparison pass, the difference reported here is the
    evidence that it did.
    """
    whole = [event.as_row() for event in continuous_events(month)]
    baseline = _content_multiset(whole)

    perturbed = [dict(row) for row in whole]
    changed = 0
    for row in perturbed:
        value = row.get("recovery_ratio")
        if value is None:
            continue
        # Perturb by one unit in the 25th significant place.
        row["recovery_ratio"] = str(Decimal(value) + Decimal("1e-25"))
        changed += 1
        break
    assert changed == 1, "fixture must contain at least one sweep with a ratio"

    assert _content_multiset(perturbed) != baseline, (
        "a change in the 25th significant figure must be reported as a "
        "difference; a comparison tolerant enough to miss it would be accepting "
        "corruption of unknown size"
    )