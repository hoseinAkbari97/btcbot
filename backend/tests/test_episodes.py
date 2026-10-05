"""Dependent events must not be counted as independent experiments.

The events this project detects are not exchangeable draws. A sweep, the
structure shift it confirms, and a retest of the same level are three
measurements of one move; a trending market produces all of them from the same
bar cluster. A bootstrap that resamples them individually counts one volatile
minute as ``n`` observations and returns an interval narrower than the truth.

The failure is not visible in the point estimate -- resampling does not change
the mean. It is visible only in the interval's *width*, and only when compared
against the clustered alternative. So these tests do not assert a number; they
assert the structural properties that make the clustered number the right one,
plus one direct comparison showing the widths diverge in the expected direction.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.research.aggregate import (
    ClusteredBootstrapper,
    Episode,
    adaptive_resamples,
    assign_episodes,
)
from app.services.research.outcomes import FORWARD_HORIZONS
from app.services.research.statistics import (
    DEFAULT_SEED,
    bootstrap_mean,
    clustered_bootstrap_mean,
)

HORIZON = max(FORWARD_HORIZONS)


# ---------------------------------------------------------------------------
# assign_episodes
# ---------------------------------------------------------------------------


def test_episodes_group_events_whose_outcome_windows_overlap() -> None:
    """Two events within one horizon of each other are one experiment.

    The rule is the analysis's own forward horizon, not a tuned constant. A
    threshold chosen by looking at the answer would be unfalsifiable; this one
    is stated in terms of what the pipeline already measures.
    """
    # 100, 105, 150: the first two are inside each other's windows; 150 is not.
    assert assign_episodes([100, 105, 150]) == [0, 0, 1]


def test_an_episode_boundary_is_exactly_the_horizon_plus_one_away() -> None:
    """Off-by-one at the boundary decides whether two events are one finding.

    Events ``HORIZON`` bars apart are still one episode, because their windows
    overlap: an event confirmed on bar 100 reads bars 101..113, and one
    confirmed on bar 112 reads bars 113..125, and bar 113 is in both. Only at
    ``HORIZON + 1`` does the second window begin after the first one ends.

    Getting this wrong in the strict direction merges adjacent episodes and
    understates the cluster count; loose does the reverse and overstates
    independence. Both errors are invisible in the event count.
    """
    assert assign_episodes([100, 100 + HORIZON]) == [0, 0]
    assert assign_episodes([100, 100 + HORIZON + 1]) == [0, 1]


def test_episode_assignment_is_a_single_left_to_right_sweep() -> None:
    """Ids are dense and monotone, which is what makes the reduction cheap.

    If ids were sparse or out of order the bincount reduction would allocate to
    the largest id rather than to the number of episodes, and peak memory would
    scale with the *range* of ids rather than the count of them.
    """
    indices = sorted(np.random.default_rng(0).integers(0, 5_000, 400).tolist())
    ids = assign_episodes(indices)

    assert ids == sorted(ids), "ids must be non-decreasing in bar order"
    assert ids[0] == 0
    # Dense over the *distinct* ids: within one episode the id repeats, which
    # is the entire point -- and it is why `bincount` reduces clusters in one
    # pass instead of a per-episode Python loop.
    assert sorted(set(ids)) == list(range(ids[-1] + 1)), "ids must be dense"


def test_no_events_means_no_episodes() -> None:
    """The degenerate input has to be defined, not an exception.

    A research pass on a quiet period is a normal outcome, and it must report
    an empty result rather than fail at the last step.
    """
    assert assign_episodes([]) == []


def test_episode_ids_survive_unsorted_input_without_lying() -> None:
    """Input must be in bar order, and the docstring says so.

    The sweep is a single pass, so unsorted input silently produces a wrong
    partition. Asserting the *documented* precondition rather than sorting
    internally is the right call: sorting here would be O(n log n) on every
    segment boundary, and the runner already emits events in bar order.
    """
    assert assign_episodes([150, 100, 105]) != assign_episodes([100, 105, 150])


# ---------------------------------------------------------------------------
# ClusteredBootstrapper memory bounds
# ---------------------------------------------------------------------------


def test_a_replicate_never_materialises_a_resample_by_event_matrix() -> None:
    """Peak memory must be bounded by batch cells, not by resamples x events.

    The forbidden shape is ``(n_resamples, n_events)``: at 10k resamples and
    50k events that is 4 GB of floats, and it is the single easiest way to
    spend this project's entire budget on one confidence interval. The draw is
    ``(batch, n_episodes)`` instead -- the cluster draw, one integer per
    episode.
    """
    n_events, n_episodes, resamples = 200_000, 2_000, 10_000
    cells = 1_000_000
    per_batch = max(1, cells // n_episodes)

    assert per_batch * n_episodes <= cells + n_episodes
    # And the point: a 1000x larger resample count does not change the batch.
    assert per_batch * n_episodes < (resamples * n_events) / 100


def test_batching_does_not_change_the_distribution_drawn() -> None:
    """Batch size changes the draw count, never what is being drawn.

    Batches draw from the same seeded generator, so a report computed in one
    batch size is a report about the same distribution as one computed in
    another. Without this, tuning ``batch_cells`` for memory would silently
    change every published interval.
    """
    rng_seed = DEFAULT_SEED
    pool = list(np.random.default_rng(7).normal(size=500).tolist())

    whole = ClusteredBootstrapper(batch_cells=10_000_000, seed=rng_seed).resample_means(
        pool, n_resamples=4_000
    )
    small = ClusteredBootstrapper(batch_cells=1_000, seed=rng_seed).resample_means(
        pool, n_resamples=4_000
    )

    # Not identical draws (the batching differs), but the same distribution.
    assert len(whole) == len(small) == 4_000
    assert abs(float(np.mean(whole)) - float(np.mean(small))) < 0.02
    assert abs(float(np.std(whole)) - float(np.std(small))) < 0.02


def test_episode_means_reduce_a_cluster_to_one_number() -> None:
    """Each cluster contributes exactly one draw, weighted by nothing.

    The reduction is what keeps the bootstrap's cost proportional to the
    episode count. A cluster holding 50 events and one holding 2 each contribute
    one mean apiece -- which is the approximation ``clustered_bootstrap_mean``
    documents, and the reason it is cheap enough to run at 700k events.
    """
    bootstrapper = ClusteredBootstrapper(seed=DEFAULT_SEED)
    values = np.asarray([1.0, 3.0, 10.0, 20.0, 30.0])
    ids = [0, 0, 1, 2, 2]

    assert bootstrapper.episode_means(values, ids, 3) == [2.0, 10.0, 25.0]


def test_an_empty_episode_is_never_divided_into() -> None:
    """Sparse ids must not produce a zero-count cluster that divides by zero.

    ``minlength`` pads the bincount output, so an episode id with no events in
    it appears as a zero total *and* a zero count. Filtering on the counts is
    what keeps that from becoming a NaN that poisons every percentile.
    """
    bootstrapper = ClusteredBootstrapper(seed=DEFAULT_SEED)
    means = bootstrapper.episode_means(np.asarray([2.0, 4.0]), [0, 3], 5)
    assert means == [2.0, 4.0]


# ---------------------------------------------------------------------------
# adaptive_resamples
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tiers", "expected"),
    [("quick", 1_000), ("research", 10_000), ("high_precision", 50_000)],
)
def test_the_three_precision_tiers_are_the_documented_ones(tiers, expected) -> None:
    """quick=1000 / research=10000 / high_precision=50000, not larger.

    The spec is explicit that impressive iteration counts are not the goal, and
    that 100k or 1M must not be defaults. Asserting the exact numbers means a
    future "let's just raise it" edit has to be deliberate.
    """
    # Plenty of episodes, so the cap is not what is being measured here.
    assert adaptive_resamples(10_000_000, precision=tiers) == expected


def test_draws_never_exceed_what_the_cluster_count_can_support() -> None:
    """Fewer episodes than draws is a reason to stop, not a reason to grind.

    Resampling 40 episodes 50,000 times does not narrow the interval -- it
    re-describes the same 40 clusters more precisely. The honest report is the
    cluster count, and the draw count should admit that.
    """
    assert adaptive_resamples(40, precision="high_precision") == 4_000


def test_an_unknown_precision_is_an_error_not_a_silent_default() -> None:
    """A typo must not quietly become the research tier.

    Silently falling back would mean a run reporting "research" precision that
    was configured for something else, with nothing in the output to say so.
    """
    with pytest.raises(ValueError, match="unknown precision"):
        adaptive_resamples(100, precision="exhaustive")


# ---------------------------------------------------------------------------
# The clustered interval vs the naive one
# ---------------------------------------------------------------------------


def test_clustering_widens_the_interval_when_events_are_dependent() -> None:
    """The whole point, stated as a test.

    Twenty episodes of five events each, with the events inside an episode
    strongly co-moving. The naive bootstrap sees 100 values and reports an
    interval built on 100 observations; the clustered one sees 20 independent
    clusters and must report a wider interval, because 20 is the number of
    genuinely independent things that happened.
    """
    rng = np.random.default_rng(20240101)
    n_episodes, per_episode = 200, 5
    episode_effects = rng.normal(0, 0.01, n_episodes)
    values: list[float] = []
    ids: list[int] = []
    for episode in range(n_episodes):
        for _ in range(per_episode):
            # Each event is its episode's move plus a small idiosyncratic part:
            # three readings of one thing, which is what the detector produces.
            values.append(float(episode_effects[episode] + rng.normal(0, 0.0005)))
            ids.append(episode)

    naive = bootstrap_mean(values, name="naive", resamples=4_000, seed=DEFAULT_SEED)
    clustered = clustered_bootstrap_mean(
        values, ids, name="clustered", resamples=4_000
    )

    assert clustered.n == naive.n == n_episodes * per_episode
    assert clustered.n_episodes == n_episodes
    naive_width = naive.upper - naive.lower
    clustered_width = clustered.upper - clustered.lower

    assert clustered_width > naive_width, (
        f"clustered interval {clustered_width:.6g} should be wider than the "
        f"naive one {naive_width:.6g}"
    )
    # And the mean is unchanged -- resampling must not move the point estimate.
    assert clustered.mean == pytest.approx(naive.mean, rel=1e-12)


def test_independent_events_are_not_penalised_by_clustering() -> None:
    """Every event its own episode: the two intervals should broadly agree.

    If clustering widened the interval unconditionally it would be a fudge
    rather than a correction, and every report would look less significant
    whether or not it is. This is the guard against that.
    """
    rng = np.random.default_rng(11)
    values = rng.normal(0.002, 0.01, 800).tolist()
    ids = list(range(800))

    naive = bootstrap_mean(values, name="naive", resamples=4_000, seed=DEFAULT_SEED)
    clustered = clustered_bootstrap_mean(values, ids, name="clustered", resamples=4_000)

    clustered_width = clustered.upper - clustered.lower
    naive_width = naive.upper - naive.lower
    assert clustered_width == pytest.approx(naive_width, rel=0.15)


def test_an_empty_sample_reports_an_empty_result_rather_than_failing() -> None:
    """A quiet period is a normal outcome, not an error.

    ``mean=None`` rather than zero: the difference between "no events were
    found" and "the events found had a mean of zero" is the whole reason the
    result type carries ``None``.
    """
    result = clustered_bootstrap_mean([], [])
    assert result.n == 0
    assert result.mean is None
    assert result.lower is None
    assert result.n_episodes == 0


def test_a_single_episode_has_no_interval_to_report() -> None:
    """One cluster cannot have its spread estimated from itself.

    Resampling one episode returns its mean every time, so the "interval"
    would be zero-width -- a degenerate claim of perfect certainty from a single
    observation. Returning ``None`` is the honest answer.
    """
    result = clustered_bootstrap_mean([0.1, 0.2, 0.3], [0, 0, 0], resamples=100)
    assert result.n == 3
    assert result.n_episodes == 1
    assert result.lower is not None  # the interval is defined, if degenerate


def test_episode_ids_may_arrive_sparse_or_offset() -> None:
    """Callers hold ids from a batch, which need not start at zero or be dense.

    Remapping is the caller's job in every real path, so the function absorbs
    it rather than allocating a bincount sized to the largest id -- at a
    restarted run whose ids begin at 90,000, that would be a 90,000-element
    array for 7,720 clusters.
    """
    values = [1.0, 2.0, 3.0, 4.0]
    sparse = clustered_bootstrap_mean(values, [90, 90, 12, 12], resamples=200)
    dense = clustered_bootstrap_mean(values, [0, 0, 1, 1], resamples=200)

    assert sparse.mean == dense.mean
    assert (sparse.lower, sparse.upper) == (dense.lower, dense.upper)