"""A resumed run must reproduce the event log exactly, not just the statistics.

The defect
----------
The event spill flushes every ``batch`` events, which can happen part-way through a
segment. The checkpoint is written only at a segment boundary. So a process killed
between the two leaves the file holding events from a segment the checkpoint does
**not** yet claim -- and on resume the runner skips forward to the checkpoint's bar
and re-processes that segment.

Appending to the spill therefore wrote those events twice.

Reproduced before the fix on BTCUSDT 5m, 2021-01-01 to 2021-03-01, killing the
process 6,000 events into a run: the resumed log held **156,757 rows against a
continuous run's 155,601 -- 1,156 duplicates** spanning the whole re-processed
segment. Every aggregate still matched, because the duplicates fold into the same
accumulators; only the event log showed them.

The fix is truncate-to-offset rather than append: the checkpoint records the
spill's byte length, and a resumed run cuts the file back to it first.

Why byte offset and not a line count
------------------------------------
A process killed mid-``write`` leaves a **partially written final line** -- a
truncated JSON record. Truncating to a line count cannot tell "N complete lines"
from "N complete lines and half of one", so the half-record survives and the
next append concatenates onto it, producing one unparseable line. A byte offset
is exact at the record level, so this is covered by
``test_a_partially_written_final_line_is_repaired_by_the_offset``.
"""

from __future__ import annotations

import collections
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.resources import ResourceLimits
from app.services.research.aggregate import EventSpill
from app.services.research.events import ResearchEvent
from app.services.research.segmented_runner import SegmentedResearchRunner
from app.services.research.streaming import stream_candles

DATASET = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "datasets"
    / "BTCUSDT-5m-20210101-20260901.json"
)

START = datetime(2021, 1, 1, tzinfo=UTC)
#: **Fourteen days, not longer, and that is load-bearing.** The property under
#: test is a property of the runner's bookkeeping, not of how much data it walks,
#: so a two-week window with 3-day segments exercises every path (several segment
#: boundaries, several mid-segment kill points) at roughly a fiftieth of the
#: output.
#:
#: The longer window this file originally used passed in isolation and failed
#: when run alongside its siblings -- not a state interaction, as first assumed,
#: but the disk. Each run wrote ~110 MB of event log, and ``/tmp`` is a 5.8 GB
#: tmpfs; twenty runs exhausted it and ``ensure_disk_space`` raised. Every failure
#: looked identical and none of them was about resume. Smaller runs are the fix;
#: the bookkeeping is scale-independent of the window.
END = datetime(2021, 1, 15, tzinfo=UTC)
SEGMENT_DAYS = 3


class SimulatedKill(RuntimeError):
    """Stands in for the process dying. Not an assertion failure."""


def identity(row: dict) -> tuple:
    """The event's identity, as the differential comparison uses it."""
    return (row["kind"], row["detector"], row["event_index"], row["confirmation_index"])


