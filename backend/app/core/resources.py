"""The budget every heavy research job runs inside.

Why this module exists
----------------------
The research workload has crashed this machine more than once. The failure was
never a bug — it was a design that assumed it could allocate what it wanted and
rely on the machine having room. So the limit is written down here, once, and
every long-running path reads it rather than choosing its own.

The numbers are *not* the machine's numbers
------------------------------------------
:class:`ResourceLimits.max_ram_gb` is deliberately below the 6 GB the machine
offers. The gap is not slack to be spent later; it is what Windows, WSL, VS Code,
PostgreSQL and the Python interpreter are already holding. A workload sized to
"fit in 6 GB" is a workload that starts swapping the moment anything else needs
memory, and swapping on WSL2 is a freeze.

Why ``/proc`` and not ``psutil``
--------------------------------
``psutil`` is not installed and would be a new dependency for a single call.
``/proc/self/statm`` and ``/proc/meminfo`` are always present on Linux, cost one
small file read, and have no import cost. :func:`_rss_from_resource` is the
fallback for a platform without ``/proc``.

One worker, always
------------------
:attr:`ResourceLimits.workers` exists so the constraint is *visible and
configurable*, not because multi-process is supported. Nothing in this codebase
may raise it: a second worker multiplies peak memory by the number of workers, and
the memory budget is the thing that has to survive. ``max_workers`` is therefore
validated to be exactly 1 and raises otherwise.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Bytes per GiB, as the operating system counts them.
GIB = 1024**3


class ResourceLimits(BaseSettings):
    """Hard bounds for any research job, overridable by environment variable.

    Every field is settable from the environment (``RESEARCH_MAX_RAM_GB`` and so
    on) so a smaller budget can be imposed for a run *without editing code* —
    which is the property that makes this a control rather than a comment.
    """

    model_config = SettingsConfigDict(
        env_prefix="RESEARCH_", env_file=".env", extra="ignore", case_sensitive=False
    )

    #: Ceiling for the research process's own resident memory. Below the 6 GB
    #: the machine offers, by design — see the module docstring.
    max_ram_gb: float = Field(default=4.0, gt=0)
    #: Emit a warning and shrink the current batch. Set well under ``max_ram_gb``
    #: so there is room to react before the ceiling is actually reached.
    warning_ram_gb: float = Field(default=3.0, gt=0)
    #: Write a checkpoint and stop cleanly. Still under ``max_ram_gb`` so the
    #: checkpoint itself has memory to run in.
    critical_ram_gb: float = Field(default=3.5, gt=0)
    #: Ceiling for everything this project writes to disk.
    max_disk_gb: float = Field(default=256.0, gt=0)

    #: Fixed at 1. Present so the constraint is visible and so a caller that
    #: reaches for it gets an error rather than a second process.
    workers: int = 1

    #: Bars held in memory at once. The unit of both the memory bound and the
    #: streaming reader's buffer.
    chunk_rows: int = Field(default=50_000, ge=100)
    #: Calendar span of one segment. A *memory* boundary, never a reset: state
    #: carries across it.
    segment_days: int = Field(default=365, ge=1)
    #: Cells in one bootstrap replicate batch. Peak bootstrap memory is bounded
    #: by this regardless of how many events were detected.
    bootstrap_batch_cells: int = Field(default=1_000_000, ge=1000)

    @field_validator("workers")
    @classmethod
    def single_worker_only(cls, value: int) -> int:
        """Refuse a worker count above 1 rather than honouring it.

        Every parallel path multiplies peak memory, and peak memory is the
        constraint that has already broken this machine. Accepting the value and
        ignoring it would be worse than refusing it.
        """
        if value != 1:
            raise ValueError(
                "workers is fixed at 1: multiple workers multiply peak memory, and "
                "the memory budget is the constraint that must hold. Run segments "
                "sequentially instead."
            )
        return value

    @field_validator("critical_ram_gb")
    @classmethod
    def critical_under_ceiling(cls, value: float, info) -> float:  # noqa: ANN001
        """The abort threshold must sit below the ceiling.

        Otherwise the process would hit the ceiling before the code noticed, and
        the checkpoint written on the way out would be competing with whatever
        allocation triggered it.
        """
        ceiling = info.data.get("max_ram_gb")
        if ceiling is not None and value >= ceiling:
            raise ValueError(
                f"critical_ram_gb ({value}) must be below max_ram_gb ({ceiling}), or the "
                "job would reach the ceiling before it could checkpoint and stop."
            )
        return value

    @field_validator("warning_ram_gb")
    @classmethod
    def warning_under_critical(cls, value: float, info) -> float:  # float:  # noqa: ANN001
        """Warning must precede the abort, or the reaction window is zero."""
        critical = info.data.get("critical_ram_gb")
        if critical is not None and value > critical:
            raise ValueError(
                f"warning_ram_gb ({value}) must not exceed critical_ram_gb ({critical})."
            )
        return value

    def as_dict(self) -> dict[str, object]:
        """The configuration as it should appear in a run's provenance block."""
        return {
            "max_ram_gb": self.max_ram_gb,
            "warning_ram_gb": self.warning_ram_gb,
            "critical_ram_gb": self.critical_ram_gb,
            "max_disk_gb": self.max_disk_gb,
            "workers": self.workers,
            "chunk_rows": self.chunk_rows,
            "segment_days": self.segment_days,
            "bootstrap_batch_cells": self.bootstrap_batch_cells,
        }


