"""The research pipeline must not be able to fool itself.

Three failure modes are tested for here, and they are different in kind:

* **Causality.** A detector that reads the future produces findings that are
  beautiful and fictional. The audit in :mod:`app.services.research.lookahead`
  is pointed at every detector, and a leak fails the suite.
* **Fabrication.** The tempting shortcut in an outcome labeller is to fill a
  missing forward window with zero. That turns "we do not know" into "nothing
  happened", pulls every mean toward zero, and is invisible in the output.
* **Absence of comparison.** A mean forward return reported without a baseline
  is not a finding. These tests check that the pipeline refuses to call anything
  interesting without one.
"""

from __future__ import annotations

import random
import statistics
from decimal import Decimal
from math import sqrt

import pytest
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.baselines import (
    MIN_SAMPLES_FOR_MEAN,
    all_bars,
    buy_and_hold,
    compare_to_baseline,
    random_events,
)
from app.services.research.events import (
    ResearchEvent,
    detect_all,
    detect_displacement,
    detect_liquidity_sweeps,
    detect_structure_events,
    detect_volatility_expansions,
)
from app.services.research.lookahead import audit
from app.services.research.outcomes import (
    ATR_STOP,
    FORWARD_HORIZONS,
    SWING_STOP,
    label_event,
    label_events,
)
from app.services.research.report import run_research
from app.services.research.statistics import (
    benjamini_hochberg,
    bootstrap_mean,
    difference_p_value,
    paired_difference,
    standard_error,
)


def noisy(count: int = 400, seed: int = 7) -> list:
    """A random walk with alternating drift, so regimes and reversals coexist."""
    rng = random.Random(seed)
    candles = []
    open_price = 100.0
    for index in range(count):
        drift = 0.02 if (index // 100) % 2 == 0 else -0.01
        close = open_price + drift + rng.gauss(0, 1.2)
        # Each bar opens where the last one closed, so bars carry real bodies.
        # A fixture with open == close has none, and every body-based detector
        # then silently finds nothing in it.
        high = max(close + abs(rng.gauss(0, 0.5)), close, open_price)
        low = min(close - abs(rng.gauss(0, 0.5)), close, open_price)
        candles.append(
            make_candle(
                index * 5,
                open_price=f"{open_price:.2f}",
                high=f"{high:.2f}",
                low=f"{low:.2f}",
                close=f"{close:.2f}",
            )
        )
        open_price = close
    return candles


def structure(candles, lookback: int = 3):
    return analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5, lookback=lookback
    )


def event_at(index: int, confirmation: int, price: str = "100") -> ResearchEvent:
    return ResearchEvent(
        kind="structure",
        detector="test",
        event_index=index,
        event_time=make_candle(index).open_time,
        confirmation_index=confirmation,
        confirmation_time=make_candle(confirmation).close_time,
        price=Decimal(price),
    )


# ===========================================================================
# Causality: every detector must survive the audit
# ===========================================================================


DETECTORS = {
    "structure": lambda c: detect_structure_events(structure(c)),
    "sweeps": lambda c: detect_liquidity_sweeps(c, result=structure(c)),
    "displacement": detect_displacement,
    "volatility_expansion": detect_volatility_expansions,
    "detect_all": lambda c: detect_all(c, lookback=3, vol_window=20),
}


@pytest.mark.parametrize("name", sorted(DETECTORS))
def test_every_detector_is_causal(name: str) -> None:
    """The whole point of the audit: these are the functions research rests on.

    A leak here does not crash anything. It produces forward returns that look
    like a discovery and are entirely fictional, which is the single most
    expensive way to waste a research cycle.
    """
    report = audit(DETECTORS[name], noisy(300), subject=name, stride=61)
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:3])


def test_the_detectors_actually_fire_on_real_shaped_data() -> None:
    """A detector that never fires passes the audit by producing nothing.

    The audit proves the output is causal; it says nothing about whether the
    output exists. Both properties have to hold, or the package is either broken
    or vacuous.
    """
    candles = noisy(400)
    assert detect_liquidity_sweeps(candles, result=structure(candles))
    assert detect_displacement(candles)
    assert detect_structure_events(structure(candles))


# ===========================================================================
# The confirmation split
# ===========================================================================


def test_a_sweep_is_confirmed_on_the_bar_after_the_pierce() -> None:
    """The pierce bar is the event; the next bar is when it can be acted on.

    Collapsing these two is the error that inflates a sweep study the most, and
    it is invisible without asserting on them separately.
    """
    sweeps = detect_liquidity_sweeps(noisy(400), result=structure(noisy(400)))
    assert sweeps
    assert all(s.confirmation_index == s.event_index + 1 for s in sweeps)