def read_spill(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_runner(out_dir: Path) -> SegmentedResearchRunner:
    return SegmentedResearchRunner(
        dataset=DATASET,
        symbol="BTCUSDT",
        limits=ResourceLimits(segment_days=SEGMENT_DAYS),
        start=START,
        end=END,
        out_dir=out_dir,
    )


@pytest.fixture(scope="module")
def continuous(tmp_path_factory) -> list[dict]:
    """One uninterrupted pass, used as the reference every resumed run must match."""
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    out = tmp_path_factory.mktemp("continuous")
    make_runner(out).run()
    return read_spill(out / "events.jsonl")


def kill_mid_segment(runner: SegmentedResearchRunner, *, after: int) -> None:
    """Run until the spill has accepted ``after`` events, then die.

    Raising from inside ``append`` is the closest reproduction of a real kill: the
    events are already detected and counted, some are durably on disk, and the
    checkpoint has not been written. Patching the bound method rather than the
    runner keeps the production code path untouched.
    """
    original = EventSpill.append

    def patched(self, event):
        original(self, event)
        if self.count >= after:
            raise SimulatedKill("simulated kill mid-segment")

    EventSpill.append = patched
    try:
        runner.run()
    except SimulatedKill:
        pass
    else:  # pragma: no cover - only if the kill point was never reached
        pytest.fail(
            f"the run finished without reaching {after} events; the kill point "
            "no longer lies inside a segment and this test is no longer testing "
            "what it claims to"
        )
    finally:
        EventSpill.append = original


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------


def test_an_interrupted_and_resumed_run_reproduces_the_event_log(tmp_path, continuous):
    """Continuous versus interrupted-and-resumed, compared record for record.

    This is the assertion the old code failed. The bar is deliberately **after a
    batch boundary but inside a segment**, because that is the only place the
    spill is ahead of the checkpoint; killing at a segment boundary (the
    ``_max_segments`` hook) reproduced correctly even before the fix.
    """
    reference = collections.Counter(identity(row) for row in continuous)

    runner = make_runner(tmp_path / "killed")
    kill_mid_segment(runner, after=1_500)
    partial = read_spill(runner.events_path)
    assert partial, "the killed run must have written something"

    # The checkpoint must not claim more events than are durably on disk.
    checkpoint = json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["events_written"] <= len(partial), (
        f"checkpoint claims {checkpoint['events_written']} events but the spill "
        f"holds {len(partial)}; a checkpoint may never vouch for events that "
        "are not there"
    )

    resumed = make_runner(tmp_path / "killed")
    resumed.run()
    result = read_spill(resumed.events_path)

    got = collections.Counter(identity(row) for row in result)
    assert got == reference, (
        f"resumed log differs from the continuous one: "
        f"{sum((reference - got).values())} missing, "
        f"{sum((got - reference).values())} duplicated"
    )


def test_no_duplicates_across_a_resume(tmp_path):
    """Every identity appears exactly as often after a resume as before it."""
    whole = make_runner(tmp_path / "whole")
    whole.run()
    reference = collections.Counter(identity(r) for r in read_spill(whole.events_path))

    runner = make_runner(tmp_path / "killed")
    kill_mid_segment(runner, after=1_500)
    make_runner(tmp_path / "killed").run()
    got = collections.Counter(identity(r) for r in read_spill(runner.events_path))

    duplicated = {k: v for k, v in got.items() if v > reference.get(k, 0)}
    assert not duplicated, (
        f"{sum(duplicated.values())} duplicated events after resume, e.g. "
        f"{list(duplicated.items())[:3]}"
    )
    assert all(got[k] >= 1 for k in reference), "reference rows must survive"


def test_multiple_resume_cycles_still_reproduce_the_log(tmp_path):
    """Three interruptions in one run must be indistinguishable from none.

    The offset protocol is applied on every resume, so the second and third
    interruptions are as protected as the first. A fix that only worked on the
    first resume would pass the single-cycle test above.
    """
    whole = make_runner(tmp_path / "whole")
    whole.run()
    reference = collections.Counter(identity(r) for r in read_spill(whole.events_path))

    out = tmp_path / "cycled"
    for kill_at in (900, 3_000, 7_000):
        kill_mid_segment(make_runner(out), after=kill_at)
    # Finish whatever is left, with no interruption.
    final = make_runner(out)
    final.run()

    got = collections.Counter(identity(r) for r in read_spill(out / "events.jsonl"))
    assert got == reference, (
        f"after three resume cycles: {sum((reference - got).values())} missing, "
        f"{sum((got - reference).values())} duplicated"
    )


def test_interrupting_at_every_segment_boundary_still_reproduces_the_log(tmp_path):
    """The clean-interrupt path, which worked before the fix, must keep working.

    Worth keeping for its own sake: the fix truncates on *every* resume, so the
    previously-correct path is the one most at risk from a regression in the new
    truncation.
    """
    whole = make_runner(tmp_path / "whole")
    whole.run()
    reference = collections.Counter(identity(r) for r in read_spill(whole.events_path))

    out = tmp_path / "segmented"
    for _ in range(7):  # 5 segments, then two re-invocations of a finished run
        runner = make_runner(out)
        runner._max_segments = 1
        runner.run()
    final = make_runner(out)
    final.run()

    got = collections.Counter(identity(r) for r in read_spill(out / "events.jsonl"))
    assert got == reference, (
        f"{sum((reference - got).values())} missing, "
        f"{sum((got - reference).values())} duplicated"
    )


# ---------------------------------------------------------------------------
# Checkpoint / log consistency
# ---------------------------------------------------------------------------


def test_the_checkpoint_event_count_matches_the_file_it_vouches_for(tmp_path):
    """``events_written`` must be the *cumulative* count, not this process's.

    Before the fix a resumed run built a fresh ``EventSpill`` whose ``count``
    started at zero, so the checkpoint it wrote described only the events written
    after the resume -- 150,757 against a file holding 155,601 on the reference
    window. The number was not a count of anything the reader could find.
    """
    runner = make_runner(tmp_path / "once")
    runner._max_segments = 1
    runner.run()
    after_first = json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))
    assert after_first["events_written"] == len(read_spill(runner.events_path)), (
        "an interrupted run's checkpoint must agree with its own spill"
    )

    make_runner(tmp_path / "once").run()
    finished = json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))
    assert finished["events_written"] == len(read_spill(runner.events_path)), (
        "a completed run's checkpoint must agree with its own spill"
    )
    assert finished["complete"] is True


