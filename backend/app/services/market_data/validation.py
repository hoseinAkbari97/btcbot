from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import log
from statistics import median
from typing import Any

from app.schemas.market_data import CandleData, Timeframe


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    timestamp: datetime | None = None
    severity: str = "error"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "severity": self.severity,
        }


@dataclass
class ValidationResult:
    valid_candles: list[CandleData] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    duplicate_count: int = 0
    missing_count: int = 0
    invalid_count: int = 0
    anomaly_count: int = 0

    @property
    def passed(self) -> bool:
        return self.invalid_count == 0 and self.duplicate_count == 0 and self.missing_count == 0


class CandleValidator:
    def __init__(self, anomaly_threshold: float = 12.0) -> None:
        self.anomaly_threshold = anomaly_threshold

    def validate(self, candles: list[CandleData], timeframe: Timeframe) -> ValidationResult:
        result = ValidationResult()
        if not candles:
            result.issues.append(ValidationIssue("empty_dataset", "dataset contains no candles"))
            result.invalid_count = 1
            return result

        original_times = [c.open_time for c in candles]
        if original_times != sorted(original_times):
            result.issues.append(ValidationIssue("wrong_order", "timestamps were not increasing"))

        unique: dict[datetime, CandleData] = {}
        for candle in candles:
            if candle.open_time in unique:
                result.duplicate_count += 1
                result.issues.append(
                    ValidationIssue(
                        "duplicate_timestamp", "duplicate candle timestamp", candle.open_time
                    )
                )
                continue
            unique[candle.open_time] = candle

        sorted_candles = sorted(unique.values(), key=lambda item: item.open_time)
        for candle in sorted_candles:
            errors = self._candle_errors(candle, timeframe)
            if errors:
                result.invalid_count += 1
                result.issues.extend(errors)
            else:
                result.valid_candles.append(candle)

        interval = timedelta(seconds=timeframe.seconds)
        for previous, current in zip(result.valid_candles, result.valid_candles[1:], strict=False):
            delta = current.open_time - previous.open_time
            if delta > interval:
                missing = int(delta.total_seconds() // timeframe.seconds) - 1
                result.missing_count += missing
                result.issues.append(
                    ValidationIssue(
                        "missing_candles",
                        f"{missing} candle(s) missing after {previous.open_time.isoformat()}",
                        current.open_time,
                    )
                )
            elif delta < interval:
                result.invalid_count += 1
                result.issues.append(
                    ValidationIssue(
                        "overlapping_candles", "candle timestamps overlap", current.open_time
                    )
                )

        self._detect_anomalies(result)
        return result

    @staticmethod
    def _candle_errors(candle: CandleData, timeframe: Timeframe) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        timestamp = candle.open_time
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            issues.append(
                ValidationIssue("timezone_missing", "open_time is not timezone-aware", timestamp)
            )
        elif timestamp.astimezone(UTC).utcoffset() != timedelta(0):
            issues.append(
                ValidationIssue("timezone_not_utc", "open_time is not normalized to UTC", timestamp)
            )
        if candle.close_time.tzinfo is None or candle.close_time.utcoffset() is None:
            issues.append(
                ValidationIssue("timezone_missing", "close_time is not timezone-aware", timestamp)
            )
        if candle.high < max(candle.open, candle.close):
            issues.append(ValidationIssue("invalid_high", "high is below open or close", timestamp))
        if candle.low > min(candle.open, candle.close):
            issues.append(ValidationIssue("invalid_low", "low is above open or close", timestamp))
        if candle.high < candle.low:
            issues.append(ValidationIssue("invalid_range", "high is below low", timestamp))
        if candle.volume < Decimal(0):
            issues.append(ValidationIssue("negative_volume", "volume is negative", timestamp))
        if min(candle.open, candle.high, candle.low, candle.close) <= Decimal(0):
            issues.append(
                ValidationIssue("non_positive_price", "price must be positive", timestamp)
            )
        if candle.close_time <= candle.open_time:
            issues.append(
                ValidationIssue(
                    "invalid_close_time", "close_time is not after open_time", timestamp
                )
            )
        if int(timestamp.timestamp()) % timeframe.seconds != 0:
            issues.append(
                ValidationIssue(
                    "misaligned_timestamp", "open_time is off timeframe boundary", timestamp
                )
            )
        return issues

    def _detect_anomalies(self, result: ValidationResult) -> None:
        if len(result.valid_candles) < 5:
            return
        returns = [
            log(float(current.close / previous.close))
            for previous, current in zip(
                result.valid_candles, result.valid_candles[1:], strict=False
            )
        ]
        center = median(returns)
        mad = median(abs(value - center) for value in returns)
        if mad == 0:
            return
        for candle, value in zip(result.valid_candles[1:], returns, strict=False):
            robust_z = 0.6745 * abs(value - center) / mad
            if robust_z > self.anomaly_threshold:
                result.anomaly_count += 1
                result.issues.append(
                    ValidationIssue(
                        "extreme_return",
                        f"suspicious close-to-close move (robust z={robust_z:.2f})",
                        candle.open_time,
                        severity="warning",
                    )
                )
