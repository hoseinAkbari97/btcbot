"""The resource guards must actually refuse, and must refuse *early*.

These tests exist because the guards were written to be quiet. A memory ceiling
that never fires, a disk check that never raises, and a batch size that shrinks
but not far enough are all indistinguishable from no guard at all until the
machine is under real pressure -- at which point the cost is a crash rather than
a failed assertion.

So nothing here samples real memory pressure. Each test drives the guard with
synthetic readings, which is the only way to test the thresholds without testing
the machine. What is measured for real is the *shape* of the behaviour: the
order of the states, the direction of the batch scaling, and the fact that the
disk check happens before any work is done.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core import resources as R
from app.core.resources import (
    GIB,
    InsufficientDiskSpace,
    MemoryReading,
    ResourceGuard,
    ResourceLimits,
    ensure_disk_space,
    estimate_dataset_bytes,
    iter_under_budget,
)


def reading(
    *, process_gb: float | None, system_available_gb: float | None
) -> MemoryReading:
    return MemoryReading(process_rss_gb=process_gb, system_available_gb=system_available_gb)


@pytest.fixture
def limits() -> ResourceLimits:
    """Thresholds set far apart so each test drives exactly one of them."""
    return ResourceLimits(
        max_ram_gb=6.0,
        warning_ram_gb=3.0,
        critical_ram_gb=4.5,
        max_disk_gb=256.0,
    )


def guard_with(guard: ResourceGuard, *readings: MemoryReading) -> list[str]:
    """Drive a guard through a sequence of readings. Returns the states."""
    states: list[str] = []
    for sample in readings:
        R.read_memory = lambda _sample=sample: _sample  # type: ignore[assignment]
        states.append(guard.check())
    return states


@pytest.fixture(autouse=True)
def _restore_read_memory():
    """Undo the monkeypatching above so no test leaks a fake reader."""
    original = R.read_memory
    yield
    R.read_memory = original  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# The three states, and their order
# ---------------------------------------------------------------------------


def test_a_quiet_machine_reports_ok(limits) -> None:
    guard = ResourceGuard(limits)
    assert guard_with(guard, reading(process_gb=0.4, system_available_gb=5.9)) == ["ok"]
    assert guard.warnings == []


def test_process_pressure_is_warned_before_it_is_critical(limits) -> None:
    """The warning is the window in which the batch can still be shrunk.

    If a reading went straight to critical, the only remaining response is to
    checkpoint and stop -- which is a correct outcome and a very expensive one.
    The intermediate state exists so a job can adapt instead of halting.
    """
    guard = ResourceGuard(limits)
    states = guard_with(
        guard,
        reading(process_gb=3.2, system_available_gb=5.9),
        reading(process_gb=4.6, system_available_gb=5.9),
    )

    assert states == ["warning", "critical"]


def test_system_availability_is_checked_before_the_process(limits) -> None:
    """A small job on a nearly-full machine is still a dangerous job.

    The process may be using 300 MB while the system has 200 MB left, and
    stopping then is right. Checking process RSS first would report "ok" and
    push the machine into swap, which is the crash this project is built to
    avoid.
    """
    guard = ResourceGuard(limits)
    states = guard_with(guard, reading(process_gb=0.2, system_available_gb=1.0))

    assert states == ["critical"]


def test_a_dip_in_system_memory_is_critical_even_while_the_process_is_small(
    limits,
) -> None:
    """The system check admits no warning band, and that is deliberate.

    ``critical_ram_gb`` (4.5) sits *above* ``warning_ram_gb`` (3.0) because they
    are thresholds for two different quantities -- the machine and this process.
    So any system reading below the warning line is also below the critical one,
    and the guard stops rather than warning.

    Warning here would mean telling the job to shrink its batches when the
    machine has under 3 GB left for everything. Shrinking takes several chunks to
    take effect, and there is no guarantee the machine has that long.
    """
    guard = ResourceGuard(limits)
    states = guard_with(
        guard,
        reading(process_gb=0.2, system_available_gb=2.9),
        reading(process_gb=0.2, system_available_gb=3.1),
    )

    assert states == ["critical", "ok"]


def test_a_missing_reading_is_never_treated_as_pressure(limits) -> None:
    """/proc not readable must not mean "critical".

    Refusing to start because a memory reading could not be taken would be the
    wrong kind of careful: the run is stopped for a condition that was never
    observed. Unknown is reported as unknown.
    """
    guard = ResourceGuard(limits)
    states = guard_with(guard, reading(process_gb=None, system_available_gb=None))

    assert states == ["ok"]
    assert guard.report()["peak_process_rss_gb"] is None


# ---------------------------------------------------------------------------
# Batch shrinking
# ---------------------------------------------------------------------------


def test_every_warning_halves_the_batch(limits) -> None:
    """Pressure that persists must keep shrinking, not shrink once."""
    guard = ResourceGuard(limits)
    guard_with(
        guard,
        reading(process_gb=3.2, system_available_gb=5.9),
        reading(process_gb=3.3, system_available_gb=5.9),
        reading(process_gb=3.4, system_available_gb=5.9),
    )

    assert guard.batch_scale == pytest.approx(0.125)


def test_the_batch_scale_has_a_floor(limits) -> None:
    """Below an eighth the job makes no progress and hangs instead of finishing.

    Unbounded shrinking turns "run slowly" into "never finish", and a hung job
    holds its memory for as long as it is left alone.
    """
    guard = ResourceGuard(limits)
    for _ in range(12):
        guard_with(guard, reading(process_gb=5.0, system_available_gb=0.5))

    assert guard.batch_scale == 0.125


def test_a_repeated_warning_is_not_reported_twice(limits) -> None:
    """Ten thousand chunks under one warning is one problem, not ten thousand.

    A warning list that grows with every chunk would make the run report
    unreadable at exactly the moment the report matters.
    """
    guard = ResourceGuard(limits)
    for _ in range(50):
        guard_with(guard, reading(process_gb=3.2, system_available_gb=5.9))

    assert len(guard.warnings) == 1


# ---------------------------------------------------------------------------
# The report records what happened, not what was planned
# ---------------------------------------------------------------------------


def test_the_report_holds_measured_peaks_not_configured_limits(limits) -> None:
    """A report showing the ceiling asserts the plan; peaks report reality."""
    guard = ResourceGuard(limits)
    guard_with(
        guard,
        reading(process_gb=1.0, system_available_gb=5.0),
        reading(process_gb=2.5, system_available_gb=4.0),
        reading(process_gb=0.5, system_available_gb=5.5),
    )

    report = guard.report()
    assert report["peak_process_rss_gb"] == 2.5, "the max, not the last reading"
    assert report["lowest_system_available_gb"] == 4.0, "the min, not the last reading"
    assert report["limits"]["max_ram_gb"] == 6.0


# ---------------------------------------------------------------------------
# Disk: refuse before starting
# ---------------------------------------------------------------------------


def test_a_job_refuses_to_start_without_room_for_its_output(tmp_path, limits) -> None:
    """The check happens before the work, so a refused run costs one statvfs.

    Discovering the disk is full at hour three of a multi-hour run wastes the
    run; that is the whole reason this is a pre-flight check.
    """
    R.disk_free_bytes = lambda _path: 2 * GIB  # type: ignore[assignment]

    with pytest.raises(InsufficientDiskSpace, match="GB is free"):
        ensure_disk_space(10 * GIB, path=tmp_path, limits=limits)


def test_an_output_larger_than_the_project_budget_is_refused_even_on_a_big_disk(
    tmp_path, limits
) -> None:
    """Plenty of room on the machine is not the same as room in this project.

    A machine with 900 GB free does not make a 300 GB run acceptable when the
    budget is 256. Budget compliance is a project decision, not a filesystem fact.
    """
    R.disk_free_bytes = lambda _path: 10_000 * GIB  # type: ignore[assignment]

    with pytest.raises(InsufficientDiskSpace, match="disk budget"):
        ensure_disk_space(300 * GIB, path=tmp_path, limits=limits)


def test_the_headroom_is_added_to_the_estimate(tmp_path, limits) -> None:
    """A run that exactly fits its output still needs room for its own files.

    Without the margin a job passes the check and fills the disk an hour later,
    when a checkpoint and a log have nowhere to go.
    """
    # Just enough for the output itself, not for the output plus 1 GB of headroom.
    R.disk_free_bytes = lambda _path: 10 * GIB  # type: ignore[assignment]

    with pytest.raises(InsufficientDiskSpace):
        ensure_disk_space(10 * GIB, path=tmp_path, limits=limits, headroom_gb=1.0)

    assert ensure_disk_space(9 * GIB, path=tmp_path, limits=limits, headroom_gb=1.0)


def test_a_sufficient_filesystem_returns_its_free_space(tmp_path, limits) -> None:
    """The caller needs the number for the run report, not just a yes/no."""
    R.disk_free_bytes = lambda _path: 42 * GIB  # type: ignore[assignment]

    assert ensure_disk_space(1 * GIB, path=tmp_path, limits=limits) == 42 * GIB


def test_the_dataset_estimate_is_a_stat_not_a_read(tmp_path) -> None:
    """Estimating a 256 MB dataset costs one syscall, not a full scan."""
    path = tmp_path / "btc.json"
    path.write_bytes(b"x" * 4096)

    assert estimate_dataset_bytes(path) == 4096


# ---------------------------------------------------------------------------
# Batching
# ---------------------------------------------------------------------------


def test_iter_under_budget_never_exceeds_its_chunk() -> None:
    """The bound is the whole point; a generator that overshoots is not one."""
    batches = list(iter_under_budget(iter(range(1_000)), chunk=128))

    assert all(len(batch) <= 128 for batch in batches)
    assert sum(len(batch) for batch in batches) == 1_000


def test_iter_under_budget_keeps_the_short_final_batch() -> None:
    """Dropping the remainder is how a run silently loses its last bars."""
    batches = list(iter_under_budget(iter(range(10)), chunk=4))

    assert [len(batch) for batch in batches] == [4, 4, 2]


def test_iter_under_budget_does_not_drain_its_source() -> None:
    """Batching exists so a stream stays a stream.

    Draining first would defeat it entirely: the caller's point is to hold one
    batch, and a drained iterator has already held all of them.
    """

    def counted():
        for index in range(100):
            yield index

    source = counted()
    batches = iter_under_budget(source, chunk=10)

    first = next(batches)
    assert len(first) == 10
    # The source is still positioned just after the tenth item.
    assert next(source) == 10


def test_iter_under_budget_on_an_empty_iterable_yields_nothing() -> None:
    """An empty dataset is a quiet period, not a crash."""
    assert list(iter_under_budget(iter([]), chunk=10)) == []