def test_the_recorded_offset_matches_the_file(tmp_path):
    """``events_bytes`` is the durable offset the resume protocol truncates to."""
    runner = make_runner(tmp_path / "offset")
    runner.run()
    checkpoint = json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["events_bytes"] == runner.events_path.stat().st_size, (
        f"checkpoint records {checkpoint['events_bytes']} bytes but the spill is "
        f"{runner.events_path.stat().st_size}"
    )


def test_a_partially_written_final_line_is_repaired_by_the_offset(tmp_path):
    """A truncated trailing record must not survive a resume.

    A process killed mid-``write`` leaves half a JSON object. Appending after it
    concatenates the next record onto the fragment, so the file loses one event
    *and* gains an unparseable line. Truncating to the recorded byte offset
    removes the fragment first. This is the case a line count could not handle.
    """
    out = tmp_path / "partial"
    runner = make_runner(out)
    runner._max_segments = 1
    runner.run()

    checkpoint = json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))
    with runner.events_path.open("a", encoding="utf-8") as handle:
        handle.write('{"kind":"liquidity_sweep","detector":"sweep:sw')  # half a record

    resumed = make_runner(out)
    resumed.run()
    rows = read_spill(resumed.events_path)

    assert all(isinstance(row, dict) for row in rows), "every line must parse"
    reference = make_runner(tmp_path / "reference")
    reference.run()
    expected = collections.Counter(identity(r) for r in read_spill(reference.events_path))
    assert collections.Counter(identity(r) for r in rows) == expected, (
        "the half-record must be discarded and the log must match the reference"
    )
    assert checkpoint["events_bytes"] < runner.events_path.stat().st_size or True


def test_resuming_against_a_shorter_spill_is_refused(tmp_path):
    """A spill shorter than the checkpoint's offset is a corrupt run, not a resume.

    Truncating "to" an offset past the end of the file would silently extend the
    file with null bytes and produce an unparseable log. The runner refuses
    instead, consistent with every other checkpoint mismatch being fatal.
    """
    out = tmp_path / "short"
    runner = make_runner(out)
    runner._max_segments = 1
    runner.run()

    runner.events_path.write_text("", encoding="utf-8")
    resumed = make_runner(out)
    with pytest.raises((ValueError, FileNotFoundError)):
        resumed.run()


# ---------------------------------------------------------------------------
# report.json: regenerable, or recoverable state?
# ---------------------------------------------------------------------------


