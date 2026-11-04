"""Stage 2I K2 entry-guard precedence tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from stage2i_readiness.entry_guard import DEV_END_MS, DEV_START_MS, classify_entry

BAR = 900_000
ATR = Decimal("100")


def classify(open_ms: int, *, present: bool = True, actual_ms: int | None = None):
    return classify_entry(
        expected_entry_open_ms=open_ms,
        entry_bar_present=present,
        actual_entry_open_ms=open_ms if actual_ms is None else actual_ms,
        entry_open=Decimal("30000"),
        atr=ATR,
    )


def test_entry_exactly_at_interval_start_is_inside() -> None:
    result = classify(DEV_START_MS)
    assert (result.accepted, result.primary) == (True, "accepted")


def test_entry_immediately_before_interval_start_is_outside() -> None:
    result = classify(DEV_START_MS - 1)
    assert (result.accepted, result.primary) == (False, "entry_outside_interval")


def test_entry_immediately_before_interval_end_is_inside() -> None:
    result = classify(DEV_END_MS - 1)
    assert (result.accepted, result.primary) == (True, "accepted")


def test_entry_exactly_at_exclusive_interval_end_is_outside() -> None:
    result = classify(DEV_END_MS)
    assert (result.accepted, result.primary) == (False, "entry_outside_interval")


def test_missing_entry_bar_inside_interval_is_no_entry_bar() -> None:
    result = classify(DEV_START_MS + BAR, present=False)
    assert (result.accepted, result.primary) == (False, "no_entry_bar")


def test_missing_entry_bar_outside_interval_is_entry_outside_interval() -> None:
    result = classify(DEV_END_MS, present=False)
    assert (result.accepted, result.primary) == (False, "entry_outside_interval")
    assert "no_entry_bar" in result.secondary


def test_off_grid_entry_bar_is_no_entry_bar() -> None:
    result = classify(DEV_START_MS + BAR, actual_ms=DEV_START_MS + BAR + 1)
    assert (result.accepted, result.primary) == (False, "no_entry_bar")


@pytest.mark.parametrize(
    ("open_price", "atr", "label"),
    [
        (Decimal("0"), ATR, "invalid_entry_price"),
        (Decimal("30000"), Decimal("0"), "invalid_stop"),
        (Decimal("30000"), Decimal("-1"), "invalid_stop"),
        (Decimal("30000"), Decimal("30000"), "invalid_stop"),
    ],
)
def test_price_and_stop_follow_presence(open_price: Decimal, atr: Decimal, label: str) -> None:
    result = classify_entry(
        expected_entry_open_ms=DEV_START_MS + BAR,
        entry_bar_present=True,
        actual_entry_open_ms=DEV_START_MS + BAR,
        entry_open=open_price,
        atr=atr,
    )
    assert (result.accepted, result.primary) == (False, label)
