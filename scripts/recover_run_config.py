"""Recover a run's invocation by matching its checkpoint config fingerprint.

The checkpoint stores only a hash of the analysis parameters. Recomputing that
hash over candidate argument combinations identifies which invocation produced
it, without reading anything outside the repository.

Usage: python scripts/recover_run_config.py <dataset>
"""

from __future__ import annotations

import itertools
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.resources import ResourceLimits  # noqa: E402
from app.services.research.segmented_runner import SegmentedResearchRunner  # noqa: E402
from app.services.research.setup1 import Setup1Config  # noqa: E402

TARGETS = {
    "71ab2005064f30f7": "run-setup1-dev-20261027-approved (in progress)",
    "71714c24d462ed4c": "run-setup1-dev-20261025 (complete)",
}


def dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def main() -> None:
    dataset = Path(sys.argv[1])
    dates = [
        None,
        "2021-01-01",
        "2024-07-01",
        "2025-07-01",
        "2026-09-01",
        "2026-08-31",
        "2022-01-01",
    ]
    segments = [1, 3, 5, 6, 7, 10, 14, 15, 21, 30, 31, 60, 90, 120, 180, 365]
    lookbacks = [None, 10, 20, 50, 100, 200]
    out_dir = Path(__file__).resolve().parent.parent / "backend" / "data" / "research"

    found: dict[str, str] = {}
    for start, end, seg, lookback in itertools.product(dates, dates, segments, lookbacks):
        runner = SegmentedResearchRunner(
            dataset=dataset,
            out_dir=out_dir,
            limits=ResourceLimits(segment_days=seg),
            start=dt(start),
            end=dt(end),
            lookback=lookback,
            setup1=Setup1Config.proposed(split="development"),
        )
        digest = runner.config_fingerprint()
        if digest in TARGETS and digest not in found:
            found[digest] = (
                f"start={start} end={end} segment_days={seg} lookback={lookback}"
            )
        if len(found) == len(TARGETS):
            break

    for digest, label in TARGETS.items():
        print(f"{label}: {found.get(digest, 'NO MATCH among candidates')}")


if __name__ == "__main__":
    main()