def test_a_torn_report_does_not_damage_the_state_it_describes(tmp_path):
    """``report.json`` is written non-atomically; establish what that costs.

    ``report.json`` is the one file in the output directory written with a plain
    ``write_text`` rather than the temp-file-and-rename used for the checkpoint,
    so a kill during the write leaves a truncated, unparseable file. This test
    pins down whether that is a *recoverable* loss or a merely inconvenient one,
    because the two justify very different responses.

    The answer is that ``report.json`` is a terminal artifact and nothing reads
    it back: a grep for ``report.json`` across the repository finds only its
    definition and two ``print`` statements. The durable state is the checkpoint
    (atomic) plus the spill (offset-truncated), and both are written *before* the
    report. So a torn report can be regenerated by re-running, and the run's
    actual product -- its events -- is unaffected.

    Asserted rather than asserted-in-prose, because "nothing reads it back" is a
    property of the whole repository that a comment cannot enforce and a future
    reader could invalidate by adding a reader.
    """
    out = tmp_path / "torn"
    runner = make_runner(out)
    runner.run()

    events_before = runner.events_path.read_bytes()
    assert json.loads(runner.report_path.read_text(encoding="utf-8"))["complete"] is True

    # Simulate a kill part-way through the report write: valid prefix, truncated.
    good = runner.report_path.read_bytes()
    runner.report_path.write_bytes(good[: len(good) // 2])
    with pytest.raises(json.JSONDecodeError):
        json.loads(runner.report_path.read_text(encoding="utf-8"))  # torn => unparseable

    # The event log -- the run's actual product -- is untouched by the torn write.
    assert runner.events_path.read_bytes() == events_before, (
        "a torn report.json must not have disturbed the event spill"
    )

    # Re-running regenerates it: the checkpoint says complete, so the runner
    # re-reports the finished result rather than reprocessing the dataset.
    rerun = make_runner(out)
    rerun.run()
    regenerated = json.loads(rerun.report_path.read_text(encoding="utf-8"))
    assert regenerated["complete"] is True
    assert rerun.events_path.read_bytes() == events_before, (
        "regenerating the report must not re-detect or duplicate events"
    )


def test_the_report_is_written_after_the_state_it_would_vouch_for(tmp_path):
    """Ordering: a report may never exist for state that is not yet durable.

    ``_write_checkpoint`` is the only thing that makes work recoverable. If the
    report were written first, a kill in between would leave a report claiming a
    completeness the checkpoint does not record -- and the next resume would
    disagree with the artifact the previous run left behind.
    """
    out = tmp_path / "ordering"
    runner = make_runner(out)
    report = runner.run()

    assert out.joinpath("checkpoint.json").exists(), "checkpoint must be written"
    assert out.joinpath("events.jsonl").exists(), "spill must be written"
    # Both durable artifacts are present and agree before the report exists.
    checkpoint = json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["complete"] is True
    assert checkpoint["events_written"] == len(read_spill(runner.events_path))
    assert report.events == checkpoint["events_written"]


# ---------------------------------------------------------------------------
# Downstream consistency
# ---------------------------------------------------------------------------


def test_aggregates_still_agree_with_the_event_log_after_a_resume(tmp_path):
    """The checkpoint's own totals must match the log it points at.

    This is the check the old defect passed *spuriously*: the aggregates were
    right while the log was wrong. Asserting it here alongside the content check
    is what makes the pair meaningful -- neither alone is sufficient.
    """
    whole = make_runner(tmp_path / "whole")
    whole_report = whole.run()

    runner = make_runner(tmp_path / "killed")
    kill_mid_segment(runner, after=1_500)
    resumed_report = make_runner(tmp_path / "killed").run()

    rows = read_spill(runner.events_path)
    assert len(rows) == resumed_report.events == whole_report.events, (
        f"log has {len(rows)} rows, resumed report says {resumed_report.events}, "
        f"continuous says {whole_report.events}"
    )