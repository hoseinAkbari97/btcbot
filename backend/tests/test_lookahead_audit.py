"""The lookahead audit must catch real leaks, not just pass on good code.

An audit utility that never reports a violation is worse than no audit: it
buys a false assurance. These tests therefore spend most of their effort on
*deliberately broken* functions — a centred rolling mean, a globally fitted
scaler, a future-shifted signal, a timestamped record that names a bar it
could not have known — and assert the audit finds each one.

The positive tests matter too, but only to confirm the audit does not fire on
correct code, which is the other failure mode: an audit so sensitive that it
cries to flag everything will be switched off.
"""

from __future__ import annotations

import math
from datetime import timedelta
from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.lookahead import (
    AuditReport,
    audit,
    audit_no_future_timestamps,
    audit_prefix_invariance,
)


def zigzag(count: int = 60) -> list:
    """A series with reversals, a spike, a flat stretch and a trend.

    Chosen so that a detector which peeks even slightly is caught: a global
    maximum, a whole-sample scaler, or a centred window all produce different
    answers at different prefixes on this shape, whereas on a monotone series
    they would often agree and hide the defect.
    """
    prices = []
    for index in range(count):
        if index < 20:
            prices.append(100 + index)
        elif index < 25:  # a spike well above everything before it
            prices.append(200 + (index - 20) * 30)
        elif index < 35:  # a flat stretch, where a rolling mean and a global one agree
            prices.append(260)
        else:  # a decline, so the spike is not simply the series maximum
            prices.append(260 - (index - 35) * 3)
    return [
        make_candle(
            index * 5,
            open_price=str(price),
            high=str(price + 2),
            low=str(price - 2),
            close=str(price),
        )
        for index, price in enumerate(prices)
    ]


# ===========================================================================
# The audit must CATCH leaks
# ===========================================================================


def test_it_catches_a_centred_rolling_mean() -> None:
    """The classic leak: a window that reaches into the future.

    A centred mean at bar *n* uses bars ``n+1..n+k``. It is causal-looking, it
    is what every tutorial recommends, and it makes a backtest look excellent.
    """

    def centred_mean(candles: list):
        half = 2
        out = []
        for index in range(len(candles)):
            window = candles[max(0, index - half) : index + half + 1]
            out.append(sum(c.close for c in window) / len(window))
        return out

    report = audit_prefix_invariance(centred_mean, zigzag(), subject="centred rolling mean")
    assert not report.is_clean, "a centred window is lookahead bias and must be reported"
    assert report.prefixes_checked > 0


def test_it_catches_a_centred_window_when_it_is_renamed_to_look_tight() -> None:
    """The name of a function says nothing about what it computes."""
    assert not audit_prefix_invariance(
        lambda c: [sum(x.close for x in c[max(0, i - 1) : i + 2]) for i in range(len(c))],
        zigzag(),
        subject="innocuous name",
    ).is_clean


def test_it_catches_a_scaler_fitted_on_the_whole_sample() -> None:
    """Standardising by the full-sample mean and range leaks the future level.

    Subtract the sample mean and you have used every price that ever existed,
    including the ones after the bar you are scoring.
    """

    def globally_scaled(candles: list):
        closes = [c.close for c in candles]
        mean = sum(closes) / len(closes)
        spread = max(closes) - min(closes)
        return [(c - mean) / spread for c in closes]

    assert not audit_prefix_invariance(
        globally_scaled, zigzag(), subject="globally scaled series"
    ).is_clean


def test_it_catches_a_globally_ranked_indicator() -> None:
    """A percentile rank over the whole sample is a function of the future."""
    assert not audit_prefix_invariance(
        lambda c: [
            sum(1 for o in c if o.close < x.close) / len(c) for x in c
        ],
        zigzag(),
        subject="global percentile rank",
    ).is_clean


