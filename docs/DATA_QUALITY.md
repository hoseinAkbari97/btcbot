# Data Quality Contract

Phase 1 validation runs before PostgreSQL and Parquet persistence. Provider-native raw payloads are
preserved regardless of validation outcome.

## Hard validity rules

A candle is excluded from normalized stores when any hard rule fails:

- `high >= max(open, close)`
- `low <= min(open, close)`
- `high >= low`
- all OHLC prices are positive
- `volume >= 0`
- open and close timestamps are timezone-aware
- open timestamp is UTC and aligned to its timeframe boundary
- close timestamp is later than open timestamp

## Dataset checks

- Original input ordering is checked before sorting.
- Duplicate open timestamps are reported and only the first observation is retained.
- Adjacent timestamps are checked against the exact timeframe interval.
- Missing intervals are counted precisely and reported as a gap.
- Intervals shorter than the timeframe are reported as overlap errors.

`passed` requires zero invalid rows, duplicates, and missing candles. A wrong-order issue is recorded
but normalization can safely sort unique valid candles.

## Anomaly warnings

Suspicious close-to-close moves are detected with a robust median/MAD z-score once at least five
candles exist. These are warnings because a large BTC move can be real. The raw record and warning
allow a researcher to investigate instead of silently deleting a legitimate market event.

## Quality report fields

Every ingestion records:

- symbol, timeframe, source, observed period, and row count
- duplicate, missing, invalid, and anomaly counts
- pass/fail state and structured issue list
- immutable raw capture path
- generated Parquet paths

## Known Phase 1 limits

- Gaps are measured inside the returned range, not before its first or after its last candle.
- Exchange maintenance is reported as missing data but not automatically classified by cause.
- There is no cross-provider price reconciliation yet.
- Parquet part files are immutable but a dataset manifest/checksum registry is a later enhancement.

