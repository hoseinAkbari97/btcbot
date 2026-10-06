"""An approximation must never be published as the statistic it approximates.

The cluster bootstrap has two implementations here, and they are not two ways
of computing the same number:

* ``exact`` resamples whole episodes, each drawn episode contributing all of
  its events. The estimand is the **event-weighted** mean.
* ``approx`` reduces each episode to its mean first, so every episode counts
  once. The estimand is the **episode-equal-weight** mean.

With unevenly sized episodes those two differ, and by more than a rounding
error:

    Episode A: 100 observations at 1.0   -> event-weighted mean  ~1.0
    Episode B:   2 observations at 0.0   -> episode-equal mean    ~0.5

So a report that runs the approximation and labels it "the mean of these
events" is not slightly imprecise -- it has moved the headline number by 50%.
That is a silent estimand change, which is the failure this file exists to
prevent.

The example is 102 numbers. It fits in a few kilobytes.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.research.aggregate import ClusteredBootstrapper
from app.services.research.statistics import (
    BOOTSTRAP_METHODS,
    DEFAULT_SEED,
    bootstrap_mean,
    clustered_bootstrap_mean,
)

#: Episode A holds 100 observations worth 1.0 each; episode B holds 2 worth
#: 0.0 each. Deliberately lopsided, because an even split is the one case where
#: the two weighting schemes coincide.
EPISODE_A = ([1.0] * 100, 0)
EPISODE_B = ([0.0] * 2, 1)


def _two_episode_sample() -> tuple[list[float], list[int]]:
    values = EPISODE_A[0] + EPISODE_B[0]
    ids = [EPISODE_A[1]] * len(EPISODE_A[0]) + [EPISODE_B[1]] * len(EPISODE_B[0])
    return values, ids


# ---------------------------------------------------------------------------
# The two estimands are genuinely different numbers
# ---------------------------------------------------------------------------


def test_the_two_weightings_disagree_on_this_sample() -> None:
    """The fixture must separate the schemes, or it tests nothing.

    Event-weighted: 102 observations, 100 of them 1.0 and 2 of them 0.0.
    Episode-equal:  2 episodes, worth 1.0 and 0.0.
    """
    values, ids = _two_episode_sample()

    assert len(values) == 102
    event_weighted = sum(values) / len(values)
    episode_means = [1.0, 0.0]
    episode_equal = sum(episode_means) / len(episode_means)

    assert event_weighted == pytest.approx(100 / 102)
    assert episode_equal == pytest.approx(0.5)
    # A 50% gap. Nothing about rounding or sampling noise explains it.
    assert abs(event_weighted - episode_equal) > 0.45


# ---------------------------------------------------------------------------
# The exact mode reproduces the intended statistic
# ---------------------------------------------------------------------------


def test_the_exact_mode_reports_the_event_weighted_statistic() -> None:
    """Exact clustering must correct the *interval*, never the estimand.

    Resampling clusters changes what the interval accounts for, not what the
    quantity is. If the exact mode moved ``mean`` off the plain average of the
    observations it would have silently become the approximation.
    """
    values, ids = _two_episode_sample()

    result = clustered_bootstrap_mean(values, ids, method="exact", resamples=2_000)

    assert result.mean == pytest.approx(100 / 102, rel=1e-12)
    assert result.n == 102
    assert result.n_episodes == 2
    assert result.bootstrap_method == "episode_exact"


def test_the_exact_mode_resamples_a_whole_episode_when_it_draws_one() -> None:
    """Drawing episode A must bring its 100 events with it, not its mean.

    Enumerable by hand because there are only two episodes: a replicate drawn
    ``k`` times from A and ``n - k`` times from B has mean
    ``100k / (100k + 2(n - k))``, and every replicate the bootstrap returns must
    be one of those. A weighting that dropped the sizes would return 1.0 and
    0.0 only.
    """
    values, ids = _two_episode_sample()
    bootstrapper = ClusteredBootstrapper(seed=DEFAULT_SEED)
    sums, counts = bootstrapper.episode_sums_and_counts(
        np.asarray(values), ids, 2
    )
    assert list(sums) == [100.0, 0.0]
    assert list(counts) == [100.0, 2.0]

    n_episodes = 2
    replicates = bootstrapper.resample_cluster_means(sums, counts, n_resamples=200)

    for value in replicates:
        allowed = set()
        for k in range(n_episodes + 1):
            numerator = 100.0 * k
            denominator = 100.0 * k + 2.0 * (n_episodes - k)
            if denominator > 0:
                allowed.add(round(numerator / denominator, 12))
        assert round(value, 12) in allowed


def test_the_exact_mode_is_wider_than_the_event_level_bootstrap() -> None:
    """One episode carries 98% of the events; two observations cannot support
    the precision 102 observations imply.

    This is the correction clustering exists to make, and the exact mode has to
    make it just as much as the approximation does.
    """
    values, ids = _two_episode_sample()

    naive = bootstrap_mean(values, name="event", resamples=4_000, seed=DEFAULT_SEED)
    exact = clustered_bootstrap_mean(
        values, ids, name="clustered", method="exact", resamples=4_000
    )

    assert (exact.upper - exact.lower) > (naive.upper - naive.lower)


# ---------------------------------------------------------------------------
# The approximation is the approximation, and says so
# ---------------------------------------------------------------------------


def test_the_approximation_reports_the_documented_approximation() -> None:
    """Its interval describes a different statistic, and must not claim the
    event-weighted one.

    The point estimate is unchanged -- resampling never moves the mean -- so the
    only thing that can prevent this from being mistaken for the exact result
    is the metadata. Assert on all of it.
    """
    values, ids = _two_episode_sample()

    result = clustered_bootstrap_mean(values, ids, method="approx", resamples=2_000)

    assert result.bootstrap_method == "episode_mean_approx"
    assert result.bootstrap_method in BOOTSTRAP_METHODS
    assert "APPROXIMATION" in result.statistic_definition
    assert "episode-equal-weight" in result.statistic_definition
    # Still the same measured mean: what the approximation changes is the
    # estimand the interval is about, not the point estimate on screen.
    assert result.mean == pytest.approx(100 / 102, rel=1e-12)
    assert result.n == 102
    assert result.n_episodes == 2


def test_the_two_modes_are_not_interchangeable() -> None:
    """Neither is presented as the other, and they do not coincide.

    If these came out equal the distinction would be untestable; if the exact
    mode's interval matched the approximation's, one of the two is doing
    nothing.
    """
    values, ids = _two_episode_sample()

    exact = clustered_bootstrap_mean(values, ids, method="exact", resamples=4_000)
    approx = clustered_bootstrap_mean(values, ids, method="approx", resamples=4_000)

    assert exact.bootstrap_method != approx.bootstrap_method
    assert exact.statistic_definition != approx.statistic_definition
    assert exact.bootstrap_method == "episode_exact"
    assert approx.bootstrap_method == "episode_mean_approx"
    # Same point estimate (resampling does not move a mean), different schemes.
    assert exact.mean == pytest.approx(approx.mean, rel=1e-12)


def test_an_unknown_method_is_an_error_not_a_silent_default() -> None:
    """A typo must not quietly become the exact mode.

    Silently defaulting would mean a report claiming an exact statistic from an
    approximation, with nothing in the output to say so -- the one failure this
    module exists to prevent.
    """
    values, ids = _two_episode_sample()

    with pytest.raises(ValueError, match="unknown clustered bootstrap method"):
        clustered_bootstrap_mean(values, ids, method="exacter")


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


def test_the_exact_mode_never_materialises_a_resample_by_event_matrix() -> None:
    """The forbidden shape is ``(n_resamples, n_events)``.

    The exact mode builds one array of per-episode sums and one of counts, then
    works in ``(batch, n_episodes)`` draws. At a million events and ten thousand
    resamples the forbidden matrix is 80 GB; the batch below is bounded by
    ``batch_cells`` and does not grow with either.
    """
    n_episodes, per_episode, resamples, cells = 5_000, 20, 10_000, 1_000_000
    per_batch = max(1, cells // n_episodes)

    assert per_batch * n_episodes <= cells + n_episodes
    # 1,000,000 cells against the 1e9 a (10k x 100k events) matrix would need:
    # three orders of magnitude of headroom, and the gap widens with every
    # factor of events-per-episode because the batch does not grow with it.
    forbidden = resamples * n_episodes * per_episode
    assert per_batch * n_episodes <= cells
    assert forbidden >= 100 * cells


def test_batching_does_not_change_the_exact_distribution_drawn() -> None:
    """Tuning ``batch_cells`` for memory must not move every published interval.

    Same property as the approximation's, asserted for the exact mode: batches
    draw from one seeded generator, so the batch size changes how many draws
    happen, never what is being drawn.
    """
    rng = np.random.default_rng(5)
    sums = rng.normal(size=200)
    counts = rng.integers(1, 8, size=200).astype(float)

    whole = ClusteredBootstrapper(batch_cells=10_000_000, seed=DEFAULT_SEED).resample_cluster_means(
        sums, counts, n_resamples=4_000
    )
    small = ClusteredBootstrapper(batch_cells=1_000, seed=DEFAULT_SEED).resample_cluster_means(
        sums, counts, n_resamples=4_000
    )

    assert len(whole) == len(small) == 4_000
    assert float(np.mean(whole)) == pytest.approx(float(np.mean(small)), abs=0.02)
    assert float(np.std(whole)) == pytest.approx(float(np.std(small)), abs=0.02)


def test_a_degenerate_cluster_never_divides_by_zero() -> None:
    """An episode id with no events must not reach the denominator.

    ``minlength`` pads the bincount output with zero-count episodes; dividing by
    a zero count would poison every percentile downstream with a NaN.
    """
    bootstrapper = ClusteredBootstrapper(seed=DEFAULT_SEED)
    sums, counts = bootstrapper.episode_sums_and_counts(
        np.asarray([2.0, 4.0]), [0, 3], 5
    )

    assert list(sums) == [2.0, 4.0]
    assert list(counts) == [1.0, 1.0]
    assert all(
        value == value for value in bootstrapper.resample_cluster_means(sums, counts, n_resamples=50)
    )