def test_it_catches_a_signal_shifted_into_the_past() -> None:
    """Labelling bar *n* with the state at bar *n+1* is the most dangerous leak.

    It produces a perfect, entirely fictional backtest, and it is easy to write
    by accident when aligning two series.
    """

    def one_bar_ahead(candles: list):
        closes = [c.close for c in candles]
        out = []
        for index in range(len(closes)):
            # The last bar has no successor, so it is labelled "down". That is
            # not the point: the point is that bars 0..n-1 are all labelled by
            # what the *next* bar does, which on a longer run is a different
            # answer than on a shorter one.
            following = closes[index + 1] if index + 1 < len(closes) else closes[index]
            out.append("up" if following > closes[index] else "down")
        return out

    assert not audit_prefix_invariance(one_bar_ahead, zigzag(), subject="future-shifted signal").is_clean


def test_it_catches_a_max_drawn_from_the_whole_series() -> None:
    """Using a global high as a 'resistance level' embeds the future in a level."""
    assert not audit_prefix_invariance(
        lambda c: [max(x.high for x in c) for _ in c],
        zigzag(),
        subject="global high as resistance",
    ).is_clean


def test_it_catches_a_barrier_placed_beyond_the_data() -> None:
    """A stop derived from the eventual extreme is a stop that could never trigger.

    A take-profit set at the all-time high of a series is unreachable by
    construction, and the backtest that uses it will report a perfect win rate
    on a trade that could never have filled.
    """
    assert not audit_prefix_invariance(
        lambda c: [max(x.high for x in c)] * len(c),
        zigzag(),
        subject="global high as a target",
    ).is_clean


def test_a_leak_that_only_affects_the_earliest_bars_is_still_caught() -> None:
    """The first prefixes are audited, not just the late ones.

    ``min_prefix`` is small by default, so a defect that contaminates only the
    opening bars is still caught. Starting the audit late would hide exactly the
    values a rolling indicator is least able to recover from.
    """
    # Contaminates bar 0 onward: the first output already knows the whole range.
    def early_only_leak(candles: list):
        spread = max(x.high for x in candles) - min(x.low for x in candles)
        return [spread for _ in candles]

    report = audit_prefix_invariance(early_only_leak, zigzag(), subject="whole-range width")
    assert not report.is_clean
    assert report.violations[0].as_of_index == 2, "the earliest legal prefix must be audited"