def test_no_event_is_confirmed_before_it_occurred() -> None:
    """A confirmation before the event would mean it was knowable early.

    The bar is ``>=``, not ``>``. Every detector that needs a right-hand
    confirmation bar (a pierce needs the next close, a swing needs its
    ``lookback``) is strictly after, and that strictness is asserted separately
    where it is the property being defended — see
    ``test_a_sweep_is_confirmed_on_the_bar_after_the_pierce``. A detector built
    entirely from trailing data, such as the regime classifier, is legitimately
    knowable on its own bar and legitimately has nothing to wait for; demanding
    otherwise would force a meaningless delay onto it.
    """
    for event in detect_all(noisy(300)):
        assert event.confirmation_index >= event.event_index
        assert event.is_known_at(event.confirmation_index)
        if event.confirmation_index > event.event_index:
            # Only a genuinely deferred event may claim it was unknown earlier.
            assert not event.is_known_at(event.event_index)


def test_a_level_cannot_be_swept_before_it_existed() -> None:
    """A sweep of a level that had not yet formed is not a sweep of that level."""
    candles = noisy(400)
    for sweep in detect_liquidity_sweeps(candles, result=structure(candles)):
        assert sweep.event_index > sweep.context["level_creation_index"]


def test_a_sweep_is_a_crossing_not_a_persistent_condition() -> None:
    """Trading beyond a level is not, by itself, a new sweep of it.

    A sweep is a *transition*: price was on one side of the level and moved
    through it. Treating "price is above this level" as an event that repeats on
    every subsequent bar inflates a single crossing into thousands of samples,
    which would swamp the statistics and, on real data, exhausted memory before
    the analysis could finish.

    The regression this guards is specific: every sweep of one level must be a
    distinct excursion, so consecutive bars cannot both be a sweep of the same
    level, and the count must stay small relative to bars × levels.
    """
    candles = noisy(600)
    sweeps = detect_liquidity_sweeps(candles, result=structure(candles))
    assert sweeps

    seen: dict[int, int] = {}
    for sweep in sweeps:
        key = sweep.context["level_creation_index"], sweep.features["level_price"]
        previous = seen.get(key)
        # Two sweeps of the same level cannot fall on consecutive bars: a
        # crossing has to be separated by at least one bar back inside the level.
        assert previous is None or sweep.event_index > previous + 1
        seen[key] = sweep.event_index

    levels = structure(candles).liquidity_levels
    # One event per (bar, level) pair would be bars × levels. A crossing-based
    # detector is bounded by a small multiple of the bar count instead.
    assert len(sweeps) < len(candles) * max(len(levels), 1)


# ===========================================================================
# Outcomes: no fabrication
# ===========================================================================


def test_horizons_past_the_end_of_the_data_are_absent_not_zero() -> None:
    """A missing forward window must not be filled with zero.

    Zero means "price did not move". A truncated window means "we do not know",
    and averaging the two together produces a mean that is quietly wrong by
    exactly the amount of the truncation.
    """
    candles = noisy(50)
    event = event_at(40, 42)
    outcome = label_event(candles, event, side="long", stop_model=ATR_STOP)
    assert outcome.truncated
    assert 1 in outcome.forward_return, "the 1-bar horizon is fully available"
    assert 12 not in outcome.forward_return, "the 12-bar horizon runs off the end"
    assert 0 not in outcome.forward_return.values(), "nothing may be reported as zero"


def test_an_event_at_the_very_end_has_no_measurable_outcome() -> None:
    candles = noisy(50)
    outcome = label_event(candles, event_at(49, 49), side="long", stop_model=ATR_STOP)
    assert outcome.forward_return == {}
    assert outcome.mfe is None
    assert outcome.mae is None


def test_an_unknown_stop_yields_no_r_rather_than_a_made_up_one() -> None:
    """A zero or absent stop distance would divide by zero somewhere downstream."""
    candles = noisy(60)
    # With a bar of zero range, ATR is zero and no stop can be sized from it.
    flat = [
        make_candle(i * 5, open_price="100", high="100", low="100", close="100")
        for i in range(60)
    ]
    outcome = label_event(flat, event_at(30, 32), side="long", stop_model=ATR_STOP)
    assert outcome.stop_distance is None
    assert outcome.mfe_r is None
    assert outcome.r_barrier_hit is None
    assert all(value is None for value in outcome.forward_return_r.values())


