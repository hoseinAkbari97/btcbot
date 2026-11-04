"""Stage 2I entry-classification guard (K2).

The interval guard is evaluated before the entry-presence check. The primary
label is therefore ``entry_outside_interval`` whenever the expected entry
open is outside the frozen half-open development interval, even if the bar is
also missing. Inside the interval, a missing or off-grid entry bar is
``no_entry_bar``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

DEV_START_MS = 1_609_459_200_000
DEV_END_MS = 1_719_792_000_000


@dataclass(frozen=True)
class EntryClassification:
    accepted: bool
    primary: str
    secondary: tuple[str, ...] = field(default_factory=tuple)


def classify_entry(
    *,
    expected_entry_open_ms: int,
    entry_bar_present: bool,
    actual_entry_open_ms: int | None = None,
    entry_open: Decimal | None = None,
    atr: Decimal | None = None,
    dev_start_ms: int = DEV_START_MS,
    dev_end_ms: int = DEV_END_MS,
) -> EntryClassification:
    """Classify an entry using the frozen label precedence.

    Step 1: interval guard on the expected entry open.
    Step 2: entry-bar presence and grid check.
    Step 3: positive open and valid stop.
    """
    secondary: list[str] = []

    # Step 1: interval guard first (K2).
    if expected_entry_open_ms < dev_start_ms or expected_entry_open_ms >= dev_end_ms:
        if not entry_bar_present:
            secondary.append("no_entry_bar")
        return EntryClassification(False, "entry_outside_interval", tuple(secondary))

    # Step 2: presence and exact next-bar grid.
    if not entry_bar_present:
        return EntryClassification(False, "no_entry_bar")
    if actual_entry_open_ms is None or actual_entry_open_ms != expected_entry_open_ms:
        return EntryClassification(False, "no_entry_bar")

    # Step 3: price and stop validity.
    if entry_open is None or entry_open <= 0:
        return EntryClassification(False, "invalid_entry_price")
    if atr is None or atr <= 0:
        return EntryClassification(False, "invalid_stop")
    stop = entry_open - atr
    if stop <= 0 or (entry_open - stop) <= 0:
        return EntryClassification(False, "invalid_stop")

    return EntryClassification(True, "accepted")
