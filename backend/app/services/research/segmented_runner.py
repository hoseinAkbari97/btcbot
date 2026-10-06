"""The segmented research runner: one bounded pass over a whole dataset.

What this is for
----------------
The research pipeline is structurally single-shot: ``detect_all`` and
``run_research`` each want the entire ``list[CandleData]``. At 1h and 49k bars
that is fine. At 5m and 198,554 bars it is not, and the reason is not only
memory -- the outcome labelling builds four ``EventOutcome`` objects per event,
which at a few hundred thousand events is gigabytes of live Python objects.

So the run is split in two, and the split is deliberately *not* symmetric:

* **Structure** is genuinely global. A liquidity level's price is frozen at its
  first confirmed swing, and a level swept in January is the same level revisited
  in June. This cannot be chunked into independent pieces; it can only be
  *carried*. :class:`~app.services.market_structure.segmented.StructureState`
  holds the minimum required state -- level buckets, swings, the swept set, the
  trailing bars a swing needs to confirm -- and nothing else.
* **Outcomes** are local. An event's forward window is at most 12 bars, so an
  event near a boundary is labelled from the next segment's bars. Nothing about
  an outcome survives a boundary, and nothing has to.

The rule the whole design exists to satisfy
-------------------------------------------
A segment boundary is a *memory* boundary and nothing else. Processing the same
history in any segmentation must produce the same events, the same outcomes and
the same statistics as processing it in one pass -- not approximately, exactly.
There is deliberately no ``reset`` anywhere in this module or in
``StructureState``: a reset that callers can reach for is a reset that eventually
gets called at the start of every segment, at which point the segmented run
quietly stops matching the continuous one while both still produce plausible
output.

How memory stays bounded
------------------------
Three things grow with the dataset and each is handled:

* **Bars** -- read through :func:`~app.services.research.streaming.stream_candles`,
  which yields one ``CandleData`` at a time from a 1 MB buffer. A segment holds
  ``segment_days`` of bars and then lets them go. Nothing accumulates.
* **Levels** -- these genuinely accumulate, because they are the analysis. At
  5m over six years that is tens of thousands of small objects, which is
  affordable; what is *not* affordable is the ``(n_resamples, n_events)``
  bootstrap matrix, and that is bounded separately by
  :class:`~app.services.research.aggregate.ClusteredBootstrapper` -- whose exact and
  episode-mean-approximation paths are both batched the same way.
* **Outcomes** -- never retained. Each is folded into a fixed-size accumulator and
  discarded, so the outcome population is O(families x models x horizons) = 96
  numbers regardless of event count.

Aborting and resuming
---------------------
Memory pressure is sampled once per segment. A warning shrinks the next batch
while there is still room to react; a critical reading writes a checkpoint and
exits with :data:`EXIT_RESUMABLE`, and the next invocation continues from it.
The checkpoint carries the dataset version, the bar index reached, the engine and
state schema versions, and a configuration hash -- enough to *refuse* a resume
that would silently combine two different analyses.

Running it
----------
``python -m scripts.run_segmented_research --end 2022-01-01`` and then stop and
read the report. See ``docs/`` for the measured 2021 numbers.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.core.resources import (
    GIB,
    ResourceGuard,
    ResourceLimits,
    ensure_disk_space,
)
from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure.segmented import (
    STATE_SCHEMA_VERSION,
    StructureState,
)
from app.services.research.aggregate import (
    BaselineAccumulator,
    EventSpill,
    OutcomeAccumulator,
    adaptive_resamples,
    label_events_streaming,
)
from app.services.research.events import ResearchEvent, SweepCarried, detect_liquidity_sweeps
from app.services.research.outcomes import (
    ENTRY_OFFSET,
    FORWARD_HORIZONS,
    OffsetCandles,
)
from app.services.research.streaming import dataset_timeframe, stream_candles

#: How far past an event's confirmation bar its forward window reaches. An
#: event needs this many *future* bars before its outcome is fully determined,
#: so this is the lag between detecting it and being able to label it -- and
#: therefore the number of events a checkpoint has to carry.
OUTCOME_LAG_BARS = ENTRY_OFFSET + max(FORWARD_HORIZONS)

#: Bars of history an outcome's stop calculation reaches backwards. The ATR is
#: trailing and the structural stop reaches back to the swing that made the
#: level, so labelling an event near a segment's start needs bars from before it.
#: Carried rather than re-read: they are a fixed count, not a slice of history.
OUTCOME_LOOKBACK_BARS = 64

#: Sentinel for "the dataset has more bars than this run has seen". Larger than
#: any reachable bar index, so every target bar reads as present; the last flush
#: replaces it with the real total so genuinely truncated outcomes are marked.
UNKNOWN_BARS = 1 << 40


def _split_by_window(
    events: list[ResearchEvent], last_available: int, window_start: int
) -> tuple[list[ResearchEvent], list[ResearchEvent]]:
    """Partition events into those labelable from the window in hand, and those
    still waiting for bars this segment does not have.

    An outcome needs bars on *both* sides of its event, and the two conditions
    are checked together because the second is the one that fails silently. The
    forward side is ``confirmation_index + OUTCOME_LAG_BARS <= last_available``:
    confirmation, entry offset, longest horizon. The backward side is the ATR
    window and the structural stop, which reach ``OUTCOME_LOOKBACK_BARS`` bars
    *before* the confirmation -- and those bars are gone once the window has moved
    past them. Testing only the forward side releases an event as soon as its
    horizon exists, which on the following segment is 1600 bars too late: the
    ATR comes back ``None``, the swing stop is unreadable, and the outcome is
    quietly recorded as "no stop" rather than as a wrong one.

    ``window_start`` is the absolute index of the window's first bar. An event's
    confirmation bar must lie inside it, which is the *only* backward
    requirement: ``label_event`` asks for the confirmation bar and whatever
    earlier bars the ATR window needs, and ``_atr`` returns ``None`` when there
    are not enough -- exactly as it does on the batch path for a dataset's
    first bars. Requiring a full ``OUTCOME_LOOKBACK_BARS`` of history behind
    every event would instead make the events just after each window's start
    unlabelable, and since this scan stops at the first blocked event, one such
    event would hold back every event behind it for the rest of the run.

    Events arrive in confirmation order and both thresholds are monotone in that
    order, so this is a single scan that stops at the first event that cannot be
    labelled. Everything after it waits too -- stopping rather than filtering is
    what keeps the pending list from being re-scanned in full every segment.
    """
    split = 0
    while split < len(events):
        event = events[split]
        if event.confirmation_index + OUTCOME_LAG_BARS > last_available:
            break
        if event.confirmation_index < window_start:
            break
        split += 1
    return events[:split], events[split:]

#: Exit code for "stopped cleanly at a checkpoint, run me again". Distinct from
#: an ordinary failure so a scheduler can tell a resource abort from a bug
#: without parsing stderr.
EXIT_RESUMABLE = 75

#: Bumped when the meaning of a research event or outcome changes. A checkpoint
#: written by a different engine version describes a different analysis, and
#: merging the two produces a report that is confidently wrong.
ENGINE_VERSION = 1


class CheckpointMismatch(RuntimeError):
    """A checkpoint cannot be resumed because it describes a different run."""


@dataclass
class Checkpoint:
    """Everything needed to continue a run, and nothing that grows with it.

    The field list is the specification of what crosses a segment boundary. If a
    piece of engine state is not here and not reconstructible from what is here,
    the resumed run is not the same run -- so adding to this list is a decision
    about correctness, not tidiness.
    """

    #: sha256 of the dataset file. The most important field: resuming against a
    #: re-ingested file would blend two price histories into one event log.
    dataset_sha256: str
    dataset_path: str
    #: Absolute bar index of the last bar consumed. Resumption starts here.
    bar_index: int
    last_open_time: str | None
    engine_version: int
    state_schema_version: int
    #: Hash of the analysis configuration -- lookback, tolerance, horizons. Two
    #: runs with different parameters are different analyses even on identical
    #: data, and their events must not be concatenated.
    config_hash: str
    structure: dict
    sweep: dict
    #: Events detected but not yet labellable. Small -- bounded by the forward
    #: horizon -- but dropping them would leave a run whose later segments are
    #: measured on fewer events than its earlier ones, which reads as a finding.
    pending_events: list[dict]
    #: The trailing bars needed to label the next segment's earliest events.
    #: Bounded by ``OUTCOME_LOOKBACK_BARS``, so carrying them costs nothing that
    #: grows with the run.
    tail: list[dict]
    #: Statistics accumulated so far. Merging is exact for the moments these
    #: hold, which is why they are carried and not recomputed.
    outcomes: dict
    baseline: dict
    events_written: int
    segments_done: int
    #: Confirmation bar of each episode's *first* event, in order. Bounded by the
    #: episode count rather than the event count, so it stays small on a busy
    #: series where events vastly outnumber clusters. Carried because an episode
    #: spans events from two segments: an episode whose first event fell just
    #: before a boundary would be counted twice on a resumed run, which is
    #: invisible in every other figure the report prints.
    episode_starts: list[int] = field(default_factory=list)
    #: True once the last segment has been processed and the tail flushed.
    #: A finished checkpoint is not resumable work -- resuming from one would
    #: skip every remaining bar while still holding pending events whose forward
    #: windows can never complete, which fails rather than quietly doing nothing.
    #: Recorded explicitly because "finished" is otherwise indistinguishable from
    #: "stopped at the last segment boundary", and only the first has flushed.
    complete: bool = False

    def to_payload(self) -> dict:
        return {
            "dataset_sha256": self.dataset_sha256,
            "dataset_path": self.dataset_path,
            "bar_index": self.bar_index,
            "last_open_time": self.last_open_time,
            "engine_version": self.engine_version,
            "state_schema_version": self.state_schema_version,
            "config_hash": self.config_hash,
            "structure": self.structure,
            "sweep": self.sweep,
            "pending_events": list(self.pending_events),
            "tail": list(self.tail),
            "outcomes": self.outcomes,
            "baseline": self.baseline,
            "events_written": self.events_written,
            "segments_done": self.segments_done,
            "episode_starts": list(self.episode_starts),
            "complete": self.complete,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> Checkpoint:
        return cls(**payload)


def config_hash(**parts: object) -> str:
    """A stable hash of the analysis parameters.

    Sorted and repr-based so it does not depend on dict ordering or on how a
    value happens to be typed. This goes into the checkpoint: resuming with a
    different lookback would produce an event log that is half one analysis and
    half another, and nothing downstream could see that.
    """
    material = "|".join(f"{key}={parts[key]!r}" for key in sorted(parts))
    return hashlib.sha256(material.encode()).hexdigest()[:16]


def dataset_digest(path: Path) -> str:
    """sha256 of the dataset, read in blocks.

    Blocked rather than ``read_bytes`` because the file is tens of megabytes and
    the point of this project is not to hold things it does not need to. A
    partially-read digest would be worse than none: it would reject a valid
    resume.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class SegmentOutcome:
    """What one segment produced, and what it cost to produce it."""

    index: int
    start: datetime
    end: datetime
    bars: int
    events: int
    swings: int
    levels: int
    seconds: float
    memory_state: str


