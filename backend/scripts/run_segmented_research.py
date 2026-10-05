#!/usr/bin/env python
"""Run one research pass over a dataset in bounded, resumable segments.

The resource budget is the reason this exists as a separate command rather than
a flag on the event-research script. A full-history 5m pass cannot be held in
memory, so it has to be a job that can be stopped and continued, and the report
it prints is the measurement that decides whether the next one is worth
starting.

Two properties are worth knowing before trusting an exit code:

* Exit code 75 means *stopped cleanly at a checkpoint*, not failed. The run
  preserved its state and re-running this command continues from where it left
  off. It is deliberately distinct from 1 so a scheduler can tell a resource
  abort from a bug without scraping stderr.
* A completed run leaves a checkpoint behind, so re-running it is a no-op that
  reprints the same report. Resuming is safe to attempt; repeating a finished
  job is not an error.

Usage
-----
    python scripts/run_segmented_research.py \\
        --dataset data/datasets/BTCUSDT-5m-20210101-20260901.json \\
        --start 2021-01-01 --end 2022-01-01 \\
        --segment-days 30 --out data/research/run-2021

Defaults come from ``ResourceLimits`` rather than being repeated here, so the
budget has exactly one definition and changing it changes every caller.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.resources import ResourceLimits  # noqa: E402
from app.services.research.segmented_runner import (  # noqa: E402
    EXIT_RESUMABLE,
    SegmentedResearchRunner,
    render_report,
)


def parse_date(value: str) -> datetime:
    """Parse ``YYYY-MM-DD`` as midnight UTC.

    UTC always, not local time: a segment boundary at local midnight would fall
    at a different bar depending on daylight saving, and the whole design rests
    on boundaries being at fixed bar indices.
    """
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def main(argv: list[str] | None = None) -> int:
    limits = ResourceLimits()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--start", type=parse_date, default=None)
    parser.add_argument("--end", type=parse_date, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--segment-days",
        type=int,
        default=limits.segment_days,
        help="bars per segment; smaller uses less memory, more segments",
    )
    parser.add_argument("--lookback", type=int, default=None)
    parser.add_argument(
        "--segment-days-max",
        type=int,
        default=None,
        help="rejected above this; a guard against a typo that would silently "
        "process the whole dataset in one segment and defeat the point",
    )
    args = parser.parse_args(argv)

    if args.segment_days_max is not None and args.segment_days > args.segment_days_max:
        parser.error(
            f"--segment-days {args.segment_days} exceeds the stated maximum "
            f"{args.segment_days_max}"
        )

    limits = ResourceLimits(segment_days=args.segment_days)
    runner = SegmentedResearchRunner(
        dataset=args.dataset,
        symbol=args.symbol,
        limits=limits,
        start=args.start,
        end=args.end,
        lookback=args.lookback,
        out_dir=args.out,
    )
    report = runner.run()
    print(render_report(report, limits))

    if report.stopped_on_memory:
        # Not a failure. The state is saved and the next invocation continues.
        return EXIT_RESUMABLE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
