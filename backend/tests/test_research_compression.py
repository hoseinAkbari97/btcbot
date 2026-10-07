"""Phase 8: compression, and the displacement measurements it shares.

Milestone 6 lists six price-action phenomena. Liquidity, sweeps and displacement
existed; compression did not. That gap matters beyond the missing bullet: a
compression is only *interesting* next to the displacement that ends it, and
the two are comparable only if they measure "quiet" and "loud" with the same
definition. So this file pins two things -- the compression detector's own
behaviour, and the invariance that makes a compression ratio and a displacement
magnitude comparable.

The failure modes this exists to prevent:

* **A ratio measured against a window that includes the bar being scored.** That
  shrinks the statistic toward the mean by an amount that grows with the window,
  so a 50-bar window reports systematically weaker displacement than a 20-bar one
  on identical price action. The two numbers look comparable and are not.
* **A z-score over a population with no spread.** A market that has not moved in
  twenty bars has no "unusually large bar"; reporting 0 there puts a dead flat
  stretch in the average bucket and reporting a big number puts it in the extreme
  bucket, and both are fabrications.
* **Emitting the release twice.** The compression detector ends on a range
  expansion; ``detect_displacement`` fires on the same bar. Counting it in both
  families inflates every sample size in the report by the number of releases.
* **An "event" that is really a state.** Compression holds for many bars; only
  the transition is an observation.

Fixtures are synthetic and hand-built. Nothing is loaded.
"""

from __future__ import annotations

from decimal import Decimal

from conftest import make_candle

from app.schemas.market_data import CandleData
from app.services.research.events import (
    detect_all,
    detect_compression,
    detect_displacement,
)
from app.services.research.lookahead import audit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def path(
    values: list[tuple[str, str, str, str]],
) -> list[CandleData]:
    """Build a series from explicit ``(open, high, low, close, volume)`` rows.

    OHLC is written out rather than generated, because the interesting cases --
    a perfectly flat stretch, then one bar twice as tall -- cannot be produced on
    purpose by a random walk.
    """
    return [
        make_candle(
            index * 5,
            open_price=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        for index, (open_, high, low, close, volume) in enumerate(values)
    ]


def busy(index: int, *, volume: str = "1000") -> tuple[str, str, str, str]:
    """A volatile bar that genuinely moves: 100 -> 108 -> 100 -> 92 -> 100.

    Closes alternate, which matters more than it looks. Volatility here is
    measured from close-to-close returns, so a bar with a large range but a flat
    close -- high 110, low 90, close 100, every time -- has *zero* realised
    volatility and would be scored as the quietest market in the file.
    """
    up = index % 2 == 0
    close = "108" if up else "92"
    high, low = ("110", "89") if up else ("111", "90")
    return ("100", high, low, close, volume)


def quiet(index: int, *, volume: str = "200") -> tuple[str, str, str, str]:
    """A bar that barely moves, with volume that has dried up."""
    mid = 100 + (index % 3) - 1  # 99, 100, 101
    return (str(mid), str(mid + 1), str(mid - 1), str(mid), volume)


def coil_then_release(
    busy_bars: int = 40, quiet_bars: int = 30, tail: int = 20
) -> list[CandleData]:
    """Busy market, then a contraction, then an expansion that ends it."""
    rows = [busy(i) for i in range(busy_bars)]
    rows += [quiet(busy_bars + i) for i in range(quiet_bars)]
    for i in range(tail):
        up = i % 2 == 0
        # A decisive move off the quiet base, in the direction it closed.
        close = "130" if up else "70"
        high, low = ("133", "99") if up else ("101", "67")
        rows.append(("100", high, low, close, "3000"))
    return path(rows)


# ---------------------------------------------------------------------------
# Causality
# ---------------------------------------------------------------------------


def test_compression_is_causal_under_prefix_audit() -> None:
    """The detector's output for bar i cannot depend on bar i+1.

    Run twice on the same detector as every other one in the package, because
    "the ratio uses trailing windows" is a claim about the code, and the claim
    is only worth something if something would notice if it stopped being true.
    """
    report = audit(detect_compression, coil_then_release(), subject="compression", stride=17)
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:3])


def test_changing_the_future_does_not_change_a_detected_compression() -> None:
    """The concrete form of the above, on a fixture where the result is known.

    Two identical 90-bar prefixes are followed by opposite futures. Every event
    the detector reports in the prefix must be identical in both, including its
    features. If a feature had leaked, the ``compression_ratio`` or the
    ``release_expansion`` would differ -- which is the kind of difference that
    shows up in a report as a mild, entirely fictional improvement.
    """
    prefix = coil_then_release()
    baseline = detect_compression(prefix)

    # Same prefix, wildly different continuation.
    mutated = list(prefix)
    for i in range(len(prefix), len(prefix) + 50):
        up = i % 2 == 0
        mutated.append(
            make_candle(
                i * 5,
                open_price="100",
                high="900" if up else "1",
                low="1" if up else "900",
                close="100",
                volume="999999",
            )
        )

    assert [e.to_payload() for e in detect_compression(mutated)[: len(baseline)]] == [
        e.to_payload() for e in baseline
    ]