@dataclass
class RunReport:
    """The run's measured facts. Every number here was observed, not planned."""

    dataset_path: str
    symbol: str
    timeframe: str
    start: datetime | None = None
    end: datetime | None = None
    bars: int = 0
    events: int = 0
    swings: int = 0
    levels: int = 0
    outcomes: int = 0
    episodes: int = 0
    segments: list[SegmentOutcome] = field(default_factory=list)
    checkpoints_written: int = 0
    resumed_from_bar: int | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stopped_on_memory: bool = False
    #: True when the last segment was processed and the tail flushed. Distinct
    #: from ``stopped_on_memory``: a run can end complete, end interrupted, or
    #: begin already complete on a re-invocation, and those are different
    #: results even when the counts agree.
    complete: bool = False
    seconds: float = 0.0
    resources: dict = field(default_factory=dict)
    #: Peak RSS sampled by an external observer, which is the only number that
    #: includes allocations the guard's own sampling might miss between
    #: checkpoints.
    peak_process_gb: float | None = None

    def as_dict(self) -> dict:
        return {
            "dataset_path": self.dataset_path,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "bars": self.bars,
            "events": self.events,
            "swings": self.swings,
            "levels": self.levels,
            "outcomes": self.outcomes,
            "episodes": self.episodes,
            "segments": [
                {
                    "index": s.index,
                    "start": s.start.isoformat(),
                    "end": s.end.isoformat(),
                    "bars": s.bars,
                    "events": s.events,
                    "swings": s.swings,
                    "levels": s.levels,
                    "seconds": round(s.seconds, 3),
                    "memory_state": s.memory_state,
                }
                for s in self.segments
            ],
            "checkpoints_written": self.checkpoints_written,
            "resumed_from_bar": self.resumed_from_bar,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "stopped_on_memory": self.stopped_on_memory,
            "complete": self.complete,
            "seconds": round(self.seconds, 2),
            "resources": self.resources,
            "peak_process_gb": self.peak_process_gb,
        }