def _read_int(path: str, index: int) -> int | None:
    """One integer out of a whitespace-separated ``/proc`` line."""
    try:
        with open(path, encoding="ascii") as handle:
            parts = handle.read().split()
        return int(parts[index])
    except (OSError, IndexError, ValueError):
        return None


def process_rss_bytes() -> int | None:
    """This process's resident set size, or ``None`` if it cannot be read.

    ``statm``'s second field is resident *pages*, and the page size is not
    available in that file, so it is taken from :func:`os.sysconf` rather than
    hard-coded to 4096 — a wrong page size would make the reading wrong by the
    same factor, which is exactly the kind of error a safety limit must not have.
    """
    pages = _read_int("/proc/self/statm", 1)
    if pages is None:
        return None
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError):
        page_size = 4096
    return pages * page_size


def system_available_bytes() -> int | None:
    """Memory available system-wide, from ``MemAvailable``.

    Deliberately ``MemAvailable`` and not ``MemFree``: ``MemFree`` excludes the
    reclaimable page cache, so on a machine with 6 GB free it can report a few
    hundred MB, and a limit keyed to it would abort on a healthy system.
    """
    try:
        with open("/proc/meminfo", encoding="ascii") as handle:
            for line in handle:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except (OSError, IndexError, ValueError):
        return None
    return None


@dataclass(frozen=True)
class MemoryReading:
    """One measurement of how much room is left."""

    process_rss_gb: float | None
    system_available_gb: float | None

    def as_dict(self) -> dict[str, float | None]:
        return {
            "process_rss_gb": self.process_rss_gb,
            "system_available_gb": self.system_available_gb,
        }


def read_memory() -> MemoryReading:
    """Sample process and system memory in one call.

    Both readings, always. Which one triggers the stop depends on the machine:
    on a dedicated host the process number is the meaningful one, and on a busy
    desktop the system number is — a process at 500 MB is not safe if the system
    has 300 MB left.
    """
    rss = process_rss_bytes()
    available = system_available_bytes()
    return MemoryReading(
        process_rss_gb=None if rss is None else rss / GIB,
        system_available_gb=None if available is None else available / GIB,
    )