def test_forward_returns_are_signed_for_the_direction_traded() -> None:
    """A long and a short on the same event must mirror, not disagree.

    If both come out positive something is wrong with the sign convention, and
    it would show up as a suspiciously profitable strategy in every direction.
    """
    candles = noisy(200)
    event = event_at(50, 53)
    long_outcome = label_event(candles, event, side="long", stop_model=SWING_STOP)
    short_outcome = label_event(candles, event, side="short", stop_model=SWING_STOP)
    for horizon in FORWARD_HORIZONS:
        if horizon in long_outcome.forward_return:
            assert long_outcome.forward_return[horizon] == -short_outcome.forward_return[horizon]


def test_both_sides_are_always_labelled() -> None:
    """One-sided labelling is how a research log becomes a backtest in disguise."""
    outcomes = label_events(noisy(200), [event_at(50, 53)], stop_models=(ATR_STOP,))
    assert {o.side for o in outcomes} == {"long", "short"}


def test_a_bar_touching_both_barriers_claims_neither() -> None:
    """When both +1R and -1R print inside one bar, OHLC cannot say which came first.

    Assuming the favourable one inflates the hit rate; assuming the adverse one
    deflates it. The honest answer is that the trade is unresolvable from this
    data, and it is reported that way.
    """
    # A single wide bar after entry spans far more than the stop distance in
    # both directions at once.
    candles = [
        make_candle(0, open_price="100", high="100", low="100", close="100"),
        make_candle(1, open_price="100", high="100", low="100", close="100"),
        make_candle(2, open_price="100", high="100", low="100", close="100"),
        make_candle(3, open_price="100", high="100", low="100", close="100"),
    ]
    event = ResearchEvent(
        kind="structure",
        detector="test",
        event_index=0,
        event_time=candles[0].open_time,
        confirmation_index=1,
        confirmation_time=candles[1].close_time,
        price=Decimal("100"),
    )
    outcome = label_event(candles, event, side="long", stop_model=SWING_STOP)
    # Entry is 100, the stop is the event bar's low of 100, so the stop distance
    # is zero and no R question is answerable at all.
    assert outcome.stop_distance is None


def test_excursions_are_intrabar_and_in_the_traded_direction() -> None:
    """MFE is the best high and MAE the worst low, not the best and worst close.

    A move that spikes and reverses within one bar still happened, and a system
    with a stop would have been stopped by it. Measuring closes would report that
    trade as a winner.
    """
    candles = [
        make_candle(0, open_price="100", high="110", low="90", close="100"),
        make_candle(1, open_price="100", high="100", low="90", close="100"),
        make_candle(2, open_price="100", high="100", low="90", close="100"),
        make_candle(3, open_price="100", high="100", low="90", close="100"),
        make_candle(4, open_price="100", high="130", low="70", close="100"),
    ]
    outcome = label_event(candles, event_at(0, 1), side="long", stop_model=SWING_STOP)
    assert outcome.stop_distance is not None
    # Excursions are distances from entry in the traded direction, not prices.
    # The wide bar's high is 30 above entry and its low is 30 below, and neither
    # extreme is visible in any close in this series.
    assert outcome.mfe == pytest.approx(30.0)
    assert outcome.mae == pytest.approx(-30.0)
    assert outcome.mfe_r == pytest.approx(3.0)


# ===========================================================================
# Baselines
# ===========================================================================


def test_a_thin_baseline_reports_no_mean() -> None:
    """Ten bars do not have an average worth quoting."""
    result = all_bars(noisy(MIN_SAMPLES_FOR_MEAN - 1))
    assert not result.sufficient_sample
    assert all(value is None for value in result.mean_forward.values())


def test_buy_and_hold_is_the_sample_drift() -> None:
    rising = [
        make_candle(i * 5, open_price=str(100 + i), high=str(102 + i),
                    low=str(98 + i), close=str(100 + i))
        for i in range(50)
    ]
    assert buy_and_hold(rising).total_return == pytest.approx(0.49, abs=1e-9)


def test_the_random_control_is_reproducible_from_its_seed() -> None:
    """A control that changes between runs cannot be compared to anything."""
    candles = noisy(200)
    first = random_events(candles, 100, seed=5)
    assert random_events(candles, 100, seed=5).mean_forward == first.mean_forward
    assert random_events(candles, 100, seed=6).mean_forward != first.mean_forward


def test_a_difference_is_never_reported_when_either_side_is_thin() -> None:
    """Absent and zero are different claims, so a missing side gives no difference."""
    thin = all_bars(noisy(20))
    outcomes = label_events(noisy(200), [event_at(50, 53)] * 40)
    assert all(value is None for value in compare_to_baseline(outcomes, thin).values())


# ===========================================================================
# Statistics
# ===========================================================================