class SegmentedResearchRunner:
    """Runs a research pass over a dataset in bounded, resumable segments.

    One instance is one run. ``workers`` is not a parameter and cannot become
    one: every parallel path multiplies peak memory, and peak memory is the
    constraint this whole module is built around.
    """

    def __init__(
        self,
        dataset: Path | str,
        *,
        symbol: str = "BTCUSDT",
        out_dir: Path | str,
        limits: ResourceLimits | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        lookback: int | None = None,
    ) -> None:
        self.dataset = Path(dataset)
        self.symbol = symbol
        self.out_dir = Path(out_dir)
        self.limits = limits or ResourceLimits()
        self.start = start
        self.end = end
        self.lookback = lookback

        if not self.dataset.exists():
            raise FileNotFoundError(self.dataset)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.guard = ResourceGuard(self.limits)
        self.state: StructureState | None = None
        self.sweep = SweepCarried()
        self.accumulators = OutcomeAccumulator()
        self.baseline = BaselineAccumulator()
        self.events_path = self.out_dir / "events.jsonl"
        self.checkpoint_path = self.out_dir / "checkpoint.json"
        self.report_path = self.out_dir / "report.json"

        self._events_written = 0
        self._segments_done = 0
        self._bar_index = 0
        self._episode_starts: list[int] = []
        #: Confirmation bar of the last event folded into ``_episode_starts``,
        #: and how far its forward window reaches. Two scalars rather than a
        #: rescan: deciding whether an event starts a new episode needs only the
        #: previous event's position, so episodes are assigned as events arrive
        #: instead of re-deriving the whole partition from every bar at the end.
        self._episode_last_index = -1
        self._episode_reach = -1
        #: Events detected but not yet labellable, because their forward window
        #: runs past the last bar seen. At most ``OUTCOME_LAG_BARS`` worth of
        #: events, so this is bounded by the horizon rather than by the run --
        #: but it *must* be carried, because an event lost at a boundary is an
        #: outcome that is silently never measured.
        self._pending_events: list[ResearchEvent] = []
        #: The last ``OUTCOME_LOOKBACK_BARS`` bars of the previous segment, kept
        #: so this segment's earliest events can be labelled with a full ATR
        #: window. Bounded by the horizon, not by the run.
        self._tail: list[CandleData] = []
        #: Set when a checkpoint was found already complete, so the run reports
        #: the finished result instead of reprocessing the dataset.
        self._resume_complete = False
        #: Test-only: stop after this many segments in :meth:`run`, producing a
        #: genuinely interrupted run to resume from. ``None`` in production --
        #: the resource guard decides when to stop, not a caller-supplied count,
        #: because a limit set by hand is a limit someone will forget to remove.
        self._max_segments: int | None = None
        #: Set by the segment generator when the segment it yielded turned out to
        #: be the last one. Reading ahead to discover this would mean holding two
        #: segments' bars at once.
        self._segment_was_final = False
        #: Total bars in the dataset, as far as the runner knows. A labelling
        #: function decides whether an outcome is ``truncated`` by comparing a
        #: target index against the dataset length, and inside a segment that is
        #: not the window's length -- so a boundary would otherwise masquerade as
        #: the end of the history. Set to a sentinel meaning "the run continues",
        #: which is the honest answer: only the events still pending at the end
        #: are genuinely truncated, and those are flushed with the real total.
        self._dataset_bars = UNKNOWN_BARS

    # -- configuration ----------------------------------------------------

    @property
    def timeframe(self) -> Timeframe:
        value = dataset_timeframe(self.dataset)
        if value is None:
            raise ValueError(f"{self.dataset} has no timeframe in its first record")
        return value

    def config_fingerprint(self) -> str:
        """Hash of everything that would make two runs different analyses.

        The date range and the segment size belong here even though they do not
        change the analysis. A checkpoint records *absolute* bar indices, so a
        one-month run resuming from a full-year checkpoint would skip 8,000 bars
        it never processed and then try to label events against bars it never
        read -- an error, but one that looks like a segmentation bug rather than
        a mismatched checkpoint. Segment size is included because bar indices are
        also relative to where segments begin.
        """
        return config_hash(
            symbol=self.symbol,
            timeframe=str(self.timeframe),
            lookback=self.lookback,
            start=self.start.isoformat() if self.start else None,
            end=self.end.isoformat() if self.end else None,
            segment_days=self.limits.segment_days,
            level_tolerance="0.001",
            min_penetration="0",
            stop_models=["atr_mult_1.5", "atr_mult_2.5"],
            horizons=[1, 3, 6, 12],
        )

    # -- checkpointing ----------------------------------------------------

    def _write_checkpoint(self, spill: EventSpill | None = None, *, complete: bool = False) -> None:
        """Save the carried state so the next invocation can continue.

        Written atomically via a temporary file and a rename. A checkpoint that
        is half-written is worse than none: it looks resumable, and resuming
        from it puts a hole in the state that no later test can see.

        The spill is flushed *first*, and ``events_written`` is then taken from
        the spill's own count rather than from a running tally. The two order
        the durability of the two files: a checkpoint that records 731,839
        events next to a spill holding 731,670 is a claim the run cannot back up,
        and it is produced whenever the process dies between a segment's
        detection and the next batch flush -- which is precisely the moment a
        memory abort kills it. Flushing first makes the spill the authority, so
        the invariant is "the spill holds at least what the checkpoint claims"
        rather than "usually".
        """
        if self.state is None:
            return
        if spill is not None:
            spill.flush()
        checkpoint = Checkpoint(
            dataset_sha256=self._digest,
            dataset_path=str(self.dataset),
            bar_index=self._bar_index,
            last_open_time=(
                self.state._last_open_time.isoformat()
                if self.state._last_open_time
                else None
            ),
            engine_version=ENGINE_VERSION,
            state_schema_version=STATE_SCHEMA_VERSION,
            config_hash=self.config_fingerprint(),
            structure=self.state.to_payload(),
            sweep=self.sweep.to_payload(),
            pending_events=[e.to_payload() for e in self._pending_events],
            tail=[c.model_dump(mode="json") for c in self._tail],
            outcomes=self.accumulators.as_dict(),
            baseline=self.baseline.as_dict(),
            events_written=(
                spill.count if spill is not None else self._events_written
            ),
            segments_done=self._segments_done,
            episode_starts=self._episode_starts,
            complete=complete,
        )
        temporary = self.checkpoint_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(checkpoint.to_payload(), separators=(",", ":")), encoding="utf-8"
        )
        temporary.replace(self.checkpoint_path)

    def _load_checkpoint(self) -> bool:
        """Restore a checkpoint, or return False if there is not one to use.

        Every mismatch is fatal rather than repaired. Resuming across a schema or
        engine change by interpreting the old fields anyway produces a clean-looking
        report of the wrong run, and detecting it later is impossible.
        """
        if not self.checkpoint_path.exists():
            return False
        payload = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        checkpoint = Checkpoint.from_payload(payload)

        if checkpoint.dataset_sha256 != self._digest:
            raise CheckpointMismatch(
                f"checkpoint was written against dataset sha256 "
                f"{checkpoint.dataset_sha256[:16]} but {self.dataset} is "
                f"{self._digest[:16]}; the file has been re-ingested and the two "
                "event logs cannot be combined"
            )
        if checkpoint.engine_version != ENGINE_VERSION:
            raise CheckpointMismatch(
                f"checkpoint engine version {checkpoint.engine_version} != "
                f"{ENGINE_VERSION}"
            )
        if checkpoint.state_schema_version != STATE_SCHEMA_VERSION:
            raise CheckpointMismatch(
                f"checkpoint state schema {checkpoint.state_schema_version} != "
                f"{STATE_SCHEMA_VERSION}"
            )
        if checkpoint.config_hash != self.config_fingerprint():
            raise CheckpointMismatch(
                "checkpoint was written with different analysis parameters "
                f"({checkpoint.config_hash} != {self.config_fingerprint()})"
            )

        self.state = StructureState.from_payload(checkpoint.structure)
        self.sweep = SweepCarried.from_payload(checkpoint.sweep)
        self._pending_events = [
            ResearchEvent.from_payload(p) for p in checkpoint.pending_events
        ]
        self._tail = [
            CandleData.model_validate(c) for c in checkpoint.tail
        ]
        self._bar_index = checkpoint.bar_index
        self._events_written = checkpoint.events_written
        self._segments_done = checkpoint.segments_done
        self._restore_accumulators(checkpoint)
        self._restore_episodes(checkpoint)
        if checkpoint.complete:
            # The work is done. Say so rather than reprocessing from bar zero:
            # a caller that re-invokes a finished run would otherwise re-detect
            # every event and append them to a spill that already holds them.
            self._pending_events = []
            self._resume_complete = True
            return False
        return True

    def _restore_episodes(self, checkpoint: Checkpoint) -> None:
        """Reinstate the episode partition a checkpointed run had reached.

        Episodes are the one figure a resumed run gets *wrong* without this,
        and wrong in a way nothing else in the report would reveal: bars, events,
        outcomes, swings and levels all resume correctly, because they are
        counters or cumulative state. Episodes are a partition of the event
        stream, so a run that resumes from bar 40,000 and re-derives them from
        the events it sees will count the episodes from bar 40,000 onward and
        silently report fewer of them -- the resumed run looks like it found a
        quieter market.

        The carry is the whole start list, not a tail: an episode spans events up
        to ``OUTCOME_LAG_BARS`` apart, so the last episode may still be open
        across the boundary and dropping it would merge or split one cluster.
        """
        self._episode_starts = list(checkpoint.episode_starts)
        last = self._episode_starts[-1] if self._episode_starts else -1
        self._episode_last_index = last
        self._episode_reach = last + max(FORWARD_HORIZONS) if last >= 0 else -1

    def _note_episode(self, confirmation_index: int) -> None:
        """Fold one event into the running episode partition.

        Incremental for the same reason ``assign_episodes`` is a single sweep:
        a new event joins the open episode when it falls inside the previous
        event's forward window, and opens its own when it does not. Keeping the
        partition rather than the raw bar list is what makes it small enough to
        checkpoint -- ~73k ints rather than ~732k for the 2021 run.
        """
        if confirmation_index <= self._episode_reach:
            self._episode_last_index = confirmation_index
            return
        self._episode_starts.append(confirmation_index)
        self._episode_last_index = confirmation_index
        self._episode_reach = confirmation_index + max(FORWARD_HORIZONS)

    def _restore_accumulators(self, checkpoint: Checkpoint) -> None:
        """Rebuild the outcome and baseline accumulators from a checkpoint.

        Moments are stored as (n, mean, m2) and converted back, because those
        three are exactly sufficient -- a running mean and variance can be
        resumed without keeping the samples that produced them. Storing a
        *summary* rather than the values is what makes a checkpoint constant-size
        no matter how many events the run has seen.

        Restores barriers and excursions too, not just the forward-return
        moments. They are the same kind of state and they were in the spill of
        every segment before the crash; dropping them on resume would make a
        resumed run's barrier counts describe only the segments after the
        checkpoint, which is indistinguishable from a detector that stopped
        finding barriers.
        """
        from app.services.research.aggregate import Moment, OutcomeKey

        for cell in checkpoint.outcomes.get("cells", []):
            key = OutcomeKey(
                cell["detector"], cell["kind"], cell["side"], cell["stop_model"]
            )
            name = key.as_str()
            self.accumulators._keys.setdefault(name, key)
            for horizon, moment in cell.get("horizons", {}).items():
                self.accumulators._moments[(name, int(horizon))] = Moment.from_dict(
                    moment
                )
            for label, moment in cell.get("excursions", {}).items():
                self.accumulators._excursions[(label, name)] = Moment.from_dict(moment)
            if cell.get("barriers"):
                self.accumulators._barriers[name] = dict(cell["barriers"])
        self.accumulators.total = int(
            checkpoint.outcomes.get("total_outcomes", 0)
        )
        self.accumulators._truncated = int(
            checkpoint.outcomes.get("truncated_outcomes", 0)
        )

        for horizon, moment in checkpoint.baseline.get("horizons", {}).items():
            self.baseline._moments[int(horizon)] = Moment.from_dict(moment)
        self.baseline.bars = int(checkpoint.baseline.get("bars", 0))

    # -- running ----------------------------------------------------------

    def run(self) -> RunReport:
        """Process the dataset, one bounded segment at a time.

        Returns a report of what was measured. Raises :class:`CheckpointMismatch`
        if a checkpoint cannot be trusted, and returns normally with
        ``stopped_on_memory`` set if the run stopped cleanly for memory -- which
        is a successful *abort*, not a failure, and the caller decides whether to
        resume.
        """
        started = time.monotonic()
        report = RunReport(
            dataset_path=str(self.dataset),
            symbol=self.symbol,
            timeframe=str(self.timeframe),
            start=self.start,
            end=self.end,
        )

        self._digest = dataset_digest(self.dataset)
        # Refuse to start if the output cannot fit. Discovering a full disk
        # halfway through wastes the run; this costs one statvfs.
        ensure_disk_space(
            self.dataset.stat().st_size, path=self.out_dir, limits=self.limits
        )

        resumed = self._load_checkpoint()
        if resumed:
            report.resumed_from_bar = self._bar_index
        elif self._resume_complete:
            report.complete = True
        else:
            self.state = StructureState(self.symbol, self.timeframe)

        # Skip forward to the resume point rather than re-reading and discarding.
        # On a resumed run this is most of the file, and reading it would cost the
        # exact time the checkpoint was supposed to save.
        source = stream_candles(self.dataset)
        if self._bar_index:
            for _ in range(self._bar_index):
                next(source)

        # Append whenever the spill already holds events -- on a resumed run, and
        # on a re-invocation of a finished one, where ``_load_checkpoint``
        # returns False *because* the work is done. Keying off the return value
        # alone would truncate the file in the one case where there is most to
        # lose.
        existing = resumed or self._resume_complete
        spill = EventSpill(self.events_path, mode="a" if existing else "w")
        try:
            # A completed checkpoint has nothing left to process, and writing a
            # fresh spill on top of the one it produced would leave the finished
            # run's events truncated to nothing.
            if not self._resume_complete:
                for segment in self._segments(source):
                    memory_state = self.guard.check()
                    if self._max_segments is not None and (
                        report.checkpoints_written >= self._max_segments
                    ):
                        # Test-only stop. A deliberately unfinished run must not
                        # flush the tail: the tail is labelled against the end of
                        # the *dataset*, so flushing it after two of twelve
                        # segments would mark every pending event truncated and
                        # make the resumed run's totals disagree for a reason
                        # that has nothing to do with resume.
                        report.stopped_on_memory = True
                        break
                    # Only the last segment can report a sweep on its own last
                    # bar. Every other one defers it, because its confirmation
                    # bar is the next segment's first -- a boundary is a memory
                    # boundary, and resolving a confirmation against the wrong bar
                    # is not.
                    self._process_segment(
                        segment, spill, report, final=self._segment_was_final
                    )

                    self._write_checkpoint(spill)
                    report.checkpoints_written += 1

                    if memory_state == "critical":
                        # Stop at a segment boundary with the state saved. The
                        # alternative -- continuing and hoping -- is what turns a
                        # resource problem into an unusable machine.
                        report.stopped_on_memory = True
                        report.warnings.append(
                            f"stopped after segment {segment.index} at the "
                            f"{self.limits.critical_ram_gb:.2f} GB critical "
                            f"threshold; resume from {self.checkpoint_path}"
                        )
                        break
        finally:
            spill.close()

        # The tail. Events whose forward window ran past the last bar are
        # labelled here, against the *real* dataset length, so their outcomes are
        # marked truncated rather than being quietly counted as flat moves. This
        # is the only place a legitimately truncated outcome is produced, and it
        # is deliberately the same code path as every other label -- a separate
        # "final" branch would be a second thing to get wrong.
        if self._pending_events and self.state is not None and not report.stopped_on_memory:
            tail_start = max(0, self._bar_index - len(self._tail))
            final_window = OffsetCandles(self._tail, tail_start, self._bar_index)
            label_events_streaming(
                final_window, self._pending_events, self.accumulators
            )
            self._pending_events.clear()

        # Only mark the checkpoint complete when the run actually reached the end
        # of the data. A run that stopped on memory has not, and marking it would
        # tell the next invocation there is nothing left to do.
        if not report.stopped_on_memory:
            self._write_checkpoint(spill, complete=True)
            report.complete = True

        report.bars = self._bar_index
        report.events = self._events_written
        report.swings = len(self.state.swings) if self.state else 0
        report.levels = len(self.state.levels()) if self.state else 0
        report.outcomes = self.accumulators.total
        report.episodes = self.episode_count()
        report.warnings.extend(self.guard.warnings)
        report.resources = self.guard.report()
        report.peak_process_gb = self.guard.peak_process_gb
        report.seconds = time.monotonic() - started

        self.report_path.write_text(
            json.dumps(report.as_dict(), indent=2, default=str), encoding="utf-8"
        )
        return report

    def _segments(self, source):
        """Group the stream into ``segment_days`` blocks, yielding the bars.

        Yields ``(index, start, end, candles)`` and sets :attr:`_segment_was_final`
        when the segment it just yielded turned out to be the last one.

        The alternative -- peeking at the iterator to see whether another
        segment exists -- means holding one extra segment's bars in memory, and a
        segment is exactly the population this design exists to bound. Here the
        generator learns a segment was final only when it resumes and finds the
        source exhausted, which costs one boolean and no extra bars.

        A list per segment is unavoidable -- a sweep needs a bar *and* the bar
        after it -- but it is the only bar population that ever exists, and it is
        released as soon as the segment is processed.
        """
        from datetime import timedelta

        from app.services.research.streaming import _floor_to_days

        span = timedelta(days=self.limits.segment_days)
        current: list[CandleData] = []
        current_start: datetime | None = None
        index = 0

        for candle in source:
            if self.start and candle.open_time < self.start:
                continue
            if self.end and candle.open_time >= self.end:
                break
            block = _floor_to_days(candle.open_time, self.limits.segment_days)
            if current_start is None:
                current_start = block
            elif block != current_start:
                self._segment_was_final = False
                yield index, current_start, current_start + span, current
                current = []
                current_start = block
                index += 1
            current.append(candle)

        if current and current_start is not None:
            self._segment_was_final = True
            yield index, current_start, current_start + span, current

    def _process_segment(
        self, segment, spill: EventSpill, report: RunReport, *, final: bool
    ) -> None:
        """Feed one segment through structure, detection and labelling.

        Ordered deliberately: the previous segment's events are labelled *first*,
        because those are the ones whose forward windows this segment completes.
        Labelling a segment's own events here would truncate them at the
        boundary -- an event eight bars before the end would have an eight-bar
        forward window instead of twelve, and the mean over all events would not
        be the mean of any single distribution.
        """
        index, start, end, bars = segment
        assert self.state is not None
        if not bars:
            return

        began = time.monotonic()
        offset = self._bar_index

        # Labelling needs bars on both sides of an event: a few before it for the
        # ATR and the structural stop, and up to ``OUTCOME_LAG_BARS`` after it for
        # the forward window. The tail comes from the previous segment, which is
        # why it is kept rather than discarded -- 64 bars, not a slice of
        # history, and without it every event near a segment's start is labelled
        # from an ATR computed over a truncated window.
        tail_start = max(0, offset - len(self._tail))
        labelled = self._tail + bars
        last_available = offset + len(bars) - 1
        window = OffsetCandles(labelled, tail_start, last_available + 1)

        # 1. Structure. This is the genuinely global state, and it is carried
        #    rather than recomputed.
        self.state.observe(bars)

        # 2. Detection. Levels accumulate across the run -- they are the
        #    analysis, not a per-segment artifact -- and the swept set is
        #    carried, so a level crossed in January and revisited in June is
        #    recognised as the same level.
        events = detect_liquidity_sweeps(
            bars,
            levels=self.state.levels(),
            offset=offset,
            carried=self.sweep,
            final=final,
        )
        for event in events:
            spill.append(event)
            self._note_episode(event.confirmation_index)
        self._events_written += len(events)

        # 3. Labelling. Done *after* detection, on this segment's own events as
        #    well as the last segment's leftovers, so that only the 13 bars still
        #    in flight cross a boundary. Labelling the previous segment's events
        #    against the *next* segment's window instead would defer a whole
        #    segment at a time, and the events released first would be the ones
        #    whose ATR and swing-stop bars had already been dropped.
        #
        #    The backlog is sorted before the split, because ``_split_by_window``
        #    stops at the first event it cannot label. Concatenating instead
        #    would order the list by *segment* rather than by bar, so one stale
        #    event from a segment ago would sit at the front and hold back every
        #    labelable event behind it -- a backlog that grows by a whole segment
        #    each time and is never drained.
        backlog = sorted(
            itertools.chain(self._pending_events, events),
            key=lambda event: event.confirmation_index,
        )
        ready, self._pending_events = _split_by_window(
            backlog, last_available, tail_start
        )
        if ready:
            label_events_streaming(window, ready, self.accumulators)

        # Keep the tail the next segment's outcomes will need. Capped across the
        # join rather than sliced out of this segment alone: a short segment (a
        # partial final one, or a gap in the data) would otherwise leave a tail
        # shorter than the lookback, and the next segment would then compute ATRs
        # and swing stops from a window that starts too late -- silently, because
        # ``_atr`` returns ``None`` and the outcome is recorded as "no stop".
        self._tail = (self._tail + bars)[-OUTCOME_LOOKBACK_BARS:]

        self._bar_index += len(bars)
        self._segments_done += 1

        report.segments.append(
            SegmentOutcome(
                index=index,
                start=start,
                end=end,
                bars=len(bars),
                events=len(events),
                swings=len(self.state.swings),
                levels=len(self.state.levels()),
                seconds=time.monotonic() - began,
                memory_state=self.guard.check(),
            )
        )

    # -- statistics -------------------------------------------------------

    def episode_count(self) -> int:
        """How many independent outcome clusters this run produced.

        The cluster count, not the event count, is what decides a bootstrap's
        resolution: resampling 40 episodes 50,000 times estimates those same 40
        clusters more precisely without narrowing the interval, so the honest
        figure to report is the number of episodes.

        ``_note_episode`` computes this incrementally rather than calling
        :func:`assign_episodes` over every event at the end. The rule is the
        same -- the sweep in ``_note_episode`` is a transcription of it -- and
        ``test_episode_partition_matches_the_batch_sweep`` asserts the two agree
        bar for bar. What the incremental form buys is that the partition is
        checkpoint-sized (~73k ints for 2021) instead of being a 732k-entry
        list that has to survive a resume intact.
        """
        return len(self._episode_starts)

    def suggested_resamples(self, *, precision: str = "research") -> int:
        """Bootstrap draws appropriate to this run's episode count.

        Fewer episodes than draws is worth stopping at: resampling 40 episodes
        50,000 times estimates those same 40 clusters more precisely without
        narrowing the interval, and the honest report is the cluster count.
        """
        return adaptive_resamples(self.episode_count(), precision=precision)


