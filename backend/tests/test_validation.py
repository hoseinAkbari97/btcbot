from datetime import timedelta

from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.market_data.validation import CandleValidator


def test_valid_candles_pass() -> None:
    candles = [make_candle(minute) for minute in (0, 5, 10, 15, 20)]
    result = CandleValidator().validate(candles, Timeframe.M5)

    assert result.passed is True
    assert result.valid_candles == candles
    assert result.issues == []


def test_duplicate_and_missing_candles_are_reported() -> None:
    first = make_candle(0)
    result = CandleValidator().validate(
        [first, first, make_candle(10), make_candle(15)], Timeframe.M5
    )

    assert result.passed is False
    assert result.duplicate_count == 1
    assert result.missing_count == 1
    assert {issue.code for issue in result.issues} >= {
        "duplicate_timestamp",
        "missing_candles",
    }


def test_invalid_ohlcv_is_rejected() -> None:
    candle = make_candle(0, high="49900", low="50100", volume="-1")
    result = CandleValidator().validate([candle], Timeframe.M5)

    assert result.invalid_count == 1
    assert result.valid_candles == []
    assert {issue.code for issue in result.issues} >= {
        "invalid_high",
        "invalid_low",
        "invalid_range",
        "negative_volume",
    }


def test_wrong_order_and_misaligned_timestamp_are_reported() -> None:
    first = make_candle(5)
    misaligned = make_candle(0).model_copy(
        update={"open_time": make_candle(0).open_time + timedelta(seconds=1)}
    )
    result = CandleValidator().validate([first, misaligned], Timeframe.M5)

    assert result.invalid_count == 1
    assert {issue.code for issue in result.issues} >= {"wrong_order", "misaligned_timestamp"}


def test_extreme_return_is_warning_not_invalid_data() -> None:
    candles = [make_candle(minute, close=str(50000 + minute)) for minute in (0, 5, 10, 15, 20)]
    candles.append(make_candle(25, open_price="80000", high="81000", low="79000", close="80000"))
    result = CandleValidator(anomaly_threshold=3).validate(candles, Timeframe.M5)

    assert result.anomaly_count == 1
    assert result.invalid_count == 0
    assert any(issue.code == "extreme_return" for issue in result.issues)
