"""Read-only verification of recorded provenance.

Verifiers compare current stored evidence with an immutable manifest or a stored
report. They never rerun a backtest, edit a run, or infer facts that were not
recorded. Every result carries an explicit status and a short reason; no raw
candle, trade or equity series leaves these helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe

from .dataset import DATASET_FINGERPRINT_VERSION, DatasetFingerprintBuilder

VerificationStatus = Literal["verified", "partial", "unavailable", "changed", "corrupted"]

#: Same hard ceiling the runner applies to one request. A verifier never scans
#: more than the recorded candle count plus one sentinel row.
MAX_VERIFY_CANDLES = 100_000
_VERIFY_BATCH_SIZE = 1000


@dataclass(frozen=True)
class DatasetVerification:
    """Comparison of an ordered candle selection with its manifest entry."""

    status: VerificationStatus
    expected_fingerprint: str | None
    observed_fingerprint: str | None
    expected_candle_count: int | None
    observed_candle_count: int | None
    fingerprint_version: str | None
    source_ids: tuple[str, ...]
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "expected_fingerprint": self.expected_fingerprint,
            "observed_fingerprint": self.observed_fingerprint,
            "expected_candle_count": self.expected_candle_count,
            "observed_candle_count": self.observed_candle_count,
            "fingerprint_version": self.fingerprint_version,
            "source_ids": list(self.source_ids),
            "detail": self.detail,
        }


def _unavailable(detail: str, *, version: str | None = None) -> DatasetVerification:
    return DatasetVerification(
        status="unavailable",
        expected_fingerprint=None,
        observed_fingerprint=None,
        expected_candle_count=None,
        observed_candle_count=None,
        fingerprint_version=version,
        source_ids=(),
        detail=detail,
    )


def _corrupted(detail: str) -> DatasetVerification:
    return DatasetVerification(
        status="corrupted",
        expected_fingerprint=None,
        observed_fingerprint=None,
        expected_candle_count=None,
        observed_candle_count=None,
        fingerprint_version=None,
        source_ids=(),
        detail=detail,
    )


def _changed(
    detail: str,
    *,
    expected_fingerprint: str | None,
    observed_fingerprint: str | None,
    expected_candle_count: int | None,
    observed_candle_count: int | None,
    version: str | None,
    source_ids: tuple[str, ...],
) -> DatasetVerification:
    return DatasetVerification(
        status="changed",
        expected_fingerprint=expected_fingerprint,
        observed_fingerprint=observed_fingerprint,
        expected_candle_count=expected_candle_count,
        observed_candle_count=observed_candle_count,
        fingerprint_version=version,
        source_ids=source_ids,
        detail=detail,
    )


async def verify_dataset(
    session: AsyncSession,
    *,
    dataset: dict[str, Any],
    market: dict[str, Any],
) -> DatasetVerification:
    """Fingerprint the recorded candle selection and compare it with the manifest.

    The scan is keyset-paginated and bounded by ``MAX_VERIFY_CANDLES``. It reads
    only the sources recorded in the manifest, so an unrecorded source can never
    be silently included.
    """
    version = dataset.get("fingerprint_version")
    expected_fingerprint = dataset.get("fingerprint")
    expected_count = dataset.get("candle_count")
    raw_sources = dataset.get("source_ids")

    if version != DATASET_FINGERPRINT_VERSION:
        return _unavailable(
            "manifest dataset fingerprint version is not verifiable", version=str(version)
        )
    if not isinstance(expected_fingerprint, str) or len(expected_fingerprint) != 64:
        return _corrupted("manifest dataset fingerprint is missing or malformed")
    if (
        not isinstance(expected_count, int)
        or isinstance(expected_count, bool)
        or expected_count < 0
    ):
        return _corrupted("manifest candle count is missing or invalid")
    if expected_count > MAX_VERIFY_CANDLES:
        return _unavailable("manifest candle count exceeds the verification bound")
    if not isinstance(raw_sources, list) or not raw_sources:
        return _unavailable("manifest records no data source for this selection")
    source_ids = tuple(
        item for item in raw_sources if isinstance(item, str) and bool(item)
    )
    if len(source_ids) != len(raw_sources):
        return _corrupted("manifest source identifiers are malformed")

    symbol, timeframe, start, end = market.get("symbol"), market.get("timeframe"), market.get(
        "period_start"
    ), market.get("period_end")
    if not isinstance(symbol, str) or not isinstance(timeframe, str):
        return _corrupted("manifest market identity is missing or malformed")
    try:
        parsed_timeframe = Timeframe(timeframe)
        parsed_start = datetime.fromisoformat(start) if isinstance(start, str) else None
        parsed_end = datetime.fromisoformat(end) if isinstance(end, str) else None
    except ValueError:
        return _corrupted("manifest market period or timeframe is invalid")

    builder = DatasetFingerprintBuilder(symbol=symbol, timeframe=timeframe)
    async for batch in MarketDataRepository(session).iter_candle_provenance_batches(
        symbol,
        parsed_timeframe,
        parsed_start,
        parsed_end,
        source_ids,
        batch_size=_VERIFY_BATCH_SIZE,
        max_rows=min(expected_count + 1, MAX_VERIFY_CANDLES),
    ):
        for candle, source_id in batch:
            builder.add(candle, source_id)
    observed = builder.build()

    common = {
        "expected_fingerprint": expected_fingerprint,
        "observed_fingerprint": observed.fingerprint,
        "expected_candle_count": expected_count,
        "observed_candle_count": observed.candle_count,
        "version": version,
        "source_ids": source_ids,
    }
    if observed.candle_count != expected_count:
        return _changed(
            f"recorded selection has {observed.candle_count} candles, manifest has "
            f"{expected_count}",
            **common,
        )
    if observed.fingerprint != expected_fingerprint:
        return _changed("candle content or source identity differs from the manifest", **common)
    return DatasetVerification(
        status="verified",
        expected_fingerprint=expected_fingerprint,
        observed_fingerprint=observed.fingerprint,
        expected_candle_count=expected_count,
        observed_candle_count=observed.candle_count,
        fingerprint_version=version,
        source_ids=source_ids,
        detail="recorded candles match the immutable dataset fingerprint",
    )