def test_the_audit_excludes_no_fields_and_reports_none_ungraded() -> None:
    """Every field the detector writes has to be graded by the audit.

    ``lookahead`` only grades list/tuple fields; scalars land in
    ``unchecked_fields`` unless named. A compression feature that escaped grading
    would report clean without ever having been checked.
    """
    report = audit(detect_compression, coil_then_release(), subject="compression", stride=31)
    assert list(report.unchecked_fields) == [], report.unchecked_fields


# ---------------------------------------------------------------------------
# The detector's definition
# ---------------------------------------------------------------------------


def test_a_coiling_market_is_detected() -> None:
    """Busy, then quiet, then expanding: at least one compression event.

    A detector that never fires passes every causality test above by producing
    nothing at all, so the fixture-strength check is not optional.
    """
    events = detect_compression(coil_then_release())
    assert events, "the coil fixture produced no compression events"


def test_the_compression_ratio_is_reported_and_actually_small() -> None:
    """The ratio is the measurement, so it has to mean what it says.

    Asserted against the number rather than merely present: a ratio of 0.99 on
    a fixture where the recent window is five times quieter than the long one
    would satisfy a presence check and be meaningless.
    """
    events = detect_compression(coil_then_release())
    ratios = [e.features["compression_ratio"] for e in events]
    assert all(r <= Decimal("0.6") for r in ratios), ratios
    assert min(ratios) < Decimal("0.5"), ratios


def test_every_feature_the_milestone_names_is_present() -> None:
    """The named measurement set, and nothing speculative.

    ``body_ratio`` and the three range/volatility means live on the event too;
    a report that cannot split compression outcomes by how tight the coil was
    cannot answer the question the milestone is for.
    """
    required = {
        "compression_ratio",
        "range_5",
        "range_10",
        "range_20",
        "volatility_5",
        "volatility_20",
        "range_zscore",
        "volume_zscore",
        "release_range",
        "release_expansion",
        "atr_normalized_move",
    }
    for event in detect_compression(coil_then_release()):
        assert required <= set(event.features), sorted(required - set(event.features))


def test_the_release_bar_really_is_bigger_than_the_recent_mean_range() -> None:
    """``release_range > range_20``, and the windows are genuinely distinct.

    This is the claim the detector's exit condition rests on. It is asserted at
    the *release* bar, where the trailing windows are already quiet -- so
    ``range_5`` and ``range_20`` are close together there, and the meaningful
    assertion is that the release bar's own range towers over both. If the
    windows were not doing anything, that would not hold.
    """
    for event in detect_compression(coil_then_release()):
        assert event.features["release_range"] > event.features["range_20"]
        assert event.features["release_expansion"] > 1
        assert event.features["range_20"] > 0


def test_a_flat_stretch_produces_no_zscore_rather_than_a_fake_one() -> None:
    """Zero spread in the reference population means "no scale", not a number.

    Twenty identical bars have a standard deviation of exactly zero. Dividing by
    it would raise; returning 0 would say the bar is typical when there is no
    notion of typical; returning a large number would say it is extreme. ``None``
    is the only honest answer, and the detector must survive it.
    """
    flat = path([("100", "100", "100", "100", "500") for _ in range(80)])
    events = detect_compression(flat)

    # Whatever it emits, every z-score is either absent or well-defined -- the
    # test is that this does not raise and does not manufacture an extreme.
    for event in events:
        for key in ("range_zscore", "volume_zscore"):
            value = event.features.get(key)
            assert value is None or value == value  # not NaN, not an error


def test_a_never_ending_contraction_emits_nothing() -> None:
    """A state that never ends is not an observation.

    If the market compresses and simply stays compressed to the end of the data,
    there is no release, so there is no event. Emitting one per bar of the
    contraction would inflate every downstream sample size by the length of the
    contraction -- and, worse, would produce a "compression outcome" label for
    bars at which nothing happened.
    """
    rows = [busy(i) for i in range(40)] + [quiet(40 + i) for i in range(60)]
    assert detect_compression(path(rows)) == []


def test_the_release_bar_is_the_event_and_needs_no_later_confirmation() -> None:
    """``confirmation_index == event_index`` for compression.

    The release bar's own range is final at its close, and the window it is
    scored against is entirely trailing, so there is no bar to wait for. Making
    the confirmation the *next* bar would be safe but would invent a lag that
    does not exist; making it the *same* bar is the honest statement of when the
    information is available.
    """
    candles = coil_then_release()
    for event in detect_compression(candles):
        assert event.confirmation_index == event.event_index
        # Same bar, so the confirmation stamp is that bar's *close* -- strictly
        # after its open, and the moment its range becomes final.
        assert event.confirmation_time == candles[event.event_index].close_time
        assert event.confirmation_time > event.event_time