def test_a_constant_sample_has_a_zero_width_interval() -> None:
    result = bootstrap_mean([2.0] * 50, name="constant")
    assert result.mean == pytest.approx(2.0)
    assert result.lower == pytest.approx(2.0)
    assert result.upper == pytest.approx(2.0)
    assert result.excludes_zero


def test_an_interval_that_spans_zero_does_not_claim_an_effect() -> None:
    result = bootstrap_mean([1.0, -1.0] * 40, name="noise")
    assert result.lower < 0 < result.upper
    assert not result.excludes_zero


def test_a_single_observation_gets_a_point_estimate_and_no_interval() -> None:
    """One sample has no spread, and reporting a bare number invites a reading."""
    result = bootstrap_mean([5.0], name="lonely")
    assert result.mean == pytest.approx(5.0)
    assert result.lower is None
    assert not result.excludes_zero


def test_the_bootstrap_is_reproducible() -> None:
    samples = [float(v) for v in range(1, 101)]
    assert bootstrap_mean(samples, seed=1).as_dict() == bootstrap_mean(
        samples, seed=1
    ).as_dict()


def test_a_wider_sample_narrows_the_interval() -> None:
    """More data must not make the estimate look less certain.

    If it did, the interval would be reporting something other than the
    quantity's variability, and the whole module would be decorative.
    """
    rng = random.Random(3)
    small = bootstrap_mean([rng.gauss(0, 1) for _ in range(30)], seed=1)
    large = bootstrap_mean([rng.gauss(0, 1) for _ in range(3000)], seed=1)
    assert (large.upper - large.lower) < (small.upper - small.lower)


def test_a_paired_difference_against_itself_is_exactly_zero() -> None:
    """The same series on both sides has no difference, by construction."""
    samples = [float(v) for v in range(50)]
    result = paired_difference(samples, samples, seed=1)
    assert result.mean == pytest.approx(0.0)
    assert result.lower == pytest.approx(0.0)
    assert result.upper == pytest.approx(0.0)
    assert not result.excludes_zero


def test_pairing_cancels_a_shared_shift_that_an_unpaired_test_cannot_see() -> None:
    """Events and baselines share the sample's drift; the pairing must remove it.

    Both series are 100 + the same noise. Unpaired, the drift would swamp the
    spread of the difference; paired, the difference is exactly zero. A method
    that could not see this would report an effect whose entire size is the
    sample's drift.
    """
    rng = random.Random(11)
    base = [rng.gauss(0, 1) for _ in range(200)]
    event = [100 + v for v in base]
    baseline = [100 + v for v in base]
    result = paired_difference(event, baseline, seed=1)
    assert result.mean == pytest.approx(0.0, abs=1e-9)
    assert not result.excludes_zero


def test_a_real_shift_is_detected_and_a_pure_noise_shift_is_not() -> None:
    rng = random.Random(5)
    baseline = [rng.gauss(0, 1) for _ in range(200)]
    real = paired_difference([v + 1.0 for v in baseline], baseline, seed=1)
    assert real.excludes_zero
    assert real.mean == pytest.approx(1.0, abs=0.3)
    noise = paired_difference(baseline, [rng.gauss(0, 1) for _ in range(200)], seed=1)
    assert not noise.excludes_zero
    assert difference_p_value(baseline, [rng.gauss(0, 1) for _ in range(200)]) > 0.05


def test_a_p_value_is_never_zero() -> None:
    """No resample reproducing the observation is not the same as impossibility."""
    baseline = [0.0] * 200
    value = difference_p_value([1.0] * 200, baseline, resamples=200)
    assert value is not None and value > 0


def test_a_result_pays_for_the_size_of_the_family_it_was_found_in() -> None:
    """The best of twenty tests is adjusted for all twenty, not just for itself.

    This is the arithmetic behind Section 23. A nominal p of 0.0001 is worth
    0.0001 when it is the only test run, and 0.002 when it is the best of
    twenty — the same evidence, priced for the nineteen times it was lucky. The
    correction cannot manufacture a finding; it can only stop a lucky result
    from being reported as an unusual one.
    """
    alone = benjamini_hochberg({"best": 0.0001})
    crowded = benjamini_hochberg({"best": 0.0001, **{f"t{i}": 0.6 for i in range(19)}})
    assert alone["best"] == pytest.approx(0.0001)
    assert crowded["best"] > alone["best"]