def test_it_catches_a_record_timestamped_in_the_future() -> None:
    """Values can be causal while the labelling is not.

    A record whose price is correct but whose timestamp names a later bar will
    silently reorder itself when the series is extended, so prefix invariance
    alone would not catch it.
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Event:
        price: Decimal
        confirmation_time: object

    def timestamped_in_the_future(candles: list):
        # The price is the current close — perfectly causal. The timestamp is
        # the current bar's close *plus three bar intervals*: a confirmation
        # point three bars after the end of everything the function was given.
        # Nothing in the data establishes when that confirmation will happen, so
        # the record is asserting a fact about the future.
        spacing = candles[1].close_time - candles[0].close_time
        return [
            Event(price=candle.close, confirmation_time=candle.close_time + 3 * spacing)
            for candle in candles
        ]

    report = audit_no_future_timestamps(
        timestamped_in_the_future, zigzag(), subject="future-dated record"
    )
    assert not report.is_clean
    assert any("confirmation_time" in str(violation) for violation in report.violations)


# ===========================================================================
# The audit must NOT fire on correct code
# ===========================================================================


def test_a_trailing_indicator_passes() -> None:
    """The same rolling mean, looking backwards only, is the correct version."""

    def trailing_mean(candles: list):
        window = 3
        return [
            sum(c.close for c in candles[max(0, i - window + 1) : i + 1]) / len(candles[max(0, i - window + 1) : i + 1])
            for i in range(len(candles))
        ]

    assert audit_prefix_invariance(trailing_mean, zigzag(), subject="trailing mean").is_clean


def test_an_expanding_indicator_passes() -> None:
    """Using all history so far is causal, even though it is a growing window."""
    assert audit_prefix_invariance(
        lambda c: [sum(x.close for x in c[: i + 1]) / (i + 1) for i in range(len(c))],
        zigzag(),
        subject="expanding mean",
    ).is_clean


def test_a_running_extreme_passes() -> None:
    """A high-water mark to date is causal; the all-time high is not."""
    assert audit_prefix_invariance(
        lambda c: [max(x.high for x in c[: i + 1]) for i in range(len(c))],
        zigzag(),
        subject="running high",
    ).is_clean


def test_a_named_structure_component_passes() -> None:
    """The audit is not a toy: it must clear the real causal detector.

    ``analyze_market_structure`` was rewritten specifically to satisfy prefix
    invariance. If the audit cannot certify it, either the audit is wrong or the
    detector still leaks — and both outcomes are worth failing a test over.
    """
    report = audit_prefix_invariance(
        lambda candles: analyze_market_structure(
            candles, symbol="BTCUSDT", timeframe=Timeframe.M5
        ),
        zigzag(80),
        subject="analyze_market_structure",
        stride=3,
        # Swings, events and levels are the per-bar outputs. ``recent_range`` is
        # a high/low over everything supplied so far, so it necessarily grows
        # with the window and is a summary rather than an indexed series.
        indexed_fields=("swings", "events", "liquidity_levels"),
    )
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:5])
    assert "recent_range" in report.unchecked_fields, (
        "a field the audit skipped must be reported as skipped, not quietly "
        "counted as verified"
    )


def test_market_structure_passes_the_timestamp_check_too() -> None:
    report = audit_no_future_timestamps(
        lambda candles: analyze_market_structure(
            candles, symbol="BTCUSDT", timeframe=Timeframe.M5
        ),
        zigzag(60),
        subject="analyze_market_structure timestamps",
        stride=2,
    )
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:5])


# ===========================================================================
# Properties of the audit itself
# ===========================================================================


def test_it_rejects_a_series_too_short_to_judge() -> None:
    """Two candles cannot distinguish a causal function from a leaky one.

    Reporting "clean" on a series this short would be a false assurance, so the
    audit says it could not tell instead.
    """
    report = audit_prefix_invariance(lambda c: [], zigzag(2), subject="trivially leaky")
    assert not report.is_clean
    assert "too few" in str(report.violations[0])


def test_raising_names_the_offending_function_and_bar() -> None:
    """A leak must fail loudly at the point of detection, not return a flag.

    A boolean return is a boolean somebody will eventually ignore; an exception
    cannot be shipped by accident.
    """
    report = audit_prefix_invariance(
        lambda c: [max(x.high for x in c) for _ in c], zigzag(), subject="global high"
    )
    with pytest.raises(AssertionError) as excinfo:
        report.raise_if_violations()
    message = str(excinfo.value)
    assert "global high" in message
    assert "bar" in message


def test_a_clean_report_raises_nothing() -> None:
    report = audit_prefix_invariance(
        lambda c: [x.close for x in c], zigzag(), subject="close series"
    )
    assert report.is_clean
    report.raise_if_violations()


def test_a_stride_skips_prefixes_but_still_checks_something() -> None:
    candles = zigzag(40)
    every = audit_prefix_invariance(lambda c: c, candles, subject="raw")
    every_other = audit_prefix_invariance(lambda c: c, candles, subject="raw", stride=2)
    assert every_other.prefixes_checked < every.prefixes_checked
    assert every_other.prefixes_checked > 0
    assert every_other.is_clean


def test_a_leak_is_still_caught_when_only_every_other_prefix_is_checked() -> None:
    """A stride is a speed optimisation, not a licence to miss a defect."""
    report = audit_prefix_invariance(
        lambda c: [max(x.high for x in c) for _ in c],
        zigzag(40),
        subject="global high",
        stride=2,
    )
    assert not report.is_clean


def test_the_report_serialises_for_a_research_writeup() -> None:
    report = audit(
        lambda c: [max(x.high for x in c) for _ in c], zigzag(20), subject="global high"
    )
    payload = report.as_dict()
    assert payload["subject"] == "global high"
    assert payload["is_clean"] is False
    assert payload["violations"] and all(isinstance(v, str) for v in payload["violations"])


def test_two_functions_leaking_in_different_ways_are_both_reported() -> None:
    """One audit call should surface every problem, not the first one found."""
    report = audit(
        lambda c: (
            [max(x.high for x in c) for _ in c],  # values leak
            [c[-1].close_time + timedelta(days=1)] * len(c),  # labels leak
        ),
        zigzag(20),
        subject="doubly leaky",
    )
    assert len(report.violations) >= 2
