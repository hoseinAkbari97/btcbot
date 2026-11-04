"""Stage 2I N4 completeness tests for explicit is_closed handling."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from backend.app.schemas.market_data import CandleData
from pydantic import ValidationError
from stage2i_readiness.loader import Candle, SchemaError, candle_from_record, strict_is_closed


def record(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "open_time": "2021-01-01 00:00:00+00:00",
        "close_time": "2021-01-01 00:14:59.999000+00:00",
        "open": "28923.63000000",
        "high": "29017.50000000",
        "low": "28690.17000000",
        "close": "28752.80000000",
        "volume": "840.07756900",
        "quote_volume": "24239724.49526467",
        "trade_count": "19318",
        "is_closed": "True",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, True), (False, False), ("True", True), ("False", False)],
)
def test_explicit_is_closed_is_honoured(value: object, expected: bool) -> None:
    assert strict_is_closed({"is_closed": value}) is expected


@pytest.mark.parametrize("value", [None, "yes", "malformed", 1, 0, 1.0])
def test_missing_or_malformed_is_closed_is_rejected(value: object) -> None:
    with pytest.raises(SchemaError):
        strict_is_closed({"is_closed": value})


def test_absent_is_closed_is_rejected() -> None:
    with pytest.raises(SchemaError):
        strict_is_closed({})


def test_production_default_would_hide_missing_completeness() -> None:
    """Documents N4: CandleData alone defaults missing/null to closed."""
    base = record()
    missing = {key: value for key, value in base.items() if key != "is_closed"}
    assert CandleData(**missing).is_closed is True  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        CandleData(**{**base, "is_closed": None})  # type: ignore[arg-type]
    strict_missing = {key: value for key, value in base.items() if key != "is_closed"}
    with pytest.raises(SchemaError):
        candle_from_record(strict_missing, "15m")
    with pytest.raises(SchemaError):
        candle_from_record({**base, "is_closed": None}, "15m")


def test_final_incomplete_candle_is_not_silently_closed() -> None:
    incomplete = record(
        open_time="2024-06-30 23:45:00+00:00",
        close_time="2024-06-30 23:59:59.999000+00:00",
        is_closed="False",
    )
    candle: Candle = candle_from_record(incomplete, "15m")
    assert candle.is_closed is False
    assert candle.open_time == datetime(2024, 6, 30, 23, 45, tzinfo=UTC)
    assert candle.open == Decimal("28923.63000000")