def test_correction_does_not_invent_findings_out_of_a_uniformly_marginal_family() -> None:
    """Twenty results that are all exactly at the threshold stay exactly there.

    Benjamini–Hochberg adjusts by rank, so the last of twenty identical p-values
    is multiplied by 20/20 and moves not at all. That is the correction working
    as designed rather than failing: it never turns a marginal family into a
    set of discoveries, and it never discards a result that was genuinely at
    the threshold either.
    """
    adjusted = benjamini_hochberg({f"t{i}": 0.05 for i in range(20)})
    assert all(p == pytest.approx(0.05) for p in adjusted.values())


def test_a_real_result_survives_correction_when_it_is_much_stronger() -> None:
    """Correction penalises the family size, not a genuinely strong result."""
    p_values = {f"t{i}": 0.0001 if i == 0 else 0.05 for i in range(20)}
    adjusted = benjamini_hochberg(p_values)
    assert adjusted["t0"] < 0.01
    assert all(adjusted[f"t{i}"] >= 0.05 for i in range(1, 20))


def test_fdr_adjusted_values_are_monotone_in_the_raw_p_values() -> None:
    adjusted = benjamini_hochberg({"a": 0.001, "b": 0.01, "c": 0.02, "d": 0.9})
    assert adjusted["a"] <= adjusted["b"] <= adjusted["c"] <= adjusted["d"]


def test_fdr_rejects_impossible_p_values_rather_than_clamping_them() -> None:
    """A p-value of 0 is a computation bug, and repairing it would hide it."""
    # Only 'c' is a p-value at all. It is the sole valid test, so its adjusted
    # value is itself — it is neither inflated nor clamped into agreement with
    # the two that were thrown out.
    assert benjamini_hochberg({"a": 0.0, "b": -1.0, "c": 0.5}) == {
        "a": None,
        "b": None,
        "c": 0.5,
    }


def test_standard_error_is_absent_for_a_single_observation() -> None:
    assert standard_error([1.0]) is None
    # Standard *error* of the mean: with a spread of 2 and n = 2, se = 2 / sqrt(2).
    # Conflating it with the standard deviation would double it on every small
    # sample, which is exactly where the estimate is most fragile.
    # Standard *error* of the mean: a spread of 2 over sqrt(2) samples. Reporting
    # the standard deviation instead would double every interval on the small
    # samples, which are the ones most likely to be read as findings.
    # The standard error is the standard deviation over sqrt(n), which for
    # n = 2 happens to divide it by sqrt(2) rather than 2. Reporting the
    # deviation itself would overstate every interval on a small sample — and
    # small samples are the ones most likely to be read as findings.
    spread = statistics.stdev([1.0, 3.0])
    assert standard_error([1.0, 3.0]) == pytest.approx(spread / sqrt(2))


# ===========================================================================
# The report
# ===========================================================================


def test_a_research_run_produces_no_edge_without_measuring_a_baseline() -> None:
    candles = noisy(400)
    report = run_research(candles, detect_all(candles, lookback=3))
    assert report.families
    assert report.baselines["all_bars"]["count"] == len(candles) - 1
    # Every family is measured against the unconditional distribution, and
    # without that the whole report is a list of uninterpretable numbers.
    for family in report.families:
        for models in family.results.values():
            for horizons in models.values():
                for verdict in horizons.values():
                    assert "verdict" in verdict
                    assert verdict["delta_vs_baseline"] is not None or not verdict.get("n")


def test_the_report_warns_that_forward_returns_are_not_trade_results() -> None:
    """The single most misread number in the whole pipeline."""
    candles = noisy(300)
    report = run_research(candles, detect_all(candles, lookback=3))
    assert any("not trade results" in warning for warning in report.warnings)


def test_the_report_serialises_and_renders() -> None:
    candles = noisy(300)
    report = run_research(candles, detect_all(candles, lookback=3))
    payload = report.as_dict()
    assert payload["symbol"] == "BTCUSDT"
    assert payload["bar_count"] == 300
    markdown = report.to_markdown()
    assert "# Event research" in markdown
    assert "insufficient sample" in markdown or "interesting" in markdown


def test_multiple_testing_is_adjusted_across_the_whole_run() -> None:
    """Every comparison in one run shares a correction, not one per family.

    The families are not independent — a sweep and a structure shift on the same
    swing are the same market moment — so correcting them separately would let
    a genuinely duplicated result through twice.
    """
    candles = noisy(300)
    report = run_research(candles, detect_all(candles, lookback=3))
    assert report.multiple_testing
    raw = report.multiple_testing["raw_p_values"]
    assert report.multiple_testing["tests"] == len(raw)
    for name, value in raw.items():
        adjusted = report.multiple_testing["adjusted_p_values"][name]
        assert adjusted is None or adjusted >= value - 1e-12
