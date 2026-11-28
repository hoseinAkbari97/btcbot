"""Canonical, streaming identity for the exact candles a run consumed.

The fingerprint covers every candle field passed to the engine, plus the source
row identity and the requested symbol/timeframe. Rows are hashed one at a time
in the order supplied; the caller is responsible for deterministic ordering.
No candle series is retained by the builder.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.schemas.market_data import CandleData, Timeframe

from .canonical import canonical_bytes

DATASET_FINGERPRINT_VERSION = "3h.1"


@dataclass(frozen=True)
class DatasetIdentity:
    """Facts about one ordered candle selection."""

    fingerprint: str
    version: str
    candle_count: int
    first_open_time: datetime | None
    last_open_time: datetime | None
    duplicate_open_times: int
    source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "fingerprint_version": self.version,
            "candle_count": self.candle_count,
            "first_open_time": self.first_open_time.isoformat() if self.first_open_time else None,
            "last_open_time": self.last_open_time.isoformat() if self.last_open_time else None,
            "duplicate_open_times": self.duplicate_open_times,
            "source_ids": list(self.source_ids),
        }


@dataclass
class DatasetFingerprintBuilder:
    """Hash a deterministic candle stream without retaining the stream."""

    symbol: str
    timeframe: str
    _digest: Any = field(default_factory=hashlib.sha256, init=False, repr=False)
    _count: int = field(default=0, init=False)
    _first_open_time: datetime | None = field(default=None, init=False)
    _last_open_time: datetime | None = field(default=None, init=False)
    _previous_open_time: datetime | None = field(default=None, init=False)
    _duplicate_open_times: int = field(default=0, init=False)
    _source_ids: set[str] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        header = canonical_bytes(
            {
                "fingerprint_version": DATASET_FINGERPRINT_VERSION,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
            }
        )
        self._update(header)

    def _update(self, chunk: bytes) -> None:
        self._digest.update(len(chunk).to_bytes(8, "big"))
        self._digest.update(chunk)

    def add(self, candle: CandleData, source_id: str) -> None:
        """Add one candle in engine order."""
        if candle.symbol != self.symbol or candle.timeframe.value != self.timeframe:
            raise ValueError("candle does not match the dataset builder's symbol/timeframe")
        row = {
            "source_id": source_id,
            "open_time": candle.open_time,
            "close_time": candle.close_time,
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
            "quote_volume": candle.quote_volume,
            "trade_count": candle.trade_count,
            "taker_buy_base_volume": candle.taker_buy_base_volume,
            "taker_buy_quote_volume": candle.taker_buy_quote_volume,
            "is_closed": candle.is_closed,
        }
        self._update(canonical_bytes(row))
        self._count += 1
        self._first_open_time = self._first_open_time or candle.open_time
        self._last_open_time = candle.open_time
        if self._previous_open_time == candle.open_time:
            self._duplicate_open_times += 1
        self._previous_open_time = candle.open_time
        self._source_ids.add(source_id)

    def build(self) -> DatasetIdentity:
        """Finish the stream with its bounded summary fields."""
        footer = canonical_bytes(
            {
                "candle_count": self._count,
                "first_open_time": self._first_open_time,
                "last_open_time": self._last_open_time,
                "duplicate_open_times": self._duplicate_open_times,
                "source_ids": sorted(self._source_ids),
            }
        )
        self._update(footer)
        return DatasetIdentity(
            fingerprint=self._digest.hexdigest(),
            version=DATASET_FINGERPRINT_VERSION,
            candle_count=self._count,
            first_open_time=self._first_open_time,
            last_open_time=self._last_open_time,
            duplicate_open_times=self._duplicate_open_times,
            source_ids=tuple(sorted(self._source_ids)),
        )


def dataset_identity(
    candles: Sequence[CandleData], source_ids: Sequence[str], *, symbol: str, timeframe: Timeframe
) -> DatasetIdentity:
    """Build an identity from an already bounded, ordered candle selection."""
    if len(candles) != len(source_ids):
        raise ValueError("candle and source_id counts must match")
    builder = DatasetFingerprintBuilder(symbol=symbol, timeframe=timeframe.value)
    for candle, source_id in zip(candles, source_ids, strict=True):
        builder.add(candle, source_id)
    return builder.build()


def dataset_rows_identity(
    rows: Iterable[tuple[CandleData, str]], *, symbol: str, timeframe: Timeframe
) -> DatasetIdentity:
    """Build an identity from an iterator without materializing it."""
    builder = DatasetFingerprintBuilder(symbol=symbol, timeframe=timeframe.value)
    for candle, source_id in rows:
        builder.add(candle, source_id)
    return builder.build()


__all__ = [
    "DATASET_FINGERPRINT_VERSION",
    "DatasetFingerprintBuilder",
    "DatasetIdentity",
    "dataset_identity",
    "dataset_rows_identity",
]
