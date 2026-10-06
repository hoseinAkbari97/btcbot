"""Streaming aggregation: run a research pass without ever holding the dataset.

The one-shot path -- ``detect_all`` then ``run_research`` -- takes a
``list[CandleData]`` and builds four ``EventOutcome`` objects per event. At 5m
over a full year that is roughly 200k bars and, depending on the detector, tens
of thousands of events, so the outcome list alone is measured in gigabytes. This
module exists so the same measurement can be made in bounded memory.

The shape of the answer: *every stage accumulates, nothing accumulates twice*.

* Events are streamed out per segment and appended to a JSONL file. They are
  small, and they are the run's primary output, so keeping them is the point.
* Outcomes are **not** kept. Each is folded into per-(detector, side, stop
  model, horizon) accumulators -- a count, a sum, a sum of squares -- which are
  O(families x models x horizons) regardless of event count.
* Baseline forward returns are accumulated as accumulators too, for the same
  reason: at 200k bars a list of per-bar returns per horizon is another large
  array, and only its summary is ever read.

What that buys is the property the aggregates have to have to be worth
anything: they must be *exactly* the numbers ``run_research`` would have
computed on the same data, in the same order. Mean, variance and the
event-vs-baseline pairing are all streaming-exact. Bootstrap confidence
intervals are not reconstructible from a sum and a sum of squares, so they are
computed on the second pass -- see :func:`ClusteredBootstrapper`, which draws
from disk in bounded batches.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator

from app.schemas.market_data import CandleData
from app.services.research.events import ResearchEvent
from app.services.research.outcomes import (
    DEFAULT_STOP_MODELS,
    FORWARD_HORIZONS,
    EventOutcome,
    label_event,
)

if TYPE_CHECKING:  # pragma: no cover - import cost, not behaviour
    import numpy as np

#: A Welford accumulator. One of these per (family, side, model, horizon):
#: six families x 2 sides x 2 stop models x 4 horizons = 96 numbers regardless of
#: how many events exist.
@dataclass
class Moment:
    """Running count, mean and variance.

    Welford rather than sum/sum-of-squares: at 200k samples of a quantity whose
    mean is small relative to its spread, ``E[x^2] - E[x]^2`` cancels most of its
    significant digits and the variance comes back slightly negative. Welford
    subtracts two numbers of comparable size at every step, so it does not.
    """

    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def add(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (value - self.mean)

    @property
    def variance(self) -> float | None:
        if self.n < 2:
            return None
        return self.m2 / (self.n - 1)

    @property
    def stderr(self) -> float | None:
        variance = self.variance
        if variance is None:
            return None
        return math.sqrt(variance / self.n)

    def as_dict(self) -> dict[str, object]:
        return {
            "n": self.n,
            "mean": self.mean if self.n else None,
            "variance": self.variance,
            "stderr": self.stderr,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Moment":
        """Rebuild from :meth:`as_dict`.

        Needed because ``as_dict`` reports *absence* as ``None`` -- an empty
        accumulator has no mean, and printing ``0.0`` would claim a measurement
        that was never taken. Reading it back has to accept that ``None`` rather
        than ``float()``-ing it, so a checkpoint written by a run whose first
        segment produced no outcomes can still be resumed.

        ``m2`` is recovered from the sample variance, which is exact for ``n>=2``
        and zero for ``n<2`` -- the two cases where a variance is undefined are
        also the two where the accumulated ``m2`` is zero.
        """
        n = int(payload["n"])
        return cls(
            n=n,
            mean=float(payload["mean"] or 0.0),
            m2=float(payload["variance"] or 0.0) * max(0, n - 1),
        )


@dataclass
class OutcomeKey:
    """The four fields that decide which accumulator an outcome belongs to."""

    detector: str
    kind: str
    side: str
    stop_model: str

    def as_str(self) -> str:
        return f"{self.detector}|{self.kind}|{self.side}|{self.stop_model}"


class OutcomeAccumulator:
    """Fold outcomes into moments; keep nothing else.

    The whole point is that this is bounded. It holds one :class:`Moment` per
    (detector, kind, side, stop model, horizon) -- a fixed, small number -- and
    every outcome passed to :meth:`add` is discarded once folded in.
    """

    def __init__(self, horizons: tuple[int, ...] = FORWARD_HORIZONS) -> None:
        self.horizons = horizons
        self._moments: dict[tuple[str, int], Moment] = {}
        self._keys: dict[str, OutcomeKey] = {}
        #: Non-return outcomes worth counting even though they are not a mean:
        #: whether the barrier was reached, and how far the trade got against
        #: itself. These are counts, so streaming them is exact.
        self._barriers: dict[str, dict[str, int]] = {}
        self._excursions: dict[tuple[str, str], Moment] = {}
        self._truncated = 0
        self.total = 0

    def add(self, outcome: EventOutcome) -> None:
        self.total += 1
        if outcome.truncated:
            self._truncated += 1
        key = OutcomeKey(
            outcome.detector, outcome.kind, outcome.side, outcome.stop_model
        )
        # ``setdefault`` rather than assignment: a key registered once must not
        # be replaced by a later outcome that happens to carry the same fields,
        # because the accumulator dict is keyed by its string form.
        name = key.as_str()
        self._keys.setdefault(name, key)

        for horizon in self.horizons:
            value = outcome.forward_return.get(horizon)
            if value is None:
                # Absent, not zero. A horizon past the end of the data is
                # unknown, and counting it as a flat move would bias the mean
                # toward zero by exactly the events that had no window.
                continue
            slot = (name, horizon)
            moment = self._moments.get(slot)
            if moment is None:
                moment = self._moments[slot] = Moment()
            moment.add(float(value))

        barrier_bucket = self._barriers.get(name)
        if barrier_bucket is None:
            barrier_bucket = self._barriers[name] = {
                "hit": 0,
                "missed": 0,
                "ambiguous": 0,
            }
        if outcome.r_barrier_hit is True:
            barrier_bucket["hit"] += 1
        elif outcome.r_barrier_hit is False:
            barrier_bucket["missed"] += 1
        else:
            # Both barriers inside one bar: which printed first is unknowable
            # from OHLC. Counted separately rather than as a miss, so the
            # ambiguity rate is visible instead of quietly inflating "missed".
            barrier_bucket["ambiguous"] += 1

        for label, value in (("mae", outcome.mae), ("mfe", outcome.mfe)):
            if value is None:
                continue
            slot = (label, name)
            moment = self._excursions.get(slot)
            if moment is None:
                moment = self._excursions[slot] = Moment()
            moment.add(float(value))

    @property
    def truncated(self) -> int:
        """Outcomes whose forward window ran off the end of the dataset.

        Reported rather than dropped: a run where 30% of events are truncated is
        a run whose later events have shorter windows than earlier ones, and the
        mean over all of them is not the mean of any single distribution.
        """
        return self._truncated

    def families(self) -> list[OutcomeKey]:
        """Every (detector, kind, side, stop model) cell that saw an outcome.

        Derived from ``_keys``, which records a cell the first time an outcome
        lands in it -- so a detector that produced events but whose outcomes were
        all truncated still appears, with empty horizons. A family missing from
        the report reads as "not investigated"; one present with n=0 reads as
        "investigated, no data". Those are different and only the second is
        honest about what was run.
        """
        return sorted(self._keys.values(), key=lambda key: key.as_str())

    def moment(self, detector: str, kind: str, side: str, model: str, horizon: int) -> Moment:
        """The accumulator for one cell, or an empty one if nothing arrived.

        Returns an empty :class:`Moment` rather than ``None`` so a caller
        reporting on a cell with no events prints ``n=0`` instead of having to
        special-case it -- an absent cell and a cell whose mean is zero are
        different claims.
        """
        name = OutcomeKey(detector, kind, side, model).as_str()
        return self._moments.get((name, horizon), Moment())

    def barrier_counts(
        self, detector: str, kind: str, side: str, model: str
    ) -> dict[str, int]:
        return self._barriers.get(
            OutcomeKey(detector, kind, side, model).as_str(),
            {"hit": 0, "missed": 0, "ambiguous": 0},
        )

    def excursion(self, label: str, detector: str, kind: str, side: str, model: str) -> Moment:
        """Running mean of MFE or MAE for one cell.

        These are absolute price moves, so they are only comparable between
        events at similar price levels; they are reported to describe how far
        trades travelled, not as an edge.
        """
        name = OutcomeKey(detector, kind, side, model).as_str()
        return self._excursions.get((label, name), Moment())

    def as_dict(self) -> dict[str, object]:
        return {
            "total_outcomes": self.total,
            "truncated_outcomes": self.truncated,
            "cells": [
                {
                    "detector": key.detector,
                    "kind": key.kind,
                    "side": key.side,
                    "stop_model": key.stop_model,
                    "barriers": self.barrier_counts(
                        key.detector, key.kind, key.side, key.stop_model
                    ),
                    "excursions": {
                        label: self.excursion(
                            label, key.detector, key.kind, key.side, key.stop_model
                        ).as_dict()
                        for label in ("mae", "mfe")
                        if self.excursion(
                            label, key.detector, key.kind, key.side, key.stop_model
                        ).n
                    },
                    "horizons": {
                        str(horizon): moment.as_dict()
                        for horizon in self.horizons
                        if (moment := self.moment(
                            key.detector, key.kind, key.side, key.stop_model, horizon
                        )).n
                    },
                }
                for key in self.families()
            ],
        }


# ---------------------------------------------------------------------------
# Baseline accumulation
# ---------------------------------------------------------------------------


class BaselineAccumulator:
    """The unconditional forward-return distribution, one moment per horizon.

    Equivalent to ``baselines.all_bars`` for everything ``run_research`` reads
    from it -- the mean, the count, the sufficient-sample flag -- without ever
    holding the per-bar values.
    """

    def __init__(self, horizons: tuple[int, ...] = FORWARD_HORIZONS) -> None:
        self.horizons = horizons
        self._moments = {h: Moment() for h in horizons}
        self.bars = 0

    def add_bar(self, candle: CandleData, closes: list[Decimal], horizon: int) -> None:
        """Fold one bar's forward return, if the horizon fits.

        ``closes`` is the full close series. This is the one place a caller
        hands over something unbounded, and it is deliberate: a forward return at
        bar ``i`` is a difference of two closes, and holding the tail of closes is
        the cheapest correct way to compute one at every bar.
        """
        target = self.bars + horizon
        if target < len(closes):
            self._moments[horizon].add(float(closes[target] - candle.close))
        self.bars += 1

    def mean_forward(self, horizon: int) -> float | None:
        moment = self._moments[horizon]
        return moment.mean if moment.n else None

    @property
    def sufficient_sample(self) -> bool:
        from app.services.research.baselines import MIN_SAMPLES_FOR_MEAN

        return self._moments[self.horizons[0]].n >= MIN_SAMPLES_FOR_MEAN

    def as_dict(self) -> dict[str, object]:
        return {
            "bars": self.bars,
            "horizons": {str(h): m.as_dict() for h, m in self._moments.items()},
        }


def label_events_streaming(
    candles: list[CandleData],
    events: Iterable[ResearchEvent],
    accumulator: OutcomeAccumulator,
    *,
    stop_models: Iterable = DEFAULT_STOP_MODELS,
    sides: tuple[str, ...] = ("long", "short"),
) -> int:
    """Label each event on every stop model and side, folding as it goes.

    The cross-product is the same one ``label_events`` produces -- two models,
    two sides, four per event -- because showing a result under several stop
    models is how one finds out whether the finding was the event's or the
    analyst's. What differs is that nothing is retained.

    :returns: how many outcomes were folded in.
    """
    models = tuple(stop_models)
    count = 0
    for event in events:
        for model in models:
            for side in sides:
                accumulator.add(label_event(candles, event, side=side, stop_model=model))
                count += 1
    return count


# ---------------------------------------------------------------------------
# Event spill
# ---------------------------------------------------------------------------


class EventSpill:
    """Append-only JSONL of detected events, flushed in bounded batches.

    Events are the run's actual product, so they are written rather than
    accumulated. Written in batches because a per-event ``write`` on a few tens
    of thousands of events is dominated by syscall overhead, and because an
    unflushed buffer held across a memory abort is a buffer lost.

    ``mode`` defaults to truncating, which is right for a fresh run. A *resumed*
    run must pass ``"a"``: the spill already holds every event from the segments
    before the checkpoint, and reopening it with ``"w"`` would delete the run's
    output while leaving its statistics intact -- a file that is silently
    empty next to a report claiming 19,000 events.
    """

    def __init__(self, path: Path | str, *, batch: int = 1_000, mode: str = "w") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open(mode, encoding="utf-8")
        self._buffer: list[str] = []
        self._batch = max(1, batch)
        self.count = 0

    def append(self, event: ResearchEvent) -> None:
        self._buffer.append(json.dumps(event.as_row(), separators=(",", ":")))
        self.count += 1
        if len(self._buffer) >= self._batch:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        self._handle.write("\n".join(self._buffer) + "\n")
        self._buffer.clear()
        self._handle.flush()

    def close(self) -> None:
        self.flush()
        self._handle.close()

    def __enter__(self) -> EventSpill:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def read_spill(path: Path | str) -> Iterator[dict]:
    """Stream an event spill back, one dict per line, without loading it."""
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


# ---------------------------------------------------------------------------
# Clustered bootstrap over the spill
# ---------------------------------------------------------------------------


@dataclass
class Episode:
    """A run of events whose outcome windows overlap.

    Overlapping windows mean the outcomes are not independent draws -- the same
    market move is being measured several times -- so resampling events
    individually would treat one volatile minute as ``n`` observations and
    report a confidence interval far narrower than the real one. Resampling
    whole episodes is what makes the interval account for that dependence.
    """

    index: int
    event_indices: list[int]


def assign_episodes(
    confirmation_indices: Iterable[int], *, horizon: int = max(FORWARD_HORIZONS)
) -> list[int]:
    """Map each event to an episode id, in a single left-to-right sweep.

    The rule is the analysis's own forward horizon, not a tuned constant: two
    events belong to the same episode exactly when their outcome windows could
    overlap. Events arrive sorted by confirmation index, so this is O(n) after
    the sort -- no clustering library, and nothing that depends on a distance
    threshold chosen after seeing the answer.

    :param confirmation_indices: events in bar order.
    :returns: an episode id per event, in the same order.
    """
    ids: list[int] = []
    current = -1
    reach = -1
    for index in confirmation_indices:
        if index > reach:
            current += 1
            reach = index + horizon
        ids.append(current)
    return ids


class ClusteredBootstrapper:
    """Bootstrap over episodes, drawing from disk in bounded batches.

    Peak memory is bounded by ``batch_cells``, not by the number of events. A
    replicate never materialises an ``(n_resamples, n_events)`` array -- at 10k
    resamples and 50k events that is 4 GB of floats, which is the single
    easiest way to spend this project's entire budget on one confidence
    interval.

    Instead each replicate is a weighted mean computed with ``np.bincount`` over
    the episode ids of the drawn episodes. The cluster draw is
    ``episode_weights``, one integer per episode, so the array is
    ``(n_events,)`` regardless of how many resamples are requested.

    Only the summary statistics of the resampled means are retained, not the
    resampled means themselves: the percentiles are all that is ever read.
    """

    def __init__(self, *, batch_cells: int = 1_000_000, seed: int = 20240101) -> None:
        self.batch_cells = max(1000, batch_cells)
        self.seed = seed

    def episode_means(
        self,
        values: "np.ndarray",
        episode_of: list[int],
        n_episodes: int,
    ) -> list[float]:
        """One mean per episode, in episode-id order.

        ``values`` is a numpy array of per-event values aligned with
        ``episode_of``. Episodes are summed with ``bincount``, so the cost is
        O(n_events) and no per-episode Python loop runs.
        """
        import numpy as np

        totals = np.bincount(episode_of, weights=values, minlength=n_episodes)
        counts = np.bincount(episode_of, minlength=n_episodes)
        present = counts > 0
        return (totals[present] / counts[present]).tolist()

    def episode_sums_and_counts(
        self,
        values: "np.ndarray",
        episode_of: list[int],
        n_episodes: int,
    ) -> tuple["np.ndarray", "np.ndarray"]:
        """Per-episode ``(sum, count)`` pairs, the input to the exact bootstrap.

        :meth:`episode_means` throws the counts away; the exact cluster bootstrap
        needs them, because an episode drawn ``k`` times contributes ``k``
        copies of itself and the replicate's denominator is the resampled event
        count rather than the episode count. Summing once and keeping both
        halves is what lets a 700k-event run build every replicate from two
        ``(n_episodes,)`` vectors instead of from the events.
        """
        import numpy as np

        sums = np.bincount(episode_of, weights=values, minlength=n_episodes)
        counts = np.bincount(episode_of, minlength=n_episodes)
        present = counts > 0
        return sums[present], counts[present]

    def resample_cluster_means(
        self,
        episode_sums: "np.ndarray",
        episode_counts: "np.ndarray",
        *,
        n_resamples: int,
    ) -> list[float]:
        """``n_resamples`` exact cluster-bootstrap means, batched.

        The *exact* cluster bootstrap: draw ``n_episodes`` episodes with
        replacement, and let a drawn episode contribute all of its events every
        time it is drawn. A replicate is therefore

            mean = sum_c k_c * S_c  /  sum_c k_c * n_c

        over the per-episode sums ``S_c`` and sizes ``n_c``, where ``k_c`` is
        how many times episode ``c`` came up in the draw. That is what makes it
        exact: the resampled sample has the same size-and-all distribution as
        the observed one, so the estimand is the plain event-weighted mean
        rather than the episode-equal-weight mean.

        This is the same thing
        :meth:`resample_means` over :meth:`episode_means` approximates, and the
        two differ whenever episodes are unevenly sized. With 100 observations
        in one episode and 2 in another, this method keeps the 100-event episode
        weighted 50x more; the approximation gives both episodes weight 1.

        Memory is bounded the same way. Within a batch the draw is
        ``(size, n_episodes)`` and the per-replicate draw counts are derived
        from it by a single offset bincount, so the largest live arrays are all
        ``size x n_episodes`` with ``size`` chosen from ``batch_cells``. No
        ``(n_resamples, n_events)`` array is ever built.
        """
        import numpy as np

        n_episodes = int(episode_sums.shape[0])
        if n_episodes == 0 or n_resamples <= 0:
            return []
        sums = np.asarray(episode_sums, dtype=float)
        counts = np.asarray(episode_counts, dtype=float)
        rng = np.random.default_rng(self.seed)
        per_batch = max(1, self.batch_cells // n_episodes)

        means: list[float] = []
        remaining = n_resamples
        while remaining > 0:
            size = min(per_batch, remaining)
            indices = rng.integers(0, n_episodes, size=(size, n_episodes))
            # Per-replicate multiplicities: one bincount over row-offset keys
            # gives every replicate's draw counts at once. The alternative,
            # comparing `indices` against `arange(n_episodes)` to build a
            # (size, n_episodes, n_episodes) indicator, is exactly the giant
            # array this project cannot afford.
            offsets = (np.arange(size, dtype=np.int64) * n_episodes)[:, None]
            drawn = np.bincount(
                (offsets + indices).ravel(), minlength=size * n_episodes
            ).reshape(size, n_episodes).astype(float)
            # Numerator via matmul rather than (drawn * sums): no (size,
            # n_episodes) float temporary for the product.
            numerator = drawn @ sums
            denominator = drawn @ counts
            means.extend((numerator / denominator).tolist())
            remaining -= size
        return means

    def resample_means(
        self, episode_means: list[float], *, n_resamples: int
    ) -> list[float]:
        """Bootstrap means of ``episode_means``, batched by ``batch_cells``.

        Each batch draws ``min(batch_cells // n_episodes, remaining)`` resamples
        at once, so a batch is exactly ``batch_cells`` floats. Batches are
        independent draws from the same seeded generator, which is why the batch
        size changes the number of draws but not the distribution they come
        from.
        """
        import numpy as np

        n_episodes = len(episode_means)
        if n_episodes == 0 or n_resamples <= 0:
            return []
        pool = np.asarray(episode_means, dtype=float)
        rng = np.random.default_rng(self.seed)
        per_batch = max(1, self.batch_cells // n_episodes)

        means: list[float] = []
        remaining = n_resamples
        while remaining > 0:
            size = min(per_batch, remaining)
            indices = rng.integers(0, n_episodes, size=(size, n_episodes))
            means.extend(pool[indices].mean(axis=1).tolist())
            remaining -= size
        return means

    def interval(
        self,
        values: "np.ndarray",
        episode_of: list[int],
        n_episodes: int,
        *,
        n_resamples: int,
    ) -> dict[str, object]:
        """Point estimate and percentile interval, respecting episode clusters."""
        from app.services.research.statistics import BootstrapResult, _percentile

        import numpy as np

        if len(episode_of) == 0:
            return {"n": 0, "mean": None, "interval": None, "n_episodes": 0}
        point = float(np.mean(values))
        means = self.resample_means(
            self.episode_means(values, episode_of, n_episodes), n_resamples=n_resamples
        )
        if not means:
            return {
                "n": len(episode_of),
                "mean": point,
                "interval": None,
                "n_episodes": n_episodes,
            }
        means.sort()
        lower = _percentile(means, 0.025)
        upper = _percentile(means, 0.975)
        return {
            "n": len(episode_of),
            "mean": point,
            "interval": [lower, upper],
            "excludes_zero": (lower > 0) or (upper < 0),
            "n_episodes": n_episodes,
        }


def adaptive_resamples(n_episodes: int, *, precision: str = "research") -> int:
    """How many bootstrap draws to run, from the requested precision tier.

    The tiers exist because the cost is linear in the draw count and the
    accuracy gain is only logarithmic: 10x the draws moves the interval
    half-width by a few percent. The default is chosen so that a full run
    returns a usable interval without a configuration decision.

    Fewer episodes than draws is worth stopping at. Resampling 40 episodes
    50,000 times does not narrow the interval -- it only estimates the same 40
    distinct clusters more precisely, and the honest report is the cluster count,
    not a tight interval that hides it.
    """
    tiers = {"quick": 1_000, "research": 10_000, "high_precision": 50_000}
    if precision not in tiers:
        raise ValueError(
            f"unknown precision {precision!r}; expected one of {sorted(tiers)}"
        )
    return min(tiers[precision], max(1_000, n_episodes * 100))
