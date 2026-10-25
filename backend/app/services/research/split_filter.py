"""Chronological split filtering for Setup 1.

Splits are **half-open UTC intervals** ``[start, end)``:

- development: 2021-01-01T00:00:00Z through 2024-07-01T00:00:00Z (exclusive)
- validation:  2024-07-01T00:00:00Z through 2025-07-01T00:00:00Z (exclusive)
- out-of-sample: 2025-07-01T00:00:00Z through 2026-09-01T00:00:00Z (exclusive)

The filter enforces:

- Warm-up observations (before split start) are not scored, but may be used
  for indicator/level state.
- A confirmation is scored only if its full eligible outcome-evaluation window
  fits within the assigned split (entry + 12-bar horizon, counting the entry
  candle as the first evaluated candle => window extends entry_index + 11).
- Boundary-crossing outcomes are excluded, never truncated.
- Episodes do not straddle boundaries: only scored observations take part in
  the Setup 1 episode partition, and every scored window fits in one split.

Gap filtering is deliberately *not* handled here. It is a property of the bars
that a Setup 1 evaluation consumed, so it lives with that evaluator in
:mod:`app.services.research.setup1` and is reported separately from split
boundary exclusions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from app.services.research.events import ResearchEvent
from app.services.research.outcomes import ENTRY_OFFSET

SplitName = Literal["development", "validation", "oos"]


@dataclass(frozen=True)
class SplitBounds:
    """One half-open chronological split ``[start, end)``."""

    name: str
    start: datetime  # inclusive
    end: datetime    # exclusive


SPLITS: tuple[SplitBounds, ...] = (
    SplitBounds(
        "development",
        datetime(2021, 1, 1, tzinfo=UTC),
        datetime(2024, 7, 1, tzinfo=UTC),
    ),
    SplitBounds(
        "validation",
        datetime(2024, 7, 1, tzinfo=UTC),
        datetime(2025, 7, 1, tzinfo=UTC),
    ),
    SplitBounds(
        "oos",
        datetime(2025, 7, 1, tzinfo=UTC),
        datetime(2026, 9, 1, tzinfo=UTC),
    ),
)

#: Barrier horizon = 12 evaluated candles total, including the entry candle.
BARRIER_HORIZON_BARS = 12


def split_bounds(name: str) -> SplitBounds:
    """Return the frozen bounds for ``name``, or raise for an unknown split."""
    for split in SPLITS:
        if split.name == name:
            return split
    raise ValueError(f"unknown split {name!r}; expected one of {[s.name for s in SPLITS]}")


def assign_split_to_time(ts: datetime) -> str | None:
    """Assign a timestamp to a split, or ``None`` if outside all splits."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    else:
        ts = ts.astimezone(UTC)
    for split in SPLITS:
        if split.start <= ts < split.end:
            return split.name
    return None


def is_confirmation_in_warmup(
    confirmation_index: int,
    split_start_index: int,
) -> bool:
    """True if the confirmation predates the split's scoring start (warm-up)."""
    return confirmation_index < split_start_index


def window_fits_in_split(
    confirmation_index: int,
    split_end_index: int,
) -> bool:
    """Check if the full evaluation window fits within the split.

    Entry is at confirmation_index + ENTRY_OFFSET.
    Barrier horizon is BARRIER_HORIZON_BARS evaluated candles including entry,
    so last evaluated candle is entry_index + BARRIER_HORIZON_BARS - 1.

    ``split_end_index`` is the **last bar index inside the split**, inclusive.
    """
    entry_index = confirmation_index + ENTRY_OFFSET
    last_evaluated = entry_index + BARRIER_HORIZON_BARS - 1
    return last_evaluated <= split_end_index


def last_evaluated_index(confirmation_index: int) -> int:
    """Absolute index of the last candle the 12-candle horizon evaluates."""
    return confirmation_index + ENTRY_OFFSET + BARRIER_HORIZON_BARS - 1


def filter_events_for_split(
    events: list[ResearchEvent],
    candles: list,
    split: str,
    split_start_idx: int,
    split_end_idx: int,
) -> tuple[list[ResearchEvent], dict[str, int]]:
    """Filter events for a split. Returns (kept_events, exclusion_stats).

    This is the low-level event-level filter. The Setup 1 research path uses
    :class:`app.services.research.setup1.Setup1Evaluator`, which additionally
    applies the frozen signal definition, spot restriction, stop validity, gap
    rules and episode boundary.
    """
    stats = {
        "warmup_excluded": 0,
        "boundary_crossing_excluded": 0,
        "outside_split_excluded": 0,
        "kept": 0,
    }

    kept = []
    for event in events:
        # Check if confirmation is in a scored split
        conf_split = assign_split_to_time(event.confirmation_time)
        if conf_split != split:
            stats["outside_split_excluded"] += 1
            continue

        # Check warm-up
        if is_confirmation_in_warmup(event.confirmation_index, split_start_idx):
            stats["warmup_excluded"] += 1
            continue

        # Check if full window fits
        if not window_fits_in_split(event.confirmation_index, split_end_idx):
            stats["boundary_crossing_excluded"] += 1
            continue

        kept.append(event)
        stats["kept"] += 1

    return kept, stats