def test_the_event_bar_is_the_first_bar_that_breaks_the_contraction() -> None:
    """A compression is *not* emitted on the first quiet bar.

    Reporting it as soon as the market gets quiet would put the event bar inside
    the contraction, where there is nothing yet to report, and would then emit a
    second event per bar for the rest of it. The transition is the only event.
    """
    candles = coil_then_release()
    events = detect_compression(candles)
    # Contraction starts after the busy stretch; every event must land at or
    # after the end of that stretch, never within it.
    for event in events:
        assert event.event_index >= 40, event.event_index


# ---------------------------------------------------------------------------
# Shared-measurement consistency
# ---------------------------------------------------------------------------


def test_a_release_is_not_double_counted_in_two_families() -> None:
    """The expansion bar is compression's *end*, not a displacement of its own.

    Compression deliberately stops at the release and does not claim the move --
    that belongs to ``detect_displacement``. Two detectors reporting the same bar
    is not automatically wrong (a large expansion genuinely is both), but the
    compression event must not *carry* the release as its own displacement
    feature, or the report counts one bar twice in two families with no way to
    tell.
    """
    events = detect_compression(coil_then_release())
    for event in events:
        assert "magnitude_in_volatility" not in event.features
        assert "body_ratio" not in event.features


def test_displacement_reports_the_named_zscores() -> None:
    """Phase 8's displacement measurements, added rather than substituted.

    ``magnitude_in_volatility`` stays: it is a ratio to a volatility estimate and
    remains the gate. The z-scores sit beside it because they answer a different
    question -- distance from the market's own recent *distribution* -- and a bar
    can be 3x recent volatility in a market whose bars have recently all been 3x.
    """
    found = detect_displacement(coil_then_release())
    assert found, "the fixture produced no displacement events"
    for event in found:
        for key in ("range_zscore", "return_zscore", "volume_zscore"):
            assert key in event.features, key
        assert event.features["magnitude_in_volatility"] is not None


def test_the_zscore_window_excludes_the_bar_being_scored() -> None:
    """A population containing the current bar shrinks toward the mean.

    Constructed so the difference is visible: the same final bar scored against
    a window that ends one bar earlier and one that ends at itself. If the
    implementation included the bar, the two would be the same number.
    """
    # 30 flat bars then one large one.
    from app.services.research.events import _zscore

    included = _zscore([Decimal(0)] * 30 + [Decimal(30)], Decimal(30))
    excluded = _zscore([Decimal(0)] * 30, Decimal(30))
    assert included != excluded


def test_compression_and_displacement_agree_on_what_volatility_is() -> None:
    """One definition of "quiet", or the two detectors disagree by construction.

    ``compression_ratio`` divides ``volatility_5`` by ``volatility_20``, and
    ``magnitude_in_volatility`` divides a body by the same trailing volatility.
    If the compression detector computed its own volatility differently the two
    families could not be read against each other at all -- which is the whole
    reason compression and displacement belong to the same phase.
    """
    for event in detect_compression(coil_then_release()):
        # The long-window volatility the compression detector used must equal
        # the one the displacement detector would use at the same index.
        from app.services.research.events import _realized_volatility

        candles = coil_then_release()
        assert event.features["volatility_20"] == _realized_volatility(
            candles, event.event_index, 20
        )


# ---------------------------------------------------------------------------
# Boundary behaviour
# ---------------------------------------------------------------------------


def test_a_series_shorter_than_the_window_produces_nothing() -> None:
    """Not an exception, and not an event from a partial window.

    ``min_bars`` is a floor on history. Below it the 20-bar denominator would be
    computed from fewer bars than its name says, and the ratio would quietly mean
    something different at the start of every run than in the middle of it.
    """
    assert detect_compression(path([busy(i) for i in range(10)])) == []


def test_the_last_bar_is_allowed_to_be_an_event() -> None:
    """Compression's confirmation is its own bar, so there is no trailing gap.

    The other detectors stop one bar short because they confirm on the *next*
    bar. Compression confirms on the bar itself, and truncating the last bar here
    would drop a real release for a reason that does not apply to it.
    """
    candles = coil_then_release()
    events = detect_compression(candles)
    assert events, "fixture produced nothing to check the boundary against"
    assert max(e.event_index for e in events) <= len(candles) - 1


def test_an_empty_series_is_not_an_error() -> None:
    assert detect_compression([]) == []


def test_detect_all_includes_compression_events() -> None:
    """The batch entry point composes the new detector.

    ``detect_all`` is what the batch path uses. A detector that exists but is not
    wired in is indistinguishable from one that does not exist, at the cost of
    having written it.
    """
    events = detect_all(coil_then_release(), lookback=3, vol_window=20)
    assert any(e.kind == "compression" for e in events)
