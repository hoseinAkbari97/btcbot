"""Is the measured difference real, or is it the sample?

The gap this module closes
--------------------------
A mean forward return after an event, compared to a baseline, is a number
computed from a few hundred correlated observations. Events cluster — a sweep
and a structure shift on the same swing are not independent draws, and both
appear in a trending market where the baseline is also trending. A difference
of a few basis points is what that produces routinely, and reporting it without
an interval is how a research log acquires an edge that does not exist.

Three questions are separated here, because they fail differently:

1. **How wide is the estimate?** A bootstrap confidence interval on the mean,
   resampling the events themselves. This uses no distributional assumption,
   which matters because forward returns are fat-tailed and a t-interval on
   them understates the range badly.
2. **Does it exceed the baseline?** A paired bootstrap of the *difference*,
   resampling with replacement. The same resample index is applied to both the
   event sample and its baseline so the two are compared on the same draw, and
   a paired comparison does not attribute to the event what is really the
   sample's drift.
3. **Is it a multiple-testing artefact?** A Benjamini–Hochberg pass over every
   event kind, detector, side, horizon and stop model that was measured. This
   run produces *dozens* of statistics, and at 20 tests the best one at p < 0.05
   is expected to be luck roughly two-thirds of the time. A list of results
   with no correction is a list with at least one false positive in it.

Everything reports ``n``. An interval computed from 20 points is reported, but
labelled with the 20, because the width is the point and hiding the count hides
the width.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt

import numpy as np

#: Resamples in a bootstrap. 2000 is well past the point where the interval's
#: own endpoints stop moving; the seed is fixed so a reported interval is
#: reproducible rather than a function of when it was run.
DEFAULT_RESAMPLES = 2000
DEFAULT_SEED = 20240101


@dataclass(frozen=True)
class BootstrapResult:
    """A mean, and the interval that says how much it could be wrong."""

    name: str
    n: int
    mean: float | None
    #: Lower and upper bound of the percentile interval.
    lower: float | None
    upper: float | None
    confidence: float
    resamples: int
    #: True when the interval excludes zero, i.e. the mean is distinguishable
    #: from zero at all. This is a *floor* on the claim, not the claim: a
    #: difference from a baseline is the question that matters, and passing this
    #: while failing the baseline test is the common case worth catching.
    excludes_zero: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "n": self.n,
            "mean": self.mean,
            "lower": self.lower,
            "upper": self.upper,
            "confidence": self.confidence,
            "resamples": self.resamples,
            "excludes_zero": self.excludes_zero,
        }


def _percentile(sorted_values: Sequence[float], fraction: float) -> float:
    """Linear-interpolation percentile, matching the trade-level module."""
    if not sorted_values:
        raise ValueError("percentile of an empty sample is undefined")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = fraction * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def bootstrap_mean(
    samples: Sequence[float],
    *,
    name: str = "mean",
    confidence: float = 0.95,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> BootstrapResult:
    """A percentile bootstrap interval for the mean of ``samples``.

    Resampling the observed values with replacement assumes only that they are
    drawn from *some* distribution. That is the right assumption here and a
    normal one is not: forward returns are fat-tailed, and the tails are
    exactly where a strategy's risk lives, so an interval that assumed
    thin-tailed noise would be narrow precisely where it matters most.
    """
    n = len(samples)
    if n == 0:
        return BootstrapResult(name, 0, None, None, None, confidence, resamples, False)
    mean = sum(samples) / n
    if n < 2:
        # One observation has no spread to estimate. Reporting a point estimate
        # with no interval would let it be read as a measured effect.
        return BootstrapResult(name, n, mean, None, None, confidence, resamples, False)

    rng = np.random.default_rng(seed)
    # Resampling in vectorised batches rather than `resamples` Python loops of
    # `n` steps each. The inner loop is O(resamples × n): on a full 1h history
    # the events alone run to six figures, and a scalar loop made a research
    # pass that should take seconds take half an hour. The draw is still
    # resampling with replacement and the seed is still fixed, so a reported
    # interval remains reproducible; only the specific resample indices differ
    # from the scalar version, which never documented those indices anyway.
    #
    # Batched rather than all at once: a full (resamples × n) index matrix is
    # gigabytes on a large event set, and materialising it would trade a slow
    # run for an out-of-memory failure. Each batch draws from the same
    # generator, so the replicate set is identical to the unbatched draw.
    values = np.asarray(samples, dtype=float)
    means = _resample_means(values, resamples, rng)
    means = sorted(float(value) for value in means)
    tail = (1.0 - confidence) / 2.0
    lower = _percentile(means, tail)
    upper = _percentile(means, 1.0 - tail)
    return BootstrapResult(
        name=name,
        n=n,
        mean=mean,
        lower=lower,
        upper=upper,
        confidence=confidence,
        resamples=resamples,
        excludes_zero=lower > 0 or upper < 0,
    )


#: Replicate indices are drawn in batches so peak memory stays bounded by
#: ``BOOTSTRAP_BATCH_CELLS`` regardless of how many events were detected. A
#: full 2000 × 100_000 matrix is 1.6 GB; the batch below is ~8 MB.
BOOTSTRAP_BATCH_CELLS = 1_000_000


def _resample_means(
    values: np.ndarray,
    resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """``resamples`` bootstrap means of ``values``, drawn in bounded batches."""
    n = values.shape[0]
    # Enough replicates to fill one batch, never fewer than one, so a tiny
    # sample does not produce a zero-width batch and spin.
    batch = max(1, BOOTSTRAP_BATCH_CELLS // max(n, 1))
    out = np.empty(resamples, dtype=float)
    done = 0
    while done < resamples:
        size = min(batch, resamples - done)
        indices = rng.integers(0, n, size=(size, n))
        out[done : done + size] = values[indices].mean(axis=1)
        done += size
    return out


def _paired_replicates(
    event_samples: Sequence[float],
    baseline_samples: Sequence[float],
    n: int,
    resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Paired bootstrap replicates: event mean minus baseline mean, per draw.

    The index drawn for the event position is the index used for the baseline
    position, so both sides are always compared on the same draw. Deriving the
    two from one draw is the difference between a paired test and two unpaired
    ones, and it is why this is the single place the resampling happens.
    """
    event_values = np.asarray(event_samples, dtype=float)
    baseline_values = np.asarray(baseline_samples, dtype=float)
    baseline_size = len(baseline_samples)
    batch = max(1, BOOTSTRAP_BATCH_CELLS // max(n, 1))
    out = np.empty(resamples, dtype=float)
    done = 0
    while done < resamples:
        size = min(batch, resamples - done)
        draws = rng.integers(0, n, size=(size, n))
        paired = event_values[draws] - baseline_values[draws % baseline_size]
        out[done : done + size] = paired.mean(axis=1)
        done += size
    return out


def paired_difference(
    event_samples: Sequence[float],
    baseline_samples: Sequence[float],
    *,
    name: str = "difference",
    confidence: float = 0.95,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> BootstrapResult:
    """Bootstrap the mean of ``event - baseline`` with paired resampling.

    The pairing matters more than the resample count. Events and baselines come
    from the same market, so they share whatever drift and volatility the sample
    happened to have; resampling each independently would put that shared
    component into the spread of the difference and report an effect as
    uncertain when it is not — or, if the effect is real but smaller than the
    drift, report noise as a shrinking interval. Resampling both on the same
    drawn index cancels the shared component first.

    The two samples may be different lengths: the baseline index wraps, so a
    shorter baseline is reused rather than silently truncated.

    Both sides are resampled from a *single* draw per replicate. That is the
    whole mechanism — two independent draws would resample two different
    markets and re-introduce exactly the shared drift the pairing exists to
    cancel, which is why a series compared against itself has to come out at
    exactly zero rather than at "about zero".
    """
    if not event_samples or not baseline_samples:
        return BootstrapResult(name, 0, None, None, None, confidence, resamples, False)
    n = len(event_samples)
    mean = sum(event_samples) / n - sum(baseline_samples) / len(baseline_samples)

    rng = np.random.default_rng(seed)
    means = _paired_replicates(event_samples, baseline_samples, n, resamples, rng)
    means = sorted(float(value) for value in means)
    tail = (1.0 - confidence) / 2.0
    lower = _percentile(means, tail)
    upper = _percentile(means, 1.0 - tail)
    return BootstrapResult(
        name=name,
        n=n,
        mean=mean,
        lower=lower,
        upper=upper,
        confidence=confidence,
        resamples=resamples,
        excludes_zero=lower > 0 or upper < 0,
    )


def benjamini_hochberg(p_values: dict[str, float]) -> dict[str, float | None]:
    """Adjusted p-values, controlling the false discovery rate.

    The one-line argument for running this: if a research pass measures twenty
    event/horizon/side/stop combinations at a nominal 5% level, the expected
    number of results that pass by chance alone is one. Reporting the pass
    count without the correction is reporting the null hypothesis.

    Returns the *adjusted* p-value per name, or ``None`` for inputs outside
    ``(0, 1]``, which are rejected rather than clamped — a p-value of 0 or a
    negative one is a computation bug, and quietly repairing it would hide it.
    """
    valid = {name: p for name, p in p_values.items() if 0 < p <= 1}
    ordered = sorted(valid.items(), key=lambda item: item[1])
    m = len(ordered)
    adjusted: dict[str, float | None] = {name: None for name in p_values}
    running_min = 1.0
    # Walking from the largest p-value backwards, the adjusted value for rank i
    # is the smallest ratio at or above it — a plain per-test multiply would
    # produce non-monotonic adjusted values and the rejection set would depend
    # on iteration order.
    for position in range(m - 1, -1, -1):
        name, p = ordered[position]
        rank = position + 1
        running_min = min(running_min, p * m / rank)
        adjusted[name] = min(1.0, running_min)
    return adjusted


def difference_p_value(
    event_samples: Sequence[float],
    baseline_samples: Sequence[float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> float | None:
    """Two-sided bootstrap p-value for "the event sample equals the baseline".

    Derived from the same paired resampling as :func:`paired_difference`, rather
    than as a separate t-test: a t-test would assume normality the fat-tailed
    return distribution violates, and using two different methods for the
    interval and the p-value would let them disagree about the same data.

    The p-value is the fraction of resamples whose difference is at least as
    extreme as the observed one, with the +1 correction — a resample count of
    zero out of 2000 gives ``1/2001``, not zero, because "no resample was this
    extreme" is not the same as "this is impossible".
    """
    import math

    if len(event_samples) < 2 or not baseline_samples:
        return None
    observed = abs(
        sum(event_samples) / len(event_samples) - sum(baseline_samples) / len(baseline_samples)
    )
    n = len(event_samples)
    rng = np.random.default_rng(seed)
    replicates = _paired_replicates(event_samples, baseline_samples, n, resamples, rng)
    extreme = int((np.abs(replicates) >= observed).sum())
    return (extreme + 1) / (resamples + 1)


def standard_error(samples: Sequence[float]) -> float | None:
    """Sample standard error of the mean, for a quick read before bootstrapping.

    Provided because a report wants a number in the summary line, but the
    bootstrap is what the conclusion should rest on: this assumes the sample
    mean is approximately normal, which for a fat-tailed distribution it is not.
    """
    n = len(samples)
    if n < 2:
        return None
    mean = sum(samples) / n
    variance = sum((s - mean) ** 2 for s in samples) / (n - 1)
    return sqrt(variance / n)