def render_report(report: RunReport, limits: ResourceLimits) -> str:
    """The run's report as the plain text a person actually reads.

    Deliberately includes the *measured* peaks next to the *configured*
    ceilings. A report showing only the limits asserts the plan; only the peaks
    say whether the plan was safe.
    """
    lines = [
        "SEGMENTED RESEARCH RUN REPORT",
        f"Dataset:      {report.dataset_path}",
        f"Symbol:       {report.symbol} {report.timeframe}",
        f"Range:        {report.start} -> {report.end}",
        "",
        f"Bars:         {report.bars:,}",
        f"Events:       {report.events:,}",
        f"Episodes:     {report.episodes:,}",
        f"Swings:       {report.swings:,}",
        f"Levels:       {report.levels:,}",
        f"Outcomes:     {report.outcomes:,}",
        f"Segments:     {len(report.segments)}",
        f"Checkpoints:  {report.checkpoints_written}",
        f"Runtime:      {report.seconds:.1f}s",
        "",
        "RESOURCES (measured / configured)",
        f"Peak process RSS:  {fmt_gb(report.peak_process_gb)} / "
        f"{limits.max_ram_gb:.2f} GB",
        f"Lowest sys avail:  "
        f"{fmt_gb(report.resources.get('lowest_system_available_gb'))} / "
        f"{limits.warning_ram_gb:.2f} GB warning",
        f"Stopped on memory: {report.stopped_on_memory}",
        "",
        f"Warnings:     {len(report.warnings)}",
        *report.warnings,
        f"Errors:       {len(report.errors)}",
        *report.errors,
    ]
    return "\n".join(lines)


def fmt_gb(value: object) -> str:
    return "n/a" if value is None else f"{float(value):.2f} GB"