class ResourceGuard:
    """Watches memory during a job and decides whether to continue.

    Three states, and the order matters: ``ok`` -> ``warning`` -> ``critical``.
    A warning does not stop the job; it is the signal to shrink the next batch
    while there is still memory to do it in. Only ``critical`` stops, and it
    stops *by checkpointing first*, so an abort costs a segment boundary rather
    than the run.

    The system-availability check is the more important of the two and is
    applied first: a run on a machine that is nearly out of memory is in danger
    regardless of how small the run itself is.
    """

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self.limits = limits or ResourceLimits()
        self.peak_process_gb: float | None = None
        self.peak_system_available_gb: float | None = None
        self.warnings: list[str] = []
        #: How much to shrink the next batch, as a multiplier. Grows on each
        #: warning so a job that stays under pressure keeps shrinking rather
        #: than sitting at a size that was not enough once.
        self.batch_scale = 1.0

    def check(self) -> str:
        """Sample memory and return ``"ok"``, ``"warning"`` or ``"critical"``.

        Never raises. The decision to stop belongs to the caller, which has the
        checkpoint it needs to write; a guard that raised would take that
        decision away and abort before the state was saved.
        """
        reading = read_memory()

        if reading.process_rss_gb is not None:
            previous = self.peak_process_gb or 0.0
            self.peak_process_gb = max(previous, reading.process_rss_gb)
        if reading.system_available_gb is not None:
            previous = self.peak_system_available_gb
            self.peak_system_available_gb = (
                reading.system_available_gb
                if previous is None
                else min(previous, reading.system_available_gb)
            )

        limits = self.limits
        if (
            reading.system_available_gb is not None
            and reading.system_available_gb < limits.warning_ram_gb
        ):
            self._record_warning(
                f"system available memory {reading.system_available_gb:.2f} GB is below "
                f"the {limits.warning_ram_gb:.2f} GB warning threshold"
            )
            if reading.system_available_gb < limits.critical_ram_gb:
                return "critical"
            return "warning"

        if reading.process_rss_gb is not None:
            if reading.process_rss_gb >= limits.critical_ram_gb:
                self._record_warning(
                    f"process RSS {reading.process_rss_gb:.2f} GB reached the "
                    f"{limits.critical_ram_gb:.2f} GB critical threshold"
                )
                return "critical"
            if reading.process_rss_gb >= limits.warning_ram_gb:
                self._record_warning(
                    f"process RSS {reading.process_rss_gb:.2f} GB is above the "
                    f"{limits.warning_ram_gb:.2f} GB warning threshold"
                )
                return "warning"
        return "ok"

    def _record_warning(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)
        # Halve, but never below an eighth: below that the job is making no
        # progress and would effectively hang rather than finish slowly.
        self.batch_scale = max(0.125, self.batch_scale / 2)

    def report(self) -> dict[str, object]:
        """Measured peaks, for the run report.

        The *measured* numbers, not the configured ceilings. A report that shows
        the limits is asserting the plan; one that shows the peaks is reporting
        what happened, and only the second one tells anyone whether the plan
        was safe.
        """
        return {
            "limits": self.limits.as_dict(),
            "peak_process_rss_gb": (
                None if self.peak_process_gb is None else round(self.peak_process_gb, 3)
            ),
            "lowest_system_available_gb": (
                None
                if self.peak_system_available_gb is None
                else round(self.peak_system_available_gb, 3)
            ),
            "warnings": list(self.warnings),
        }


class InsufficientDiskSpace(RuntimeError):
    """Raised before a job starts, when there is not room for its output.

    Raised *before* the work rather than during it. Discovering the disk is full
    halfway through a multi-hour run wastes the run; checking the estimate up
    front costs one ``statvfs``.
    """


def disk_free_bytes(path: Path | str = ".") -> int:
    """Free bytes on the filesystem holding ``path``."""
    return shutil.disk_usage(path).free


def ensure_disk_space(
    required_bytes: int,
    *,
    path: Path | str = ".",
    limits: ResourceLimits | None = None,
    headroom_gb: float = 1.0,
) -> int:
    """Confirm the filesystem can hold ``required_bytes`` plus a margin.

    ``headroom_gb`` is not optimism about the estimate — it is the room a
    checkpoint, a log and the operating system's own writes need while the job
    runs. Without it a job can pass this check and still fill the disk.

    :returns: the free bytes available, for the run's report.
    :raises InsufficientDiskSpace: if the required space is not present.
    """
    limits = limits or ResourceLimits()
    free = disk_free_bytes(path)
    needed = required_bytes + int(headroom_gb * GIB)

    # Checked against the *project's* budget, not merely "is there space".
    # The machine having 900 GB free does not make 300 GB acceptable when this
    # project is capped at 256.
    ceiling = int(limits.max_disk_gb * GIB)
    if free < needed:
        raise InsufficientDiskSpace(
            f"need {needed / GIB:.2f} GB on {path} but only {free / GIB:.2f} GB is free"
        )
    if needed > ceiling:
        raise InsufficientDiskSpace(
            f"estimated output {needed / GIB:.2f} GB exceeds this project's "
            f"{limits.max_disk_gb:.0f} GB disk budget; reduce segment_days or chunk_rows"
        )
    return free


def estimate_dataset_bytes(path: Path) -> int:
    """Size of a dataset file on disk, without reading it.

    ``stat`` rather than a scan, so estimating a 256 MB dataset costs one
    syscall. The caller turns this into an output estimate; it is an input size,
    not a promise that the output will be the same.
    """
    return path.stat().st_size


def iter_under_budget(
    items: Iterator[object], *, chunk: int
) -> Iterator[list]:
    """Group an iterator into lists of at most ``chunk``, without draining it.

    Exists so every streaming path in the project accumulates in bounded batches
    the same way. A caller that forgot to bound its batch is the failure mode
    this removes.
    """
    batch: list = []
    for item in items:
        batch.append(item)
        if len(batch) >= chunk:
            yield batch
            batch = []
    if batch:
        yield batch